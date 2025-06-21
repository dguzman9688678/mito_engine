"""
MITO Engine - Compliance & Developer Tools
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: GPG signatures, immutable logs, API explorer, and developer tools
"""

import os
import sqlite3
import hashlib
import json
import gnupg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography import x509
from cryptography.x509.oid import ExtensionOID, NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import yaml
from flask import Flask
from flask_restx import Api, Resource, fields
import subprocess

logger = logging.getLogger(__name__)

class ImmutableLogManager:
    """Write-once immutable audit log system"""
    
    def __init__(self, log_path: str = "immutable_audit.log"):
        self.log_path = log_path
        self.hash_chain = []
        self.init_log_chain()
        
    def init_log_chain(self):
        """Initialize or load existing hash chain"""
        try:
            if os.path.exists(self.log_path):
                # Load existing log and rebuild hash chain
                with open(self.log_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if 'hash' in entry:
                                self.hash_chain.append(entry['hash'])
                        except json.JSONDecodeError:
                            continue
            else:
                # Create genesis block
                genesis_hash = self._calculate_hash("MITO_GENESIS_BLOCK", "")
                self.hash_chain.append(genesis_hash)
                self._write_entry({
                    'type': 'GENESIS',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': 'MITO Engine Immutable Log Initialized',
                    'hash': genesis_hash,
                    'previous_hash': ''
                })
                
        except Exception as e:
            logger.error(f"Failed to initialize immutable log: {e}")
            
    def _calculate_hash(self, data: str, previous_hash: str) -> str:
        """Calculate SHA-256 hash for log entry"""
        content = f"{data}{previous_hash}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    def _write_entry(self, entry: Dict[str, Any]):
        """Write entry to immutable log file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            logger.error(f"Failed to write immutable log entry: {e}")
            
    def add_entry(self, entry_type: str, data: Dict[str, Any], user_id: str = None) -> str:
        """Add new immutable log entry"""
        try:
            previous_hash = self.hash_chain[-1] if self.hash_chain else ""
            entry_data = json.dumps(data, sort_keys=True)
            new_hash = self._calculate_hash(entry_data, previous_hash)
            
            log_entry = {
                'type': entry_type,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'data': data,
                'hash': new_hash,
                'previous_hash': previous_hash,
                'entry_number': len(self.hash_chain)
            }
            
            self._write_entry(log_entry)
            self.hash_chain.append(new_hash)
            
            return new_hash
            
        except Exception as e:
            logger.error(f"Failed to add immutable log entry: {e}")
            return ""
            
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire log chain"""
        try:
            verification_results = {
                'is_valid': True,
                'total_entries': 0,
                'corrupted_entries': [],
                'verification_timestamp': datetime.utcnow().isoformat()
            }
            
            with open(self.log_path, 'r') as f:
                previous_hash = ""
                entry_number = 0
                
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        verification_results['total_entries'] += 1
                        
                        # Verify hash chain
                        if entry.get('previous_hash') != previous_hash:
                            verification_results['is_valid'] = False
                            verification_results['corrupted_entries'].append({
                                'entry_number': entry_number,
                                'reason': 'Invalid previous hash',
                                'expected': previous_hash,
                                'actual': entry.get('previous_hash')
                            })
                            
                        # Verify entry hash
                        expected_hash = self._calculate_hash(
                            json.dumps(entry.get('data', {}), sort_keys=True),
                            entry.get('previous_hash', '')
                        )
                        
                        if entry.get('hash') != expected_hash:
                            verification_results['is_valid'] = False
                            verification_results['corrupted_entries'].append({
                                'entry_number': entry_number,
                                'reason': 'Invalid entry hash',
                                'expected': expected_hash,
                                'actual': entry.get('hash')
                            })
                            
                        previous_hash = entry.get('hash', '')
                        entry_number += 1
                        
                    except json.JSONDecodeError:
                        verification_results['is_valid'] = False
                        verification_results['corrupted_entries'].append({
                            'entry_number': entry_number,
                            'reason': 'Invalid JSON format'
                        })
                        entry_number += 1
                        
            return verification_results
            
        except Exception as e:
            logger.error(f"Failed to verify chain integrity: {e}")
            return {'is_valid': False, 'error': str(e)}

class GPGManager:
    """GPG signature management for audit trails"""
    
    def __init__(self, gnupghome: str = None):
        self.gnupghome = gnupghome or os.path.expanduser('~/.gnupg')
        self.gpg = gnupg.GPG(homedir=self.gnupghome)
        
    def generate_key_pair(self, name: str, email: str, passphrase: str = None) -> Dict[str, Any]:
        """Generate GPG key pair for signing"""
        try:
            input_data = self.gpg.gen_key_input(
                name_real=name,
                name_email=email,
                expire_date='2y',
                key_length=4096,
                passphrase=passphrase or ''
            )
            
            key = self.gpg.gen_key(input_data)
            
            if key.status == 'ok':
                return {
                    'success': True,
                    'fingerprint': str(key.fingerprint),
                    'key_id': str(key.fingerprint)[-8:],
                    'status': key.status
                }
            else:
                return {
                    'success': False,
                    'error': key.status,
                    'stderr': key.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to generate GPG key: {e}")
            return {'success': False, 'error': str(e)}
            
    def sign_data(self, data: str, key_id: str = None, passphrase: str = None) -> Dict[str, Any]:
        """Sign data with GPG key"""
        try:
            signed_data = self.gpg.sign(data, keyid=key_id, passphrase=passphrase)
            
            if signed_data.status == 'signature created':
                return {
                    'success': True,
                    'signature': str(signed_data),
                    'fingerprint': signed_data.fingerprint,
                    'key_id': signed_data.key_id,
                    'status': signed_data.status
                }
            else:
                return {
                    'success': False,
                    'error': signed_data.status,
                    'stderr': signed_data.stderr
                }
                
        except Exception as e:
            logger.error(f"Failed to sign data: {e}")
            return {'success': False, 'error': str(e)}
            
    def verify_signature(self, signed_data: str) -> Dict[str, Any]:
        """Verify GPG signature"""
        try:
            verified = self.gpg.verify(signed_data)
            
            return {
                'valid': verified.valid,
                'fingerprint': verified.fingerprint,
                'key_id': verified.key_id,
                'username': verified.username,
                'timestamp': verified.timestamp,
                'status': verified.status,
                'trust_level': verified.trust_level
            }
            
        except Exception as e:
            logger.error(f"Failed to verify signature: {e}")
            return {'valid': False, 'error': str(e)}
            
    def export_public_key(self, key_id: str) -> str:
        """Export public key for sharing"""
        try:
            public_key = self.gpg.export_keys(key_id)
            return public_key
        except Exception as e:
            logger.error(f"Failed to export public key: {e}")
            return ""

class X509CertManager:
    """X.509 certificate chain validation"""
    
    def __init__(self):
        pass
        
    def create_self_signed_cert(self, common_name: str, organization: str = "MITO Engine") -> Dict[str, Any]:
        """Create self-signed certificate for MITO Engine"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("*.mito.local"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Serialize certificate and key
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            return {
                'success': True,
                'certificate': cert_pem.decode(),
                'private_key': key_pem.decode(),
                'fingerprint': hashlib.sha256(cert_pem).hexdigest(),
                'valid_from': cert.not_valid_before.isoformat(),
                'valid_until': cert.not_valid_after.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            return {'success': False, 'error': str(e)}
            
    def validate_cert_chain(self, cert_pem: str, ca_cert_pem: str = None) -> Dict[str, Any]:
        """Validate X.509 certificate chain"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            validation_result = {
                'valid': True,
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'serial_number': str(cert.serial_number),
                'not_valid_before': cert.not_valid_before.isoformat(),
                'not_valid_after': cert.not_valid_after.isoformat(),
                'is_expired': datetime.utcnow() > cert.not_valid_after,
                'extensions': []
            }
            
            # Check extensions
            for extension in cert.extensions:
                validation_result['extensions'].append({
                    'oid': extension.oid.dotted_string,
                    'critical': extension.critical,
                    'value': str(extension.value)
                })
                
            # Validate against CA if provided
            if ca_cert_pem:
                ca_cert = x509.load_pem_x509_certificate(ca_cert_pem.encode())
                # Basic validation - in production would use proper chain validation
                validation_result['ca_validated'] = cert.issuer == ca_cert.subject
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate certificate: {e}")
            return {'valid': False, 'error': str(e)}

class APIExplorer:
    """Embedded API documentation and exploration tool"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.api = Api(app, version='1.0', title='MITO Engine API',
                      description='Comprehensive AI Development Platform API',
                      doc='/api/docs/')
        self.setup_api_models()
        
    def setup_api_models(self):
        """Define API models for documentation"""
        # Session models
        self.session_model = self.api.model('Session', {
            'session_id': fields.String(required=True, description='Unique session identifier'),
            'user_id': fields.String(description='User identifier'),
            'tab_states': fields.Raw(description='Tab state data'),
            'workspace_state': fields.Raw(description='Workspace configuration')
        })
        
        # Profile models
        self.profile_model = self.api.model('UserProfile', {
            'role': fields.String(required=True, description='User role (developer, operations, analyst, admin)'),
            'permissions': fields.List(fields.String, description='List of permissions'),
            'layout': fields.Raw(description='Custom layout preferences'),
            'theme': fields.Raw(description='Theme preferences')
        })
        
        # Audit models
        self.audit_entry_model = self.api.model('AuditEntry', {
            'timestamp': fields.DateTime(description='Action timestamp'),
            'action_type': fields.String(required=True, description='Type of action performed'),
            'action_details': fields.String(description='Detailed description of action'),
            'tab_context': fields.String(description='Tab where action occurred'),
            'user_id': fields.String(description='User who performed action')
        })
        
        # Network models
        self.network_interface_model = self.api.model('NetworkInterface', {
            'name': fields.String(required=True, description='Interface name'),
            'is_up': fields.Boolean(description='Interface status'),
            'addresses': fields.List(fields.Raw, description='IP addresses')
        })
        
        # System metrics
        self.system_metrics_model = self.api.model('SystemMetrics', {
            'cpu_usage': fields.Float(description='CPU usage percentage'),
            'memory_usage': fields.Float(description='Memory usage percentage'),
            'disk_usage': fields.Float(description='Disk usage percentage'),
            'network_io': fields.Raw(description='Network I/O statistics'),
            'timestamp': fields.DateTime(description='Metrics timestamp')
        })
        
    def register_endpoints(self):
        """Register documented API endpoints"""
        
        @self.api.route('/session/state')
        class SessionState(Resource):
            @self.api.doc('get_session_state')
            @self.api.marshal_with(self.session_model)
            def get(self):
                """Get current session state"""
                pass
                
            @self.api.doc('update_session_state')
            @self.api.expect(self.session_model)
            def post(self):
                """Update session state"""
                pass
                
        @self.api.route('/profile')
        class UserProfile(Resource):
            @self.api.doc('get_user_profile')
            @self.api.marshal_with(self.profile_model)
            def get(self):
                """Get user profile and permissions"""
                pass
                
            @self.api.doc('update_user_profile')
            @self.api.expect(self.profile_model)
            def post(self):
                """Update user profile"""
                pass
                
        @self.api.route('/audit/log')
        class AuditLog(Resource):
            @self.api.doc('get_audit_log')
            @self.api.marshal_list_with(self.audit_entry_model)
            def get(self):
                """Get audit trail entries"""
                pass
                
        @self.api.route('/network/interfaces')
        class NetworkInterfaces(Resource):
            @self.api.doc('get_network_interfaces')
            @self.api.marshal_list_with(self.network_interface_model)
            def get(self):
                """Get network interface information"""
                pass
                
        @self.api.route('/telemetry/metrics')
        class SystemMetrics(Resource):
            @self.api.doc('get_system_metrics')
            @self.api.marshal_with(self.system_metrics_model)
            def get(self):
                """Get real-time system metrics"""
                pass

class WorkspaceManager:
    """Template and workspace cloning system"""
    
    def __init__(self, templates_path: str = "workspace_templates"):
        self.templates_path = templates_path
        self.init_templates_directory()
        
    def init_templates_directory(self):
        """Initialize templates directory structure"""
        try:
            os.makedirs(self.templates_path, exist_ok=True)
            
            # Create default template categories
            categories = ['web-development', 'data-science', 'devops', 'api-development']
            for category in categories:
                os.makedirs(os.path.join(self.templates_path, category), exist_ok=True)
                
        except Exception as e:
            logger.error(f"Failed to initialize templates directory: {e}")
            
    def create_template(self, name: str, category: str, description: str, 
                       files: Dict[str, str], metadata: Dict[str, Any] = None) -> bool:
        """Create new workspace template"""
        try:
            template_dir = os.path.join(self.templates_path, category, name)
            os.makedirs(template_dir, exist_ok=True)
            
            # Save template files
            for filename, content in files.items():
                filepath = os.path.join(template_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            # Save template metadata
            template_metadata = {
                'name': name,
                'category': category,
                'description': description,
                'created_at': datetime.utcnow().isoformat(),
                'files': list(files.keys()),
                'metadata': metadata or {}
            }
            
            with open(os.path.join(template_dir, 'template.json'), 'w') as f:
                json.dump(template_metadata, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template {name}: {e}")
            return False
            
    def clone_workspace(self, template_name: str, category: str, target_name: str) -> Dict[str, Any]:
        """Clone workspace from template"""
        try:
            template_dir = os.path.join(self.templates_path, category, template_name)
            target_dir = os.path.join('workspaces', target_name)
            
            if not os.path.exists(template_dir):
                return {'success': False, 'error': 'Template not found'}
                
            # Copy template files
            import shutil
            shutil.copytree(template_dir, target_dir, dirs_exist_ok=True)
            
            # Update workspace metadata
            workspace_metadata = {
                'name': target_name,
                'cloned_from': template_name,
                'category': category,
                'created_at': datetime.utcnow().isoformat(),
                'last_modified': datetime.utcnow().isoformat()
            }
            
            with open(os.path.join(target_dir, 'workspace.json'), 'w') as f:
                json.dump(workspace_metadata, f, indent=2)
                
            return {
                'success': True,
                'workspace_path': target_dir,
                'template_used': template_name,
                'files_created': len(os.listdir(target_dir))
            }
            
        except Exception as e:
            logger.error(f"Failed to clone workspace: {e}")
            return {'success': False, 'error': str(e)}
            
    def list_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """List available workspace templates"""
        try:
            templates = {}
            
            for category in os.listdir(self.templates_path):
                category_path = os.path.join(self.templates_path, category)
                if os.path.isdir(category_path):
                    templates[category] = []
                    
                    for template_name in os.listdir(category_path):
                        template_path = os.path.join(category_path, template_name)
                        metadata_file = os.path.join(template_path, 'template.json')
                        
                        if os.path.exists(metadata_file):
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                                templates[category].append(metadata)
                                
            return templates
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return {}

class WebhookManager:
    """Webhook system for automation and CI/CD integration"""
    
    def __init__(self, db_path: str = "mito_webhooks.db"):
        self.db_path = db_path
        self.init_webhooks_db()
        
    def init_webhooks_db(self):
        """Initialize webhooks database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    events TEXT NOT NULL,
                    secret TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    webhook_id INTEGER,
                    event_type TEXT NOT NULL,
                    payload TEXT,
                    response_status INTEGER,
                    response_body TEXT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks (id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize webhooks database: {e}")
            
    def register_webhook(self, name: str, url: str, events: List[str], secret: str = None) -> bool:
        """Register new webhook"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO webhooks (name, url, events, secret) 
                VALUES (?, ?, ?, ?)
            """, (name, url, json.dumps(events), secret))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register webhook {name}: {e}")
            return False
            
    def trigger_webhooks(self, event_type: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger webhooks for specific event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, url, secret FROM webhooks 
                WHERE enabled = 1 AND events LIKE ?
            """, (f'%{event_type}%',))
            
            results = []
            
            for webhook_id, name, url, secret in cursor.fetchall():
                try:
                    # Trigger webhook
                    import requests
                    import hmac
                    
                    headers = {'Content-Type': 'application/json'}
                    
                    # Add signature if secret provided
                    if secret:
                        signature = hmac.new(
                            secret.encode(),
                            json.dumps(payload).encode(),
                            hashlib.sha256
                        ).hexdigest()
                        headers['X-MITO-Signature'] = f'sha256={signature}'
                        
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    
                    # Log webhook trigger
                    cursor.execute("""
                        INSERT INTO webhook_logs 
                        (webhook_id, event_type, payload, response_status, response_body) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (webhook_id, event_type, json.dumps(payload), 
                          response.status_code, response.text[:1000]))
                    
                    # Update webhook stats
                    cursor.execute("""
                        UPDATE webhooks 
                        SET last_triggered = CURRENT_TIMESTAMP, trigger_count = trigger_count + 1 
                        WHERE id = ?
                    """, (webhook_id,))
                    
                    results.append({
                        'webhook': name,
                        'success': response.status_code < 400,
                        'status_code': response.status_code,
                        'response': response.text[:100]
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to trigger webhook {name}: {e}")
                    results.append({
                        'webhook': name,
                        'success': False,
                        'error': str(e)
                    })
                    
            conn.commit()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to trigger webhooks for {event_type}: {e}")
            return []