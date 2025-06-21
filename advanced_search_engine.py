#!/usr/bin/env python3
"""
Advanced Search Engine with Transformer Embeddings for MITO Engine
Uses sentence-transformers all-MiniLM-L6-v2 for semantic search capabilities
"""

import os
import json
import sqlite3
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import pickle
from dataclasses import dataclass, asdict
import hashlib
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a search result"""
    id: str
    title: str
    content: str
    url: str
    score: float
    embedding_score: float
    tfidf_score: float
    combined_score: float
    metadata: Dict[str, Any]
    timestamp: str

@dataclass
class Document:
    """Represents an indexed document"""
    id: str
    title: str
    content: str
    url: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    indexed_at: str = None

class EmbeddingManager:
    """Manages document embeddings using transformer models"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        self.faiss_index = None
        self.document_ids = []
        self.load_model()
        
    def load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load transformer model: {e}")
            raise
            
    def encode_text(self, text: str) -> np.ndarray:
        """Encode text to embedding vector"""
        if not self.model:
            raise ValueError("Model not loaded")
            
        try:
            # Clean and truncate text if too long
            cleaned_text = self._clean_text(text)
            embedding = self.model.encode(cleaned_text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
            
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode multiple texts in batches"""
        if not self.model:
            raise ValueError("Model not loaded")
            
        try:
            cleaned_texts = [self._clean_text(text) for text in texts]
            embeddings = self.model.encode(
                cleaned_texts, 
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
            
    def build_faiss_index(self, embeddings: np.ndarray, document_ids: List[str]):
        """Build FAISS index for fast similarity search"""
        try:
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Create FAISS index
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
            self.faiss_index.add(embeddings)
            self.document_ids = document_ids
            
            logger.info(f"Built FAISS index with {len(document_ids)} documents")
        except Exception as e:
            logger.error(f"Failed to build FAISS index: {e}")
            
    def search_similar(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar documents using FAISS"""
        if not self.faiss_index:
            return []
            
        try:
            # Normalize query embedding
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.faiss_index.search(query_embedding, k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Valid index
                    doc_id = self.document_ids[idx]
                    results.append((doc_id, float(score)))
                    
            return results
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
            
    def save_index(self, filepath: str):
        """Save FAISS index to disk"""
        try:
            if self.faiss_index:
                faiss.write_index(self.faiss_index, filepath)
                
                # Save document IDs mapping
                with open(filepath + ".ids", "wb") as f:
                    pickle.dump(self.document_ids, f)
                    
                logger.info(f"Saved FAISS index to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            
    def load_index(self, filepath: str):
        """Load FAISS index from disk"""
        try:
            if os.path.exists(filepath):
                self.faiss_index = faiss.read_index(filepath)
                
                # Load document IDs mapping
                ids_file = filepath + ".ids"
                if os.path.exists(ids_file):
                    with open(ids_file, "rb") as f:
                        self.document_ids = pickle.load(f)
                        
                logger.info(f"Loaded FAISS index from {filepath}")
                return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            
        return False
        
    def _clean_text(self, text: str) -> str:
        """Clean text for encoding"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (transformer models have token limits)
        max_chars = 8000  # Conservative limit
        if len(text) > max_chars:
            text = text[:max_chars]
            
        return text

class AdvancedSearchDatabase:
    """Enhanced database for advanced search functionality"""
    
    def __init__(self, db_path: str = "advanced_search.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize advanced search database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT,
                category TEXT,
                tags TEXT,
                metadata TEXT,
                embedding BLOB,
                tfidf_scores TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_type TEXT NOT NULL,
                results_count INTEGER,
                avg_score REAL,
                execution_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings_cache (
                text_hash TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status_code INTEGER,
                content_length INTEGER,
                processing_time REAL,
                success BOOLEAN,
                error_message TEXT,
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON search_queries(timestamp)")
        
        conn.commit()
        conn.close()

class WebCrawler:
    """Advanced web crawler for document collection"""
    
    def __init__(self, db: AdvancedSearchDatabase, max_workers: int = 5):
        self.db = db
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MITO-Engine-Crawler/1.0 (+https://mito-engine.com/crawler)'
        })
        
    def add_urls_to_queue(self, urls: List[str], priority: int = 1):
        """Add URLs to crawling queue"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for url in urls:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO crawl_queue (url, priority)
                    VALUES (?, ?)
                """, (url, priority))
            except sqlite3.Error as e:
                logger.warning(f"Failed to add URL {url} to queue: {e}")
                
        conn.commit()
        conn.close()
        
    def crawl_pending_urls(self, limit: int = 50) -> List[Document]:
        """Crawl pending URLs from queue"""
        # Get pending URLs
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url FROM crawl_queue 
            WHERE status = 'pending' AND retry_count < 3
            ORDER BY priority DESC, added_at ASC
            LIMIT ?
        """, (limit,))
        
        pending_urls = cursor.fetchall()
        conn.close()
        
        if not pending_urls:
            return []
            
        documents = []
        
        # Crawl URLs in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self._crawl_single_url, url_id, url): (url_id, url)
                for url_id, url in pending_urls
            }
            
            for future in as_completed(future_to_url):
                url_id, url = future_to_url[future]
                try:
                    document = future.result()
                    if document:
                        documents.append(document)
                        self._update_crawl_status(url_id, 'completed')
                    else:
                        self._update_crawl_status(url_id, 'failed')
                except Exception as e:
                    logger.error(f"Failed to crawl {url}: {e}")
                    self._update_crawl_status(url_id, 'failed')
                    
        return documents
        
    def _crawl_single_url(self, url_id: int, url: str) -> Optional[Document]:
        """Crawl a single URL"""
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else url
            
            # Extract main content
            content = self._extract_content(soup)
            
            if not content or len(content.strip()) < 100:
                return None
                
            # Generate document ID
            doc_id = hashlib.md5(f"{url}_{title}".encode()).hexdigest()
            
            # Extract metadata
            metadata = {
                'content_length': len(content),
                'response_status': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'last_modified': response.headers.get('last-modified', ''),
                'processing_time': time.time() - start_time
            }
            
            # Log successful crawl
            self._log_crawl_attempt(url, response.status_code, len(content), 
                                  time.time() - start_time, True)
            
            return Document(
                id=doc_id,
                title=title,
                content=content,
                url=url,
                category=self._categorize_content(title, content),
                tags=self._extract_tags(title, content),
                metadata=metadata,
                indexed_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            self._log_crawl_attempt(url, 0, 0, time.time() - start_time, False, str(e))
            return None
            
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Try to find main content areas
        content_selectors = [
            'main', 'article', '.content', '#content', '.post', '.entry-content'
        ]
        
        content_text = ""
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content_text = " ".join(elem.get_text(strip=True) for elem in elements)
                break
                
        # Fallback to body text
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = body.get_text(strip=True)
                
        # Clean up text
        content_text = " ".join(content_text.split())
        
        return content_text
        
    def _categorize_content(self, title: str, content: str) -> str:
        """Categorize content based on title and content"""
        text = (title + " " + content).lower()
        
        categories = {
            'programming': ['python', 'javascript', 'java', 'programming', 'code', 'development'],
            'ai_ml': ['machine learning', 'artificial intelligence', 'neural network', 'deep learning'],
            'web': ['html', 'css', 'web development', 'frontend', 'backend'],
            'cloud': ['aws', 'azure', 'google cloud', 'kubernetes', 'docker'],
            'database': ['sql', 'database', 'mongodb', 'postgresql', 'mysql'],
            'security': ['security', 'encryption', 'cybersecurity', 'authentication'],
            'devops': ['devops', 'ci/cd', 'deployment', 'infrastructure']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
                
        return 'general'
        
    def _extract_tags(self, title: str, content: str) -> List[str]:
        """Extract tags from content"""
        text = (title + " " + content).lower()
        
        tech_tags = [
            'python', 'javascript', 'java', 'go', 'rust', 'typescript',
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'sql', 'nosql', 'mongodb', 'postgresql', 'redis',
            'ai', 'ml', 'deep learning', 'tensorflow', 'pytorch'
        ]
        
        found_tags = []
        for tag in tech_tags:
            if tag in text:
                found_tags.append(tag)
                
        return found_tags[:10]  # Limit to 10 tags
        
    def _update_crawl_status(self, url_id: int, status: str):
        """Update crawl status in queue"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE crawl_queue 
            SET status = ?, last_attempt = CURRENT_TIMESTAMP,
                retry_count = retry_count + 1
            WHERE id = ?
        """, (status, url_id))
        
        conn.commit()
        conn.close()
        
    def _log_crawl_attempt(self, url: str, status_code: int, content_length: int,
                          processing_time: float, success: bool, error_message: str = None):
        """Log crawl attempt"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO crawl_history 
            (url, status_code, content_length, processing_time, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url, status_code, content_length, processing_time, success, error_message))
        
        conn.commit()
        conn.close()

class AdvancedSearchEngine:
    """Main advanced search engine with transformer embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.db = AdvancedSearchDatabase()
        self.embedding_manager = EmbeddingManager(model_name)
        self.crawler = WebCrawler(self.db)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.document_index = {}  # Maps doc_id to index in matrices
        
        # Load existing index if available
        self._load_search_index()
        
    def index_document(self, document: Document) -> bool:
        """Index a single document"""
        try:
            # Generate embedding
            text_for_embedding = f"{document.title} {document.content}"
            embedding = self.embedding_manager.encode_text(text_for_embedding)
            document.embedding = embedding
            
            # Store in database
            self._store_document(document)
            
            # Update search indexes
            self._update_search_indexes()
            
            logger.info(f"Indexed document: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {e}")
            return False
            
    def index_documents_batch(self, documents: List[Document]) -> int:
        """Index multiple documents in batch"""
        if not documents:
            return 0
            
        try:
            # Generate embeddings in batch
            texts = [f"{doc.title} {doc.content}" for doc in documents]
            embeddings = self.embedding_manager.encode_batch(texts)
            
            # Assign embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
                
            # Store in database
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            indexed_count = 0
            for doc in documents:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO documents 
                        (id, title, content, url, category, tags, metadata, embedding)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc.id, doc.title, doc.content, doc.url, doc.category,
                        json.dumps(doc.tags), json.dumps(doc.metadata),
                        pickle.dumps(doc.embedding)
                    ))
                    indexed_count += 1
                except sqlite3.Error as e:
                    logger.warning(f"Failed to store document {doc.id}: {e}")
                    
            conn.commit()
            conn.close()
            
            # Update search indexes
            self._update_search_indexes()
            
            logger.info(f"Batch indexed {indexed_count} documents")
            return indexed_count
            
        except Exception as e:
            logger.error(f"Failed to batch index documents: {e}")
            return 0
            
    def search(self, query: str, search_type: str = "hybrid", limit: int = 10,
               category: str = None, tags: List[str] = None) -> List[SearchResult]:
        """Perform advanced search with multiple algorithms"""
        start_time = time.time()
        
        try:
            if search_type == "semantic":
                results = self._semantic_search(query, limit, category, tags)
            elif search_type == "keyword":
                results = self._keyword_search(query, limit, category, tags)
            elif search_type == "hybrid":
                results = self._hybrid_search(query, limit, category, tags)
            else:
                raise ValueError(f"Unknown search type: {search_type}")
                
            # Log search query
            execution_time = time.time() - start_time
            avg_score = sum(r.combined_score for r in results) / len(results) if results else 0
            self._log_search_query(query, search_type, len(results), avg_score, execution_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
            
    def _semantic_search(self, query: str, limit: int, category: str = None,
                        tags: List[str] = None) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        if not self.embedding_manager.faiss_index:
            return []
            
        # Generate query embedding
        query_embedding = self.embedding_manager.encode_text(query)
        
        # Search similar documents
        similar_docs = self.embedding_manager.search_similar(query_embedding, limit * 2)
        
        # Filter and format results
        results = []
        for doc_id, score in similar_docs:
            document = self._get_document(doc_id)
            if not document:
                continue
                
            # Apply filters
            if category and document.get('category') != category:
                continue
                
            if tags and not any(tag in document.get('tags', []) for tag in tags):
                continue
                
            result = SearchResult(
                id=doc_id,
                title=document['title'],
                content=document['content'][:500] + "..." if len(document['content']) > 500 else document['content'],
                url=document['url'],
                score=score,
                embedding_score=score,
                tfidf_score=0.0,
                combined_score=score,
                metadata=json.loads(document['metadata']) if document['metadata'] else {},
                timestamp=datetime.now().isoformat()
            )
            
            results.append(result)
            
            if len(results) >= limit:
                break
                
        return results
        
    def _keyword_search(self, query: str, limit: int, category: str = None,
                       tags: List[str] = None) -> List[SearchResult]:
        """Perform keyword-based search using TF-IDF"""
        if self.tfidf_matrix is None:
            return []
            
        try:
            # Transform query
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-limit*2:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] < 0.1:  # Minimum relevance threshold
                    break
                    
                # Get document ID from index mapping
                doc_id = None
                for did, didx in self.document_index.items():
                    if didx == idx:
                        doc_id = did
                        break
                        
                if not doc_id:
                    continue
                    
                document = self._get_document(doc_id)
                if not document:
                    continue
                    
                # Apply filters
                if category and document.get('category') != category:
                    continue
                    
                if tags and not any(tag in document.get('tags', []) for tag in tags):
                    continue
                    
                result = SearchResult(
                    id=doc_id,
                    title=document['title'],
                    content=document['content'][:500] + "..." if len(document['content']) > 500 else document['content'],
                    url=document['url'],
                    score=float(similarities[idx]),
                    embedding_score=0.0,
                    tfidf_score=float(similarities[idx]),
                    combined_score=float(similarities[idx]),
                    metadata=json.loads(document['metadata']) if document['metadata'] else {},
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
                
                if len(results) >= limit:
                    break
                    
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
            
    def _hybrid_search(self, query: str, limit: int, category: str = None,
                      tags: List[str] = None) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword approaches"""
        # Get results from both methods
        semantic_results = self._semantic_search(query, limit, category, tags)
        keyword_results = self._keyword_search(query, limit, category, tags)
        
        # Combine and rerank results
        combined_results = {}
        
        # Add semantic results with weight
        for result in semantic_results:
            combined_results[result.id] = result
            
        # Add keyword results with weight and combine scores
        for result in keyword_results:
            if result.id in combined_results:
                # Combine scores with weights
                existing = combined_results[result.id]
                combined_score = (0.6 * existing.embedding_score + 0.4 * result.tfidf_score)
                existing.tfidf_score = result.tfidf_score
                existing.combined_score = combined_score
                existing.score = combined_score
            else:
                result.combined_score = 0.4 * result.tfidf_score
                result.score = result.combined_score
                combined_results[result.id] = result
                
        # Sort by combined score and return top results
        final_results = sorted(
            combined_results.values(),
            key=lambda x: x.combined_score,
            reverse=True
        )
        
        return final_results[:limit]
        
    def crawl_and_index_urls(self, urls: List[str], priority: int = 1) -> Dict[str, Any]:
        """Crawl URLs and index the content"""
        try:
            # Add URLs to crawl queue
            self.crawler.add_urls_to_queue(urls, priority)
            
            # Crawl pending URLs
            documents = self.crawler.crawl_pending_urls(len(urls))
            
            # Index crawled documents
            indexed_count = self.index_documents_batch(documents)
            
            return {
                'urls_queued': len(urls),
                'documents_crawled': len(documents),
                'documents_indexed': indexed_count,
                'success_rate': indexed_count / len(urls) if urls else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to crawl and index URLs: {e}")
            return {
                'urls_queued': 0,
                'documents_crawled': 0,
                'documents_indexed': 0,
                'success_rate': 0,
                'error': str(e)
            }
            
    def get_search_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get search analytics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Query statistics
            cursor.execute("""
                SELECT search_type, COUNT(*) as count, AVG(avg_score) as avg_score
                FROM search_queries 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY search_type
            """.format(days))
            
            search_stats = {}
            for row in cursor.fetchall():
                search_stats[row[0]] = {
                    'count': row[1],
                    'avg_score': row[2]
                }
                
            # Document statistics
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM documents GROUP BY category")
            category_stats = dict(cursor.fetchall())
            
            # Recent crawl activity
            cursor.execute("""
                SELECT COUNT(*) FROM crawl_history 
                WHERE crawled_at >= datetime('now', '-{} days') AND success = 1
            """.format(days))
            successful_crawls = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'search_statistics': search_stats,
                'total_documents': total_docs,
                'category_distribution': category_stats,
                'successful_crawls_last_week': successful_crawls,
                'embedding_model': self.embedding_manager.model_name,
                'index_size': len(self.embedding_manager.document_ids)
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {}
            
    def _store_document(self, document: Document):
        """Store document in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO documents 
            (id, title, content, url, category, tags, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.id, document.title, document.content, document.url,
            document.category, json.dumps(document.tags),
            json.dumps(document.metadata), pickle.dumps(document.embedding)
        ))
        
        conn.commit()
        conn.close()
        
    def _get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document from database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, url, category, tags, metadata
            FROM documents WHERE id = ?
        """, (doc_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'title': result[1],
                'content': result[2],
                'url': result[3],
                'category': result[4],
                'tags': json.loads(result[5]) if result[5] else [],
                'metadata': result[6]
            }
            
        return None
        
    def _update_search_indexes(self):
        """Update FAISS and TF-IDF indexes"""
        try:
            # Get all documents
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, title, content, embedding FROM documents")
            documents = cursor.fetchall()
            conn.close()
            
            if not documents:
                return
                
            # Rebuild FAISS index
            embeddings = []
            doc_ids = []
            texts = []
            
            for doc_id, title, content, embedding_blob in documents:
                try:
                    embedding = pickle.loads(embedding_blob)
                    embeddings.append(embedding)
                    doc_ids.append(doc_id)
                    texts.append(f"{title} {content}")
                except:
                    continue
                    
            if embeddings:
                embeddings_array = np.vstack(embeddings)
                self.embedding_manager.build_faiss_index(embeddings_array, doc_ids)
                
                # Save index
                index_path = "search_index.faiss"
                self.embedding_manager.save_index(index_path)
                
            # Rebuild TF-IDF index
            if texts:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                
                # Update document index mapping
                self.document_index = {doc_id: idx for idx, doc_id in enumerate(doc_ids)}
                
            logger.info(f"Updated search indexes with {len(doc_ids)} documents")
            
        except Exception as e:
            logger.error(f"Failed to update search indexes: {e}")
            
    def _load_search_index(self):
        """Load existing search index"""
        index_path = "search_index.faiss"
        if self.embedding_manager.load_index(index_path):
            logger.info("Loaded existing FAISS index")
            
    def _log_search_query(self, query: str, search_type: str, results_count: int,
                         avg_score: float, execution_time: float):
        """Log search query"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO search_queries 
                (query, search_type, results_count, avg_score, execution_time)
                VALUES (?, ?, ?, ?, ?)
            """, (query, search_type, results_count, avg_score, execution_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")

def main():
    """Demo of advanced search engine"""
    print("Advanced Search Engine with Transformer Embeddings Demo")
    print("=" * 55)
    
    # Initialize search engine
    search_engine = AdvancedSearchEngine()
    
    # Demo URLs for crawling and indexing
    demo_urls = [
        "https://docs.python.org/3/tutorial/",
        "https://pytorch.org/tutorials/",
        "https://reactjs.org/docs/getting-started.html",
        "https://kubernetes.io/docs/concepts/",
        "https://aws.amazon.com/getting-started/"
    ]
    
    print("\n1. Crawling and indexing demo URLs...")
    crawl_results = search_engine.crawl_and_index_urls(demo_urls)
    print(f"   URLs queued: {crawl_results['urls_queued']}")
    print(f"   Documents crawled: {crawl_results['documents_crawled']}")
    print(f"   Documents indexed: {crawl_results['documents_indexed']}")
    print(f"   Success rate: {crawl_results['success_rate']:.2%}")
    
    # Demo searches
    print("\n2. Search demonstrations:")
    
    test_queries = [
        ("machine learning with Python", "hybrid"),
        ("React component patterns", "semantic"),
        ("Kubernetes deployment strategies", "keyword"),
        ("AWS cloud architecture", "hybrid"),
        ("deep learning frameworks", "semantic")
    ]
    
    for query, search_type in test_queries:
        print(f"\n   Query: '{query}' (Type: {search_type})")
        results = search_engine.search(query, search_type=search_type, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"     {i}. {result.title}")
                print(f"        Score: {result.combined_score:.3f} "
                      f"(Embedding: {result.embedding_score:.3f}, "
                      f"TF-IDF: {result.tfidf_score:.3f})")
                print(f"        URL: {result.url}")
        else:
            print("     No results found")
    
    # Analytics
    print("\n3. Search analytics:")
    analytics = search_engine.get_search_analytics()
    
    if analytics:
        print(f"   Total documents: {analytics.get('total_documents', 0)}")
        print(f"   Embedding model: {analytics.get('embedding_model', 'N/A')}")
        print(f"   Index size: {analytics.get('index_size', 0)}")
        
        if analytics.get('search_statistics'):
            print("   Search statistics:")
            for search_type, stats in analytics['search_statistics'].items():
                print(f"     {search_type}: {stats['count']} queries, "
                      f"avg score: {stats['avg_score']:.3f}")
                      
        if analytics.get('category_distribution'):
            print("   Category distribution:")
            for category, count in analytics['category_distribution'].items():
                print(f"     {category}: {count}")

if __name__ == "__main__":
    main()