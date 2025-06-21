#!/usr/bin/env python3
"""
MITO Engine - Quick Live System Scanner
Real-time system verification without complex process scanning
"""

import requests
import time
import json
import os
from datetime import datetime
import pytz

def quick_system_scan():
    """Perform quick live system scan"""
    base_url = "http://localhost:5000"
    pacific = pytz.timezone('US/Pacific')
    scan_time = datetime.now(pacific).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    print("🚀 MITO Engine Live System Scan")
    print("=" * 50)
    print(f"Scan Time: {scan_time}")
    print()
    
    # Test core endpoints
    print("🔍 Testing Core System...")
    core_endpoints = [
        ("/", "Main Interface"),
        ("/api/health", "Health Check"),
        ("/api/status", "System Status"),
        ("/lab-mode", "Laboratory Mode")
    ]
    
    core_working = 0
    total_response_time = 0
    
    for endpoint, name in core_endpoints:
        try:
            start = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            response_time = round((time.time() - start) * 1000, 1)
            
            if response.status_code == 200:
                print(f"   ✓ {name}: Working ({response_time}ms)")
                core_working += 1
                total_response_time += response_time
            else:
                print(f"   ✗ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ {name}: Connection failed")
    
    # Test API endpoints
    print("\n🔍 Testing API Endpoints...")
    api_endpoints = [
        "/api/providers",
        "/api/lab", 
        "/api/keys",
        "/api/tools",
        "/api/agents",
        "/api/blueprints"
    ]
    
    api_working = 0
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✓ {endpoint}: Active")
                api_working += 1
            else:
                print(f"   ✗ {endpoint}: HTTP {response.status_code}")
        except:
            print(f"   ✗ {endpoint}: Failed")
    
    # Test laboratory environments
    print("\n🔍 Testing Laboratory Environments...")
    lab_routes = [
        "/workbench",
        "/giant-workbench", 
        "/memory-manager",
        "/code-editor"
    ]
    
    lab_working = 0
    
    for route in lab_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if response.status_code == 200:
                print(f"   ✓ {route}: Accessible")
                lab_working += 1
            else:
                print(f"   ✗ {route}: HTTP {response.status_code}")
        except:
            print(f"   ✗ {route}: Failed")
    
    # Check file system
    print("\n🔍 Checking Critical Files...")
    critical_files = ["app.py", "main.py", "models.py"]
    files_present = 0
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            size = round(os.path.getsize(file_path) / 1024, 1)
            print(f"   ✓ {file_path}: Present ({size}KB)")
            files_present += 1
        else:
            print(f"   ✗ {file_path}: Missing")
    
    # Calculate results
    total_tests = len(core_endpoints) + len(api_endpoints) + len(lab_routes) + len(critical_files)
    total_passed = core_working + api_working + lab_working + files_present
    success_rate = round((total_passed / total_tests) * 100, 1)
    
    avg_response = round(total_response_time / max(core_working, 1), 1) if core_working > 0 else 0
    
    # Generate summary
    print("\n" + "=" * 50)
    print("LIVE SCAN SUMMARY")
    print("=" * 50)
    print(f"Overall Success Rate: {success_rate}%")
    print(f"Tests Passed: {total_passed}/{total_tests}")
    print(f"Average Response Time: {avg_response}ms")
    print()
    
    # Status determination
    if success_rate >= 90:
        status = "EXCELLENT"
        color = "🟢"
    elif success_rate >= 75:
        status = "GOOD" 
        color = "🟡"
    elif success_rate >= 50:
        status = "OPERATIONAL"
        color = "🟠"
    else:
        status = "NEEDS ATTENTION"
        color = "🔴"
    
    print(f"{color} System Status: {status}")
    print()
    
    # Component breakdown
    print("Component Status:")
    print(f"   Core System: {core_working}/{len(core_endpoints)} working")
    print(f"   API Endpoints: {api_working}/{len(api_endpoints)} working") 
    print(f"   Laboratory: {lab_working}/{len(lab_routes)} accessible")
    print(f"   Critical Files: {files_present}/{len(critical_files)} present")
    
    print("\n" + "=" * 50)
    print("SCAN COMPLETE")
    print("=" * 50)
    
    # Save results
    results = {
        "scan_timestamp": scan_time,
        "success_rate": success_rate,
        "total_passed": total_passed,
        "total_tests": total_tests,
        "status": status,
        "average_response_ms": avg_response,
        "components": {
            "core_system": f"{core_working}/{len(core_endpoints)}",
            "api_endpoints": f"{api_working}/{len(api_endpoints)}",
            "laboratory": f"{lab_working}/{len(lab_routes)}",
            "files": f"{files_present}/{len(critical_files)}"
        }
    }
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"live_scan_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {filename}")
    
    return results

if __name__ == "__main__":
    quick_system_scan()