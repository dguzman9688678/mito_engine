#!/usr/bin/env python3
"""
MITO Engine - Honest System Assessment
Provides truthful assessment of system status without exaggeration
"""

import requests
import json
from datetime import datetime
import pytz

def test_actual_system():
    """Test the actual running system to get real results"""
    base_url = "http://localhost:5000"
    results = {}
    
    # Test critical endpoints
    endpoints = [
        "/api/health",
        "/api/status", 
        "/",
        "/lab-mode"
    ]
    
    working_endpoints = 0
    total_endpoints = len(endpoints)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                working_endpoints += 1
                results[endpoint] = {"status": "working", "code": response.status_code}
            else:
                results[endpoint] = {"status": "error", "code": response.status_code}
        except Exception as e:
            results[endpoint] = {"status": "failed", "error": str(e)}
    
    # Calculate actual success rate
    success_rate = (working_endpoints / total_endpoints) * 100
    
    return {
        "endpoints_tested": total_endpoints,
        "endpoints_working": working_endpoints,
        "success_rate": round(success_rate, 1),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

def generate_honest_report():
    """Generate completely honest system report"""
    print("Testing actual system status...")
    
    # Test the real system
    test_results = test_actual_system()
    
    pacific = pytz.timezone('US/Pacific')
    current_time = datetime.now(pacific)
    timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    print("\n" + "="*70)
    print("MITO ENGINE v1.2.0 - HONEST SYSTEM ASSESSMENT")
    print("="*70)
    print(f"Assessment Time: {timestamp}")
    print(f"Platform: Replit Infrastructure")
    print(f"Test Method: Live system testing")
    print("-"*70)
    
    # System status
    if test_results["success_rate"] >= 75:
        status = "OPERATIONAL"
        recommendation = "System is running adequately"
    elif test_results["success_rate"] >= 50:
        status = "PARTIALLY FUNCTIONAL"
        recommendation = "Some components need attention"
    else:
        status = "NEEDS ATTENTION"
        recommendation = "Multiple issues require fixing"
    
    print(f"Overall Status: {status}")
    print(f"Success Rate: {test_results['success_rate']}%")
    print(f"Endpoints Working: {test_results['endpoints_working']}/{test_results['endpoints_tested']}")
    print("-"*70)
    
    # Detailed results
    print("ENDPOINT TEST RESULTS:")
    for endpoint, result in test_results["results"].items():
        status_symbol = "✓" if result["status"] == "working" else "✗"
        print(f"{status_symbol} {endpoint}: {result['status'].upper()}")
        if "code" in result:
            print(f"   HTTP {result['code']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    print("-"*70)
    print(f"HONEST ASSESSMENT: {recommendation}")
    print("="*70)
    
    return test_results

if __name__ == "__main__":
    generate_honest_report()