#!/usr/bin/env python3
"""
Knowledge Base Management System for MITO Engine
Continuously updates with latest trends, technologies, and best practices
"""

import os
import json
import sqlite3
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import feedparser
import hashlib
from urllib.parse import urljoin, urlparse
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import schedule
import openai
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeArticle:
    """Represents a knowledge base article"""
    id: str
    title: str
    content: str
    summary: str
    category: str
    tags: List[str]
    source_url: str
    source_type: str
    author: str
    published_at: str
    relevance_score: float
    last_updated: str

@dataclass
class TrendData:
    """Represents technology trend data"""
    id: str
    technology: str
    trend_type: str
    popularity_score: float
    growth_rate: float
    adoption_level: str
    market_data: Dict[str, Any]
    predictions: List[str]
    related_technologies: List[str]
    detected_at: str

class KnowledgeDatabase:
    """Database for knowledge base content"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize knowledge base database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                category TEXT NOT NULL,
                tags TEXT,
                source_url TEXT,
                source_type TEXT,
                author TEXT,
                published_at TIMESTAMP,
                relevance_score REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id TEXT PRIMARY KEY,
                technology TEXT NOT NULL,
                trend_type TEXT NOT NULL,
                popularity_score REAL NOT NULL,
                growth_rate REAL NOT NULL,
                adoption_level TEXT NOT NULL,
                market_data TEXT,
                predictions TEXT,
                related_technologies TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT NOT NULL,
                category TEXT,
                update_frequency TEXT,
                last_crawled TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                reliability_score REAL DEFAULT 1.0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_feedback INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS update_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_type TEXT NOT NULL,
                source TEXT,
                items_processed INTEGER,
                success_rate REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()

class ContentAggregator:
    """Aggregates content from various sources"""
    
    def __init__(self, db: KnowledgeDatabase):
        self.db = db
        self.openai_client = None
        if os.environ.get("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Initialize sources
        self.init_default_sources()
        
    def init_default_sources(self):
        """Initialize default knowledge sources"""
        default_sources = [
            {
                'name': 'Hacker News',
                'url': 'https://hnrss.org/frontpage',
                'source_type': 'rss',
                'category': 'technology',
                'update_frequency': 'hourly'
            },
            {
                'name': 'GitHub Trending',
                'url': 'https://github.com/trending',
                'source_type': 'web',
                'category': 'development',
                'update_frequency': 'daily'
            },
            {
                'name': 'Stack Overflow Blog',
                'url': 'https://stackoverflow.blog/feed/',
                'source_type': 'rss',
                'category': 'programming',
                'update_frequency': 'daily'
            },
            {
                'name': 'AWS What\'s New',
                'url': 'https://aws.amazon.com/about-aws/whats-new/recent/feed/',
                'source_type': 'rss',
                'category': 'cloud',
                'update_frequency': 'daily'
            },
            {
                'name': 'Google AI Blog',
                'url': 'https://ai.googleblog.com/feeds/posts/default',
                'source_type': 'rss',
                'category': 'ai',
                'update_frequency': 'weekly'
            },
            {
                'name': 'Microsoft DevBlogs',
                'url': 'https://devblogs.microsoft.com/feed/',
                'source_type': 'rss',
                'category': 'development',
                'update_frequency': 'daily'
            },
            {
                'name': 'Mozilla Hacks',
                'url': 'https://hacks.mozilla.org/feed/',
                'source_type': 'rss',
                'category': 'web',
                'update_frequency': 'weekly'
            }
        ]
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for source in default_sources:
            cursor.execute("""
                INSERT OR IGNORE INTO sources (name, url, source_type, category, update_frequency)
                VALUES (?, ?, ?, ?, ?)
            """, (source['name'], source['url'], source['source_type'], 
                  source['category'], source['update_frequency']))
        
        conn.commit()
        conn.close()
        
    def crawl_rss_feeds(self) -> List[KnowledgeArticle]:
        """Crawl RSS feeds for new content"""
        articles = []
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, url, category FROM sources 
            WHERE source_type = 'rss' AND is_active = TRUE
        """)
        
        sources = cursor.fetchall()
        conn.close()
        
        for source_name, url, category in sources:
            try:
                logger.info(f"Crawling RSS feed: {source_name}")
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:10]:  # Limit to 10 recent entries
                    article_id = hashlib.md5(f"{entry.link}_{entry.title}".encode()).hexdigest()
                    
                    # Check if article already exists
                    if self._article_exists(article_id):
                        continue
                    
                    # Extract content
                    content = entry.get('description', '') or entry.get('summary', '')
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].value
                    
                    # Clean content
                    content = self._clean_html(content)
                    
                    # Generate summary
                    summary = self._generate_summary(content, entry.title)
                    
                    # Extract tags
                    tags = self._extract_tags(entry.title, content, category)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance(entry.title, content, tags)
                    
                    article = KnowledgeArticle(
                        id=article_id,
                        title=entry.title,
                        content=content,
                        summary=summary,
                        category=category,
                        tags=tags,
                        source_url=entry.link,
                        source_type='rss',
                        author=entry.get('author', source_name),
                        published_at=entry.get('published', datetime.now().isoformat()),
                        relevance_score=relevance_score,
                        last_updated=datetime.now().isoformat()
                    )
                    
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Failed to crawl RSS feed {source_name}: {e}")
                
        return articles
        
    def crawl_github_trending(self) -> List[KnowledgeArticle]:
        """Crawl GitHub trending repositories"""
        articles = []
        
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': 'created:>=' + (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'sort': 'stars',
                'order': 'desc',
                'per_page': 20
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for repo in data.get('items', []):
                article_id = f"github_{repo['id']}"
                
                if self._article_exists(article_id):
                    continue
                
                # Extract programming language and topics as tags
                tags = [repo['language']] if repo['language'] else []
                tags.extend(repo.get('topics', []))
                
                # Generate content
                content = f"""
                Repository: {repo['full_name']}
                Description: {repo['description']}
                Language: {repo['language']}
                Stars: {repo['stargazers_count']}
                Forks: {repo['forks_count']}
                Created: {repo['created_at']}
                Updated: {repo['updated_at']}
                """
                
                summary = repo['description'][:200] if repo['description'] else f"Trending {repo['language']} repository"
                
                article = KnowledgeArticle(
                    id=article_id,
                    title=f"Trending: {repo['full_name']}",
                    content=content,
                    summary=summary,
                    category='development',
                    tags=tags,
                    source_url=repo['html_url'],
                    source_type='github',
                    author=repo['owner']['login'],
                    published_at=repo['created_at'],
                    relevance_score=min(repo['stargazers_count'] / 1000.0, 1.0),
                    last_updated=datetime.now().isoformat()
                )
                
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Failed to crawl GitHub trending: {e}")
            
        return articles
        
    def _article_exists(self, article_id: str) -> bool:
        """Check if article already exists"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM articles WHERE id = ?", (article_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
        
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True)
        except:
            return html_content
            
    def _generate_summary(self, content: str, title: str) -> str:
        """Generate article summary"""
        if not self.openai_client:
            # Fallback to first 200 characters
            return content[:200] + "..." if len(content) > 200 else content
            
        try:
            prompt = f"Summarize this article in 2-3 sentences:\n\nTitle: {title}\n\nContent: {content[:1000]}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Failed to generate AI summary: {e}")
            return content[:200] + "..." if len(content) > 200 else content
            
    def _extract_tags(self, title: str, content: str, category: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = [category]
        
        # Technology keywords
        tech_keywords = {
            'python', 'javascript', 'java', 'go', 'rust', 'typescript', 'react', 'vue', 'angular',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'tensorflow', 'pytorch', 'machine learning',
            'ai', 'blockchain', 'web3', 'microservices', 'devops', 'cicd', 'api', 'rest', 'graphql',
            'database', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'security', 'testing'
        }
        
        text_lower = (title + " " + content).lower()
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                tags.append(keyword)
                
        return list(set(tags))  # Remove duplicates
        
    def _calculate_relevance(self, title: str, content: str, tags: List[str]) -> float:
        """Calculate content relevance score"""
        score = 0.0
        
        # High-priority keywords
        high_priority = ['ai', 'machine learning', 'python', 'javascript', 'cloud', 'security', 'devops']
        medium_priority = ['api', 'database', 'framework', 'library', 'tool']
        
        text_lower = (title + " " + content).lower()
        
        for keyword in high_priority:
            if keyword in text_lower:
                score += 0.3
                
        for keyword in medium_priority:
            if keyword in text_lower:
                score += 0.2
                
        # Boost score based on number of relevant tags
        score += len([tag for tag in tags if tag in high_priority + medium_priority]) * 0.1
        
        return min(score, 1.0)

class TrendAnalyzer:
    """Analyzes technology trends and market data"""
    
    def __init__(self, db: KnowledgeDatabase):
        self.db = db
        
    def analyze_github_trends(self) -> List[TrendData]:
        """Analyze GitHub trends"""
        trends = []
        
        try:
            # Get trending repositories by language
            languages = ['python', 'javascript', 'typescript', 'go', 'rust', 'java']
            
            for language in languages:
                url = "https://api.github.com/search/repositories"
                params = {
                    'q': f'language:{language} created:>=' + (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 50
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                total_repos = len(data.get('items', []))
                total_stars = sum(repo['stargazers_count'] for repo in data.get('items', []))
                
                # Calculate trend metrics
                popularity_score = min(total_stars / 10000.0, 1.0)
                growth_rate = self._calculate_language_growth(language)
                adoption_level = self._determine_adoption_level(popularity_score)
                
                trend = TrendData(
                    id=f"github_trend_{language}_{datetime.now().strftime('%Y%m%d')}",
                    technology=language,
                    trend_type='programming_language',
                    popularity_score=popularity_score,
                    growth_rate=growth_rate,
                    adoption_level=adoption_level,
                    market_data={
                        'total_repositories': total_repos,
                        'total_stars': total_stars,
                        'avg_stars_per_repo': total_stars / total_repos if total_repos > 0 else 0
                    },
                    predictions=self._generate_predictions(language, popularity_score, growth_rate),
                    related_technologies=self._get_related_technologies(language),
                    detected_at=datetime.now().isoformat()
                )
                
                trends.append(trend)
                
        except Exception as e:
            logger.error(f"Failed to analyze GitHub trends: {e}")
            
        return trends
        
    def analyze_stackoverflow_trends(self) -> List[TrendData]:
        """Analyze Stack Overflow trends"""
        trends = []
        
        try:
            # Stack Overflow API for tag statistics
            url = "https://api.stackexchange.com/2.3/tags"
            params = {
                'order': 'desc',
                'sort': 'popular',
                'site': 'stackoverflow',
                'pagesize': 50
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for tag_data in data.get('items', []):
                tag_name = tag_data['name']
                count = tag_data['count']
                
                # Focus on technology tags
                if not self._is_technology_tag(tag_name):
                    continue
                
                popularity_score = min(count / 100000.0, 1.0)
                growth_rate = self._estimate_tag_growth(tag_name, count)
                adoption_level = self._determine_adoption_level(popularity_score)
                
                trend = TrendData(
                    id=f"stackoverflow_trend_{tag_name}_{datetime.now().strftime('%Y%m%d')}",
                    technology=tag_name,
                    trend_type='technology_tag',
                    popularity_score=popularity_score,
                    growth_rate=growth_rate,
                    adoption_level=adoption_level,
                    market_data={
                        'question_count': count,
                        'has_synonyms': tag_data.get('has_synonyms', False),
                        'is_moderator_only': tag_data.get('is_moderator_only', False)
                    },
                    predictions=self._generate_predictions(tag_name, popularity_score, growth_rate),
                    related_technologies=self._get_related_technologies(tag_name),
                    detected_at=datetime.now().isoformat()
                )
                
                trends.append(trend)
                
        except Exception as e:
            logger.error(f"Failed to analyze Stack Overflow trends: {e}")
            
        return trends
        
    def _calculate_language_growth(self, language: str) -> float:
        """Calculate language growth rate"""
        # Simplified growth calculation
        # In production, this would analyze historical data
        growth_rates = {
            'python': 0.15,
            'javascript': 0.10,
            'typescript': 0.25,
            'go': 0.20,
            'rust': 0.30,
            'java': 0.05
        }
        
        return growth_rates.get(language, 0.10)
        
    def _determine_adoption_level(self, popularity_score: float) -> str:
        """Determine technology adoption level"""
        if popularity_score >= 0.8:
            return 'mainstream'
        elif popularity_score >= 0.5:
            return 'growing'
        elif popularity_score >= 0.2:
            return 'emerging'
        else:
            return 'experimental'
            
    def _generate_predictions(self, technology: str, popularity: float, growth: float) -> List[str]:
        """Generate trend predictions"""
        predictions = []
        
        if growth > 0.2:
            predictions.append(f"{technology} expected to see significant growth in next 12 months")
        
        if popularity > 0.7:
            predictions.append(f"{technology} likely to maintain dominant position")
        elif popularity > 0.4 and growth > 0.15:
            predictions.append(f"{technology} may become mainstream technology")
        
        if growth < 0.05:
            predictions.append(f"{technology} growth may be plateauing")
            
        return predictions
        
    def _get_related_technologies(self, technology: str) -> List[str]:
        """Get related technologies"""
        relations = {
            'python': ['django', 'flask', 'fastapi', 'pandas', 'tensorflow', 'pytorch'],
            'javascript': ['react', 'vue', 'angular', 'node.js', 'typescript', 'webpack'],
            'typescript': ['javascript', 'react', 'angular', 'node.js', 'webpack'],
            'go': ['docker', 'kubernetes', 'microservices', 'grpc'],
            'rust': ['webassembly', 'systems programming', 'memory safety'],
            'java': ['spring', 'hibernate', 'maven', 'gradle', 'jvm']
        }
        
        return relations.get(technology, [])
        
    def _is_technology_tag(self, tag: str) -> bool:
        """Check if tag represents a technology"""
        tech_indicators = [
            'python', 'javascript', 'java', 'go', 'rust', 'typescript', 'react', 'vue', 'angular',
            'docker', 'kubernetes', 'aws', 'azure', 'machine-learning', 'tensorflow', 'pytorch',
            'api', 'database', 'sql', 'nosql', 'microservices', 'devops', 'ci-cd'
        ]
        
        return any(indicator in tag.lower() for indicator in tech_indicators)
        
    def _estimate_tag_growth(self, tag: str, current_count: int) -> float:
        """Estimate tag growth based on current metrics"""
        # Simplified estimation
        if current_count > 500000:
            return 0.05  # Mature technology
        elif current_count > 100000:
            return 0.10  # Established technology
        elif current_count > 10000:
            return 0.20  # Growing technology
        else:
            return 0.30  # Emerging technology

class KnowledgeSearchEngine:
    """Search engine for knowledge base"""
    
    def __init__(self, db: KnowledgeDatabase):
        self.db = db
        
    def search(self, query: str, category: str = None, tags: List[str] = None,
               limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Build search query
            base_query = """
                SELECT id, title, summary, category, tags, source_url, 
                       relevance_score, published_at
                FROM articles
                WHERE (title LIKE ? OR content LIKE ?)
            """
            
            params = [f"%{query}%", f"%{query}%"]
            
            if category:
                base_query += " AND category = ?"
                params.append(category)
                
            if tags:
                tag_conditions = " AND (" + " OR ".join(["tags LIKE ?" for _ in tags]) + ")"
                base_query += tag_conditions
                params.extend([f"%{tag}%" for tag in tags])
                
            base_query += " ORDER BY relevance_score DESC, published_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(base_query, params)
            results = []
            
            for row in cursor.fetchall():
                result = {
                    'id': row[0],
                    'title': row[1],
                    'summary': row[2],
                    'category': row[3],
                    'tags': json.loads(row[4]) if row[4] else [],
                    'source_url': row[5],
                    'relevance_score': row[6],
                    'published_at': row[7]
                }
                results.append(result)
                
            # Log search query
            self._log_search_query(query, len(results))
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
            
    def get_trending_topics(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending topics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT technology, popularity_score, growth_rate, adoption_level
                FROM trends
                WHERE detected_at >= datetime('now', '-{} days')
                ORDER BY popularity_score DESC, growth_rate DESC
                LIMIT 20
            """.format(days))
            
            trends = []
            for row in cursor.fetchall():
                trends.append({
                    'technology': row[0],
                    'popularity_score': row[1],
                    'growth_rate': row[2],
                    'adoption_level': row[3]
                })
                
            conn.close()
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            return []
            
    def get_recommendations(self, user_interests: List[str]) -> List[Dict[str, Any]]:
        """Get personalized recommendations"""
        recommendations = []
        
        for interest in user_interests:
            results = self.search(interest, limit=3)
            recommendations.extend(results)
            
        # Remove duplicates and sort by relevance
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec['id'] not in seen:
                seen.add(rec['id'])
                unique_recommendations.append(rec)
                
        return sorted(unique_recommendations, key=lambda x: x['relevance_score'], reverse=True)[:10]
        
    def _log_search_query(self, query: str, results_count: int):
        """Log search query for analytics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO search_queries (query, results_count)
                VALUES (?, ?)
            """, (query, results_count))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")

class KnowledgeBaseManager:
    """Main knowledge base management system"""
    
    def __init__(self):
        self.db = KnowledgeDatabase()
        self.content_aggregator = ContentAggregator(self.db)
        self.trend_analyzer = TrendAnalyzer(self.db)
        self.search_engine = KnowledgeSearchEngine(self.db)
        self.update_scheduler = None
        self.start_scheduler()
        
    def start_scheduler(self):
        """Start automatic update scheduler"""
        schedule.every(1).hours.do(self.update_content)
        schedule.every(1).days.do(self.update_trends)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        self.update_scheduler = threading.Thread(target=run_scheduler, daemon=True)
        self.update_scheduler.start()
        logger.info("Knowledge base update scheduler started")
        
    def update_content(self):
        """Update knowledge base content"""
        try:
            logger.info("Starting content update...")
            
            # Crawl RSS feeds
            rss_articles = self.content_aggregator.crawl_rss_feeds()
            
            # Crawl GitHub trending
            github_articles = self.content_aggregator.crawl_github_trending()
            
            # Store articles
            all_articles = rss_articles + github_articles
            self._store_articles(all_articles)
            
            # Log update
            self._log_update('content_update', 'aggregator', len(all_articles), 1.0)
            
            logger.info(f"Content update completed: {len(all_articles)} new articles")
            
        except Exception as e:
            logger.error(f"Content update failed: {e}")
            self._log_update('content_update', 'aggregator', 0, 0.0, str(e))
            
    def update_trends(self):
        """Update trend analysis"""
        try:
            logger.info("Starting trend analysis...")
            
            # Analyze GitHub trends
            github_trends = self.trend_analyzer.analyze_github_trends()
            
            # Analyze Stack Overflow trends
            stackoverflow_trends = self.trend_analyzer.analyze_stackoverflow_trends()
            
            # Store trends
            all_trends = github_trends + stackoverflow_trends
            self._store_trends(all_trends)
            
            # Log update
            self._log_update('trend_analysis', 'analyzer', len(all_trends), 1.0)
            
            logger.info(f"Trend analysis completed: {len(all_trends)} trends analyzed")
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            self._log_update('trend_analysis', 'analyzer', 0, 0.0, str(e))
            
    def search_knowledge(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        return self.search_engine.search(query, **kwargs)
        
    def get_latest_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get latest technology trends"""
        return self.search_engine.get_trending_topics(days)
        
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Article statistics
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM articles GROUP BY category")
            category_stats = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            recent_articles = cursor.fetchone()[0]
            
            # Trend statistics
            cursor.execute("SELECT COUNT(*) FROM trends")
            total_trends = cursor.fetchone()[0]
            
            # Search statistics
            cursor.execute("""
                SELECT COUNT(*) FROM search_queries 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            recent_searches = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'category_distribution': category_stats,
                'recent_articles': recent_articles,
                'total_trends': total_trends,
                'recent_searches': recent_searches,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {}
            
    def _store_articles(self, articles: List[KnowledgeArticle]):
        """Store articles in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for article in articles:
            cursor.execute("""
                INSERT OR REPLACE INTO articles 
                (id, title, content, summary, category, tags, source_url, 
                 source_type, author, published_at, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.id, article.title, article.content, article.summary,
                article.category, json.dumps(article.tags), article.source_url,
                article.source_type, article.author, article.published_at,
                article.relevance_score
            ))
            
        conn.commit()
        conn.close()
        
    def _store_trends(self, trends: List[TrendData]):
        """Store trends in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for trend in trends:
            cursor.execute("""
                INSERT OR REPLACE INTO trends 
                (id, technology, trend_type, popularity_score, growth_rate,
                 adoption_level, market_data, predictions, related_technologies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trend.id, trend.technology, trend.trend_type, trend.popularity_score,
                trend.growth_rate, trend.adoption_level, json.dumps(trend.market_data),
                json.dumps(trend.predictions), json.dumps(trend.related_technologies)
            ))
            
        conn.commit()
        conn.close()
        
    def _log_update(self, update_type: str, source: str, items_processed: int, 
                   success_rate: float, details: str = None):
        """Log update activity"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO update_history 
                (update_type, source, items_processed, success_rate, details)
                VALUES (?, ?, ?, ?, ?)
            """, (update_type, source, items_processed, success_rate, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log update: {e}")

def main():
    """Demo of knowledge base management"""
    print("Knowledge Base Management System Demo")
    print("=" * 40)
    
    # Initialize knowledge base
    kb = KnowledgeBaseManager()
    
    # Run immediate content update
    print("\n1. Updating knowledge base content...")
    kb.update_content()
    
    # Run trend analysis
    print("\n2. Analyzing technology trends...")
    kb.update_trends()
    
    # Search demonstrations
    print("\n3. Search demonstrations:")
    
    search_queries = [
        "machine learning",
        "python frameworks",
        "cloud computing",
        "javascript libraries",
        "DevOps tools"
    ]
    
    for query in search_queries:
        print(f"\n   Searching for: '{query}'")
        results = kb.search_knowledge(query, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"     {i}. {result['title']}")
                print(f"        Category: {result['category']}")
                print(f"        Score: {result['relevance_score']:.2f}")
        else:
            print("     No results found")
    
    # Show trending topics
    print("\n4. Latest technology trends:")
    trends = kb.get_latest_trends(days=30)
    
    for trend in trends[:5]:
        print(f"   {trend['technology']} - {trend['adoption_level']} "
              f"(Score: {trend['popularity_score']:.2f}, Growth: {trend['growth_rate']:.1%})")
    
    # Knowledge base statistics
    print("\n5. Knowledge base statistics:")
    stats = kb.get_knowledge_stats()
    
    if stats:
        print(f"   Total articles: {stats.get('total_articles', 0)}")
        print(f"   Recent articles: {stats.get('recent_articles', 0)}")
        print(f"   Total trends: {stats.get('total_trends', 0)}")
        print(f"   Recent searches: {stats.get('recent_searches', 0)}")
        
        if stats.get('category_distribution'):
            print("   Category distribution:")
            for category, count in stats['category_distribution'].items():
                print(f"     {category}: {count}")

if __name__ == "__main__":
    main()