#!/usr/bin/env python3
"""
MITO Engine - Memory Management System
Provides intelligent memory management for AI conversations and system operations
"""

import os
import time
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MITOMemoryManager:
    """Advanced memory management for MITO Engine operations"""
    
    def __init__(self, db_path: str = "mito_memory.db"):
        self.db_path = db_path
        self.memory_cache = {}
        self.conversation_context = []
        self.system_state = {}
        self.session_id = None
        self.init_database()
        
    def init_database(self):
        """Initialize memory database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Conversation memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_hash TEXT,
                    importance_score REAL DEFAULT 1.0,
                    retention_priority INTEGER DEFAULT 5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System state memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    state_key TEXT NOT NULL,
                    state_value TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    expiry_time TEXT,
                    access_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User preferences and context
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_identifier TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    context_data TEXT NOT NULL,
                    confidence_score REAL DEFAULT 1.0,
                    last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Memory optimization metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    memory_usage INTEGER,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Memory management database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")
            raise
    
    def start_session(self, session_id: str = None) -> str:
        """Start a new memory session"""
        if not session_id:
            session_id = f"session_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        self.session_id = session_id
        self.conversation_context = []
        self.load_session_context(session_id)
        
        logger.info(f"Memory session started: {session_id}")
        return session_id
    
    def store_conversation(self, message_type: str, content: str, 
                          importance_score: float = 1.0, retention_priority: int = 5) -> bool:
        """Store conversation message in memory"""
        if not self.session_id:
            self.start_session()
        
        try:
            # Generate context hash
            context_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_memory 
                (session_id, timestamp, message_type, content, context_hash, importance_score, retention_priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.session_id,
                datetime.now().isoformat(),
                message_type,
                content,
                context_hash,
                importance_score,
                retention_priority
            ))
            
            conn.commit()
            conn.close()
            
            # Add to current context
            self.conversation_context.append({
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'importance': importance_score
            })
            
            # Limit context size
            if len(self.conversation_context) > 50:
                self.conversation_context = self.conversation_context[-40:]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False
    
    def get_conversation_context(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        if not self.session_id:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT message_type, content, timestamp, importance_score
                FROM conversation_memory
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (self.session_id, limit))
            
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
            
            return list(reversed(context))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return self.conversation_context
    
    def store_system_state(self, component: str, state_key: str, 
                          state_value: Any, expiry_hours: int = 24) -> bool:
        """Store system state information"""
        try:
            # Convert value to JSON string
            if isinstance(state_value, (dict, list)):
                value_str = json.dumps(state_value)
            else:
                value_str = str(state_value)
            
            # Calculate expiry time
            expiry_time = (datetime.now() + timedelta(hours=expiry_hours)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update or insert
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
            
            # Update local cache
            if component not in self.system_state:
                self.system_state[component] = {}
            self.system_state[component][state_key] = state_value
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store system state: {e}")
            return False
    
    def get_system_state(self, component: str, state_key: str = None) -> Any:
        """Get system state information"""
        try:
            # Check cache first
            if component in self.system_state:
                if state_key:
                    return self.system_state[component].get(state_key)
                else:
                    return self.system_state[component]
            
            # Query database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if state_key:
                cursor.execute("""
                    SELECT state_value FROM system_memory
                    WHERE component = ? AND state_key = ? AND 
                          (expiry_time IS NULL OR expiry_time > ?)
                """, (component, state_key, datetime.now().isoformat()))
                
                result = cursor.fetchone()
                if result:
                    # Update access count
                    cursor.execute("""
                        UPDATE system_memory SET access_count = access_count + 1
                        WHERE component = ? AND state_key = ?
                    """, (component, state_key))
                    
                    conn.commit()
                    conn.close()
                    
                    # Try to parse as JSON
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
                
                # Update cache
                self.system_state[component] = state_dict
                return state_dict
                
        except Exception as e:
            logger.error(f"Failed to get system state: {e}")
            return None
    
    def store_user_context(self, user_identifier: str, context_type: str, 
                          context_data: Dict[str, Any], confidence_score: float = 1.0) -> bool:
        """Store user context and preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_context
                (user_identifier, context_type, context_data, confidence_score, last_accessed)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_identifier,
                context_type,
                json.dumps(context_data),
                confidence_score,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store user context: {e}")
            return False
    
    def get_user_context(self, user_identifier: str, context_type: str = None) -> Dict[str, Any]:
        """Get user context and preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if context_type:
                cursor.execute("""
                    SELECT context_data, confidence_score FROM user_context
                    WHERE user_identifier = ? AND context_type = ?
                    ORDER BY last_accessed DESC LIMIT 1
                """, (user_identifier, context_type))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'data': json.loads(result[0]),
                        'confidence': result[1]
                    }
            else:
                cursor.execute("""
                    SELECT context_type, context_data, confidence_score FROM user_context
                    WHERE user_identifier = ?
                    ORDER BY last_accessed DESC
                """, (user_identifier,))
                
                results = cursor.fetchall()
                context = {}
                for row in results:
                    context[row[0]] = {
                        'data': json.loads(row[1]),
                        'confidence': row[2]
                    }
                return context
            
            conn.close()
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return {}
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage by cleaning old data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean expired system state
            cursor.execute("""
                DELETE FROM system_memory 
                WHERE expiry_time IS NOT NULL AND expiry_time < ?
            """, (datetime.now().isoformat(),))
            expired_count = cursor.rowcount
            
            # Clean old low-priority conversations (keep last 1000)
            cursor.execute("""
                DELETE FROM conversation_memory
                WHERE id NOT IN (
                    SELECT id FROM conversation_memory
                    ORDER BY 
                        CASE WHEN retention_priority >= 8 THEN timestamp END DESC,
                        importance_score DESC,
                        timestamp DESC
                    LIMIT 1000
                )
            """, )
            cleaned_conversations = cursor.rowcount
            
            # Clean old user context (keep last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute("""
                DELETE FROM user_context
                WHERE last_accessed < ? AND confidence_score < 0.5
            """, (thirty_days_ago,))
            cleaned_context = cursor.rowcount
            
            # Update metadata
            cursor.execute("""
                INSERT INTO memory_metadata (operation_type, execution_time, memory_usage)
                VALUES (?, ?, ?)
            """, (
                'optimization',
                time.time(),
                self.get_memory_usage()
            ))
            
            conn.commit()
            conn.close()
            
            optimization_result = {
                'expired_states_cleaned': expired_count,
                'conversations_cleaned': cleaned_conversations,
                'context_entries_cleaned': cleaned_context,
                'optimization_time': time.time()
            }
            
            logger.info(f"Memory optimization completed: {optimization_result}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {'error': str(e)}
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        try:
            if os.path.exists(self.db_path):
                return os.path.getsize(self.db_path)
            return 0
        except Exception:
            return 0
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Conversation stats
            cursor.execute("SELECT COUNT(*) FROM conversation_memory")
            conversation_count = cursor.fetchone()[0]
            
            # System state stats
            cursor.execute("SELECT COUNT(*) FROM system_memory")
            system_state_count = cursor.fetchone()[0]
            
            # User context stats
            cursor.execute("SELECT COUNT(*) FROM user_context")
            user_context_count = cursor.fetchone()[0]
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM conversation_memory
                WHERE timestamp > ?
            """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
            recent_conversations = cursor.fetchone()[0]
            
            conn.close()
            
            stats = {
                'database_size_bytes': self.get_memory_usage(),
                'total_conversations': conversation_count,
                'total_system_states': system_state_count,
                'total_user_contexts': user_context_count,
                'recent_24h_conversations': recent_conversations,
                'active_session': self.session_id,
                'cache_size': len(self.memory_cache),
                'system_state_cache': len(self.system_state),
                'current_context_length': len(self.conversation_context)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {'error': str(e)}
    
    def load_session_context(self, session_id: str):
        """Load existing session context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT message_type, content, timestamp, importance_score
                FROM conversation_memory
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
            """, (session_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            self.conversation_context = []
            for row in reversed(results):  # Reverse to get chronological order
                self.conversation_context.append({
                    'type': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'importance': row[3]
                })
            
            logger.info(f"Loaded {len(self.conversation_context)} context items for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to load session context: {e}")
    
    def clear_session(self, session_id: str = None) -> bool:
        """Clear specific session data"""
        target_session = session_id or self.session_id
        if not target_session:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM conversation_memory WHERE session_id = ?
            """, (target_session,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if target_session == self.session_id:
                self.conversation_context = []
            
            logger.info(f"Cleared {deleted_count} items from session {target_session}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
    
    def export_memory_data(self, format_type: str = 'json') -> Dict[str, Any]:
        """Export memory data for backup or analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Export all tables
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'format': format_type,
                'data': {}
            }
            
            # Conversations
            cursor.execute("SELECT * FROM conversation_memory ORDER BY timestamp")
            conversations = cursor.fetchall()
            export_data['data']['conversations'] = conversations
            
            # System states
            cursor.execute("SELECT * FROM system_memory ORDER BY last_updated")
            system_states = cursor.fetchall()
            export_data['data']['system_states'] = system_states
            
            # User contexts
            cursor.execute("SELECT * FROM user_context ORDER BY last_accessed")
            user_contexts = cursor.fetchall()
            export_data['data']['user_contexts'] = user_contexts
            
            conn.close()
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export memory data: {e}")
            return {'error': str(e)}


# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MITOMemoryManager:
    """Get or create global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MITOMemoryManager()
    return _memory_manager

def store_conversation_memory(message_type: str, content: str, importance: float = 1.0) -> bool:
    """Convenience function to store conversation memory"""
    manager = get_memory_manager()
    return manager.store_conversation(message_type, content, importance)

def get_conversation_context(limit: int = 20) -> List[Dict[str, Any]]:
    """Convenience function to get conversation context"""
    manager = get_memory_manager()
    return manager.get_conversation_context(limit)

def store_system_memory(component: str, key: str, value: Any, expiry_hours: int = 24) -> bool:
    """Convenience function to store system memory"""
    manager = get_memory_manager()
    return manager.store_system_state(component, key, value, expiry_hours)

def get_system_memory(component: str, key: str = None) -> Any:
    """Convenience function to get system memory"""
    manager = get_memory_manager()
    return manager.get_system_state(component, key)


if __name__ == "__main__":
    # Test the memory manager
    manager = MITOMemoryManager()
    
    # Start a session
    session_id = manager.start_session()
    print(f"Started session: {session_id}")
    
    # Store some test data
    manager.store_conversation("user_input", "Hello, I need help with the MITO Engine", 0.9)
    manager.store_conversation("assistant_response", "I'll help you with the MITO Engine configuration", 0.8)
    manager.store_system_state("mito_engine", "version", "1.2.0")
    manager.store_system_state("mito_engine", "status", "operational")
    
    # Get stats
    stats = manager.get_memory_stats()
    print("Memory stats:", json.dumps(stats, indent=2))
    
    # Get context
    context = manager.get_conversation_context()
    print("Conversation context:", json.dumps(context, indent=2))
    
    # Optimize memory
    optimization = manager.optimize_memory()
    print("Optimization result:", json.dumps(optimization, indent=2))