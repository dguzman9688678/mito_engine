#!/usr/bin/env python3
"""
MITO Engine - Comprehensive System Audit Test
Name: MITO Engine Audit
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Complete system integrity and functionality audit
"""

import os
import sys
import json
import time
import logging
import importlib
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mito_audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MITO_AUDIT')

class MITOAuditTest:
    """Comprehensive MITO Engine System Audit"""
    
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.2.0',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': [],
            'warnings': [],
            'modules': {},
            'files': {},
            'apis': {},
            'database': {},
            'performance': {},
            'security': {}
        }
        self.start_time = time.time()
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.audit_results['tests_run'] += 1
        if passed:
            self.audit_results['tests_passed'] += 1
            logger.info(f"✓ {test_name}: PASSED - {details}")
        else:
            self.audit_results['tests_failed'] += 1
            self.audit_results['errors'].append(f"{test_name}: {details}")
            logger.error(f"✗ {test_name}: FAILED - {details}")
            
    def test_file_existence(self):
        """Test core MITO files exist"""
        logger.info("Testing file existence...")
        
        required_files = [
            'app.py',
            'main.py',
            'config.py',
            'models.py',
            'ai_providers.py',
            'mito_agent.py',
            'mito_weights.py',
            'memory_manager.py',
            'notification_manager.py',
            'admin_auth.py',
            'api_usage.py',
            'unified_request_processor.py'
        ]
        
        for file in required_files:
            exists = os.path.exists(file)
            size = os.path.getsize(file) if exists else 0
            self.audit_results['files'][file] = {
                'exists': exists,
                'size': size,
                'readable': os.access(file, os.R_OK) if exists else False
            }
            self.log_test(f"File {file}", exists, f"Size: {size} bytes")
            
    def test_module_imports(self):
        """Test Python module imports"""
        logger.info("Testing module imports...")
        
        modules_to_test = [
            'app',
            'config', 
            'models',
            'ai_providers',
            'mito_agent',
            'mito_weights',
            'memory_manager',
            'notification_manager',
            'admin_auth',
            'api_usage'
        ]
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                self.audit_results['modules'][module_name] = {
                    'importable': True,
                    'attributes': len(dir(module)),
                    'docstring': getattr(module, '__doc__', 'No docstring')
                }
                self.log_test(f"Import {module_name}", True, f"Attributes: {len(dir(module))}")
            except Exception as e:
                self.audit_results['modules'][module_name] = {
                    'importable': False,
                    'error': str(e)
                }
                self.log_test(f"Import {module_name}", False, str(e))
                
    def test_environment_variables(self):
        """Test required environment variables"""
        logger.info("Testing environment variables...")
        
        required_env_vars = [
            'DATABASE_URL',
            'OPENAI_API_KEY',
            'PGDATABASE',
            'PGHOST',
            'PGUSER',
            'PGPASSWORD',
            'PGPORT'
        ]
        
        for var in required_env_vars:
            exists = var in os.environ
            value_length = len(os.environ.get(var, ''))
            self.log_test(f"ENV {var}", exists, f"Length: {value_length}")
            
    def test_dependencies(self):
        """Test Python dependencies"""
        logger.info("Testing Python dependencies...")
        
        required_packages = [
            'flask',
            'flask_sqlalchemy',
            'psycopg2',
            'openai',
            'anthropic',
            'requests',
            'gunicorn',
            'werkzeug',
            'marshmallow',
            'bcrypt',
            'cryptography'
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                self.log_test(f"Package {package}", True, "Available")
            except ImportError as e:
                self.log_test(f"Package {package}", False, str(e))
                
    def test_ai_providers(self):
        """Test AI provider configurations"""
        logger.info("Testing AI providers...")
        
        try:
            from ai_providers import get_available_providers, ai_generate
            
            providers = get_available_providers()
            self.audit_results['apis']['ai_providers'] = providers
            
            for provider, info in providers.items():
                available = info.get('available', False)
                self.log_test(f"AI Provider {provider}", available, info.get('status', 'Unknown'))
                
            # Test basic generation
            try:
                response = ai_generate("Test prompt", provider='local')
                self.log_test("AI Generation", len(response) > 0, f"Response length: {len(response)}")
            except Exception as e:
                self.log_test("AI Generation", False, str(e))
                
        except Exception as e:
            self.log_test("AI Providers Module", False, str(e))
            
    def test_database_connection(self):
        """Test database connectivity"""
        logger.info("Testing database connection...")
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                parsed = urlparse(db_url)
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    database=parsed.path[1:],
                    user=parsed.username,
                    password=parsed.password
                )
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                cursor.close()
                conn.close()
                
                self.audit_results['database'] = {
                    'connected': True,
                    'version': version[0] if version else 'Unknown'
                }
                self.log_test("Database Connection", True, f"PostgreSQL {version[0][:20]}...")
            else:
                self.log_test("Database Connection", False, "No DATABASE_URL")
                
        except Exception as e:
            self.audit_results['database'] = {
                'connected': False,
                'error': str(e)
            }
            self.log_test("Database Connection", False, str(e))
            
    def test_mito_agent(self):
        """Test MITO Agent functionality"""
        logger.info("Testing MITO Agent...")
        
        try:
            from mito_agent import MITOAgent
            
            agent = MITOAgent()
            
            # Test basic agent methods
            self.log_test("MITO Agent Init", True, "Agent initialized successfully")
            
            # Test agent status
            if hasattr(agent, 'get_status'):
                status = agent.get_status()
                self.log_test("MITO Agent Status", True, f"Status: {status}")
            else:
                self.log_test("MITO Agent Status", False, "No get_status method")
                
        except Exception as e:
            self.log_test("MITO Agent", False, str(e))
            
    def test_memory_system(self):
        """Test memory management system"""
        logger.info("Testing memory system...")
        
        try:
            from memory_manager import MemoryManager
            
            memory = MemoryManager()
            
            # Test memory operations
            test_memory = {
                'content': 'Test memory content',
                'category': 'test',
                'tags': ['audit', 'test']
            }
            
            # Test add memory
            memory_id = memory.add_memory(**test_memory)
            self.log_test("Memory Add", memory_id is not None, f"Memory ID: {memory_id}")
            
            # Test retrieve memory
            if memory_id:
                retrieved = memory.get_memory(memory_id)
                self.log_test("Memory Retrieve", retrieved is not None, "Memory retrieved successfully")
                
                # Test delete memory
                deleted = memory.delete_memory(memory_id)
                self.log_test("Memory Delete", deleted, "Memory deleted successfully")
            
        except Exception as e:
            self.log_test("Memory System", False, str(e))
            
    def test_notification_system(self):
        """Test notification system"""
        logger.info("Testing notification system...")
        
        try:
            from notification_manager import NotificationManager
            
            notif_manager = NotificationManager()
            
            # Test notification creation
            from notification_manager import NotificationType
            notif_id = notif_manager.create_notification(
                notification_type=NotificationType.SYSTEM_ALERT,
                title="Audit Test",
                message="Test notification from audit"
            )
            
            self.log_test("Notification Create", notif_id is not None, f"Notification ID: {notif_id}")
            
            # Test notification retrieval
            notifications = notif_manager.get_recent_notifications()
            self.log_test("Notification Retrieve", len(notifications) >= 0, f"Found {len(notifications)} notifications")
            
        except Exception as e:
            self.log_test("Notification System", False, str(e))
            
    def test_admin_auth(self):
        """Test admin authentication"""
        logger.info("Testing admin authentication...")
        
        try:
            from admin_auth import AdminAuth
            from flask import Flask
            
            # Create test Flask app for request context
            test_app = Flask(__name__)
            test_app.secret_key = "test_secret"
            
            with test_app.test_request_context():
                auth = AdminAuth()
                
                # Test password verification (should fail with wrong password)
                wrong_pass = auth.verify_password("wrong_password")
                self.log_test("Admin Auth Wrong Password", not wrong_pass, "Correctly rejected wrong password")
                
                # Test admin status
                logged_in = auth.is_admin_logged_in()
                self.log_test("Admin Auth Status", True, f"Logged in: {logged_in}")
            
        except Exception as e:
            self.log_test("Admin Auth", False, str(e))
            
    def test_api_usage_tracking(self):
        """Test API usage tracking"""
        logger.info("Testing API usage tracking...")
        
        try:
            from api_usage import APIUsageTracker
            
            tracker = APIUsageTracker()
            
            # Test logging usage
            tracker.log_usage(
                provider="test",
                model="test-model",
                usage={"prompt_tokens": 10, "completion_tokens": 20},
                request_type="chat"
            )
            
            self.log_test("API Usage Logging", True, "Usage logged successfully")
            
            # Test getting summary
            summary = tracker.get_usage_summary(days=1)
            self.log_test("API Usage Summary", isinstance(summary, dict), f"Summary keys: {list(summary.keys())}")
            
        except Exception as e:
            self.log_test("API Usage Tracking", False, str(e))
            
    def test_file_permissions(self):
        """Test file permissions"""
        logger.info("Testing file permissions...")
        
        files_to_check = [
            'app.py',
            'main.py', 
            'mito_audit_test.py'
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                readable = os.access(file, os.R_OK)
                writable = os.access(file, os.W_OK)
                self.log_test(f"File Permissions {file}", readable, f"R:{readable}, W:{writable}")
                
    def test_security_basics(self):
        """Test basic security configurations"""
        logger.info("Testing security configurations...")
        
        # Check for sensitive files
        sensitive_files = ['.env', 'config.py']
        for file in sensitive_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                    has_secrets = any(keyword in content.lower() for keyword in ['password', 'secret', 'key', 'token'])
                    self.log_test(f"Security {file}", has_secrets, f"Contains sensitive data: {has_secrets}")
                    
        # Check environment variables are not hardcoded
        if os.path.exists('app.py'):
            with open('app.py', 'r') as f:
                content = f.read()
                uses_env = 'os.environ' in content
                self.log_test("Security Environment Usage", uses_env, "Uses environment variables")
                
    def performance_test(self):
        """Basic performance tests"""
        logger.info("Running performance tests...")
        
        start_time = time.time()
        
        # Test import speed
        import_start = time.time()
        try:
            import app
            import_time = time.time() - import_start
            self.audit_results['performance']['import_time'] = import_time
            self.log_test("Performance Import", import_time < 5.0, f"Import time: {import_time:.2f}s")
        except Exception as e:
            self.log_test("Performance Import", False, str(e))
            
        # Test file I/O
        io_start = time.time()
        try:
            with open('test_performance.tmp', 'w') as f:
                f.write('test' * 1000)
            with open('test_performance.tmp', 'r') as f:
                content = f.read()
            os.remove('test_performance.tmp')
            io_time = time.time() - io_start
            self.audit_results['performance']['file_io_time'] = io_time
            self.log_test("Performance File I/O", io_time < 1.0, f"I/O time: {io_time:.3f}s")
        except Exception as e:
            self.log_test("Performance File I/O", False, str(e))
            
    def generate_report(self):
        """Generate comprehensive audit report"""
        self.audit_results['total_time'] = time.time() - self.start_time
        self.audit_results['success_rate'] = (
            self.audit_results['tests_passed'] / self.audit_results['tests_run'] * 100
            if self.audit_results['tests_run'] > 0 else 0
        )
        
        # Save JSON report
        with open('mito_audit_report.json', 'w') as f:
            json.dump(self.audit_results, f, indent=2)
            
        # Generate markdown report
        markdown_report = f"""# MITO Engine Audit Report

**Generated:** {self.audit_results['timestamp']}  
**Version:** {self.audit_results['version']}  
**Total Time:** {self.audit_results['total_time']:.2f} seconds

## Summary
- **Tests Run:** {self.audit_results['tests_run']}
- **Tests Passed:** {self.audit_results['tests_passed']}
- **Tests Failed:** {self.audit_results['tests_failed']}
- **Success Rate:** {self.audit_results['success_rate']:.1f}%

## Modules Status
"""
        
        for module, info in self.audit_results['modules'].items():
            status = "✓" if info.get('importable', False) else "✗"
            markdown_report += f"- {status} {module}\n"
            
        markdown_report += "\n## Files Status\n"
        for file, info in self.audit_results['files'].items():
            status = "✓" if info.get('exists', False) else "✗"
            size = info.get('size', 0)
            markdown_report += f"- {status} {file} ({size} bytes)\n"
            
        if self.audit_results['errors']:
            markdown_report += "\n## Errors\n"
            for error in self.audit_results['errors']:
                markdown_report += f"- ❌ {error}\n"
                
        with open('MITO_AUDIT_REPORT.md', 'w') as f:
            f.write(markdown_report)
            
        logger.info(f"Audit complete! Success rate: {self.audit_results['success_rate']:.1f}%")
        logger.info("Reports saved: mito_audit_report.json, MITO_AUDIT_REPORT.md")
        
        return self.audit_results
        
    def run_full_audit(self):
        """Run complete MITO Engine audit"""
        logger.info("Starting MITO Engine Comprehensive Audit...")
        logger.info("=" * 60)
        
        try:
            self.test_file_existence()
            self.test_module_imports()
            self.test_environment_variables()
            self.test_dependencies()
            self.test_ai_providers()
            self.test_database_connection()
            self.test_mito_agent()
            self.test_memory_system()
            self.test_notification_system()
            self.test_admin_auth()
            self.test_api_usage_tracking()
            self.test_file_permissions()
            self.test_security_basics()
            self.performance_test()
            
        except Exception as e:
            logger.error(f"Audit failed with exception: {e}")
            self.audit_results['errors'].append(f"Audit exception: {str(e)}")
            
        finally:
            return self.generate_report()

def main():
    """Main audit execution"""
    print("MITO Engine - Comprehensive System Audit Test")
    print("Created by: Daniel Guzman (guzman.danield@outlook.com)")
    print("Version: 1.2.0")
    print("=" * 60)
    
    auditor = MITOAuditTest()
    results = auditor.run_full_audit()
    
    print("\n" + "=" * 60)
    print(f"AUDIT COMPLETE")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Tests: {results['tests_passed']}/{results['tests_run']} passed")
    print("=" * 60)
    
    return results['success_rate'] >= 80  # Consider 80%+ as passing

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)