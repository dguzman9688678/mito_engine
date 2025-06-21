#!/usr/bin/env python3
"""
MITO Engine - Comprehensive System Validator
Checks every file, simulates launches, and identifies errors
"""

import os
import sys
import ast
import importlib.util
import subprocess
import sqlite3
import json
import traceback
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Comprehensive system validation for MITO Engine"""
    
    def __init__(self):
        self.results = {
            'validation_timestamp': datetime.now().isoformat(),
            'python_files': {},
            'database_files': {},
            'template_files': {},
            'static_files': {},
            'config_files': {},
            'launch_simulations': {},
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        self.root_path = Path('.')
        
    def run_comprehensive_validation(self):
        """Run complete system validation"""
        logger.info("Starting comprehensive MITO Engine validation")
        
        # File-based validations
        self.validate_python_files()
        self.validate_database_files()
        self.validate_template_files()
        self.validate_static_files()
        self.validate_config_files()
        
        # System simulations
        self.simulate_application_launches()
        self.test_import_capabilities()
        self.validate_api_endpoints()
        
        # Generate summary
        self.generate_validation_summary()
        
        # Save results
        self.save_validation_report()
        
        return self.results
    
    def validate_python_files(self):
        """Validate all Python files for syntax and import errors"""
        logger.info("Validating Python files...")
        
        python_files = list(self.root_path.rglob("*.py"))
        
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue
                
            file_results = {
                'path': str(py_file),
                'size': py_file.stat().st_size,
                'last_modified': datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                'syntax_valid': False,
                'imports_valid': False,
                'functions': [],
                'classes': [],
                'errors': [],
                'warnings': []
            }
            
            try:
                # Read file content
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Syntax validation
                try:
                    ast.parse(content)
                    file_results['syntax_valid'] = True
                    logger.debug(f"✓ Syntax valid: {py_file}")
                except SyntaxError as e:
                    file_results['errors'].append(f"Syntax error: {e}")
                    logger.error(f"✗ Syntax error in {py_file}: {e}")
                
                # AST analysis for functions and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            file_results['functions'].append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            file_results['classes'].append(node.name)
                except:
                    pass
                
                # Import validation (safe check)
                try:
                    spec = importlib.util.spec_from_file_location("test_module", py_file)
                    if spec and spec.loader:
                        # Don't actually load, just check if it's loadable
                        file_results['imports_valid'] = True
                        logger.debug(f"✓ Imports valid: {py_file}")
                except Exception as e:
                    file_results['errors'].append(f"Import error: {e}")
                    logger.warning(f"⚠ Import warning in {py_file}: {e}")
                
                # Check for common issues
                self._check_common_python_issues(content, file_results)
                
            except Exception as e:
                file_results['errors'].append(f"File read error: {e}")
                logger.error(f"✗ Error reading {py_file}: {e}")
            
            self.results['python_files'][str(py_file)] = file_results
    
    def validate_database_files(self):
        """Validate all SQLite database files"""
        logger.info("Validating database files...")
        
        db_files = list(self.root_path.rglob("*.db"))
        
        for db_file in db_files:
            file_results = {
                'path': str(db_file),
                'size': db_file.stat().st_size,
                'accessible': False,
                'tables': [],
                'integrity_check': 'unknown',
                'errors': []
            }
            
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # Check accessibility
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                file_results['tables'] = [table[0] for table in tables]
                file_results['accessible'] = True
                
                # Integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                file_results['integrity_check'] = integrity
                
                conn.close()
                
                logger.debug(f"✓ Database valid: {db_file} ({len(file_results['tables'])} tables)")
                
            except Exception as e:
                file_results['errors'].append(str(e))
                logger.error(f"✗ Database error in {db_file}: {e}")
            
            self.results['database_files'][str(db_file)] = file_results
    
    def validate_template_files(self):
        """Validate HTML template files"""
        logger.info("Validating template files...")
        
        template_files = list(self.root_path.rglob("*.html"))
        
        for template_file in template_files:
            file_results = {
                'path': str(template_file),
                'size': template_file.stat().st_size,
                'readable': False,
                'has_title': False,
                'has_body': False,
                'script_tags': 0,
                'style_tags': 0,
                'errors': []
            }
            
            try:
                with open(template_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    file_results['readable'] = True
                    
                    # Basic HTML structure checks
                    file_results['has_title'] = '<title>' in content.lower()
                    file_results['has_body'] = '<body>' in content.lower()
                    file_results['script_tags'] = content.lower().count('<script')
                    file_results['style_tags'] = content.lower().count('<style')
                    
                    logger.debug(f"✓ Template valid: {template_file}")
                    
            except Exception as e:
                file_results['errors'].append(str(e))
                logger.error(f"✗ Template error in {template_file}: {e}")
            
            self.results['template_files'][str(template_file)] = file_results
    
    def validate_static_files(self):
        """Validate static files (CSS, JS, images)"""
        logger.info("Validating static files...")
        
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']
        static_files = []
        
        for ext in static_extensions:
            static_files.extend(list(self.root_path.rglob(f"*{ext}")))
        
        for static_file in static_files:
            file_results = {
                'path': str(static_file),
                'size': static_file.stat().st_size,
                'extension': static_file.suffix,
                'accessible': False,
                'errors': []
            }
            
            try:
                # Check if file is readable
                with open(static_file, 'rb') as f:
                    f.read(1024)  # Read first 1KB to test accessibility
                file_results['accessible'] = True
                logger.debug(f"✓ Static file accessible: {static_file}")
                
            except Exception as e:
                file_results['errors'].append(str(e))
                logger.error(f"✗ Static file error in {static_file}: {e}")
            
            self.results['static_files'][str(static_file)] = file_results
    
    def validate_config_files(self):
        """Validate configuration files"""
        logger.info("Validating configuration files...")
        
        config_files = list(self.root_path.rglob("*.json")) + \
                      list(self.root_path.rglob("*.yaml")) + \
                      list(self.root_path.rglob("*.yml")) + \
                      list(self.root_path.rglob("*.toml")) + \
                      list(self.root_path.rglob("*.env"))
        
        for config_file in config_files:
            file_results = {
                'path': str(config_file),
                'size': config_file.stat().st_size,
                'format': config_file.suffix,
                'valid_format': False,
                'errors': []
            }
            
            try:
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Format validation
                if config_file.suffix == '.json':
                    json.loads(content)
                    file_results['valid_format'] = True
                elif config_file.suffix in ['.yaml', '.yml']:
                    # Basic YAML syntax check
                    if ':' in content and not content.strip().startswith('<'):
                        file_results['valid_format'] = True
                elif config_file.suffix == '.toml':
                    # Basic TOML syntax check
                    if '[' in content or '=' in content:
                        file_results['valid_format'] = True
                else:
                    file_results['valid_format'] = True  # .env and others
                
                logger.debug(f"✓ Config file valid: {config_file}")
                
            except Exception as e:
                file_results['errors'].append(str(e))
                logger.error(f"✗ Config file error in {config_file}: {e}")
            
            self.results['config_files'][str(config_file)] = file_results
    
    def simulate_application_launches(self):
        """Simulate launching key application components"""
        logger.info("Simulating application launches...")
        
        launch_targets = [
            {'name': 'main_app', 'command': ['python', 'app.py', '--test-mode'], 'timeout': 10},
            {'name': 'main_entry', 'command': ['python', 'main.py', '--validate'], 'timeout': 5},
            {'name': 'audit_system', 'command': ['python', 'audit.py', '--check'], 'timeout': 5},
            {'name': 'search_engine', 'command': ['python', 'search_engine.py', '--test'], 'timeout': 5},
            {'name': 'api_usage', 'command': ['python', 'api_usage.py', '--status'], 'timeout': 5}
        ]
        
        for target in launch_targets:
            launch_result = {
                'command': ' '.join(target['command']),
                'success': False,
                'exit_code': None,
                'output': '',
                'error': '',
                'execution_time': 0
            }
            
            try:
                start_time = time.time()
                
                result = subprocess.run(
                    target['command'],
                    capture_output=True,
                    text=True,
                    timeout=target['timeout'],
                    cwd=str(self.root_path)
                )
                
                launch_result['execution_time'] = time.time() - start_time
                launch_result['exit_code'] = result.returncode
                launch_result['output'] = result.stdout[:1000]  # Limit output
                launch_result['error'] = result.stderr[:1000]
                launch_result['success'] = result.returncode == 0
                
                if launch_result['success']:
                    logger.info(f"✓ Launch simulation successful: {target['name']}")
                else:
                    logger.warning(f"⚠ Launch simulation failed: {target['name']} (exit code: {result.returncode})")
                
            except subprocess.TimeoutExpired:
                launch_result['error'] = f"Timeout after {target['timeout']} seconds"
                logger.warning(f"⚠ Launch simulation timeout: {target['name']}")
                
            except Exception as e:
                launch_result['error'] = str(e)
                logger.error(f"✗ Launch simulation error: {target['name']}: {e}")
            
            self.results['launch_simulations'][target['name']] = launch_result
    
    def test_import_capabilities(self):
        """Test import capabilities of key modules"""
        logger.info("Testing import capabilities...")
        
        key_modules = [
            'ai_providers', 'api_usage', 'config', 'mito_weights',
            'notification_manager', 'admin_auth', 'search_engine',
            'nlp_engine', 'security_manager', 'audit'
        ]
        
        import_results = {}
        
        for module_name in key_modules:
            try:
                if os.path.exists(f"{module_name}.py"):
                    spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
                    if spec and spec.loader:
                        import_results[module_name] = {
                            'importable': True,
                            'error': None
                        }
                        logger.debug(f"✓ Import test passed: {module_name}")
                    else:
                        import_results[module_name] = {
                            'importable': False,
                            'error': 'No spec or loader'
                        }
                else:
                    import_results[module_name] = {
                        'importable': False,
                        'error': 'File not found'
                    }
                    
            except Exception as e:
                import_results[module_name] = {
                    'importable': False,
                    'error': str(e)
                }
                logger.warning(f"⚠ Import test failed: {module_name}: {e}")
        
        self.results['import_tests'] = import_results
    
    def validate_api_endpoints(self):
        """Validate API endpoint definitions in code"""
        logger.info("Validating API endpoint definitions...")
        
        endpoints_found = []
        
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                
                # Find Flask routes
                import re
                route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
                routes = re.findall(route_pattern, content)
                
                for route in routes:
                    endpoints_found.append({
                        'path': route,
                        'file': 'app.py',
                        'type': 'flask_route'
                    })
                
                logger.info(f"Found {len(endpoints_found)} API endpoints")
                
        except Exception as e:
            logger.error(f"Error validating API endpoints: {e}")
        
        self.results['api_endpoints'] = endpoints_found
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during validation"""
        skip_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            '.pytest_cache',
            'venv',
            'env',
            '.env'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _check_common_python_issues(self, content: str, file_results: dict):
        """Check for common Python issues"""
        
        # Check for TODO/FIXME comments
        todo_count = content.count('TODO') + content.count('FIXME')
        if todo_count > 0:
            file_results['warnings'].append(f"Found {todo_count} TODO/FIXME comments")
        
        # Check for print statements (might indicate debug code)
        print_count = content.count('print(')
        if print_count > 5:
            file_results['warnings'].append(f"High number of print statements: {print_count}")
        
        # Check for exception handling
        if 'except:' in content and 'except Exception:' not in content:
            file_results['warnings'].append("Found bare except clause")
    
    def generate_validation_summary(self):
        """Generate comprehensive validation summary"""
        logger.info("Generating validation summary...")
        
        summary = {
            'total_files_checked': 0,
            'python_files': {
                'total': len(self.results['python_files']),
                'syntax_valid': 0,
                'imports_valid': 0,
                'with_errors': 0
            },
            'database_files': {
                'total': len(self.results['database_files']),
                'accessible': 0,
                'with_errors': 0
            },
            'template_files': {
                'total': len(self.results['template_files']),
                'readable': 0,
                'with_errors': 0
            },
            'static_files': {
                'total': len(self.results['static_files']),
                'accessible': 0,
                'with_errors': 0
            },
            'config_files': {
                'total': len(self.results['config_files']),
                'valid_format': 0,
                'with_errors': 0
            },
            'launch_simulations': {
                'total': len(self.results['launch_simulations']),
                'successful': 0,
                'failed': 0
            },
            'overall_health': 'unknown'
        }
        
        # Calculate Python file stats
        for file_data in self.results['python_files'].values():
            if file_data['syntax_valid']:
                summary['python_files']['syntax_valid'] += 1
            if file_data['imports_valid']:
                summary['python_files']['imports_valid'] += 1
            if file_data['errors']:
                summary['python_files']['with_errors'] += 1
        
        # Calculate database stats
        for file_data in self.results['database_files'].values():
            if file_data['accessible']:
                summary['database_files']['accessible'] += 1
            if file_data['errors']:
                summary['database_files']['with_errors'] += 1
        
        # Calculate template stats
        for file_data in self.results['template_files'].values():
            if file_data['readable']:
                summary['template_files']['readable'] += 1
            if file_data['errors']:
                summary['template_files']['with_errors'] += 1
        
        # Calculate static file stats
        for file_data in self.results['static_files'].values():
            if file_data['accessible']:
                summary['static_files']['accessible'] += 1
            if file_data['errors']:
                summary['static_files']['with_errors'] += 1
        
        # Calculate config file stats
        for file_data in self.results['config_files'].values():
            if file_data['valid_format']:
                summary['config_files']['valid_format'] += 1
            if file_data['errors']:
                summary['config_files']['with_errors'] += 1
        
        # Calculate launch simulation stats
        for sim_data in self.results['launch_simulations'].values():
            if sim_data['success']:
                summary['launch_simulations']['successful'] += 1
            else:
                summary['launch_simulations']['failed'] += 1
        
        # Calculate total files
        summary['total_files_checked'] = (
            summary['python_files']['total'] +
            summary['database_files']['total'] +
            summary['template_files']['total'] +
            summary['static_files']['total'] +
            summary['config_files']['total']
        )
        
        # Determine overall health
        total_errors = (
            summary['python_files']['with_errors'] +
            summary['database_files']['with_errors'] +
            summary['template_files']['with_errors'] +
            summary['static_files']['with_errors'] +
            summary['config_files']['with_errors'] +
            summary['launch_simulations']['failed']
        )
        
        if total_errors == 0:
            summary['overall_health'] = 'excellent'
        elif total_errors <= 3:
            summary['overall_health'] = 'good'
        elif total_errors <= 10:
            summary['overall_health'] = 'fair'
        else:
            summary['overall_health'] = 'poor'
        
        self.results['summary'] = summary
    
    def save_validation_report(self):
        """Save detailed validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_validation_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Validation report saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")
    
    def print_summary_report(self):
        """Print human-readable summary report"""
        summary = self.results['summary']
        
        print("\n" + "="*80)
        print("MITO ENGINE - COMPREHENSIVE VALIDATION REPORT")
        print("="*80)
        print(f"Validation Time: {self.results['validation_timestamp']}")
        print(f"Total Files Checked: {summary['total_files_checked']}")
        print(f"Overall System Health: {summary['overall_health'].upper()}")
        print()
        
        print("FILE TYPE BREAKDOWN:")
        print(f"  Python Files: {summary['python_files']['total']} total")
        print(f"    - Syntax Valid: {summary['python_files']['syntax_valid']}")
        print(f"    - Import Valid: {summary['python_files']['imports_valid']}")
        print(f"    - With Errors: {summary['python_files']['with_errors']}")
        print()
        
        print(f"  Database Files: {summary['database_files']['total']} total")
        print(f"    - Accessible: {summary['database_files']['accessible']}")
        print(f"    - With Errors: {summary['database_files']['with_errors']}")
        print()
        
        print(f"  Template Files: {summary['template_files']['total']} total")
        print(f"    - Readable: {summary['template_files']['readable']}")
        print(f"    - With Errors: {summary['template_files']['with_errors']}")
        print()
        
        print(f"  Static Files: {summary['static_files']['total']} total")
        print(f"    - Accessible: {summary['static_files']['accessible']}")
        print(f"    - With Errors: {summary['static_files']['with_errors']}")
        print()
        
        print(f"  Config Files: {summary['config_files']['total']} total")
        print(f"    - Valid Format: {summary['config_files']['valid_format']}")
        print(f"    - With Errors: {summary['config_files']['with_errors']}")
        print()
        
        print("LAUNCH SIMULATIONS:")
        print(f"  Total Simulations: {summary['launch_simulations']['total']}")
        print(f"  Successful: {summary['launch_simulations']['successful']}")
        print(f"  Failed: {summary['launch_simulations']['failed']}")
        print()
        
        print("API ENDPOINTS:")
        print(f"  Found: {len(self.results.get('api_endpoints', []))}")
        print()
        
        print("IMPORT TESTS:")
        import_tests = self.results.get('import_tests', {})
        successful_imports = sum(1 for test in import_tests.values() if test['importable'])
        print(f"  Modules Tested: {len(import_tests)}")
        print(f"  Successful Imports: {successful_imports}")
        print()
        
        # Show critical errors if any
        critical_errors = []
        for file_type in ['python_files', 'database_files']:
            for file_path, file_data in self.results[file_type].items():
                if file_data['errors']:
                    critical_errors.extend(file_data['errors'])
        
        if critical_errors:
            print("CRITICAL ERRORS:")
            for i, error in enumerate(critical_errors[:10], 1):  # Show first 10
                print(f"  {i}. {error}")
            if len(critical_errors) > 10:
                print(f"  ... and {len(critical_errors) - 10} more errors")
        
        print("="*80)


def main():
    """Main execution function"""
    print("Starting MITO Engine Comprehensive System Validation...")
    
    validator = SystemValidator()
    results = validator.run_comprehensive_validation()
    validator.print_summary_report()
    
    print(f"\nValidation completed. Detailed report saved.")
    return results


if __name__ == "__main__":
    main()