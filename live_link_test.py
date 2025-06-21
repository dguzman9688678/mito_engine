#!/usr/bin/env python3
"""
Live Link Verification for MITO Engine
Tests actual deployed application for broken links
"""

import requests
import os
import time
from urllib.parse import urljoin, urlparse
import json

def get_deployment_url():
    """Get the live deployment URL"""
    repl_slug = os.environ.get('REPL_SLUG', 'workspace')
    repl_owner = os.environ.get('REPL_OWNER', 'dguzman9688678')
    return f"https://{repl_slug}-{repl_owner}.replit.app"

def test_endpoint(base_url, endpoint, method='GET', data=None):
    """Test a specific endpoint"""
    url = urljoin(base_url, endpoint)
    
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': response.status_code,
            'status': 'OK' if response.status_code < 400 else 'BROKEN',
            'response_time': response.elapsed.total_seconds(),
            'content_type': response.headers.get('content-type', 'unknown'),
            'size': len(response.content)
        }
    except requests.exceptions.ConnectionError:
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': 0,
            'status': 'CONNECTION_ERROR',
            'error': 'Cannot connect to server'
        }
    except requests.exceptions.Timeout:
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': 0,
            'status': 'TIMEOUT',
            'error': 'Request timed out'
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'url': url,
            'status_code': 0,
            'status': 'ERROR',
            'error': str(e)
        }

def main():
    """Run comprehensive link test on live deployment"""
    
    print("MITO Engine Live Link Verification")
    print("=" * 50)
    
    # Get deployment URL
    base_url = get_deployment_url()
    print(f"Testing deployment: {base_url}")
    print("-" * 50)
    
    # Define endpoints to test
    endpoints = [
        # Main pages
        ('/', 'GET'),
        ('/lab-mode', 'GET'),
        ('/mobile', 'GET'),
        ('/mobile-test', 'GET'),
        ('/arcsec-identity', 'GET'),
        ('/test-chat', 'GET'),
        
        # API endpoints
        ('/api/generate', 'POST', {'prompt': 'test'}),
        ('/api/arcsec-identity/token', 'POST', {}),
        ('/api/arcsec-identity/verify', 'POST', {'token': 'test'}),
        
        # Static resources (common paths)
        ('/static/css/style.css', 'GET'),
        ('/static/js/app.js', 'GET'),
        ('/static/images/logo.png', 'GET'),
        ('/favicon.ico', 'GET'),
        
        # Templates and other resources
        ('/templates/giant_workbench.html', 'GET'),
        ('/templates/mobile_workbench.html', 'GET'),
    ]
    
    results = []
    broken_links = []
    working_links = []
    
    for endpoint_data in endpoints:
        if len(endpoint_data) == 2:
            endpoint, method = endpoint_data
            data = None
        else:
            endpoint, method, data = endpoint_data
        
        result = test_endpoint(base_url, endpoint, method, data)
        results.append(result)
        
        # Print result
        status_symbol = "✓" if result['status'] == 'OK' else "✗"
        print(f"{status_symbol} {endpoint:<30} {result.get('status_code', 'N/A'):<4} {result['status']}")
        
        if result['status'] != 'OK':
            broken_links.append(result)
            if 'error' in result:
                print(f"  Error: {result['error']}")
        else:
            working_links.append(result)
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total endpoints tested: {len(results)}")
    print(f"Working links: {len(working_links)}")
    print(f"Broken links: {len(broken_links)}")
    
    if broken_links:
        print(f"\nBROKEN LINKS ({len(broken_links)}):")
        print("-" * 30)
        for link in broken_links:
            print(f"• {link['endpoint']} - {link['status']} ({link.get('status_code', 'N/A')})")
            if 'error' in link:
                print(f"  {link['error']}")
    
    # Save detailed results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = f"live_link_test_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'base_url': base_url,
            'summary': {
                'total': len(results),
                'working': len(working_links),
                'broken': len(broken_links)
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nDetailed report saved: {report_file}")
    
    # Return status
    return len(broken_links) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)