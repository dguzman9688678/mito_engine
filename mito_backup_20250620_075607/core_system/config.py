"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

import os
from datetime import datetime

class Config:
    """Application configuration"""
    
    # Platform Info
    PLATFORM_NAME = "MITO Engine - AI Agent & Tool Creator"
    PLATFORM_VERSION = "1.2.0"
    PLATFORM_CREATOR = "Daniel Guzman"
    PLATFORM_CONTACT = "guzman.danield@outlook.com"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "mito-engine-secret-key-2025")
    
    # AI Provider Configuration
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
    LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "llama-3.1-70b-versatile")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Free Groq API key
    
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "llama")
    
    # File handling
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'json', 'xml', 'md', 'py', 'js', 'html', 'css', 'yaml', 'yml'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Debug
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
