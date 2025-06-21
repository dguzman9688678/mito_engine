"""
DATABASE MODELS & MANAGEMENT
"""

import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import bcrypt
import json

from config import config
from logging_setup import logger

@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

@dataclass
class Project:
    id: str
    name: str
    description: str
    industry: str
    manager_type: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class FileRecord:
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime
    processed: bool = False
    processing_results: Optional[Dict] = None

class DatabaseManager:
    """Advanced database management with connection pooling"""

    def __init__(self):
        self.connection_pool = []
        self.max_connections = 20
        self.redis_client = redis.from_url(config.REDIS_URL)
        self.initialize_database()

    def get_connection(self):
        """Get database connection from pool"""
        try:
            return psycopg2.connect(
                config.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise

    def initialize_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(100) NOT NULL,
                    permissions JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    description TEXT,
                    industry VARCHAR(100) NOT NULL,
                    manager_type VARCHAR(100) NOT NULL,
                    status VARCHAR(100) NOT NULL,
                    created_by VARCHAR(255) REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id VARCHAR(255) PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    original_name VARCHAR(500) NOT NULL,
                    file_type VARCHAR(100) NOT NULL,
                    file_size BIGINT NOT NULL,
                    mime_type VARCHAR(200),
                    uploaded_by VARCHAR(255) REFERENCES users(id),
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_results JSONB
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id VARCHAR(255) PRIMARY KEY,
                    key_hash VARCHAR(255) UNIQUE NOT NULL,
                    user_id VARCHAR(255) REFERENCES users(id),
                    name VARCHAR(200),
                    permissions JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    level VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    module VARCHAR(200),
                    user_id VARCHAR(255),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("database_initialized", tables_created=5)
        except Exception as e:
            logger.error("database_initialization_failed", error=str(e))
            raise

    def create_default_admin(self):
        """Create default admin user for Daniel Guzman"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            admin_id = "daniel_guzman_admin"
            password_hash = bcrypt.hashpw("529504Djg1.".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, role, permissions, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                admin_id,
                "guzman.daniel@outlook.com",
                password_hash,
                "administrator",
                json.dumps(["all"]),
                datetime.utcnow()
            ))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("default_admin_created", user_id=admin_id)
        except Exception as e:
            logger.error("default_admin_creation_failed", error=str(e))

db_manager = DatabaseManager()
db_manager.create_default_admin()