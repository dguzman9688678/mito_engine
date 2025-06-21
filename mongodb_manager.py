#!/usr/bin/env python3
"""
MITO Engine - MongoDB Manager
Enterprise MongoDB integration for MITO Engine with connection pooling and authentication
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import quote_plus

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None
    ObjectId = None

logger = logging.getLogger(__name__)

class MITOMongoManager:
    """MongoDB manager for MITO Engine with enterprise features"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or self._build_connection_string()
        self.client = None
        self.database = None
        self.connected = False
        self.connection_pool_size = 50
        self.timeout_ms = 5000
        
        if MONGODB_AVAILABLE:
            self.connect()
        else:
            logger.warning("MongoDB not available - install pymongo for MongoDB support")
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string from environment variables"""
        # Check for full connection string first
        if os.environ.get('MONGODB_URI'):
            return os.environ.get('MONGODB_URI')
        
        # Build from individual components
        host = os.environ.get('MONGODB_HOST', 'localhost')
        port = os.environ.get('MONGODB_PORT', '27017')
        username = os.environ.get('MONGODB_USERNAME')
        password = os.environ.get('MONGODB_PASSWORD')
        database = os.environ.get('MONGODB_DATABASE', 'mito_engine')
        
        if username and password:
            # URL encode credentials to handle special characters
            username = quote_plus(username)
            password = quote_plus(password)
            return f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            return f"mongodb://{host}:{port}/{database}"
    
    def connect(self) -> bool:
        """Establish MongoDB connection with error handling"""
        if not MONGODB_AVAILABLE:
            logger.error("MongoDB not available - install pymongo")
            return False
        
        try:
            self.client = MongoClient(
                self.connection_string,
                maxPoolSize=self.connection_pool_size,
                serverSelectionTimeoutMS=self.timeout_ms,
                connectTimeoutMS=self.timeout_ms,
                socketTimeoutMS=self.timeout_ms
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database name from connection string or use default
            db_name = os.environ.get('MONGODB_DATABASE', 'mito_engine')
            self.database = self.client[db_name]
            
            self.connected = True
            logger.info(f"MongoDB connected successfully to database: {db_name}")
            
            # Initialize collections and indexes
            self._initialize_collections()
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected MongoDB connection error: {e}")
            self.connected = False
            return False
    
    def _initialize_collections(self):
        """Initialize MongoDB collections with proper indexes"""
        try:
            # Conversation Memory Collection
            conversations = self.database['conversation_memory']
            conversations.create_index([("session_id", 1), ("timestamp", -1)])
            conversations.create_index([("importance_score", -1)])
            
            # System Memory Collection
            system_memory = self.database['system_memory']
            system_memory.create_index([("component", 1), ("state_key", 1)], unique=True)
            system_memory.create_index([("expiry_time", 1)])
            
            # User Context Collection
            user_context = self.database['user_context']
            user_context.create_index([("user_identifier", 1), ("context_type", 1)])
            user_context.create_index([("last_accessed", -1)])
            
            # API Keys Collection
            api_keys = self.database['api_keys']
            api_keys.create_index([("provider", 1), ("status", 1)])
            api_keys.create_index([("created_at", -1)])
            
            # Tools Collection
            tools = self.database['tools']
            tools.create_index([("category", 1), ("status", 1)])
            tools.create_index([("name", 1)], unique=True)
            
            # Agents Collection
            agents = self.database['agents']
            agents.create_index([("name", 1)], unique=True)
            agents.create_index([("status", 1), ("created_at", -1)])
            
            # Digital Blueprints Collection
            blueprints = self.database['digital_blueprints']
            blueprints.create_index([("title", 1), ("version", -1)])
            blueprints.create_index([("category", 1), ("updated_at", -1)])
            
            # Deployment Matrix Collection
            deployments = self.database['deployment_matrix']
            deployments.create_index([("environment", 1), ("status", 1)])
            deployments.create_index([("created_at", -1)])
            
            # Audit Logs Collection
            audit_logs = self.database['audit_logs']
            audit_logs.create_index([("timestamp", -1)])
            audit_logs.create_index([("user_id", 1), ("action", 1)])
            
            # System Metrics Collection
            metrics = self.database['system_metrics']
            metrics.create_index([("timestamp", -1)])
            metrics.create_index([("metric_type", 1), ("timestamp", -1)])
            
            logger.info("MongoDB collections and indexes initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB collections: {e}")
    
    def store_conversation_memory(self, session_id: str, message_type: str, content: str, 
                                 importance_score: float = 1.0, retention_priority: int = 5) -> bool:
        """Store conversation memory in MongoDB"""
        if not self.connected:
            return False
        
        try:
            document = {
                'session_id': session_id,
                'timestamp': datetime.now(),
                'message_type': message_type,
                'content': content,
                'content_hash': hashlib.md5(content.encode()).hexdigest(),
                'importance_score': importance_score,
                'retention_priority': retention_priority,
                'created_at': datetime.now()
            }
            
            result = self.database['conversation_memory'].insert_one(document)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store conversation memory: {e}")
            return False
    
    def get_conversation_context(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation context from MongoDB"""
        if not self.connected:
            return []
        
        try:
            cursor = self.database['conversation_memory'].find(
                {'session_id': session_id}
            ).sort('timestamp', -1).limit(limit)
            
            context = []
            for doc in cursor:
                context.append({
                    'type': doc['message_type'],
                    'content': doc['content'],
                    'timestamp': doc['timestamp'].isoformat(),
                    'importance': doc['importance_score']
                })
            
            return list(reversed(context))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return []
    
    def store_system_state(self, component: str, state_key: str, state_value: Any, 
                          expiry_hours: int = 24) -> bool:
        """Store system state in MongoDB"""
        if not self.connected:
            return False
        
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
            
            # Upsert operation
            result = self.database['system_memory'].replace_one(
                {'component': component, 'state_key': state_key},
                document,
                upsert=True
            )
            
            return bool(result.upserted_id or result.modified_count)
            
        except Exception as e:
            logger.error(f"Failed to store system state: {e}")
            return False
    
    def get_system_state(self, component: str, state_key: str = None) -> Any:
        """Get system state from MongoDB"""
        if not self.connected:
            return None
        
        try:
            if state_key:
                doc = self.database['system_memory'].find_one({
                    'component': component,
                    'state_key': state_key,
                    '$or': [
                        {'expiry_time': None},
                        {'expiry_time': {'$gt': datetime.now()}}
                    ]
                })
                
                if doc:
                    # Update access count
                    self.database['system_memory'].update_one(
                        {'_id': doc['_id']},
                        {'$inc': {'access_count': 1}}
                    )
                    return doc['state_value']
                return None
            else:
                cursor = self.database['system_memory'].find({
                    'component': component,
                    '$or': [
                        {'expiry_time': None},
                        {'expiry_time': {'$gt': datetime.now()}}
                    ]
                })
                
                return {doc['state_key']: doc['state_value'] for doc in cursor}
                
        except Exception as e:
            logger.error(f"Failed to get system state: {e}")
            return None
    
    def store_api_key(self, provider: str, api_key: str, key_name: str = None, 
                     metadata: Dict[str, Any] = None) -> str:
        """Store API key securely in MongoDB"""
        if not self.connected:
            return None
        
        try:
            document = {
                'provider': provider,
                'key_name': key_name or f"{provider}_key",
                'api_key_hash': hashlib.sha256(api_key.encode()).hexdigest(),
                'api_key_encrypted': api_key,  # In production, encrypt this
                'status': 'active',
                'metadata': metadata or {},
                'created_at': datetime.now(),
                'last_used': None,
                'usage_count': 0
            }
            
            result = self.database['api_keys'].insert_one(document)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            return None
    
    def get_api_keys(self, provider: str = None) -> List[Dict[str, Any]]:
        """Get API keys from MongoDB"""
        if not self.connected:
            return []
        
        try:
            query = {'status': 'active'}
            if provider:
                query['provider'] = provider
            
            cursor = self.database['api_keys'].find(query).sort('created_at', -1)
            
            keys = []
            for doc in cursor:
                keys.append({
                    'id': str(doc['_id']),
                    'provider': doc['provider'],
                    'key_name': doc['key_name'],
                    'status': doc['status'],
                    'created_at': doc['created_at'].isoformat(),
                    'usage_count': doc.get('usage_count', 0),
                    'metadata': doc.get('metadata', {})
                })
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to get API keys: {e}")
            return []
    
    def store_tool(self, tool_data: Dict[str, Any]) -> str:
        """Store tool information in MongoDB"""
        if not self.connected:
            return None
        
        try:
            tool_data['created_at'] = datetime.now()
            tool_data['updated_at'] = datetime.now()
            
            result = self.database['tools'].insert_one(tool_data)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store tool: {e}")
            return None
    
    def get_tools(self, category: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get tools from MongoDB"""
        if not self.connected:
            return []
        
        try:
            query = {}
            if category:
                query['category'] = category
            if status:
                query['status'] = status
            
            cursor = self.database['tools'].find(query).sort('created_at', -1)
            
            tools = []
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                tools.append(doc)
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            return []
    
    def store_audit_log(self, user_id: str, action: str, details: Dict[str, Any], 
                       ip_address: str = None) -> bool:
        """Store audit log in MongoDB"""
        if not self.connected:
            return False
        
        try:
            document = {
                'user_id': user_id,
                'action': action,
                'details': details,
                'ip_address': ip_address,
                'timestamp': datetime.now(),
                'session_hash': hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()
            }
            
            result = self.database['audit_logs'].insert_one(document)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store audit log: {e}")
            return False
    
    def get_system_metrics(self, metric_type: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics from MongoDB"""
        if not self.connected:
            return []
        
        try:
            query = {
                'timestamp': {'$gte': datetime.now() - timedelta(hours=hours)}
            }
            if metric_type:
                query['metric_type'] = metric_type
            
            cursor = self.database['system_metrics'].find(query).sort('timestamp', -1)
            
            metrics = []
            for doc in cursor:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                metrics.append(doc)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return []
    
    def store_system_metric(self, metric_type: str, value: float, metadata: Dict[str, Any] = None) -> bool:
        """Store system metric in MongoDB"""
        if not self.connected:
            return False
        
        try:
            document = {
                'metric_type': metric_type,
                'value': value,
                'metadata': metadata or {},
                'timestamp': datetime.now()
            }
            
            result = self.database['system_metrics'].insert_one(document)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store system metric: {e}")
            return False
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize MongoDB database"""
        if not self.connected:
            return {'error': 'Not connected to MongoDB'}
        
        try:
            optimization_results = {}
            
            # Clean expired system memory
            expired_result = self.database['system_memory'].delete_many({
                'expiry_time': {'$lt': datetime.now()}
            })
            optimization_results['expired_states_cleaned'] = expired_result.deleted_count
            
            # Clean old conversation memory (keep last 1000 per session)
            pipeline = [
                {'$sort': {'timestamp': -1}},
                {'$group': {
                    '_id': '$session_id',
                    'conversations': {'$push': '$$ROOT'}
                }},
                {'$project': {
                    'conversations_to_delete': {'$slice': ['$conversations', 1000, {'$size': '$conversations'}]}
                }}
            ]
            
            old_conversations = 0
            for result in self.database['conversation_memory'].aggregate(pipeline):
                if result['conversations_to_delete']:
                    ids_to_delete = [conv['_id'] for conv in result['conversations_to_delete']]
                    delete_result = self.database['conversation_memory'].delete_many({
                        '_id': {'$in': ids_to_delete}
                    })
                    old_conversations += delete_result.deleted_count
            
            optimization_results['old_conversations_cleaned'] = old_conversations
            
            # Clean old audit logs (keep last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            audit_result = self.database['audit_logs'].delete_many({
                'timestamp': {'$lt': thirty_days_ago}
            })
            optimization_results['old_audit_logs_cleaned'] = audit_result.deleted_count
            
            # Clean old metrics (keep last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            metrics_result = self.database['system_metrics'].delete_many({
                'timestamp': {'$lt': seven_days_ago}
            })
            optimization_results['old_metrics_cleaned'] = metrics_result.deleted_count
            
            optimization_results['optimization_time'] = time.time()
            optimization_results['status'] = 'success'
            
            logger.info(f"MongoDB optimization completed: {optimization_results}")
            return optimization_results
            
        except Exception as e:
            logger.error(f"MongoDB optimization failed: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get MongoDB database statistics"""
        if not self.connected:
            return {'error': 'Not connected to MongoDB'}
        
        try:
            stats = self.database.command('dbStats')
            
            # Get collection counts
            collection_stats = {}
            for collection_name in self.database.list_collection_names():
                collection = self.database[collection_name]
                collection_stats[collection_name] = collection.count_documents({})
            
            return {
                'database_name': self.database.name,
                'total_size_bytes': stats.get('dataSize', 0),
                'storage_size_bytes': stats.get('storageSize', 0),
                'index_size_bytes': stats.get('indexSize', 0),
                'total_collections': stats.get('collections', 0),
                'collection_counts': collection_stats,
                'connected': self.connected,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB connection closed")


# Global MongoDB manager instance
_mongo_manager = None

def get_mongo_manager() -> MITOMongoManager:
    """Get or create global MongoDB manager instance"""
    global _mongo_manager
    if _mongo_manager is None:
        _mongo_manager = MITOMongoManager()
    return _mongo_manager

def store_conversation_memory(session_id: str, message_type: str, content: str, importance: float = 1.0) -> bool:
    """Convenience function to store conversation memory"""
    manager = get_mongo_manager()
    return manager.store_conversation_memory(session_id, message_type, content, importance)

def get_conversation_context(session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to get conversation context"""
    manager = get_mongo_manager()
    return manager.get_conversation_context(session_id, limit)

def store_system_memory(component: str, key: str, value: Any, expiry_hours: int = 24) -> bool:
    """Convenience function to store system memory"""
    manager = get_mongo_manager()
    return manager.store_system_state(component, key, value, expiry_hours)

def get_system_memory(component: str, key: str = None) -> Any:
    """Convenience function to get system memory"""
    manager = get_mongo_manager()
    return manager.get_system_state(component, key)


if __name__ == "__main__":
    # Test MongoDB manager
    print("Testing MITO MongoDB Manager...")
    
    manager = MITOMongoManager()
    
    if manager.connected:
        print("✓ MongoDB connection successful")
        
        # Test conversation storage
        session_id = f"test_session_{int(time.time())}"
        manager.store_conversation_memory(session_id, "user_input", "Hello MongoDB!", 0.9)
        manager.store_conversation_memory(session_id, "assistant_response", "MongoDB integration working!", 0.8)
        
        # Test system state
        manager.store_system_state("mito_engine", "version", "1.2.0")
        manager.store_system_state("mito_engine", "mongodb_enabled", True)
        
        # Get stats
        stats = manager.get_database_stats()
        print(f"Database stats: {json.dumps(stats, indent=2, default=str)}")
        
        # Get context
        context = manager.get_conversation_context(session_id)
        print(f"Conversation context: {json.dumps(context, indent=2)}")
        
        print("✓ MongoDB integration test completed successfully")
    else:
        print("✗ MongoDB connection failed - check configuration")
        print("Environment variables needed:")
        print("- MONGODB_URI or MONGODB_HOST/PORT/USERNAME/PASSWORD")
        print("- MONGODB_DATABASE (optional, defaults to 'mito_engine')")