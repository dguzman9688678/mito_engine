"""
MITO Engine - Advanced Security Management
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Security, encryption, and access control systems
"""

import os
import jwt
import pyotp
import qrcode
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sqlite3
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import session, request
import json

logger = logging.getLogger(__name__)

class SecretVault:
    """Encrypted secrets management system"""
    
    def __init__(self, vault_path: str = "mito_vault.db"):
        self.vault_path = vault_path
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
        self.init_vault_db()
        
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        key_file = "vault_master.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read-only for owner
            return key
            
    def init_vault_db(self):
        """Initialize encrypted vault database"""
        try:
            conn = sqlite3.connect(self.vault_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    encrypted_value BLOB NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    secret_name TEXT,
                    user_id TEXT,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    success BOOLEAN
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Secret vault initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize vault: {e}")
            
    def store_secret(self, name: str, value: str, description: str = "", tags: List[str] = None) -> bool:
        """Store encrypted secret"""
        try:
            encrypted_value = self.cipher.encrypt(value.encode())
            tags_str = json.dumps(tags) if tags else ""
            
            conn = sqlite3.connect(self.vault_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO secrets 
                (name, encrypted_value, description, tags) 
                VALUES (?, ?, ?, ?)
            """, (name, encrypted_value, description, tags_str))
            
            conn.commit()
            conn.close()
            
            self._log_access(name, "store", True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret {name}: {e}")
            self._log_access(name, "store", False)
            return False
            
    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve and decrypt secret"""
        try:
            conn = sqlite3.connect(self.vault_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT encrypted_value FROM secrets WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                # Update access statistics
                cursor.execute("""
                    UPDATE secrets 
                    SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1 
                    WHERE name = ?
                """, (name,))
                conn.commit()
                
                decrypted_value = self.cipher.decrypt(result[0]).decode()
                self._log_access(name, "retrieve", True)
                conn.close()
                return decrypted_value
            
            conn.close()
            self._log_access(name, "retrieve", False)
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {name}: {e}")
            self._log_access(name, "retrieve", False)
            return None
            
    def list_secrets(self) -> List[Dict[str, Any]]:
        """List all secrets (without values)"""
        try:
            conn = sqlite3.connect(self.vault_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, description, created_at, accessed_at, access_count, tags 
                FROM secrets ORDER BY name
            """)
            
            secrets = []
            for row in cursor.fetchall():
                secrets.append({
                    'name': row[0],
                    'description': row[1],
                    'created_at': row[2],
                    'accessed_at': row[3],
                    'access_count': row[4],
                    'tags': json.loads(row[5]) if row[5] else []
                })
            
            conn.close()
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []
            
    def _log_access(self, secret_name: str, action: str, success: bool):
        """Log secret access"""
        try:
            conn = sqlite3.connect(self.vault_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO access_log 
                (secret_name, user_id, action, ip_address, success) 
                VALUES (?, ?, ?, ?, ?)
            """, (
                secret_name,
                session.get('user_id', 'anonymous') if 'session' in globals() else 'system',
                action,
                request.remote_addr if 'request' in globals() and request else 'localhost',
                success
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log access: {e}")

class TwoFactorAuth:
    """Two-factor authentication system"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        self.init_2fa_db()
        
    def init_2fa_db(self):
        """Initialize 2FA database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_2fa (
                    user_id TEXT PRIMARY KEY,
                    secret_key TEXT NOT NULL,
                    backup_codes TEXT,
                    enabled BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize 2FA database: {e}")
            
    def setup_2fa(self, user_id: str) -> Dict[str, Any]:
        """Set up 2FA for user"""
        try:
            secret = pyotp.random_base32()
            backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_id,
                issuer_name="MITO Engine"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Convert QR code to base64 image
            from io import BytesIO
            qr_img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            qr_code_b64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Store in database (not enabled yet)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_2fa 
                (user_id, secret_key, backup_codes, enabled) 
                VALUES (?, ?, ?, 0)
            """, (user_id, secret, json.dumps(backup_codes)))
            
            conn.commit()
            conn.close()
            
            return {
                'secret': secret,
                'qr_code': qr_code_b64,
                'backup_codes': backup_codes,
                'setup_complete': False
            }
            
        except Exception as e:
            logger.error(f"Failed to setup 2FA for {user_id}: {e}")
            return {}
            
    def verify_2fa(self, user_id: str, token: str) -> bool:
        """Verify 2FA token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT secret_key, backup_codes FROM user_2fa WHERE user_id = ? AND enabled = 1", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
                
            secret_key, backup_codes_str = result
            backup_codes = json.loads(backup_codes_str) if backup_codes_str else []
            
            # Verify TOTP token
            totp = pyotp.TOTP(secret_key)
            if totp.verify(token, valid_window=1):
                # Update last used
                cursor.execute("UPDATE user_2fa SET last_used = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                return True
                
            # Check backup codes
            if token in backup_codes:
                backup_codes.remove(token)
                cursor.execute("UPDATE user_2fa SET backup_codes = ?, last_used = CURRENT_TIMESTAMP WHERE user_id = ?", 
                             (json.dumps(backup_codes), user_id))
                conn.commit()
                conn.close()
                return True
                
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify 2FA for {user_id}: {e}")
            return False
            
    def enable_2fa(self, user_id: str, verification_token: str) -> bool:
        """Enable 2FA after verification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT secret_key FROM user_2fa WHERE user_id = ? AND enabled = 0", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
                
            secret_key = result[0]
            totp = pyotp.TOTP(secret_key)
            
            if totp.verify(verification_token, valid_window=1):
                cursor.execute("UPDATE user_2fa SET enabled = 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                return True
                
            conn.close()
            return False
            
        except Exception as e:
            logger.error(f"Failed to enable 2FA for {user_id}: {e}")
            return False

class RBACManager:
    """Role-Based Access Control with detailed logging"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        self.init_rbac_db()
        
        # Define permission hierarchy
        self.permissions = {
            'read_dashboard': ['analyst', 'developer', 'operations', 'admin'],
            'read_analytics': ['analyst', 'developer', 'operations', 'admin'],
            'read_audit': ['operations', 'admin'],
            'write_code': ['developer', 'admin'],
            'execute_shell': ['developer', 'operations', 'admin'],
            'manage_networking': ['operations', 'admin'],
            'manage_secrets': ['admin'],
            'manage_users': ['admin'],
            'system_admin': ['admin']
        }
        
    def init_rbac_db(self):
        """Initialize RBAC database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rbac_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    permission TEXT NOT NULL,
                    resource TEXT,
                    action TEXT NOT NULL,
                    granted BOOLEAN NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    context TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize RBAC database: {e}")
            
    def check_permission(self, user_id: str, user_role: str, permission: str, resource: str = None) -> bool:
        """Check if user has permission and log the access"""
        try:
            has_permission = user_role in self.permissions.get(permission, [])
            
            # Log the access attempt
            self._log_rbac_access(user_id, user_role, permission, resource, 'check', has_permission)
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Failed to check permission {permission} for {user_id}: {e}")
            self._log_rbac_access(user_id, user_role, permission, resource, 'check', False)
            return False
            
    def require_permission(self, permission: str, resource: str = None):
        """Decorator to require permission for routes"""
        def decorator(f):
            def wrapper(*args, **kwargs):
                user_id = session.get('user_id', 'anonymous')
                user_role = session.get('user_role', 'guest')
                
                if not self.check_permission(user_id, user_role, permission, resource):
                    self._log_rbac_access(user_id, user_role, permission, resource, 'denied', False)
                    return {'error': 'Access denied', 'required_permission': permission}, 403
                    
                self._log_rbac_access(user_id, user_role, permission, resource, 'granted', True)
                return f(*args, **kwargs)
            return wrapper
        return decorator
        
    def _log_rbac_access(self, user_id: str, role: str, permission: str, resource: str, action: str, granted: bool):
        """Log RBAC access attempt"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO rbac_log 
                (user_id, role, permission, resource, action, granted, ip_address, user_agent, context) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, role, permission, resource, action, granted,
                request.remote_addr if 'request' in globals() and request else 'localhost',
                request.headers.get('User-Agent') if 'request' in globals() and request else 'system',
                json.dumps({'session_id': session.get('mito_session_id')}) if 'session' in globals() else '{}'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log RBAC access: {e}")
            
    def get_rbac_audit_log(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get RBAC audit log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM rbac_log 
                WHERE timestamp >= datetime('now', '-{} days') 
                ORDER BY timestamp DESC 
                LIMIT 1000
            """.format(days))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get RBAC audit log: {e}")
            return []

class TokenManager:
    """JWT token management for API access"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.environ.get('JWT_SECRET', 'mito-default-secret-change-in-production')
        
    def generate_token(self, user_id: str, role: str, permissions: List[str] = None, expires_hours: int = 24) -> str:
        """Generate JWT token"""
        try:
            payload = {
                'user_id': user_id,
                'role': role,
                'permissions': permissions or [],
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=expires_hours),
                'iss': 'mito-engine'
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate token for {user_id}: {e}")
            return None
            
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None
            
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh JWT token if valid"""
        payload = self.verify_token(token)
        if payload:
            return self.generate_token(
                payload['user_id'], 
                payload['role'], 
                payload.get('permissions', [])
            )
        return None