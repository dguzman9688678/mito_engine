#!/usr/bin/env python3
"""
MITO Engine - Complete Integrated AI Development Platform
Version: 1.0.0
Author: Daniel Guzman
Description: Secure AI development platform with real-time WebSocket capabilities,
            multi-industry project management, and advanced weight management system.
"""

import os
import json
import redis
import bcrypt
import jwt
import psycopg2
import requests
import secrets
import hashlib
import logging
import time
import threading
import uuid
import psutil
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
from functools import wraps
from threading import Lock

# Flask and extensions
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from werkzeug.utils import secure_filename

# Input validation
import bleach
from marshmallow import Schema, fields, validate, ValidationError

# ================================
# 1. LOGGING SETUP
# ================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mito_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ================================
# 2. CONFIGURATION
# ================================

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    RATELIMIT_DEFAULT = "100 per hour"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = "RedisCache"
    CACHE_DEFAULT_TIMEOUT = 600
    PLATFORM_NAME = "MITO Engine"
    PLATFORM_VERSION = "1.0.0"
    PLATFORM_CREATOR = "Daniel Guzman"
    PLATFORM_CONTACT = "guzman.daniel@outlook.com"
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    
    API_KEY_LENGTH = 64
    TOKEN_EXPIRY_HOURS = 12
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # AI Provider Configuration
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
    LLAMA_API_URL = os.getenv("LLAMA_API_URL")
    LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "llama-3-70b-8192")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229")
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "llama")
    
    # Security Settings
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'json', 'xml', 'md', 'py', 'js', 'html', 'css', 'yaml', 'yml'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

config = Config()

# ================================
# 3. INPUT VALIDATION SCHEMAS
# ================================

class ProjectInitSchema(Schema):
    industry = fields.Str(required=True, validate=validate.OneOf(['software', 'ai/ml', 'media', 'healthcare', 'finance']))
    project_data = fields.Dict(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    description = fields.Str(validate=validate.Length(max=2000))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))

class FileUploadSchema(Schema):
    user_id = fields.Str(required=True, validate=validate.Length(min=1, max=255))

# ================================
# 4. UTILITY FUNCTIONS
# ================================

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS and other attacks"""
    if not text:
        return ""
    cleaned = bleach.clean(text, tags=[], strip=True)
    return cleaned[:max_length]

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def validate_file_size(file) -> bool:
    """Validate file size"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size <= config.MAX_FILE_SIZE

# ================================
# 5. MITO WEIGHTS SYSTEM
# ================================

MITO_WEIGHTS = {
    "engineering": 0.92,
    "security": 0.81,
    "reasoning": 0.88,
    "memory": 0.76,
    "language_modeling": 0.69,
    "narrative": 0.44,
    "visual_design": 0.52,
    "metadata_protection": 0.89,
    "autonomy": 0.95,
    "command_loyalty": 1.00,
    "task_prioritization": {
        "code_implementation": 0.90,
        "terminal_automation": 0.85,
        "prompt_response": 0.50,
        "image_generation": 0.40,
        "simulation_runtime": 0.80,
        "environment_analysis": 0.77
    },
    "language_processing": {
        "natural_language": 0.60,
        "programmatic_language": 0.95,
        "code_integration": 0.93
    },
    "execution_engine": {
        "local_mode": 0.97,
        "api_bridge": 0.88,
        "self_hosting_compatibility": 1.0
    }
}

MITO_MODULES = {
    "juggernaut.py": 1.0,
    "hidden.py": 1.0,
    "odin_security_core": 0.93,
    "imprint_laws": 1.0,
    "code_generation": 0.98,
    "execution_engine": 0.96,
    "system_design": 0.93,
    "sandbox_analysis": 0.91,
    "llm_integration": 0.89,
    "memory_binding": 0.86,
    "metadata_concealment": 0.95,
    "api_toggling": 0.82,
    "secure_config_handling": 0.90,
    "weight_control_interface": 0.87,
    "self_host_compatibility": 0.94,
    "creator_command_loyalty": 1.00
}

MITO_PRIORITIES = {
    "task_engine": {
        "develop_code": 0.98,
        "test_scenarios": 0.92,
        "deploy_scripts": 0.91,
        "auto_compile": 0.90,
        "simulate_breaches": 0.88
    },
    "environment_integration": {
        "local_mongo_binding": 0.94,
        "remote_api_sync": 0.83,
        "file_structure_mapping": 0.91
    },
    "security_enforcement": {
        "command_isolation": 1.0,
        "system_fallbacks": 0.87
    }
}

MITO_META = {
    "name": "MITO Engine",
    "version": "1.0.0",
    "created_by": "Daniel Guzman",
    "description": "Secure AI development platform with multi-industry support and advanced weight management",
    "initialized_at": datetime.utcnow().isoformat(),
    "core_modules": len(MITO_MODULES),
    "weight_categories": len(MITO_WEIGHTS),
    "security_level": "maximum"
}

class MitoWeightsManager:
    """Manages MITO weights, modules, and system configuration"""
    
    def __init__(self):
        self.weights = MITO_WEIGHTS.copy()
        self.modules = MITO_MODULES.copy()
        self.priorities = MITO_PRIORITIES.copy()
        self.meta = MITO_META.copy()
        self.logger = logger
        
    def get_weight(self, category: str, subcategory: str = None) -> Optional[float]:
        """Get specific weight value"""
        try:
            if subcategory:
                return self.weights.get(category, {}).get(subcategory)
            return self.weights.get(category)
        except Exception as e:
            self.logger.error(f"Weight retrieval failed: {e}")
            return None
    
    def set_weight(self, category: str, value: float, subcategory: str = None) -> bool:
        """Set weight value (admin only)"""
        try:
            if not 0.0 <= value <= 1.0:
                raise ValueError("Weight must be between 0.0 and 1.0")
            
            if subcategory:
                if category not in self.weights:
                    self.weights[category] = {}
                self.weights[category][subcategory] = value
            else:
                self.weights[category] = value
            
            self.logger.info(f"Weight updated: {category}.{subcategory or ''} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"Weight update failed: {e}")
            return False
    
    def _calculate_system_health(self) -> Dict[str, float]:
        """Calculate overall system health metrics"""
        try:
            core_weights = [v for k, v in self.weights.items() if isinstance(v, (int, float))]
            avg_weight = sum(core_weights) / len(core_weights) if core_weights else 0.0
            
            active_modules = sum(1 for v in self.modules.values() if v >= 0.8)
            module_availability = active_modules / len(self.modules) if self.modules else 0.0
            
            security_weight = self.weights.get("security", 0.0)
            command_loyalty = self.weights.get("command_loyalty", 0.0)
            security_score = (security_weight + command_loyalty) / 2
            
            return {
                "overall_health": (avg_weight + module_availability + security_score) / 3,
                "average_weight": avg_weight,
                "module_availability": module_availability,
                "security_score": security_score,
                "critical_systems": command_loyalty
            }
        except Exception as e:
            self.logger.error(f"System health calculation failed: {e}")
            return {"overall_health": 0.0, "error": "calculation_failed"}

# Initialize global weights manager
mito_weights = MitoWeightsManager()

# ================================
# 6. AI PROVIDERS
# ================================

try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
except ImportError:
    Anthropic = None
    HUMAN_PROMPT = "\n\nHuman:"
    AI_PROMPT = "\n\nAssistant:"
    logger.warning("Anthropic package not installed")

def llama3_generate(prompt: str) -> str:
    """Generate text using LLaMA API"""
    try:
        clean_prompt = sanitize_input(prompt, 4000)
        
        url = os.getenv("LLAMA_API_URL")
        api_key = os.getenv("LLAMA_API_KEY")
        
        if not url or not api_key:
            raise ValueError("LLAMA_API_URL and LLAMA_API_KEY must be configured")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": os.getenv("LLAMA_MODEL_NAME", "llama-3-70b-8192"),
            "messages": [{"role": "user", "content": clean_prompt}],
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
        
    except Exception as e:
        logger.error(f"LLaMA generation error: {e}")
        return "Error: LLaMA generation failed"

def claude_generate(prompt: str) -> str:
    """Generate text using Claude API"""
    try:
        if Anthropic is None:
            raise ImportError("anthropic package not installed")
        
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise ValueError("CLAUDE_API_KEY not configured")
        
        clean_prompt = sanitize_input(prompt, 4000)
        
        client = Anthropic(api_key=claude_api_key)
        completion = client.completions.create(
            model=os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229"),
            max_tokens_to_sample=1024,
            prompt=f"{HUMAN_PROMPT} {clean_prompt}{AI_PROMPT}"
        )
        return completion.completion
        
    except Exception as e:
        logger.error(f"Claude generation error: {e}")
        return "Error: Claude generation failed"

def ai_generate(prompt: str, provider: str = None) -> str:
    """Generate text using configured AI provider with fallback"""
    provider = provider or os.getenv("MODEL_PROVIDER", "llama")
    
    try:
        if provider == "claude":
            return claude_generate(prompt)
        else:
            return llama3_generate(prompt)
    except Exception as e:
        logger.error(f"AI generation failed for provider '{provider}': {e}")
        
        # Fallback logic
        try:
            if provider == "claude":
                logger.info("Attempting fallback to LLaMA")
                return llama3_generate(prompt)
            else:
                logger.info("Attempting fallback to Claude")
                return claude_generate(prompt)
        except Exception as fallback_error:
            logger.error(f"Fallback provider also failed: {fallback_error}")
            return "Error: All AI providers failed"

AVAILABLE_PROVIDERS = ["llama", "claude"]

# ================================
# 7. DATABASE MODELS & MANAGEMENT
# ================================

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
        self.redis_client = redis.from_url(config.REDIS_URL)
        self.logger = logger
        self.initialize_database()

    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(
                config.DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise

    def initialize_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
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
            
            # Projects table
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
            
            # Files table
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
                    processing_results JSONB,
                    project_id VARCHAR(255) REFERENCES projects(id)
                )
            """)
            
            # API keys table
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
            
            # MITO weights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mito_weights (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(100) NOT NULL,
                    subcategory VARCHAR(100),
                    weight_value DECIMAL(4,3) NOT NULL CHECK (weight_value >= 0.0 AND weight_value <= 1.0),
                    updated_by VARCHAR(255) REFERENCES users(id),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    UNIQUE(category, subcategory)
                )
            """)
            
            # System logs table
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
            self.logger.info("Database tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def create_default_admin(self):
        """Create default admin user for Daniel Guzman"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if admin already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", ("guzman.daniel@outlook.com",))
            if cursor.fetchone():
                self.logger.info("Default admin already exists")
                return
            
            # Use environment variable for password
            admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
            if not admin_password:
                self.logger.warning("DEFAULT_ADMIN_PASSWORD not set, using temporary password")
                admin_password = "TempPass123!ChangeMe"
            
            admin_id = "daniel_guzman_admin"
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, role, permissions, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                admin_id,
                "guzman.daniel@outlook.com",
                password_hash,
                "administrator",
                json.dumps(["all"]),
                datetime.utcnow()
            ))
            
            conn.commit()
            self.logger.info("Default admin user created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create default admin: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
        except Exception as e:
            self.logger.error(f"Get user by email failed: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def create_user(self, email: str, password: str, role: str = "user") -> Optional[str]:
        """Create new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            user_id = secrets.token_hex(16)
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, role, permissions, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id, email, password_hash, role, 
                json.dumps(["read", "write"]), datetime.utcnow()
            ))
            conn.commit()
            self.logger.info(f"User created: {email}")
            return user_id
        except psycopg2.IntegrityError:
            self.logger.warning(f"User creation failed - duplicate email: {email}")
            return None
        except Exception as e:
            self.logger.error(f"User creation failed: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def create_project(self, name: str, description: str, industry: str, 
                      manager_type: str, created_by: str, metadata: dict = None) -> Optional[str]:
        """Create new project"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            project_id = secrets.token_hex(16)
            now = datetime.utcnow()
            
            cursor.execute("""
                INSERT INTO projects (id, name, description, industry, manager_type, 
                                    status, created_by, created_at, updated_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, name, description, industry, manager_type,
                "active", created_by, now, now, json.dumps(metadata or {})
            ))
            conn.commit()
            self.logger.info(f"Project created: {project_id}")
            return project_id
        except Exception as e:
            self.logger.error(f"Project creation failed: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def create_file_record(self, filename: str, original_name: str, file_type: str,
                          file_size: int, mime_type: str, uploaded_by: str,
                          project_id: str = None) -> Optional[str]:
        """Create file record in database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            file_id = secrets.token_hex(16)
            
            cursor.execute("""
                INSERT INTO files (id, filename, original_name, file_type, file_size,
                                 mime_type, uploaded_by, uploaded_at, project_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                file_id, filename, original_name, file_type, file_size,
                mime_type, uploaded_by, datetime.utcnow(), project_id
            ))
            conn.commit()
            self.logger.info(f"File record created: {file_id}")
            return file_id
        except Exception as e:
            self.logger.error(f"File record creation failed: {e}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def update_file_processing_results(self, file_id: str, results: dict) -> bool:
        """Update file processing results"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE files SET processed = TRUE, processing_results = %s 
                WHERE id = %s
            """, (json.dumps(results), file_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"File processing update failed: {e}")
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

# Initialize database manager
db_manager = DatabaseManager()
db_manager.create_default_admin()

# ================================
# 8. SECURITY MANAGER
# ================================

class AdvancedSecurityManager:
    def __init__(self):
        self.fernet_key = Fernet.generate_key()
        self.fernet = Fernet(self.fernet_key)
        self.jwt_secret = config.SECRET_KEY
        self.redis = db_manager.redis_client
        self.logger = logger

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hash_pw: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hash_pw.encode("utf-8"))
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False

    def generate_jwt_token(self, user_id: str, role: str, expires_hours: int = None) -> str:
        try:
            payload = {
                "user_id": user_id,
                "role": role,
                "exp": datetime.utcnow() + timedelta(hours=expires_hours or config.TOKEN_EXPIRY_HOURS),
                "iat": datetime.utcnow()
            }
            return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        except Exception as e:
            self.logger.error(f"JWT token generation failed: {e}")
            raise

    def verify_jwt_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token expired")
            return {}
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid JWT token")
            return {}
        except Exception as e:
            self.logger.error(f"JWT verification failed: {e}")
            return {}

    def log_auth_attempt(self, email: str, success: bool, ip_address: str = None):
        self.logger.info(f"Auth attempt - Email: {email}, Success: {success}, IP: {ip_address}")

security_manager = AdvancedSecurityManager()

# ================================
# 9. AUTHENTICATION MIDDLEWARE
# ================================

def require_auth(roles=None):
    """Authentication decorator for protected endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authentication required"}), 401
            
            token = auth_header.split(' ')[1]
            payload = security_manager.verify_jwt_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            if roles and payload.get('role') not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            
            request.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ================================
# 10. FILE PROCESSOR
# ================================

class AdvancedFileProcessor:
    def __init__(self):
        self.logger = logger

    def process_file(self, file_path: str, file_type: str, user_id: str) -> dict:
        """Process uploaded file with comprehensive error handling"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if file_type not in config.ALLOWED_EXTENSIONS:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            clean_user_id = sanitize_input(user_id, 255)
            self.logger.info(f"Processing file: {file_path}, type: {file_type}, user: {clean_user_id}")
            
            if file_type in ["txt", "md", "csv", "py", "js", "json", "xml", "html", "css", "yaml", "yml"]:
                content = self._read_text_file(file_path)
                analysis = self._analyze_text(content)
                return {"type": "text", "analysis": analysis, "status": "success"}
            
            elif file_type == "pdf":
                content = self._read_pdf_file(file_path)
                analysis = self._analyze_text(content)
                return {"type": "pdf", "analysis": analysis, "status": "success"}
            
            elif file_type in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"]:
                analysis = self._analyze_image(file_path)
                return {"type": "image", "analysis": analysis, "status": "success"}
            
            else:
                return {"error": "Unsupported file type", "status": "error"}
                
        except Exception as e:
            self.logger.error(f"File processing failed: {e}")
            return {"error": f"File processing failed: {str(e)}", "status": "error"}
        
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to clean up file {file_path}: {e}")

    def _read_text_file(self, file_path: str) -> str:
        """Read text file with encoding detection"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return content[:50000]  # 50KB limit
        except Exception as e:
            self.logger.error(f"Failed to read text file {file_path}: {e}")
            raise

    def _read_pdf_file(self, file_path: str) -> str:
        """Read PDF file with error handling"""
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_content = []
                max_pages = min(len(reader.pages), 50)
                for i in range(max_pages):
                    page_text = reader.pages[i].extract_text() or ""
                    text_content.append(page_text)
                return "\n".join(text_content)[:50000]
        except Exception as e:
            self.logger.error(f"Failed to read PDF file {file_path}: {e}")
            raise

    def _analyze_text(self, content: str) -> dict:
        """Analyze text content using AI"""
        try:
            if not content.strip():
                return {"summary": "Empty file.", "word_count": 0}
            
            word_count = len(content.split())
            char_count = len(content)
            
            if len(content) <= 3500:
                prompt = f"Provide a brief summary and key points for this document:\n{content}"
                summary = ai_generate(prompt)
            else:
                prompt = f"Provide a brief summary and key points for this document (excerpt):\n{content[:3500]}"
                summary = ai_generate(prompt)
                summary += f"\n\nNote: This is a partial analysis of a {word_count} word document."
            
            return {
                "summary": summary,
                "word_count": word_count,
                "char_count": char_count
            }
            
        except Exception as e:
            self.logger.error(f"Text analysis failed: {e}")
            return {"summary": "Analysis failed", "error": str(e)}

    def _analyze_image(self, file_path: str) -> dict:
        """Analyze image file"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
            
            return {
                "description": "Image analysis requires vision-enabled AI models",
                "width": width,
                "height": height,
                "format": format_type,
                "mode": mode
            }
            
        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return {"description": "Image analysis failed", "error": str(e)}

# ================================
# 11. PROJECT MANAGERS
# ================================

class AdvancedProjectManager:
    def __init__(self, industry: str, specializations: List[str]):
        self.industry = industry
        self.specializations = specializations
        self.logger = logger

    def initialize_project(self, project_data: dict) -> dict:
        """Initialize project with validation"""
        try:
            clean_data = {}
            for key, value in project_data.items():
                if isinstance(value, str):
                    clean_data[sanitize_input(key, 100)] = sanitize_input(value, 1000)
                else:
                    clean_data[sanitize_input(str(key), 100)] = value
            
            prompt = self._create_initialization_prompt(clean_data)
            response = ai_generate(prompt)
            
            self.logger.info(f"Project initialized for industry: {self.industry}")
            
            return {
                "status": "success",
                "industry": self.industry,
                "specializations": self.specializations,
                "response": response,
                "project_data": clean_data
            }
            
        except Exception as e:
            self.logger.error(f"Project initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "industry": self.industry
            }

    def _create_initialization_prompt(self, project_data: dict) -> str:
        return f"""
        Initialize a new {self.industry} project with the following specifications:
        - Industry: {self.industry}
        - Specializations: {', '.join(self.specializations)}
        - Project Data: {json.dumps(project_data, indent=2)}
        
        Please provide:
        1. Project structure recommendations
        2. Key milestones
        3. Technology stack suggestions
        4. Best practices for this industry
        """

# Project manager instances
software_manager = AdvancedProjectManager("software", ["web", "mobile", "backend"])
aiml_manager = AdvancedProjectManager("ai/ml", ["vision", "nlp", "recommendation"])
media_manager = AdvancedProjectManager("media", ["video", "audio", "graphics"])
healthcare_manager = AdvancedProjectManager("healthcare", ["ehr", "telemedicine"])
finance_manager = AdvancedProjectManager("finance", ["fintech", "analytics"])

# ================================
# 12. REAL-TIME WEBSOCKET SYSTEM
# ================================

@dataclass
class RealTimeEvent:
    event_type: str
    category: str
    data: Dict[str, Any]
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    priority: str = "normal"

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_current_metrics(self) -> Dict[str, Any]:
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "active_connections": len(psutil.net_connections()),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"System metrics failed: {e}")
            return {"error": "metrics_unavailable"}
    
    def get_uptime(self) -> str:
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

class RealTimeEventManager:
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.active_sessions = {}
        self.event_queue = []
        self.event_lock = Lock()
        self.logger = logger
        self.system_monitor = SystemMonitor()
        
    def register_session(self, session_id: str, user_id: str, user_role: str):
        with self.event_lock:
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "user_role": user_role,
                "connected_at": datetime.utcnow().isoformat(),
                "last_ping": datetime.utcnow().isoformat()
            }
        
        self.logger.info(f"WebSocket session registered: {session_id}")
        self._send_initial_state(session_id)
    
    def unregister_session(self, session_id: str):
        with self.event_lock:
            if session_id in self.active_sessions:
                user_info = self.active_sessions.pop(session_id)
                self.logger.info(f"WebSocket session unregistered: {session_id}")
    
    def broadcast_event(self, event: RealTimeEvent, room: str = None):
        try:
            event_data = {
                "event_type": event.event_type,
                "category": event.category,
                "data": event.data,
                "timestamp": event.timestamp,
                "priority": event.priority
            }
            
            with self.event_lock:
                self.event_queue.append(event_data)
                if len(self.event_queue) > 100:
                    self.event_queue.pop(0)
            
            if room:
                self.socketio.emit('real_time_event', event_data, room=room)
            else:
                self.socketio.emit('real_time_event', event_data)
            
            self.logger.info(f"Event broadcasted: {event.event_type}")
            
        except Exception as e:
            self.logger.error(f"Event broadcast failed: {e}")
    
    def _send_initial_state(self, session_id: str):
        try:
            initial_state = {
                "system_health": mito_weights._calculate_system_health(),
                "active_sessions": len(self.active_sessions),
                "recent_events": self.event_queue[-10:] if self.event_queue else [],
                "system_metrics": self.system_monitor.get_current_metrics(),
                "mito_status": {
                    "version": MITO_META["version"],
                    "uptime": self.system_monitor.get_uptime(),
                    "modules_active": sum(1 for v in mito_weights.modules.values() if v >= 0.8)
                }
            }
            
            self.socketio.emit('initial_state', initial_state, room=session_id)
            
        except Exception as e:
            self.logger.error(f"Initial state send failed: {e}")

# ================================
# 13. FLASK APPLICATION SETUP
# ================================

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

CORS(app, origins=["*"])
limiter = Limiter(
    app, 
    key_func=get_remote_address, 
    default_limits=[config.RATELIMIT_DEFAULT], 
    storage_uri=config.REDIS_URL
)
cache = Cache(app, config={
    'CACHE_TYPE': config.CACHE_TYPE,
    'CACHE_REDIS_URL': config.REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': config.CACHE_DEFAULT_TIMEOUT
})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize processors
file_processor = AdvancedFileProcessor()

# Create upload directory
Path(config.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialize event manager
event_manager = RealTimeEventManager(socketio)

# ================================
# 14. WEBSOCKET HANDLERS
# ================================

@socketio.on('connect')
def handle_connect(auth):
    try:
        if not auth or 'token' not in auth:
            disconnect()
            return False
        
        payload = security_manager.verify_jwt_token(auth['token'])
        if not payload:
            disconnect()
            return False
        
        user_id = payload['user_id']
        user_role = payload['role']
        session_id = request.sid
        
        join_room(f"user_{user_id}")
        join_room(f"role_{user_role}")
        
        event_manager.register_session(session_id, user_id, user_role)
        
        event_manager.broadcast_event(RealTimeEvent(
            event_type="user_connected",
            category="system",
            data={"user_id": user_id, "role": user_role},
            timestamp=datetime.utcnow().isoformat()
        ), room=f"role_{user_role}")
        
        logger.info(f"WebSocket connected: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"WebSocket connect failed: {e}")
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    try:
        session_id = request.sid
        event_manager.unregister_session(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket disconnect failed: {e}")

@socketio.on('ping')
def handle_ping():
    try:
        session_id = request.sid
        if session_id in event_manager.active_sessions:
            event_manager.active_sessions[session_id]["last_ping"] = datetime.utcnow().isoformat()
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(f"WebSocket ping failed: {e}")

# ================================
# 15. API ENDPOINTS
# ================================

@app.route("/")
def home():
    """Home page with platform information"""
    platform_info = {
        "name": config.PLATFORM_NAME,
        "version": config.PLATFORM_VERSION,
        "creator": config.PLATFORM_CREATOR,
        "contact": config.PLATFORM_CONTACT,
        "status": "active",
        "features": [
            "AI Project Management",
            "Advanced File Processing", 
            "Multi-Industry Support",
            "Secure Authentication",
            "Real-time WebSocket Updates",
            "MITO Weight Management"
        ],
        "supported_industries": ["software", "ai/ml", "media", "healthcare", "finance"]
    }
    return jsonify(platform_info)

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def api_auth_login():
    """User login"""
    try:
        schema = LoginSchema()
        data = schema.load(request.json)
        
        email = data["email"]
        password = data["password"]
        ip_address = request.remote_addr
        
        user = db_manager.get_user_by_email(email)
        if not user:
            security_manager.log_auth_attempt(email, False, ip_address)
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not security_manager.verify_password(password, user['password_hash']):
            security_manager.log_auth_attempt(email, False, ip_address)
            return jsonify({"error": "Invalid credentials"}), 401
        
        token = security_manager.generate_jwt_token(user['id'], user['role'])
        
        security_manager.log_auth_attempt(email, True, ip_address)
        logger.info(f"User logged in: {email}")
        
        # Broadcast login event
        event_manager.broadcast_event(RealTimeEvent(
            event_type="user_login",
            category="authentication",
            data={"user_id": user['id'], "email": email},
            timestamp=datetime.utcnow().isoformat(),
            user_id=user['id']
        ), room=f"role_{user['role']}")
        
        return jsonify({
            "token": token,
            "user_id": user['id'],
            "role": user['role'],
            "message": "Login successful"
        })
        
    except ValidationError as e:
        return jsonify({"error": "Invalid input data", "details": e.messages}), 400
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/file/analyze", methods=["POST"])
@limiter.limit("5 per minute")
@require_auth()
def api_file_analyze():
    """Analyze uploaded file with real-time updates"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files['file']
        user_id = request.current_user['user_id']
        project_id = request.form.get('project_id')
        
        if file.filename == '' or not allowed_file(file.filename) or not validate_file_size(file):
            return jsonify({"error": "Invalid file"}), 400
        
        # Broadcast file upload start
        event_manager.broadcast_event(RealTimeEvent(
            event_type="file_upload_started",
            category="file_processing",
            data={
                "filename": file.filename,
                "user_id": user_id,
                "project_id": project_id
            },
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id
        ), room=f"user_{user_id}")
        
        # Process file
        filename = secure_filename(file.filename)
        file_type = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{secrets.token_hex(8)}_{filename}"
        save_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
        file.save(save_path)
        
        # Create file record
        file_id = db_manager.create_file_record(
            filename=unique_filename,
            original_name=filename,
            file_type=file_type,
            file_size=os.path.getsize(save_path),
            mime_type=file.content_type,
            uploaded_by=user_id,
            project_id=project_id
        )
        
        # Broadcast processing start
        event_manager.broadcast_event(RealTimeEvent(
            event_type="file_processing_started",
            category="file_processing",
            data={
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type
            },
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id
        ), room=f"user_{user_id}")
        
        # Process file
        result = file_processor.process_file(save_path, file_type, user_id)
        
        # Save results and broadcast completion
        if file_id and result.get('status') == 'success':
            db_manager.update_file_processing_results(file_id, result)
            
            event_manager.broadcast_event(RealTimeEvent(
                event_type="file_processing_completed",
                category="file_processing",
                data={
                    "file_id": file_id,
                    "filename": filename,
                    "result": result
                },
                timestamp=datetime.utcnow().isoformat(),
                user_id=user_id,
                priority="high"
            ), room=f"user_{user_id}")
        
        result['file_id'] = file_id
        return jsonify(result)
        
    except Exception as e:
        event_manager.broadcast_event(RealTimeEvent(
            event_type="file_processing_error",
            category="file_processing",
            data={"error": str(e)},
            timestamp=datetime.utcnow().isoformat(),
            user_id=request.current_user.get('user_id'),
            priority="critical"
        ))
        
        logger.error(f"File analysis failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/ai/generate", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth()
def api_ai_generate():
    """AI generation with real-time progress updates"""
    try:
        data = request.json
        user_id = request.current_user['user_id']
        prompt = data.get("prompt")
        provider = data.get("provider")
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Broadcast AI generation start
        generation_id = str(uuid.uuid4())
        event_manager.broadcast_event(RealTimeEvent(
            event_type="ai_generation_started",
            category="ai_processing",
            data={
                "generation_id": generation_id,
                "provider": provider or os.getenv("MODEL_PROVIDER", "llama"),
                "prompt_length": len(prompt)
            },
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id
        ), room=f"user_{user_id}")
        
        # Generate response
        clean_prompt = sanitize_input(prompt, 4000)
        start_time = time.time()
        response = ai_generate(clean_prompt, provider=provider)
        processing_time = time.time() - start_time
        
        # Broadcast completion
        event_manager.broadcast_event(RealTimeEvent(
            event_type="ai_generation_completed",
            category="ai_processing",
            data={
                "generation_id": generation_id,
                "response_length": len(response),
                "processing_time": f"{processing_time:.2f}s",
                "provider_used": provider or os.getenv("MODEL_PROVIDER", "llama")
            },
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            priority="high"
        ), room=f"user_{user_id}")
        
        return jsonify({
            "response": response,
            "generation_id": generation_id,
            "provider_used": provider or os.getenv("MODEL_PROVIDER", "llama"),
            "processing_time": f"{processing_time:.2f}s"
        })
        
    except Exception as e:
        event_manager.broadcast_event(RealTimeEvent(
            event_type="ai_generation_error",
            category="ai_processing",
            data={"error": str(e)},
            timestamp=datetime.utcnow().isoformat(),
            user_id=request.current_user.get('user_id'),
            priority="critical"
        ))
        
        logger.error(f"AI generation failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/project/initialize", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth()
def api_initialize_project():
    """Initialize a new project"""
    try:
        schema = ProjectInitSchema()
        data = schema.load(request.json)
        
        industry = data["industry"]
        user_id = request.current_user['user_id']
        
        # Select appropriate manager
        managers = {
            "software": software_manager,
            "ai/ml": aiml_manager,
            "media": media_manager,
            "healthcare": healthcare_manager,
            "finance": finance_manager
        }
        
        manager = managers.get(industry)
        if not manager:
            return jsonify({"error": "Invalid industry"}), 400
        
        # Create project in database
        project_id = db_manager.create_project(
            name=data["name"],
            description=data.get("description", ""),
            industry=industry,
            manager_type=industry,
            created_by=user_id,
            metadata=data.get("project_data", {})
        )
        
        if not project_id:
            return jsonify({"error": "Failed to create project"}), 400
        
        # Initialize project with AI
        result = manager.initialize_project(data["project_data"])
        result["project_id"] = project_id
        
        # Broadcast project creation
        event_manager.broadcast_event(RealTimeEvent(
            event_type="project_created",
            category="project_management",
            data={
                "project_id": project_id,
                "name": data["name"],
                "industry": industry,
                "created_by": user_id
            },
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            priority="high"
        ), room=f"user_{user_id}")
        
        logger.info(f"Project initialized: {project_id}")
        return jsonify(result)
        
    except ValidationError as e:
        return jsonify({"error": "Invalid input data", "details": e.messages}), 400
    except Exception as e:
        logger.error(f"Project initialization failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/mito/weights", methods=["GET"])
@require_auth()
def api_get_mito_weights():
    """Get MITO weights configuration"""
    return jsonify({
        "weights": mito_weights.weights,
        "system_health": mito_weights._calculate_system_health(),
        "last_updated": datetime.utcnow().isoformat()
    })

@app.route("/api/mito/weights/<category>", methods=["PUT"])
@require_auth(roles=["administrator"])
def api_update_weight(category):
    """Update weight with real-time broadcast"""
    try:
        data = request.json
        user_id = request.current_user['user_id']
        value = data.get("value")
        subcategory = data.get("subcategory")
        
        if value is None or not 0.0 <= value <= 1.0:
            return jsonify({"error": "Invalid value"}), 400
        
        old_value = mito_weights.get_weight(category, subcategory)
        success = mito_weights.set_weight(category, value, subcategory)
        
        if success:
            # Broadcast weight update to all administrators
            event_manager.broadcast_event(RealTimeEvent(
                event_type="mito_weight_updated",
                category="mito_system",
                data={
                    "category": category,
                    "subcategory": subcategory,
                    "old_value": old_value,
                    "new_value": value,
                    "updated_by": user_id
                },
                timestamp=datetime.utcnow().isoformat(),
                user_id=user_id,
                priority="high"
            ), room="role_administrator")
            
            # Broadcast system health update
            new_health = mito_weights._calculate_system_health()
            event_manager.broadcast_event(RealTimeEvent(
                event_type="system_health_updated",
                category="mito_system",
                data={"health_metrics": new_health},
                timestamp=datetime.utcnow().isoformat(),
                priority="normal"
            ))
            
            return jsonify({
                "message": "Weight updated", 
                "category": category, 
                "value": value,
                "system_health": new_health
            })
        
        return jsonify({"error": "Failed to update weight"}), 400
        
    except Exception as e:
        logger.error(f"Weight update failed: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        db_manager.redis_client.ping()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": config.PLATFORM_VERSION,
            "database": "connected",
            "redis": "connected",
            "websocket": "active",
            "active_sessions": len(event_manager.active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 503

# ================================
# 16. SYSTEM MONITORING
# ================================

def start_system_monitoring():
    """Start background system monitoring task"""
    def monitor_loop():
        while True:
            try:
                metrics = event_manager.system_monitor.get_current_metrics()
                health = mito_weights._calculate_system_health()
                
                # Broadcast system metrics every 30 seconds
                event_manager.broadcast_event(RealTimeEvent(
                    event_type="system_metrics_update",
                    category="system_monitoring",
                    data={
                        "metrics": metrics,
                        "health": health,
                        "active_sessions": len(event_manager.active_sessions)
                    },
                    timestamp=datetime.utcnow().isoformat(),
                    priority="low"
                ))
                
                # Check for critical conditions
                if metrics.get("cpu_percent", 0) > 90:
                    event_manager.broadcast_event(RealTimeEvent(
                        event_type="high_cpu_usage",
                        category="system_alerts",
                        data={"cpu_percent": metrics["cpu_percent"]},
                        timestamp=datetime.utcnow().isoformat(),
                        priority="critical"
                    ), room="role_administrator")
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(30)
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info("System monitoring started")

def initialize_websocket_system():
    """Initialize WebSocket system on startup"""
    try:
        start_system_monitoring()
        
        event_manager.broadcast_event(RealTimeEvent(
            event_type="system_startup",
            category="system",
            data={
                "version": MITO_META["version"],
                "startup_time": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow().isoformat(),
            priority="high"
        ))
        
        logger.info("WebSocket system initialized")
        return True
        
    except Exception as e:
        logger.error(f"WebSocket initialization failed: {e}")
        return False

# ================================
# 17. ERROR HANDLERS
# ================================

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"Bad request: {error}")
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"Unauthorized access: {error}")
    return jsonify({"error": "Unauthorized"}), 401

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"Forbidden access: {error}")
    return jsonify({"error": "Forbidden"}), 403

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Not found: {error}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(413)
def payload_too_large(error):
    logger.warning(f"Payload too large: {error}")
    return jsonify({"error": "File too large"}), 413

@app.errorhandler(429)
def ratelimit_handler(error):
    logger.warning(f"Rate limit exceeded: {error}")
    return jsonify({"error": "Rate limit exceeded"}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ================================
# 18. MIDDLEWARE
# ================================

@app.before_request
def log_request_info():
    """Log request information"""
    logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    """Log response information"""
    logger.info(f"Response: {response.status_code} for {request.method} {request.url}")
    return response

# ================================
# 19. ADDITIONAL API ENDPOINTS
# ================================

@app.route("/api/mito/system", methods=["GET"])
@require_auth()
def api_get_mito_system():
    """Get complete MITO system profile"""
    return jsonify({
        "weights": mito_weights.weights,
        "modules": mito_weights.modules,
        "priorities": mito_weights.priorities,
        "meta": mito_weights.meta,
        "system_health": mito_weights._calculate_system_health(),
        "active_sessions": len(event_manager.active_sessions),
        "uptime": event_manager.system_monitor.get_uptime()
    })

@app.route("/api/ai/providers", methods=["GET"])
def api_ai_providers():
    """Get available AI providers"""
    return jsonify({
        "available_providers": AVAILABLE_PROVIDERS,
        "current_default": os.getenv("MODEL_PROVIDER", "llama"),
        "provider_info": {
            "llama": {
                "name": "LLaMA (OpenAI Compatible)",
                "cost": "Paid",
                "model": os.getenv("LLAMA_MODEL_NAME", "llama-3-70b-8192"),
                "requires_key": True,
                "configured": bool(os.getenv("LLAMA_API_KEY")) and bool(os.getenv("LLAMA_API_URL"))
            },
            "claude": {
                "name": "Anthropic Claude",
                "cost": "Paid",
                "model": os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229"),
                "requires_key": True,
                "configured": bool(os.getenv("CLAUDE_API_KEY"))
            }
        }
    })

@app.route("/api/websocket/status", methods=["GET"])
@require_auth()
def api_websocket_status():
    """Get WebSocket system status"""
    return jsonify({
        "active_sessions": len(event_manager.active_sessions),
        "total_events_processed": len(event_manager.event_queue),
        "system_monitoring": "active",
        "real_time_features": [
            "File processing updates",
            "AI generation progress",
            "MITO weight changes",
            "System health monitoring",
            "User activity tracking"
        ]
    })

# ================================
# 20. STARTUP AND MAIN EXECUTION
# ================================

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["SECRET_KEY", "DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True

def print_startup_banner():
    """Print startup banner with system information"""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                        MITO ENGINE                           ║
║                   Version {config.PLATFORM_VERSION}          ║
║                                                              ║
║  Advanced AI Development Platform                            ║
║  Created by: {config.PLATFORM_CREATOR}                       ║
║  Contact: {config.PLATFORM_CONTACT}                          ║
║                                                              ║
║  Features:                                                   ║
║  • Multi-Industry Project Management                         ║
║  • Real-time WebSocket Updates                               ║
║  • Advanced File Processing                                  ║
║  • MITO Weight Management System                             ║
║  • Secure Authentication & Authorization                     ║
║  • AI Provider Integration (LLaMA, Claude)                   ║
║                                                              ║
║  Status: INITIALIZING...                                     ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    try:
        # Print startup banner
        print_startup_banner()
        
        # Validate environment
        if not validate_environment():
            exit(1)
        
        # Initialize WebSocket system
        initialize_websocket_system()
        
        # Log successful startup
        logger.info(f"Starting {config.PLATFORM_NAME} v{config.PLATFORM_VERSION}")
        logger.info(f"Debug mode: {config.DEBUG}")
        logger.info(f"Database: Connected")
        logger.info(f"Redis: Connected") 
        logger.info(f"WebSocket: Active")
        logger.info(f"AI Providers: {', '.join(AVAILABLE_PROVIDERS)}")
        logger.info(f"MITO Modules: {len(MITO_MODULES)} loaded")
        logger.info(f"Security Level: {MITO_META['security_level']}")
        
        print(f"\nMITO Engine is running on http://localhost:{os.getenv('PORT', 8080)}")
        print(f"WebSocket endpoint: ws://localhost:{os.getenv('PORT', 8080)}")
        print(f"Admin Email: guzman.daniel@outlook.com")
        print(f"MITO Weight System: ACTIVE")
        print(f"Security Level: MAXIMUM")
        print(f"Real-time Updates: ENABLED")
        print("\n" + "="*60)
        print("MITO ENGINE READY FOR OPERATIONS")
        print("="*60 + "\n")
        
        # Start the Flask-SocketIO application
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=int(os.getenv("PORT", 8080)), 
            debug=config.DEBUG,
            use_reloader=False  # Disable reloader to prevent double initialization
        )
        
    except KeyboardInterrupt:
        logger.info("MITO Engine shutdown requested by user")
        print("\n MITO Engine shutting down...")
        
    except Exception as e:
        logger.error(f"MITO Engine startup failed: {e}")
        print(f"\n MITO Engine failed to start: {e}")
        exit(1)

# ================================
# 21. WEBSOCKET CLIENT EXAMPLE
# ================================

"""
JavaScript WebSocket Client Example:

const socket = io('http://localhost:8080', {
    auth: {
        token: localStorage.getItem('mito_jwt_token')
    }
});

// Connection events
socket.on('connect', () => {
    console.log(' Connected to MITO Engine');
});

// Receive initial state
socket.on('initial_state', (data) => {
    console.log('Initial system state:', data);
    updateDashboard(data);
});

// Real-time event handling
socket.on('real_time_event', (event) => {
    console.log('⚡ Real-time event:', event);
    
    switch(event.event_type) {
        case 'file_processing_completed':
            showNotification('File processed successfully!');
            updateFileList();
            break;
            
        case 'ai_generation_completed':
            displayAIResponse(event.data);
            break;
            
        case 'mito_weight_updated':
            updateWeightDisplay(event.data);
            break;
            
        case 'system_health_updated':
            updateHealthMetrics(event.data.health_metrics);
            break;
            
        case 'user_connected':
            updateActiveUsers();
            break;
    }
});

// System monitoring
socket.on('system_metrics_update', (data) => {
    updateSystemMetrics(data.metrics);
});

// Keepalive
setInterval(() => {
    socket.emit('ping');
}, 30000);

socket.on('pong', (data) => {
    console.log('Pong:', data.timestamp);
});

// Error handling
socket.on('connect_error', (error) => {
    console.error('Connection failed:', error);
});

socket.on('disconnect', (reason) => {
    console.log(' Disconnected:', reason);
});
"""

# ================================
# 22. ENVIRONMENT VARIABLES TEMPLATE
# ================================

"""
Environment Variables Required (.env file):

# Core Configuration
SECRET_KEY=your-super-secret-jwt-key-here
DATABASE_URL=postgresql://username:password@localhost:5432/mito_engine
REDIS_URL=redis://localhost:6379/0
DEFAULT_ADMIN_PASSWORD=YourSecurePassword123!

# AI Providers
MODEL_PROVIDER=llama
LLAMA_API_URL=https://api.groq.com/openai/v1/chat/completions
LLAMA_API_KEY=your_groq_api_key_here
LLAMA_MODEL_NAME=llama-3-70b-8192
CLAUDE_API_KEY=your_claude_api_key_here
CLAUDE_MODEL_NAME=claude-3-opus-20240229

# Optional Configuration
DEBUG=false
PORT=8080
UPLOAD_FOLDER=uploads
"""

# ================================
# END OF MITO ENGINE
# ================================