"""
MITO Engine - Web Scraper Manager
Complete web scraping and content extraction system
"""

import requests
import trafilatura
from bs4 import BeautifulSoup
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path
import csv
import sqlite3

class ScrapedContent:
    """Scraped content data structure"""
    
    def __init__(self, url: str, title: str = None, content: str = None,
                 metadata: Dict[str, Any] = None):
        self.url = url
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        self.scraped_at = datetime.now().isoformat()
        self.content_type = "text"
        self.word_count = len(content.split()) if content else 0

class WebScraperManager:
    """Complete web scraping and content extraction system"""
    
    def __init__(self, db_path: str = "scraper.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MITO Engine Scraper 1.0 (Educational/Research Purpose)'
        })
        self.delay_between_requests = 1.0  # seconds
        self.timeout = 30
        self.max_retries = 3
        
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize scraper database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Scraped content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                content_type TEXT DEFAULT 'text',
                word_count INTEGER DEFAULT 0,
                metadata TEXT,
                scraped_at TEXT NOT NULL,
                status TEXT DEFAULT 'success'
            )
        ''')
        
        # Scraping jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                urls TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                total_urls INTEGER DEFAULT 0,
                processed_urls INTEGER DEFAULT 0,
                failed_urls INTEGER DEFAULT 0,
                config TEXT
            )
        ''')
        
        # URL queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                url TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                last_attempt TEXT,
                error_message TEXT,
                FOREIGN KEY (job_id) REFERENCES scraping_jobs (job_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def scrape_url(self, url: str, extract_content: bool = True, 
                   extract_links: bool = False) -> Dict[str, Any]:
        """Scrape single URL"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {"success": False, "error": "Invalid URL format"}
            
            # Make request with retries
            response = None
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    if attempt == self.max_retries - 1:
                        return {"success": False, "error": f"Failed to fetch URL: {str(e)}"}
                    time.sleep(self.delay_between_requests * (attempt + 1))
            
            if not response:
                return {"success": False, "error": "Failed to get response"}
            
            # Extract content using trafilatura
            content = ""
            title = ""
            
            if extract_content:
                # Use trafilatura for main content extraction
                content = trafilatura.extract(response.text)
                if not content:
                    content = ""
                
                # Use BeautifulSoup for title and additional metadata
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                title = title_tag.get_text().strip() if title_tag else ""
            
            # Extract metadata
            metadata = {
                "status_code": response.status_code,
                "content_length": len(response.text),
                "content_type": response.headers.get('content-type', ''),
                "encoding": response.encoding,
                "final_url": response.url
            }
            
            # Extract links if requested
            if extract_links:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(url, href)
                    link_text = link.get_text().strip()
                    links.append({
                        "url": absolute_url,
                        "text": link_text,
                        "internal": urlparse(absolute_url).netloc == parsed_url.netloc
                    })
                metadata["links"] = links
                metadata["link_count"] = len(links)
            
            # Create scraped content object
            scraped_content = ScrapedContent(url, title, content, metadata)
            
            # Store in database
            self._store_scraped_content(scraped_content)
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "content": content,
                "metadata": metadata,
                "word_count": scraped_content.word_count,
                "scraped_at": scraped_content.scraped_at
            }
            
            if extract_links:
                result["links"] = metadata.get("links", [])
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scrape_multiple_urls(self, urls: List[str], job_name: str = None,
                           delay: float = None, extract_links: bool = False) -> Dict[str, Any]:
        """Scrape multiple URLs"""
        try:
            if delay:
                self.delay_between_requests = delay
            
            job_id = f"job_{int(time.time())}"
            if not job_name:
                job_name = f"Scraping Job {job_id}"
            
            # Create scraping job
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scraping_jobs (job_id, name, urls, total_urls, created_at, config)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job_id, job_name, json.dumps(urls), len(urls), 
                  datetime.now().isoformat(), json.dumps({"extract_links": extract_links})))
            
            # Add URLs to queue
            for i, url in enumerate(urls):
                cursor.execute('''
                    INSERT INTO url_queue (job_id, url, priority)
                    VALUES (?, ?, ?)
                ''', (job_id, url, i + 1))
            
            conn.commit()
            
            # Start scraping
            cursor.execute("UPDATE scraping_jobs SET status = ?, started_at = ? WHERE job_id = ?",
                          ("running", datetime.now().isoformat(), job_id))
            conn.commit()
            
            results = []
            processed = 0
            failed = 0
            
            for url in urls:
                try:
                    # Update URL status
                    cursor.execute('''
                        UPDATE url_queue SET status = ?, last_attempt = ?, attempts = attempts + 1
                        WHERE job_id = ? AND url = ?
                    ''', ("processing", datetime.now().isoformat(), job_id, url))
                    conn.commit()
                    
                    # Scrape URL
                    result = self.scrape_url(url, extract_links=extract_links)
                    results.append(result)
                    
                    if result["success"]:
                        processed += 1
                        cursor.execute('''
                            UPDATE url_queue SET status = ? WHERE job_id = ? AND url = ?
                        ''', ("completed", job_id, url))
                    else:
                        failed += 1
                        cursor.execute('''
                            UPDATE url_queue SET status = ?, error_message = ?
                            WHERE job_id = ? AND url = ?
                        ''', ("failed", result.get("error", "Unknown error"), job_id, url))
                    
                    conn.commit()
                    
                    # Delay between requests
                    if url != urls[-1]:  # Don't delay after last URL
                        time.sleep(self.delay_between_requests)
                        
                except Exception as e:
                    failed += 1
                    cursor.execute('''
                        UPDATE url_queue SET status = ?, error_message = ?
                        WHERE job_id = ? AND url = ?
                    ''', ("failed", str(e), job_id, url))
                    results.append({"success": False, "url": url, "error": str(e)})
                    conn.commit()
            
            # Update job status
            cursor.execute('''
                UPDATE scraping_jobs SET status = ?, completed_at = ?, processed_urls = ?, failed_urls = ?
                WHERE job_id = ?
            ''', ("completed", datetime.now().isoformat(), processed, failed, job_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "job_id": job_id,
                "job_name": job_name,
                "total_urls": len(urls),
                "processed": processed,
                "failed": failed,
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_and_scrape(self, search_query: str, search_engine: str = "duckduckgo",
                         max_results: int = 10) -> Dict[str, Any]:
        """Search web and scrape results"""
        try:
            # Get search results
            search_results = self.web_search(search_query, search_engine, max_results)
            
            if not search_results["success"]:
                return search_results
            
            # Extract URLs from search results
            urls = [result["url"] for result in search_results["results"]]
            
            # Scrape the URLs
            scraping_result = self.scrape_multiple_urls(
                urls, 
                job_name=f"Search: {search_query}",
                extract_links=False
            )
            
            return {
                "success": True,
                "search_query": search_query,
                "search_engine": search_engine,
                "search_results": search_results["results"],
                "scraping_job": scraping_result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def web_search(self, query: str, search_engine: str = "duckduckgo", 
                   max_results: int = 10) -> Dict[str, Any]:
        """Perform web search"""
        try:
            if search_engine == "duckduckgo":
                return self._duckduckgo_search(query, max_results)
            else:
                return {"success": False, "error": f"Unsupported search engine: {search_engine}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _duckduckgo_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo"""
        try:
            # Simple DuckDuckGo search (this is a basic implementation)
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result__body')
            
            for div in result_divs[:max_results]:
                title_link = div.find('a', class_='result__a')
                snippet_span = div.find('a', class_='result__snippet')
                
                if title_link:
                    title = title_link.get_text().strip()
                    url = title_link.get('href', '')
                    snippet = snippet_span.get_text().strip() if snippet_span else ""
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_data_from_page(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract specific data from page using CSS selectors"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            extracted_data = {}
            
            for field_name, selector in selectors.items():
                elements = soup.select(selector)
                
                if len(elements) == 1:
                    # Single element
                    element = elements[0]
                    extracted_data[field_name] = element.get_text().strip()
                elif len(elements) > 1:
                    # Multiple elements
                    extracted_data[field_name] = [elem.get_text().strip() for elem in elements]
                else:
                    # No elements found
                    extracted_data[field_name] = None
            
            return {
                "success": True,
                "url": url,
                "data": extracted_data,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scrape_sitemap(self, sitemap_url: str) -> Dict[str, Any]:
        """Scrape URLs from sitemap"""
        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse sitemap XML
            soup = BeautifulSoup(response.text, 'xml')
            
            urls = []
            
            # Standard sitemap format
            for url_tag in soup.find_all('url'):
                loc_tag = url_tag.find('loc')
                if loc_tag:
                    url_info = {
                        "url": loc_tag.get_text().strip(),
                        "lastmod": None,
                        "priority": None,
                        "changefreq": None
                    }
                    
                    # Extract additional sitemap data
                    lastmod_tag = url_tag.find('lastmod')
                    if lastmod_tag:
                        url_info["lastmod"] = lastmod_tag.get_text().strip()
                    
                    priority_tag = url_tag.find('priority')
                    if priority_tag:
                        url_info["priority"] = priority_tag.get_text().strip()
                    
                    changefreq_tag = url_tag.find('changefreq')
                    if changefreq_tag:
                        url_info["changefreq"] = changefreq_tag.get_text().strip()
                    
                    urls.append(url_info)
            
            return {
                "success": True,
                "sitemap_url": sitemap_url,
                "urls": urls,
                "count": len(urls)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def monitor_page_changes(self, url: str, check_interval: int = 3600) -> Dict[str, Any]:
        """Monitor page for changes"""
        try:
            # Get current content
            current_result = self.scrape_url(url)
            if not current_result["success"]:
                return current_result
            
            current_content = current_result["content"]
            current_hash = hashlib.md5(current_content.encode()).hexdigest()
            
            # Check if we have previous content
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content, metadata FROM scraped_content 
                WHERE url = ? ORDER BY scraped_at DESC LIMIT 1
            ''', (url,))
            
            previous_data = cursor.fetchone()
            
            if previous_data:
                previous_content = previous_data[0]
                previous_metadata = json.loads(previous_data[1]) if previous_data[1] else {}
                previous_hash = previous_metadata.get("content_hash")
                
                if previous_hash and previous_hash != current_hash:
                    # Content has changed
                    changes = self._detect_content_changes(previous_content, current_content)
                    
                    conn.close()
                    return {
                        "success": True,
                        "url": url,
                        "changed": True,
                        "changes": changes,
                        "current_hash": current_hash,
                        "previous_hash": previous_hash
                    }
                else:
                    conn.close()
                    return {
                        "success": True,
                        "url": url,
                        "changed": False,
                        "message": "No changes detected"
                    }
            else:
                # First time monitoring this URL
                conn.close()
                return {
                    "success": True,
                    "url": url,
                    "changed": False,
                    "message": "Baseline content stored for future monitoring"
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def export_scraped_data(self, output_format: str = "json", 
                           job_id: str = None, filename: str = None) -> Dict[str, Any]:
        """Export scraped data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if job_id:
                # Export specific job data
                cursor.execute('''
                    SELECT sc.url, sc.title, sc.content, sc.metadata, sc.scraped_at
                    FROM scraped_content sc
                    JOIN url_queue uq ON sc.url = uq.url
                    WHERE uq.job_id = ? AND uq.status = 'completed'
                ''', (job_id,))
            else:
                # Export all data
                cursor.execute('''
                    SELECT url, title, content, metadata, scraped_at
                    FROM scraped_content
                ''')
            
            data = cursor.fetchall()
            conn.close()
            
            if not data:
                return {"success": False, "error": "No data to export"}
            
            # Convert to list of dictionaries
            export_data = []
            for row in data:
                item = {
                    "url": row[0],
                    "title": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "scraped_at": row[4]
                }
                export_data.append(item)
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scraped_data_{timestamp}"
            
            # Export based on format
            if output_format == "json":
                filename += ".json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif output_format == "csv":
                filename += ".csv"
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    if export_data:
                        writer = csv.DictWriter(f, fieldnames=["url", "title", "content", "scraped_at"])
                        writer.writeheader()
                        for item in export_data:
                            writer.writerow({
                                "url": item["url"],
                                "title": item["title"],
                                "content": item["content"],
                                "scraped_at": item["scraped_at"]
                            })
            
            elif output_format == "txt":
                filename += ".txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    for item in export_data:
                        f.write(f"URL: {item['url']}\n")
                        f.write(f"Title: {item['title']}\n")
                        f.write(f"Scraped: {item['scraped_at']}\n")
                        f.write("Content:\n")
                        f.write(item['content'])
                        f.write("\n" + "="*80 + "\n\n")
            
            else:
                return {"success": False, "error": f"Unsupported export format: {output_format}"}
            
            return {
                "success": True,
                "filename": filename,
                "format": output_format,
                "records": len(export_data),
                "message": f"Data exported to {filename}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_scraping_jobs(self) -> List[Dict[str, Any]]:
        """Get all scraping jobs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_id, name, status, created_at, started_at, completed_at,
                       total_urls, processed_urls, failed_urls
                FROM scraping_jobs ORDER BY created_at DESC
            ''')
            
            jobs = []
            for row in cursor.fetchall():
                jobs.append({
                    "job_id": row[0],
                    "name": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "started_at": row[4],
                    "completed_at": row[5],
                    "total_urls": row[6],
                    "processed_urls": row[7],
                    "failed_urls": row[8]
                })
            
            conn.close()
            return jobs
            
        except Exception:
            return []
    
    def _store_scraped_content(self, content: ScrapedContent):
        """Store scraped content in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO scraped_content 
                (url, title, content, content_type, word_count, metadata, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (content.url, content.title, content.content, content.content_type,
                  content.word_count, json.dumps(content.metadata), content.scraped_at))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def _detect_content_changes(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Detect changes between content versions"""
        import difflib
        
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        return {
            "lines_added": len([line for line in diff if line.startswith('+')]),
            "lines_removed": len([line for line in diff if line.startswith('-')]),
            "total_changes": len(diff),
            "diff_preview": diff[:20]  # First 20 lines of diff
        }

# Global web scraper manager instance
web_scraper = WebScraperManager()

def main():
    """Demo of web scraper functionality"""
    
    # Scrape a single URL
    result = web_scraper.scrape_url("https://example.com")
    print("Single URL scraping:", json.dumps(result, indent=2))
    
    # Search and scrape
    search_result = web_scraper.search_and_scrape("Python programming", max_results=3)
    print("Search and scrape:", json.dumps(search_result, indent=2))
    
    # Get scraping jobs
    jobs = web_scraper.get_scraping_jobs()
    print("Scraping jobs:", json.dumps(jobs, indent=2))

if __name__ == "__main__":
    main()