#!/usr/bin/env python3
"""
Search Engine with Package Manager Demo
Comprehensive demonstration of the search engine and package management system.
"""

import os
import sys
import time
import json
from search_engine import SearchEngine
from search_package_manager import PackageManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_search_engine():
    """Demonstrate search engine capabilities"""
    print("=" * 60)
    print("SEARCH ENGINE DEMONSTRATION")
    print("=" * 60)
    
    # Initialize search engine
    search_engine = SearchEngine()
    
    # Sample URLs to crawl (educational websites)
    seed_urls = [
        "https://docs.python.org/3/",
        "https://flask.palletsprojects.com/",
        "https://www.nltk.org/",
        "https://scikit-learn.org/stable/",
        "https://requests.readthedocs.io/"
    ]
    
    print("\n1. Crawling sample educational websites...")
    print(f"Seed URLs: {len(seed_urls)} sites")
    
    try:
        pages_crawled = search_engine.crawl_urls(seed_urls, max_depth=1, max_pages=50)
        print(f"Successfully crawled {pages_crawled} pages")
    except Exception as e:
        print(f"Crawling failed: {e}")
        return False
    
    # Get search engine statistics
    print("\n2. Search Engine Statistics:")
    stats = search_engine.get_stats()
    print(f"   Total Pages: {stats['total_pages']}")
    print(f"   Total Domains: {stats['total_domains']}")
    print(f"   Index Entries: {stats['index_entries']}")
    
    if stats['top_domains']:
        print("   Top Domains:")
        for domain, count in stats['top_domains'][:5]:
            print(f"     {domain}: {count} pages")
    
    # Demonstrate search functionality
    print("\n3. Search Demonstrations:")
    
    search_queries = [
        "python programming",
        "flask web framework",
        "machine learning",
        "natural language processing",
        "HTTP requests"
    ]
    
    for query in search_queries:
        print(f"\n   Query: '{query}'")
        results = search_engine.search(query, max_results=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"     {i}. {result.title}")
                print(f"        URL: {result.url}")
                print(f"        Score: {result.score:.3f}")
                print(f"        Snippet: {result.snippet[:100]}...")
        else:
            print("     No results found")
    
    return True

def demo_package_manager():
    """Demonstrate package manager capabilities"""
    print("\n" + "=" * 60)
    print("PACKAGE MANAGER DEMONSTRATION")
    print("=" * 60)
    
    # Initialize package manager
    pm = PackageManager()
    
    print("\n1. Package Manager Configuration:")
    print(f"   Database: {pm.db.db_path}")
    print(f"   Install Root: {pm.installer.install_root}")
    print(f"   Sources: {len(pm.config.get('sources', []))}")
    
    # Create sample packages for demonstration
    sample_packages = [
        "search-indexer",
        "web-crawler-utils",
        "text-processor",
        "ranking-algorithms",
        "search-analytics"
    ]
    
    print("\n2. Installing sample packages:")
    installed_packages = []
    
    for package in sample_packages:
        print(f"   Installing {package}...")
        try:
            if pm.install(package):
                installed_packages.append(package)
                print(f"   ✓ {package} installed successfully")
            else:
                print(f"   ✗ {package} installation failed")
        except Exception as e:
            print(f"   ✗ {package} error: {e}")
    
    # List installed packages
    print("\n3. Installed Packages:")
    packages = pm.list_packages()
    
    if packages:
        for pkg in packages:
            print(f"   {pkg['name']} v{pkg['version']}")
            print(f"     Path: {pkg['install_path']}")
            print(f"     Installed: {pkg['installed_at']}")
    else:
        print("   No packages installed")
    
    # Demonstrate package information
    if installed_packages:
        sample_pkg = installed_packages[0]
        print(f"\n4. Package Information for '{sample_pkg}':")
        info = pm.get_info(sample_pkg)
        
        if info:
            for key, value in info.items():
                if key not in ['id', 'dependencies']:
                    print(f"   {key}: {value}")
        
        # Verify package installation
        print(f"\n5. Verifying '{sample_pkg}' installation:")
        is_valid = pm.verify_installation(sample_pkg)
        print(f"   Verification: {'PASSED' if is_valid else 'FAILED'}")
    
    # Cleanup demonstration
    print("\n6. Package Cleanup:")
    try:
        if pm.cleanup():
            print("   ✓ Cleanup completed successfully")
        else:
            print("   ✗ Cleanup failed")
    except Exception as e:
        print(f"   ✗ Cleanup error: {e}")
    
    return True

def demo_integration():
    """Demonstrate integration between search engine and package manager"""
    print("\n" + "=" * 60)
    print("INTEGRATION DEMONSTRATION")
    print("=" * 60)
    
    print("\n1. Search Engine Extensions via Package Manager:")
    
    # Simulate installing search engine extensions
    extensions = [
        "semantic-search",
        "image-indexer", 
        "pdf-processor",
        "spell-checker",
        "query-autocomplete"
    ]
    
    pm = PackageManager()
    search_engine = SearchEngine()
    
    for ext in extensions:
        print(f"   Installing extension: {ext}")
        if pm.install(ext):
            print(f"   ✓ Extension {ext} ready for integration")
        else:
            print(f"   ✗ Extension {ext} installation failed")
    
    print("\n2. Enhanced Search Capabilities:")
    print("   Available after extensions:")
    print("   - Semantic similarity search")
    print("   - Image content indexing") 
    print("   - PDF document processing")
    print("   - Automatic spell correction")
    print("   - Query auto-completion")
    
    print("\n3. Plugin Architecture:")
    print("   Search engine supports modular extensions through:")
    print("   - Package-based plugin system")
    print("   - Dependency management")
    print("   - Version compatibility checks")
    print("   - Automatic updates")
    
    return True

def performance_benchmark():
    """Run performance benchmarks"""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    search_engine = SearchEngine()
    
    print("\n1. Search Performance Test:")
    
    test_queries = [
        "python", "web development", "machine learning", 
        "data science", "artificial intelligence"
    ]
    
    total_time = 0
    total_results = 0
    
    for query in test_queries:
        start_time = time.time()
        results = search_engine.search(query, max_results=10)
        end_time = time.time()
        
        query_time = end_time - start_time
        total_time += query_time
        total_results += len(results)
        
        print(f"   Query: '{query}' - {len(results)} results in {query_time:.3f}s")
    
    avg_time = total_time / len(test_queries)
    avg_results = total_results / len(test_queries)
    
    print(f"\n   Average Performance:")
    print(f"   - Query time: {avg_time:.3f} seconds")
    print(f"   - Results per query: {avg_results:.1f}")
    print(f"   - Total time: {total_time:.3f} seconds")
    
    return True

def main():
    """Main demonstration function"""
    print("ADVANCED SEARCH ENGINE & PACKAGE MANAGER")
    print("Complete demonstration of web crawling, indexing, search, and package management")
    print("Created for educational and development purposes")
    
    try:
        # Run demonstrations
        success = True
        
        # Demo search engine
        if not demo_search_engine():
            success = False
            
        # Demo package manager  
        if not demo_package_manager():
            success = False
            
        # Demo integration
        if not demo_integration():
            success = False
            
        # Run benchmarks
        if not performance_benchmark():
            success = False
        
        print("\n" + "=" * 60)
        if success:
            print("DEMONSTRATION COMPLETED SUCCESSFULLY")
            print("\nNext Steps:")
            print("1. Customize crawling URLs for your domain")
            print("2. Install additional packages as needed")
            print("3. Configure search ranking parameters")
            print("4. Set up automated crawling schedules")
            print("5. Implement user interface for search")
        else:
            print("DEMONSTRATION COMPLETED WITH SOME ISSUES")
            print("Check the logs above for specific error details")
            
        print("\nUsage Examples:")
        print("# Search Engine CLI:")
        print("python search_engine.py --crawl https://example.com --max-pages 100")
        print("python search_engine.py --search 'your query here'")
        print("python search_engine.py --stats")
        print("\n# Package Manager CLI:")
        print("python search_package_manager.py install package-name")
        print("python search_package_manager.py list")
        print("python search_package_manager.py update package-name")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user")
    except Exception as e:
        print(f"\n\nDemonstration failed with error: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)

if __name__ == "__main__":
    main()