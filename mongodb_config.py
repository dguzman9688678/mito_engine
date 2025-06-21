#!/usr/bin/env python3
"""
MITO Engine - MongoDB Configuration & Fallback System
Provides MongoDB integration with SQLite fallback for development
"""

import os
import json
import time
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MITODataManager:
    """Unified data manager supporting MongoDB with SQLite fallback"""
    
    def __init__(self):
        self.mongodb_enabled = False
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_db = "mito_unified.db"
        
        # Try MongoDB first, fallback to SQLite
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage system - MongoDB first, SQLite fallback"""
        
        # Check for MongoDB connection string
        mongodb_uri = os.environ.get('MONGODB_URI') or os.environ.get('DATABASE_URL')
        
        if mongodb_uri and 'mongodb' in mongodb_uri.lower():
            try:
                # Try importing pymongo
                from pymongo import MongoClient
                from pymongo.errors import ConnectionFailure
                
                self.mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
                self.mongo_client.admin.command('ping')
                
                db_name = os.environ.get('MONGODB_DATABASE', 'mito_engine')
                self.mongo_db = self.mongo_client[db_name]
                self.mongodb_enabled = True
                
                logger.info(f"MongoDB connected successfully: {db_name}")
                self._setup_mongodb_collections()
                
            except ImportError:
                logger.warning("PyMongo not installed - using SQLite fallback")
                self._setup_sqlite()
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e} - using SQLite fallback")
                self._setup_sqlite()
        else:
            logger.info("No MongoDB URI found - using SQLite")
            self._setup_sqlite()
    
    def _setup_mongodb_collections(self):
        """Setup MongoDB collections with indexes"""
        collections = {
            'conversation_memory': [
                [("session_id", 1), ("timestamp", -1)],
                [("importance_score", -1)]
            ],
            'system_memory': [
                [("component", 1), ("state_key", 1)],
                [("expiry_time", 1)]
            ],
            'api_keys': [
                [("provider", 1), ("status", 1)],
                [("created_at", -1)]
            ],
            'tools': [
                [("name", 1)],
                [("category", 1), ("status", 1)]
            ],
            'agents': [
                [("name", 1)],
                [("status", 1), ("created_at", -1)]
            ],
            'audit_logs': [
                [("timestamp", -1)],
                [("user_id", 1), ("action", 1)]
            ]
        }
        
        for collection_name, indexes in collections.items():
            collection = self.mongo_db[collection_name]
            for index_spec in indexes:
                try:
                    collection.create_index(index_spec)
                except Exception as e:
                    logger.warning(f"Failed to create index on {collection_name}: {e}")
    
    def _setup_sqlite(self):
        """Setup SQLite database as fallback"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            # Conversation memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance_score REAL DEFAULT 1.0,
                    retention_priority INTEGER DEFAULT 5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    state_key TEXT NOT NULL,
                    state_value TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    expiry_time TEXT,
                    access_count INTEGER DEFAULT 0,
                    UNIQUE(component, state_key)
                )
            """)
            
            # API keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    key_name TEXT NOT NULL,
                    api_key_hash TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            # Tools table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    configuration TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    configuration TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '{}',
                    ip_address TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("SQLite database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup SQLite: {e}")
            raise
    
    def store_conversation_memory(self, session_id: str, message_type: str, content: str, 
                                 importance_score: float = 1.0, retention_priority: int = 5) -> bool:
        """Store conversation memory"""
        if self.mongodb_enabled:
            return self._store_conversation_mongodb(session_id, message_type, content, importance_score, retention_priority)
        else:
            return self._store_conversation_sqlite(session_id, message_type, content, importance_score, retention_priority)
    
    def _store_conversation_mongodb(self, session_id: str, message_type: str, content: str, 
                                   importance_score: float, retention_priority: int) -> bool:
        """Store conversation in MongoDB"""
        try:
            document = {
                'session_id': session_id,
                'timestamp': datetime.now(),
                'message_type': message_type,
                'content': content,
                'importance_score': importance_score,
                'retention_priority': retention_priority,
                'created_at': datetime.now()
            }
            
            result = self.mongo_db['conversation_memory'].insert_one(document)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store conversation in MongoDB: {e}")
            return False
    
    def _store_conversation_sqlite(self, session_id: str, message_type: str, content: str, 
                                  importance_score: float, retention_priority: int) -> bool:
        """Store conversation in SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_memory 
                (session_id, timestamp, message_type, content, importance_score, retention_priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                datetime.now().isoformat(),
                message_type,
                content,
                importance_score,
                retention_priority
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store conversation in SQLite: {e}")
            return False
    
    def get_conversation_context(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation context"""
        if self.mongodb_enabled:
            return self._get_conversation_mongodb(session_id, limit)
        else:
            return self._get_conversation_sqlite(session_id, limit)
    
    def _get_conversation_mongodb(self, session_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get conversation from MongoDB"""
        try:
            cursor = self.mongo_db['conversation_memory'].find(
                {'session_id': session_id}
            ).sort('timestamp', -1).limit(limit)
            
            context = []
            for doc in cursor:
                context.append({
                    'type': doc['message_type'],
                    'content': doc['content'],
                    'timestamp': doc['timestamp'].isoformat() if hasattr(doc['timestamp'], 'isoformat') else str(doc['timestamp']),
                    'importance': doc['importance_score']
                })
            
            return list(reversed(context))
            
        except Exception as e:
            logger.error(f"Failed to get conversation from MongoDB: {e}")
            return []
    
    def _get_conversation_sqlite(self, session_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get conversation from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT message_type, content, timestamp, importance_score
                FROM conversation_memory
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            context = []
            for row in results:
                context.append({
                    'type': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'importance': row[3]
                })
            
            return list(reversed(context))
            
        except Exception as e:
            logger.error(f"Failed to get conversation from SQLite: {e}")
            return []
    
    def store_system_state(self, component: str, state_key: str, state_value: Any, 
                          expiry_hours: int = 24) -> bool:
        """Store system state"""
        if self.mongodb_enabled:
            return self._store_system_mongodb(component, state_key, state_value, expiry_hours)
        else:
            return self._store_system_sqlite(component, state_key, state_value, expiry_hours)
    
    def _store_system_mongodb(self, component: str, state_key: str, state_value: Any, 
                             expiry_hours: int) -> bool:
        """Store system state in MongoDB"""
        try:
            expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            
            document = {
                'component': component,
                'state_key': state_key,
                'state_value': state_value,
                'last_updated': datetime.now(),
                'expiry_time': expiry_time,
                'access_count': 0
            }
            
            result = self.mongo_db['system_memory'].replace_one(
                {'component': component, 'state_key': state_key},
                document,
                upsert=True
            )
            
            return bool(result.upserted_id or result.modified_count)
            
        except Exception as e:
            logger.error(f"Failed to store system state in MongoDB: {e}")
            return False
    
    def _store_system_sqlite(self, component: str, state_key: str, state_value: Any, 
                            expiry_hours: int) -> bool:
        """Store system state in SQLite"""
        try:
            value_str = json.dumps(state_value) if isinstance(state_value, (dict, list)) else str(state_value)
            expiry_time = (datetime.now() + timedelta(hours=expiry_hours)).isoformat()
            
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO system_memory 
                (component, state_key, state_value, last_updated, expiry_time, access_count)
                VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT access_count FROM system_memory WHERE component = ? AND state_key = ?), 0))
            """, (
                component, state_key, value_str, datetime.now().isoformat(), expiry_time,
                component, state_key
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store system state in SQLite: {e}")
            return False
    
    def get_system_state(self, component: str, state_key: str = None) -> Any:
        """Get system state"""
        if self.mongodb_enabled:
            return self._get_system_mongodb(component, state_key)
        else:
            return self._get_system_sqlite(component, state_key)
    
    def _get_system_mongodb(self, component: str, state_key: str = None) -> Any:
        """Get system state from MongoDB"""
        try:
            if state_key:
                doc = self.mongo_db['system_memory'].find_one({
                    'component': component,
                    'state_key': state_key,
                    '$or': [
                        {'expiry_time': None},
                        {'expiry_time': {'$gt': datetime.now()}}
                    ]
                })
                
                if doc:
                    self.mongo_db['system_memory'].update_one(
                        {'_id': doc['_id']},
                        {'$inc': {'access_count': 1}}
                    )
                    return doc['state_value']
                return None
            else:
                cursor = self.mongo_db['system_memory'].find({
                    'component': component,
                    '$or': [
                        {'expiry_time': None},
                        {'expiry_time': {'$gt': datetime.now()}}
                    ]
                })
                
                return {doc['state_key']: doc['state_value'] for doc in cursor}
                
        except Exception as e:
            logger.error(f"Failed to get system state from MongoDB: {e}")
            return None
    
    def _get_system_sqlite(self, component: str, state_key: str = None) -> Any:
        """Get system state from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            if state_key:
                cursor.execute("""
                    SELECT state_value FROM system_memory
                    WHERE component = ? AND state_key = ? AND 
                          (expiry_time IS NULL OR expiry_time > ?)
                """, (component, state_key, datetime.now().isoformat()))
                
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        UPDATE system_memory SET access_count = access_count + 1
                        WHERE component = ? AND state_key = ?
                    """, (component, state_key))
                    
                    conn.commit()
                    conn.close()
                    
                    try:
                        return json.loads(result[0])
                    except:
                        return result[0]
                
                conn.close()
                return None
            else:
                cursor.execute("""
                    SELECT state_key, state_value FROM system_memory
                    WHERE component = ? AND (expiry_time IS NULL OR expiry_time > ?)
                """, (component, datetime.now().isoformat()))
                
                results = cursor.fetchall()
                conn.close()
                
                state_dict = {}
                for row in results:
                    try:
                        state_dict[row[0]] = json.loads(row[1])
                    except:
                        state_dict[row[0]] = row[1]
                
                return state_dict
                
        except Exception as e:
            logger.error(f"Failed to get system state from SQLite: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if self.mongodb_enabled:
            return self._get_mongodb_stats()
        else:
            return self._get_sqlite_stats()
    
    def _get_mongodb_stats(self) -> Dict[str, Any]:
        """Get MongoDB statistics"""
        try:
            stats = self.mongo_db.command('dbStats')
            
            collection_stats = {}
            for collection_name in self.mongo_db.list_collection_names():
                collection = self.mongo_db[collection_name]
                collection_stats[collection_name] = collection.count_documents({})
            
            return {
                'database_type': 'MongoDB',
                'database_name': self.mongo_db.name,
                'total_size_bytes': stats.get('dataSize', 0),
                'storage_size_bytes': stats.get('storageSize', 0),
                'total_collections': stats.get('collections', 0),
                'collection_counts': collection_stats,
                'connected': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get MongoDB stats: {e}")
            return {'error': str(e), 'database_type': 'MongoDB'}
    
    def _get_sqlite_stats(self) -> Dict[str, Any]:
        """Get SQLite statistics"""
        try:
            db_size = os.path.getsize(self.sqlite_db) if os.path.exists(self.sqlite_db) else 0
            
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.cursor()
            
            # Get table counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            collection_stats = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                collection_stats[table_name] = count
            
            conn.close()
            
            return {
                'database_type': 'SQLite',
                'database_file': self.sqlite_db,
                'total_size_bytes': db_size,
                'total_tables': len(tables),
                'table_counts': collection_stats,
                'connected': True,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get SQLite stats: {e}")
            return {'error': str(e), 'database_type': 'SQLite'}


# Global data manager instance
_data_manager = None

def get_data_manager() -> MITODataManager:
    """Get or create global data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = MITODataManager()
    return _data_manager

# Convenience functions
def store_conversation_memory(session_id: str, message_type: str, content: str, importance: float = 1.0) -> bool:
    """Store conversation memory"""
    manager = get_data_manager()
    return manager.store_conversation_memory(session_id, message_type, content, importance)

def get_conversation_context(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get conversation context"""
    manager = get_data_manager()
    return manager.get_conversation_context(session_id, limit)

def store_system_memory(component: str, key: str, value: Any, expiry_hours: int = 24) -> bool:
    """Store system memory"""
    manager = get_data_manager()
    return manager.store_system_state(component, key, value, expiry_hours)

def get_system_memory(component: str, key: str = None) -> Any:
    """Get system memory"""
    manager = get_data_manager()
    return manager.get_system_state(component, key)


if __name__ == "__main__":
    # Test the data manager
    print("Testing MITO Data Manager...")
    
    manager = MITODataManager()
    
    print(f"Database type: {'MongoDB' if manager.mongodb_enabled else 'SQLite'}")
    
    # Test conversation storage
    session_id = f"test_session_{int(time.time())}"
    success1 = manager.store_conversation_memory(session_id, "user_input", "Hello MITO!", 0.9)
    success2 = manager.store_conversation_memory(session_id, "assistant_response", "MongoDB/SQLite integration working!", 0.8)
    
    print(f"Conversation storage: {success1 and success2}")
    
    # Test system state
    success3 = manager.store_system_state("mito_engine", "version", "1.2.0")
    success4 = manager.store_system_state("mito_engine", "database_type", "MongoDB" if manager.mongodb_enabled else "SQLite")
    
    print(f"System state storage: {success3 and success4}")
    
    # Get stats
    stats = manager.get_database_stats()
    print(f"Database stats: {json.dumps(stats, indent=2, default=str)}")
    
    # Get context
    context = manager.get_conversation_context(session_id)
    print(f"Conversation context: {json.dumps(context, indent=2)}")
    
    print("✓ Data manager test completed successfully")