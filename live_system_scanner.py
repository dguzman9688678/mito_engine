#!/usr/bin/env python3
"""
MITO Engine - Live System Scanner
Comprehensive real-time system health and component verification
"""

import requests
import time
import json
import os
import psutil
from datetime import datetime
import pytz

class LiveSystemScanner:
    """Comprehensive live system scanning and monitoring"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.pacific = pytz.timezone('US/Pacific')
        self.scan_start = datetime.now(self.pacific)
        self.results = {
            "scan_timestamp": self.scan_start.isoformat(),
            "system_health": {},
            "api_endpoints": {},
            "laboratory_access": {},
            "performance_metrics": {},
            "security_status": {},
            "file_system": {},
            "processes": {},
            "overall_status": "SCANNING"
        }
    
    def scan_system_resources(self):
        """Scan system resources and performance"""
        print("🔍 Scanning system resources...")
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('.')
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Process count
            process_count = len(psutil.pids())
            
            self.results["system_health"] = {
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                    "status": "healthy" if memory.percent < 80 else "warning"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_percent": round((disk.used / disk.total) * 100, 1),
                    "status": "healthy" if disk.free > 1024**3 else "warning"
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": psutil.cpu_count(),
                    "status": "healthy" if cpu_percent < 70 else "warning"
                },
                "processes": {
                    "count": process_count,
                    "status": "normal"
                }
            }
            print(f"   ✓ Memory: {memory.percent}% used")
            print(f"   ✓ Disk: {round((disk.used / disk.total) * 100, 1)}% used")
            print(f"   ✓ CPU: {cpu_percent}% usage")
            
        except Exception as e:
            print(f"   ✗ Error scanning resources: {e}")
            self.results["system_health"]["error"] = str(e)
    
    def scan_api_endpoints(self):
        """Scan all API endpoints for availability and response times"""
        print("🔍 Scanning API endpoints...")
        
        endpoints = [
            "/api/health",
            "/api/status",
            "/api/providers",
            "/api/lab",
            "/api/keys",
            "/api/tools",
            "/api/agents",
            "/api/blueprints",
            "/api/deploy",
            "/api/memory",
            "/api/link-repair/anchors",
            "/api/link-repair/navigation"
        ]
        
        working_count = 0
        total_response_time = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                self.results["api_endpoints"][endpoint] = {
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "status": "working" if response.status_code == 200 else "error",
                    "content_length": len(response.content) if response.content else 0
                }
                
                if response.status_code == 200:
                    working_count += 1
                    total_response_time += response_time
                    print(f"   ✓ {endpoint}: {response.status_code} ({response_time}ms)")
                else:
                    print(f"   ✗ {endpoint}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ✗ {endpoint}: ERROR - {e}")
                self.results["api_endpoints"][endpoint] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Calculate performance metrics
        if working_count > 0:
            avg_response_time = round(total_response_time / working_count, 2)
            self.results["performance_metrics"] = {
                "endpoints_working": working_count,
                "endpoints_total": len(endpoints),
                "success_rate": round((working_count / len(endpoints)) * 100, 1),
                "average_response_time_ms": avg_response_time,
                "performance_status": "excellent" if avg_response_time < 50 else "good" if avg_response_time < 200 else "slow"
            }
            print(f"   📊 API Success Rate: {self.results['performance_metrics']['success_rate']}%")
            print(f"   📊 Average Response: {avg_response_time}ms")
    
    def scan_laboratory_access(self):
        """Scan laboratory environment accessibility"""
        print("🔍 Scanning laboratory environments...")
        
        lab_routes = [
            "/lab-mode",
            "/workbench", 
            "/giant-workbench",
            "/memory-manager",
            "/code-editor",
            "/mito-files"
        ]
        
        working_labs = 0
        
        for route in lab_routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=10)
                
                self.results["laboratory_access"][route] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "content_length": len(response.content) if response.content else 0
                }
                
                if response.status_code == 200:
                    working_labs += 1
                    print(f"   ✓ {route}: Accessible")
                else:
                    print(f"   ✗ {route}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ✗ {route}: ERROR - {e}")
                self.results["laboratory_access"][route] = {
                    "accessible": False,
                    "error": str(e)
                }
        
        lab_success_rate = round((working_labs / len(lab_routes)) * 100, 1)
        print(f"   📊 Laboratory Access Rate: {lab_success_rate}%")
    
    def scan_file_system(self):
        """Scan critical file system components"""
        print("🔍 Scanning file system...")
        
        critical_files = [
            "app.py",
            "main.py", 
            "models.py",
            "config.py",
            "requirements.txt"
        ]
        
        critical_dirs = [
            "static",
            "templates",
            "mito_uploads",
            "docs"
        ]
        
        file_status = {}
        
        # Check files
        for file_path in critical_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                file_status[file_path] = {
                    "exists": True,
                    "size_bytes": size,
                    "readable": os.access(file_path, os.R_OK)
                }
                print(f"   ✓ {file_path}: {size} bytes")
            else:
                file_status[file_path] = {"exists": False}
                print(f"   ✗ {file_path}: Missing")
        
        # Check directories
        for dir_path in critical_dirs:
            if os.path.isdir(dir_path):
                try:
                    file_count = len(os.listdir(dir_path))
                    file_status[dir_path] = {
                        "exists": True,
                        "type": "directory",
                        "file_count": file_count
                    }
                    print(f"   ✓ {dir_path}/: {file_count} files")
                except:
                    file_status[dir_path] = {"exists": True, "accessible": False}
                    print(f"   ⚠ {dir_path}/: Not accessible")
            else:
                file_status[dir_path] = {"exists": False, "type": "directory"}
                print(f"   ✗ {dir_path}/: Missing")
        
        self.results["file_system"] = file_status
    
    def scan_running_processes(self):
        """Scan for MITO-related processes"""
        print("🔍 Scanning running processes...")
        
        mito_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline.lower() for keyword in ['mito', 'gunicorn', 'flask', 'python']):
                    if 'app' in cmdline or 'main' in cmdline or 'gunicorn' in cmdline:
                        mito_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "command": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline,
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_percent": round(proc.info['memory_percent'], 2)
                        })
                        print(f"   ✓ PID {proc.info['pid']}: {proc.info['name']}")
            except:
                continue
        
        self.results["processes"] = {
            "mito_related": mito_processes,
            "total_count": len(mito_processes)
        }
        print(f"   📊 MITO processes found: {len(mito_processes)}")
    
    def calculate_overall_status(self):
        """Calculate overall system status based on all scans"""
        print("🔍 Calculating overall status...")
        
        # Check critical metrics
        api_success = self.results.get("performance_metrics", {}).get("success_rate", 0)
        memory_status = self.results.get("system_health", {}).get("memory", {}).get("status", "unknown")
        process_count = self.results.get("processes", {}).get("total_count", 0)
        
        # Determine overall status
        if api_success >= 90 and memory_status == "healthy" and process_count > 0:
            overall = "EXCELLENT"
            confidence = "HIGH"
        elif api_success >= 75 and memory_status != "critical":
            overall = "GOOD"
            confidence = "MEDIUM"
        elif api_success >= 50:
            overall = "OPERATIONAL"
            confidence = "MEDIUM"
        else:
            overall = "NEEDS_ATTENTION"
            confidence = "LOW"
        
        scan_duration = (datetime.now(self.pacific) - self.scan_start).total_seconds()
        
        self.results["overall_status"] = overall
        self.results["confidence_level"] = confidence
        self.results["scan_duration_seconds"] = round(scan_duration, 2)
        
        print(f"   📊 Overall Status: {overall}")
        print(f"   📊 Confidence: {confidence}")
        print(f"   📊 Scan Duration: {scan_duration:.2f}s")
    
    def generate_report(self):
        """Generate comprehensive scan report"""
        timestamp = datetime.now(self.pacific).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        print("\n" + "="*80)
        print("MITO ENGINE v1.2.0 - LIVE SYSTEM SCAN REPORT")
        print("="*80)
        print(f"Scan Completed: {timestamp}")
        print(f"Platform: Replit Infrastructure")
        print(f"Scan Duration: {self.results.get('scan_duration_seconds', 0)}s")
        print("-"*80)
        
        # Overall status
        print(f"🎯 OVERALL STATUS: {self.results.get('overall_status', 'UNKNOWN')}")
        print(f"🎯 CONFIDENCE LEVEL: {self.results.get('confidence_level', 'UNKNOWN')}")
        print()
        
        # System health summary
        if "system_health" in self.results:
            memory = self.results["system_health"].get("memory", {})
            cpu = self.results["system_health"].get("cpu", {})
            print(f"💾 Memory: {memory.get('used_percent', 0)}% used ({memory.get('status', 'unknown')})")
            print(f"⚡ CPU: {cpu.get('usage_percent', 0)}% usage ({cpu.get('status', 'unknown')})")
        
        # API performance
        if "performance_metrics" in self.results:
            perf = self.results["performance_metrics"]
            print(f"🌐 API Success Rate: {perf.get('success_rate', 0)}%")
            print(f"🚀 Average Response Time: {perf.get('average_response_time_ms', 0)}ms")
        
        # Process status
        proc_count = self.results.get("processes", {}).get("total_count", 0)
        print(f"⚙️  Active MITO Processes: {proc_count}")
        
        print("-"*80)
        print("SCAN COMPLETE - System is being monitored")
        print("="*80)
        
        return self.results
    
    def save_results(self):
        """Save scan results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"live_system_scan_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Scan results saved to: {filename}")
        return filename

def main():
    """Run comprehensive live system scan"""
    scanner = LiveSystemScanner()
    
    print("🚀 Starting MITO Engine Live System Scan...")
    print()
    
    # Run all scans
    scanner.scan_system_resources()
    scanner.scan_api_endpoints()
    scanner.scan_laboratory_access()
    scanner.scan_file_system()
    scanner.scan_running_processes()
    scanner.calculate_overall_status()
    
    # Generate and save report
    results = scanner.generate_report()
    scanner.save_results()
    
    return results

if __name__ == "__main__":
    main()