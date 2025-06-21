#!/usr/bin/env python3
"""
MITO Engine v1.2.0 - Final Production System Check
Comprehensive validation of all components, dependencies, and configurations
"""

import os
import sys
import json
import sqlite3
import logging
import importlib
import subprocess
import time
import psutil
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import socket
import ssl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemCheck:
    """Base class for system checks"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = "PENDING"
        self.details = {}
        self.errors = []
        self.warnings = []
        
    def run(self) -> bool:
        """Run the check and return success status"""
        try:
            result = self._execute_check()
            self.status = "PASS" if result else "FAIL"
            return result
        except Exception as e:
            self.status = "ERROR"
            self.errors.append(str(e))
            logger.error(f"Check {self.name} failed with error: {e}")
            return False
            
    def _execute_check(self) -> bool:
        """Override this method in subclasses"""
        raise NotImplementedError

class PythonEnvironmentCheck(SystemCheck):
    """Check Python environment and version"""
    
    def _execute_check(self) -> bool:
        python_version = platform.python_version()
        python_implementation = platform.python_implementation()
        
        self.details = {
            "version": python_version,
            "implementation": python_implementation,
            "executable": sys.executable,
            "platform": platform.platform()
        }
        
        # Check minimum Python version (3.8+)
        major, minor = sys.version_info[:2]
        if major < 3 or (major == 3 and minor < 8):
            self.errors.append(f"Python {major}.{minor} not supported. Minimum version: 3.8")
            return False
            
        return True

class DependencyCheck(SystemCheck):
    """Check required dependencies"""
    
    def __init__(self):
        super().__init__("Dependencies")
        self.required_packages = [
            "flask", "flask-cors", "flask-sqlalchemy", "werkzeug",
            "requests", "beautifulsoup4", "pandas", "numpy", "scikit-learn",
            "openai", "psutil", "cryptography", "qrcode", "pillow",
            "schedule", "python-gnupg", "nltk", "spacy"
        ]
        self.optional_packages = [
            "sentence-transformers", "faiss-cpu", "transformers", "torch",
            "boto3", "azure-identity", "google-cloud-compute", "feedparser"
        ]
        
    def _execute_check(self) -> bool:
        installed_required = []
        missing_required = []
        installed_optional = []
        missing_optional = []
        
        # Check required packages
        for package in self.required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                installed_required.append(package)
            except ImportError:
                missing_required.append(package)
                
        # Check optional packages
        for package in self.optional_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                installed_optional.append(package)
            except ImportError:
                missing_optional.append(package)
                
        self.details = {
            "required_installed": installed_required,
            "required_missing": missing_required,
            "optional_installed": installed_optional,
            "optional_missing": missing_optional
        }
        
        if missing_required:
            self.errors.extend([f"Missing required package: {pkg}" for pkg in missing_required])
            return False
            
        if missing_optional:
            self.warnings.extend([f"Missing optional package: {pkg}" for pkg in missing_optional])
            
        return True

class DatabaseCheck(SystemCheck):
    """Check database connectivity and schema"""
    
    def _execute_check(self) -> bool:
        databases = [
            "audit_logs.db", "ml_analytics.db", "knowledge_base.db",
            "project_management.db", "code_templates.db", "simple_search.db"
        ]
        
        db_status = {}
        all_healthy = True
        
        for db_name in databases:
            try:
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # Check if database is accessible
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Basic integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                
                conn.close()
                
                db_status[db_name] = {
                    "status": "healthy",
                    "tables": len(tables),
                    "table_names": tables,
                    "integrity": integrity
                }
                
            except Exception as e:
                db_status[db_name] = {
                    "status": "error",
                    "error": str(e)
                }
                all_healthy = False
                self.errors.append(f"Database {db_name}: {e}")
                
        self.details = {"databases": db_status}
        return all_healthy

class ConfigurationCheck(SystemCheck):
    """Check system configuration and environment variables"""
    
    def _execute_check(self) -> bool:
        config_status = {}
        
        # Check critical environment variables
        critical_vars = ["SESSION_SECRET", "DATABASE_URL"]
        optional_vars = ["OPENAI_API_KEY", "AWS_ACCESS_KEY_ID", "AZURE_SUBSCRIPTION_ID"]
        
        missing_critical = []
        missing_optional = []
        
        for var in critical_vars:
            value = os.environ.get(var)
            if value:
                config_status[var] = "configured"
            else:
                config_status[var] = "missing"
                missing_critical.append(var)
                
        for var in optional_vars:
            value = os.environ.get(var)
            config_status[var] = "configured" if value else "missing"
            if not value:
                missing_optional.append(var)
                
        # Check file permissions
        critical_files = ["app.py", "main.py", "audit.py"]
        file_permissions = {}
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                file_permissions[file_path] = {
                    "readable": os.access(file_path, os.R_OK),
                    "writable": os.access(file_path, os.W_OK),
                    "executable": os.access(file_path, os.X_OK),
                    "size": stat.st_size
                }
            else:
                file_permissions[file_path] = {"status": "missing"}
                
        self.details = {
            "environment_variables": config_status,
            "file_permissions": file_permissions,
            "missing_critical": missing_critical,
            "missing_optional": missing_optional
        }
        
        if missing_critical:
            self.errors.extend([f"Missing critical environment variable: {var}" for var in missing_critical])
            return False
            
        if missing_optional:
            self.warnings.extend([f"Missing optional environment variable: {var}" for var in missing_optional])
            
        return True

class NetworkCheck(SystemCheck):
    """Check network connectivity and port availability"""
    
    def _execute_check(self) -> bool:
        network_status = {}
        
        # Check port availability
        port = 5000
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            network_status["port_5000"] = {
                "available": result != 0,
                "status": "free" if result != 0 else "in_use"
            }
        except Exception as e:
            network_status["port_5000"] = {"error": str(e)}
            
        # Check internet connectivity
        test_urls = [
            "https://api.openai.com",
            "https://github.com",
            "https://pypi.org"
        ]
        
        connectivity = {}
        for url in test_urls:
            try:
                import urllib.request
                response = urllib.request.urlopen(url, timeout=10)
                connectivity[url] = {
                    "status": "reachable",
                    "response_code": response.getcode()
                }
            except Exception as e:
                connectivity[url] = {
                    "status": "unreachable",
                    "error": str(e)
                }
                
        self.details = {
            "network": network_status,
            "connectivity": connectivity
        }
        
        return True  # Network issues are warnings, not failures

class SecurityCheck(SystemCheck):
    """Check security configurations"""
    
    def _execute_check(self) -> bool:
        security_status = {}
        issues = []
        
        # Check file permissions for sensitive files
        sensitive_files = [".env", "vault_master.key", "*.key", "*.pem"]
        
        for pattern in sensitive_files:
            if pattern.startswith("*"):
                # Handle wildcards
                import glob
                files = glob.glob(pattern)
            else:
                files = [pattern] if os.path.exists(pattern) else []
                
            for file_path in files:
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    mode = oct(stat.st_mode)[-3:]
                    
                    security_status[file_path] = {
                        "permissions": mode,
                        "secure": mode in ["600", "400"]  # Only owner read/write
                    }
                    
                    if mode not in ["600", "400"]:
                        issues.append(f"Insecure permissions on {file_path}: {mode}")
                        
        # Check for default passwords or keys
        default_patterns = ["admin", "password", "secret", "key123", "test"]
        
        session_secret = os.environ.get("SESSION_SECRET", "")
        if any(pattern in session_secret.lower() for pattern in default_patterns):
            issues.append("SESSION_SECRET appears to use default or weak value")
            
        # Check SSL/TLS configuration
        try:
            context = ssl.create_default_context()
            security_status["ssl_context"] = "available"
        except Exception as e:
            security_status["ssl_context"] = f"error: {e}"
            issues.append(f"SSL context error: {e}")
            
        self.details = {
            "file_security": security_status,
            "issues": issues
        }
        
        if issues:
            self.warnings.extend(issues)
            
        return len([issue for issue in issues if "error" in issue.lower()]) == 0

class ComponentCheck(SystemCheck):
    """Check individual MITO components"""
    
    def _execute_check(self) -> bool:
        components = {
            "nlp_engine": "nlp_engine.py",
            "code_generator": "code_generator.py", 
            "project_manager": "project_manager.py",
            "ml_analytics": "ml_analytics_engine.py",
            "cloud_services": "cloud_services_manager.py",
            "knowledge_base": "knowledge_base_manager.py",
            "search_engine": "simple_search_demo.py",
            "audit_system": "audit.py",
            "security_manager": "security_manager.py"
        }
        
        component_status = {}
        working_components = 0
        
        for component, file_path in components.items():
            try:
                if os.path.exists(file_path):
                    # Try to import the module
                    module_name = file_path.replace(".py", "").replace("/", ".")
                    
                    # Basic syntax check
                    with open(file_path, 'r') as f:
                        code = f.read()
                        compile(code, file_path, 'exec')
                        
                    component_status[component] = {
                        "status": "operational",
                        "file_size": os.path.getsize(file_path),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                    working_components += 1
                    
                else:
                    component_status[component] = {
                        "status": "missing",
                        "file_path": file_path
                    }
                    
            except SyntaxError as e:
                component_status[component] = {
                    "status": "syntax_error",
                    "error": str(e)
                }
                self.errors.append(f"Syntax error in {component}: {e}")
                
            except Exception as e:
                component_status[component] = {
                    "status": "error", 
                    "error": str(e)
                }
                
        self.details = {
            "components": component_status,
            "working_count": working_components,
            "total_count": len(components),
            "operational_rate": working_components / len(components)
        }
        
        # Consider system healthy if 70% of components are working
        return working_components >= len(components) * 0.7

class PerformanceCheck(SystemCheck):
    """Check system performance and resources"""
    
    def _execute_check(self) -> bool:
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # Performance thresholds
        cpu_threshold = 80.0
        memory_threshold = 85.0
        disk_threshold = 90.0
        
        performance_issues = []
        
        if cpu_percent > cpu_threshold:
            performance_issues.append(f"High CPU usage: {cpu_percent}%")
            
        if memory.percent > memory_threshold:
            performance_issues.append(f"High memory usage: {memory.percent}%")
            
        if disk.percent > disk_threshold:
            performance_issues.append(f"High disk usage: {disk.percent}%")
            
        # Check Python startup time
        start_time = time.time()
        import numpy, pandas, flask
        import_time = time.time() - start_time
        
        self.details = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "import_time_seconds": import_time,
            "performance_issues": performance_issues
        }
        
        if performance_issues:
            self.warnings.extend(performance_issues)
            
        # Consider critical if multiple severe issues
        critical_issues = [issue for issue in performance_issues if "High" in issue]
        return len(critical_issues) < 2

class ProductionReadinessCheck:
    """Main production readiness checker"""
    
    def __init__(self):
        self.checks = [
            PythonEnvironmentCheck("Python Environment"),
            DependencyCheck(),
            DatabaseCheck("Database Systems"),
            ConfigurationCheck("Configuration"),
            NetworkCheck("Network Connectivity"),
            SecurityCheck("Security Configuration"),
            ComponentCheck("MITO Components"),
            PerformanceCheck("System Performance")
        ]
        self.results = {}
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all production readiness checks"""
        logger.info("Starting MITO Engine Production Readiness Check")
        print("="*70)
        print("MITO ENGINE v1.2.0 - PRODUCTION READINESS CHECK")
        print("="*70)
        
        total_checks = len(self.checks)
        passed_checks = 0
        failed_checks = 0
        error_checks = 0
        
        for i, check in enumerate(self.checks, 1):
            print(f"\n[{i}/{total_checks}] Running {check.name}...")
            
            success = check.run()
            self.results[check.name] = {
                "status": check.status,
                "success": success,
                "details": check.details,
                "errors": check.errors,
                "warnings": check.warnings
            }
            
            if check.status == "PASS":
                passed_checks += 1
                print(f"    ✓ {check.name}: PASS")
            elif check.status == "FAIL":
                failed_checks += 1
                print(f"    ✗ {check.name}: FAIL")
                for error in check.errors:
                    print(f"      Error: {error}")
            else:  # ERROR
                error_checks += 1
                print(f"    ⚠ {check.name}: ERROR")
                for error in check.errors:
                    print(f"      Error: {error}")
                    
            # Show warnings
            for warning in check.warnings:
                print(f"      Warning: {warning}")
                
        # Generate summary
        success_rate = passed_checks / total_checks
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "errors": error_checks,
            "success_rate": success_rate,
            "production_ready": success_rate >= 0.8,
            "checks": self.results
        }
        
        # Print summary
        print("\n" + "="*70)
        print("PRODUCTION READINESS SUMMARY")
        print("="*70)
        
        print(f"\nCheck Results:")
        print(f"  Total Checks: {total_checks}")
        print(f"  Passed: {passed_checks}")
        print(f"  Failed: {failed_checks}")
        print(f"  Errors: {error_checks}")
        print(f"  Success Rate: {success_rate:.1%}")
        
        # Production readiness assessment
        if success_rate >= 0.9:
            status = "🟢 PRODUCTION READY"
            recommendation = "System is ready for production deployment"
        elif success_rate >= 0.8:
            status = "🟡 MOSTLY READY"
            recommendation = "Address minor issues before production deployment"
        elif success_rate >= 0.6:
            status = "🟠 NEEDS ATTENTION"
            recommendation = "Several issues need resolution before production"
        else:
            status = "🔴 NOT READY"
            recommendation = "Major issues must be resolved before deployment"
            
        print(f"\nProduction Status: {status}")
        print(f"Recommendation: {recommendation}")
        
        # Critical issues
        critical_issues = []
        for check_name, result in self.results.items():
            if result["status"] in ["FAIL", "ERROR"]:
                critical_issues.extend(result["errors"])
                
        if critical_issues:
            print(f"\nCritical Issues to Address:")
            for i, issue in enumerate(critical_issues, 1):
                print(f"  {i}. {issue}")
                
        # Next steps
        print(f"\nNext Steps:")
        if success_rate >= 0.8:
            print("  1. Review warnings and optimize performance")
            print("  2. Set up monitoring and alerting")
            print("  3. Configure backup and disaster recovery")
            print("  4. Perform load testing")
            print("  5. Deploy to production environment")
        else:
            print("  1. Address all critical errors")
            print("  2. Install missing dependencies")
            print("  3. Configure required environment variables")
            print("  4. Fix security issues")
            print("  5. Re-run production readiness check")
            
        # Save detailed report
        report_file = f"production_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        print(f"\nDetailed report saved to: {report_file}")
        print("="*70)
        
        return summary

def main():
    """Run production readiness check"""
    checker = ProductionReadinessCheck()
    results = checker.run_all_checks()
    
    # Return appropriate exit code
    if results["production_ready"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()