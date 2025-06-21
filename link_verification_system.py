#!/usr/bin/env python3
"""
MITO Engine - Link Verification System
Comprehensive link testing and validation for all interface pages
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class MITOLinkVerifier:
    """Comprehensive link verification for MITO Engine interfaces"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        self.broken_links = []
        self.working_links = []
        self.session = requests.Session()
        self.session.timeout = 10
        
    def verify_all_links(self) -> Dict[str, Any]:
        """Verify all links across the MITO Engine interface"""
        
        print("MITO Engine Link Verification System")
        print("=" * 50)
        
        # Test server availability first
        if not self.test_server_availability():
            return {
                'success': False,
                'error': 'Server not accessible',
                'server_url': self.base_url
            }
        
        # Define all pages to test
        pages_to_test = {
            'main_dashboard': '/',
            'lab_mode': '/lab-mode',
            'health_check': '/health',
            'api_status': '/api/status',
            'mobile_interface': '/mobile',
            'mobile_test': '/mobile-test'
        }
        
        print(f"Testing {len(pages_to_test)} main pages...")
        
        for page_name, url in pages_to_test.items():
            print(f"\nTesting {page_name}: {url}")
            self.test_page_links(page_name, url)
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Generate comprehensive report
        return self.generate_report()
    
    def test_server_availability(self) -> bool:
        """Test if the server is running and accessible"""
        try:
            response = self.session.get(self.base_url, timeout=5)
            if response.status_code in [200, 302, 404]:  # Any response means server is up
                print(f"✓ Server accessible at {self.base_url}")
                return True
            else:
                print(f"✗ Server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Server not accessible: {e}")
            return False
    
    def test_page_links(self, page_name: str, url: str):
        """Test all links on a specific page"""
        try:
            full_url = urljoin(self.base_url, url)
            response = self.session.get(full_url)
            
            if response.status_code != 200:
                self.broken_links.append({
                    'page': page_name,
                    'url': url,
                    'status_code': response.status_code,
                    'error': f'Page not accessible: {response.status_code}'
                })
                print(f"  ✗ Page not accessible: {response.status_code}")
                return
            
            print(f"  ✓ Page accessible: {response.status_code}")
            self.working_links.append({
                'page': page_name,
                'url': url,
                'status_code': response.status_code
            })
            
            # Extract and test links from HTML content
            content = response.text
            self.extract_and_test_links(page_name, content)
            
        except Exception as e:
            self.broken_links.append({
                'page': page_name,
                'url': url,
                'error': str(e)
            })
            print(f"  ✗ Error accessing page: {e}")
    
    def extract_and_test_links(self, page_name: str, content: str):
        """Extract and test all links from HTML content"""
        import re
        
        # Extract href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        hrefs = re.findall(href_pattern, content)
        
        # Extract JavaScript onclick handlers
        onclick_pattern = r'onclick=["\']([^"\']+)["\']'
        onclicks = re.findall(onclick_pattern, content)
        
        # Extract form actions
        action_pattern = r'action=["\']([^"\']+)["\']'
        actions = re.findall(action_pattern, content)
        
        # Test href links
        for href in hrefs:
            if href.startswith('#'):
                # Fragment links - test if target exists
                self.test_fragment_link(page_name, href, content)
            elif href.startswith('http'):
                # External links - test accessibility
                self.test_external_link(page_name, href)
            elif href.startswith('/'):
                # Internal links - test on our server
                self.test_internal_link(page_name, href)
            elif href.startswith('javascript:'):
                # JavaScript links - validate syntax
                self.test_javascript_link(page_name, href)
        
        # Test form actions
        for action in actions:
            if action.startswith('/'):
                self.test_form_action(page_name, action)
        
        # Test onclick handlers
        for onclick in onclicks:
            self.test_onclick_handler(page_name, onclick)
    
    def test_fragment_link(self, page_name: str, href: str, content: str):
        """Test fragment links (anchors)"""
        target_id = href[1:]  # Remove #
        if f'id="{target_id}"' in content or f"id='{target_id}'" in content:
            print(f"    ✓ Fragment link: {href}")
            self.working_links.append({
                'page': page_name,
                'type': 'fragment',
                'url': href,
                'status': 'target_found'
            })
        else:
            print(f"    ✗ Fragment link missing target: {href}")
            self.broken_links.append({
                'page': page_name,
                'type': 'fragment',
                'url': href,
                'error': 'Target element not found'
            })
    
    def test_external_link(self, page_name: str, href: str):
        """Test external links"""
        try:
            # Quick head request to check if link is accessible
            response = self.session.head(href, timeout=5)
            if response.status_code < 400:
                print(f"    ✓ External link: {href}")
                self.working_links.append({
                    'page': page_name,
                    'type': 'external',
                    'url': href,
                    'status_code': response.status_code
                })
            else:
                print(f"    ✗ External link broken: {href} ({response.status_code})")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'external',
                    'url': href,
                    'status_code': response.status_code
                })
        except Exception as e:
            print(f"    ✗ External link error: {href} ({e})")
            self.broken_links.append({
                'page': page_name,
                'type': 'external',
                'url': href,
                'error': str(e)
            })
    
    def test_internal_link(self, page_name: str, href: str):
        """Test internal links"""
        try:
            full_url = urljoin(self.base_url, href)
            response = self.session.get(full_url, timeout=5)
            
            if response.status_code == 200:
                print(f"    ✓ Internal link: {href}")
                self.working_links.append({
                    'page': page_name,
                    'type': 'internal',
                    'url': href,
                    'status_code': response.status_code
                })
            elif response.status_code == 404:
                print(f"    ✗ Internal link not found: {href}")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'internal',
                    'url': href,
                    'status_code': 404,
                    'error': 'Page not found'
                })
            else:
                print(f"    ⚠ Internal link warning: {href} ({response.status_code})")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'internal',
                    'url': href,
                    'status_code': response.status_code,
                    'error': f'Unexpected status: {response.status_code}'
                })
                
        except Exception as e:
            print(f"    ✗ Internal link error: {href} ({e})")
            self.broken_links.append({
                'page': page_name,
                'type': 'internal',
                'url': href,
                'error': str(e)
            })
    
    def test_javascript_link(self, page_name: str, href: str):
        """Test JavaScript links for basic syntax"""
        js_code = href.replace('javascript:', '')
        
        # Basic syntax validation
        if js_code.strip():
            # Check for common patterns that might indicate broken JS
            broken_patterns = [
                'undefined',
                'null()',
                'NaN',
                'error',
                'Error',
                '{{',
                '}}',
                'undefined()',
                'function()'
            ]
            
            is_broken = any(pattern in js_code for pattern in broken_patterns)
            
            if is_broken:
                print(f"    ✗ JavaScript link suspicious: {href}")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'javascript',
                    'url': href,
                    'error': 'Suspicious JavaScript code'
                })
            else:
                print(f"    ✓ JavaScript link: {href}")
                self.working_links.append({
                    'page': page_name,
                    'type': 'javascript',
                    'url': href,
                    'status': 'syntax_ok'
                })
        else:
            print(f"    ✗ Empty JavaScript link: {href}")
            self.broken_links.append({
                'page': page_name,
                'type': 'javascript',
                'url': href,
                'error': 'Empty JavaScript code'
            })
    
    def test_form_action(self, page_name: str, action: str):
        """Test form action URLs"""
        try:
            full_url = urljoin(self.base_url, action)
            # Use HEAD request to check if endpoint exists
            response = self.session.head(full_url, timeout=5)
            
            if response.status_code < 500:  # Accept any non-server-error response
                print(f"    ✓ Form action: {action}")
                self.working_links.append({
                    'page': page_name,
                    'type': 'form_action',
                    'url': action,
                    'status_code': response.status_code
                })
            else:
                print(f"    ✗ Form action error: {action} ({response.status_code})")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'form_action',
                    'url': action,
                    'status_code': response.status_code
                })
                
        except Exception as e:
            print(f"    ✗ Form action error: {action} ({e})")
            self.broken_links.append({
                'page': page_name,
                'type': 'form_action',
                'url': action,
                'error': str(e)
            })
    
    def test_onclick_handler(self, page_name: str, onclick: str):
        """Test onclick handlers for basic syntax"""
        # Basic validation of onclick handlers
        if onclick.strip():
            # Check for common broken patterns
            broken_patterns = [
                'undefined(',
                'null(',
                'NaN(',
                'function(',
                'Error(',
                '{{'
            ]
            
            is_broken = any(pattern in onclick for pattern in broken_patterns)
            
            if is_broken:
                print(f"    ✗ Onclick handler suspicious: {onclick[:50]}...")
                self.broken_links.append({
                    'page': page_name,
                    'type': 'onclick',
                    'code': onclick[:100],
                    'error': 'Suspicious onclick handler'
                })
            else:
                print(f"    ✓ Onclick handler: {onclick[:50]}...")
                self.working_links.append({
                    'page': page_name,
                    'type': 'onclick',
                    'code': onclick[:100],
                    'status': 'syntax_ok'
                })
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        print(f"\nTesting API endpoints...")
        
        api_endpoints = [
            '/api/status',
            '/api/health',
            '/api/generate',
            '/api/providers',
            '/api/memory',
            '/api/lab/status',
            '/api/keys',
            '/api/tools',
            '/api/agents',
            '/api/blueprints',
            '/api/deploy'
        ]
        
        for endpoint in api_endpoints:
            try:
                full_url = urljoin(self.base_url, endpoint)
                response = self.session.get(full_url, timeout=5)
                
                if response.status_code == 200:
                    print(f"  ✓ API endpoint: {endpoint}")
                    self.working_links.append({
                        'page': 'api_endpoints',
                        'type': 'api',
                        'url': endpoint,
                        'status_code': response.status_code
                    })
                elif response.status_code == 404:
                    print(f"  ✗ API endpoint not found: {endpoint}")
                    self.broken_links.append({
                        'page': 'api_endpoints',
                        'type': 'api',
                        'url': endpoint,
                        'status_code': 404,
                        'error': 'Endpoint not implemented'
                    })
                else:
                    print(f"  ⚠ API endpoint warning: {endpoint} ({response.status_code})")
                    self.broken_links.append({
                        'page': 'api_endpoints',
                        'type': 'api',
                        'url': endpoint,
                        'status_code': response.status_code,
                        'error': f'Unexpected status: {response.status_code}'
                    })
                    
            except Exception as e:
                print(f"  ✗ API endpoint error: {endpoint} ({e})")
                self.broken_links.append({
                    'page': 'api_endpoints',
                    'type': 'api',
                    'url': endpoint,
                    'error': str(e)
                })
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive link verification report"""
        
        total_links = len(self.working_links) + len(self.broken_links)
        success_rate = (len(self.working_links) / total_links * 100) if total_links > 0 else 0
        
        report = {
            'verification_timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_links_tested': total_links,
            'working_links': len(self.working_links),
            'broken_links': len(self.broken_links),
            'success_rate': success_rate,
            'status': 'GOOD' if success_rate >= 90 else 'WARNING' if success_rate >= 70 else 'CRITICAL',
            'detailed_results': {
                'working_links': self.working_links,
                'broken_links': self.broken_links
            },
            'summary_by_type': self.generate_type_summary(),
            'recommendations': self.generate_recommendations()
        }
        
        self.print_summary(report)
        self.save_report(report)
        
        return report
    
    def generate_type_summary(self) -> Dict[str, Any]:
        """Generate summary by link type"""
        summary = {}
        
        # Count by type for working links
        for link in self.working_links:
            link_type = link.get('type', 'unknown')
            if link_type not in summary:
                summary[link_type] = {'working': 0, 'broken': 0}
            summary[link_type]['working'] += 1
        
        # Count by type for broken links
        for link in self.broken_links:
            link_type = link.get('type', 'unknown')
            if link_type not in summary:
                summary[link_type] = {'working': 0, 'broken': 0}
            summary[link_type]['broken'] += 1
        
        return summary
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on broken links"""
        recommendations = []
        
        if len(self.broken_links) == 0:
            recommendations.append("All links are working correctly!")
            return recommendations
        
        # Analyze broken links
        broken_by_type = {}
        for link in self.broken_links:
            link_type = link.get('type', 'unknown')
            if link_type not in broken_by_type:
                broken_by_type[link_type] = []
            broken_by_type[link_type].append(link)
        
        for link_type, links in broken_by_type.items():
            if link_type == 'internal':
                recommendations.append(f"Fix {len(links)} internal links that return 404 or errors")
            elif link_type == 'api':
                recommendations.append(f"Implement {len(links)} missing API endpoints")
            elif link_type == 'fragment':
                recommendations.append(f"Add missing anchor targets for {len(links)} fragment links")
            elif link_type == 'javascript':
                recommendations.append(f"Fix JavaScript syntax in {len(links)} links")
            elif link_type == 'external':
                recommendations.append(f"Update or remove {len(links)} broken external links")
        
        return recommendations
    
    def print_summary(self, report: Dict[str, Any]):
        """Print verification summary"""
        print(f"\n{'='*50}")
        print("LINK VERIFICATION SUMMARY")
        print(f"{'='*50}")
        print(f"Base URL: {report['base_url']}")
        print(f"Total Links Tested: {report['total_links_tested']}")
        print(f"Working Links: {report['working_links']}")
        print(f"Broken Links: {report['broken_links']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"Overall Status: {report['status']}")
        
        if report['broken_links'] > 0:
            print(f"\nBROKEN LINKS FOUND:")
            for i, link in enumerate(report['detailed_results']['broken_links'], 1):
                page = link.get('page', 'unknown')
                url = link.get('url', link.get('code', 'unknown'))
                error = link.get('error', f"Status: {link.get('status_code', 'unknown')}")
                print(f"  {i}. [{page}] {url} - {error}")
        
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"{'='*50}")
    
    def save_report(self, report: Dict[str, Any]) -> str:
        """Save verification report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"link_verification_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Report saved: {filename}")
            return filename
        except Exception as e:
            print(f"Failed to save report: {e}")
            return ""


def main():
    """Execute link verification"""
    verifier = MITOLinkVerifier()
    return verifier.verify_all_links()


if __name__ == "__main__":
    main()