#!/usr/bin/env python3
"""
MITO Engine - API Key Lab
Enterprise API management with identifiers, access logs, integrations, and key generation
"""

import os
import json
import sqlite3
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class APIKeyType(Enum):
    """Types of API keys"""
    STANDARD = "standard"
    PREMIUM = "premium" 
    ENTERPRISE = "enterprise"
    DEVELOPER = "developer"
    ANALYTICS = "analytics"
    CLOUD_SERVICE = "cloud_service"
    DATA_PIPELINE = "data_pipeline"

class APIKeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"

@dataclass
class APIKey:
    """API key data structure"""
    key_id: str
    key_value: str
    name: str
    key_type: str
    status: str
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]
    usage_count: int
    rate_limit: int
    permissions: List[str]
    metadata: Dict[str, Any]
    owner_id: str

@dataclass
class AccessLog:
    """API access log entry"""
    log_id: str
    key_id: str
    timestamp: str
    endpoint: str
    method: str
    ip_address: str
    user_agent: str
    response_code: int
    response_time_ms: float
    bytes_transferred: int
    error_message: Optional[str]

class APIKeyGenerator:
    """Generates secure API keys with various formats"""
    
    def __init__(self):
        self.prefix_formats = {
            APIKeyType.STANDARD: "STD",
            APIKeyType.PREMIUM: "PRM", 
            APIKeyType.ENTERPRISE: "ENT",
            APIKeyType.DEVELOPER: "DEV",
            APIKeyType.ANALYTICS: "ANL",
            APIKeyType.CLOUD_SERVICE: "CLD",
            APIKeyType.DATA_PIPELINE: "DPL"
        }
    
    def generate_key(self, key_type: APIKeyType, format_style: str = "dashed") -> str:
        """Generate secure API key with specified format"""
        prefix = self.prefix_formats.get(key_type, "GEN")
        
        if format_style == "dashed":
            # Format: PREFIX-XXXX-XXXX-XXXX
            parts = [
                prefix,
                self._generate_hex_segment(4),
                self._generate_hex_segment(4), 
                self._generate_hex_segment(4)
            ]
            return "-".join(parts)
        
        elif format_style == "compact":
            # Format: PREFIXXXXXXXXXXXXXXXXX
            return prefix + self._generate_hex_segment(20)
        
        elif format_style == "segmented":
            # Format: PREFIX.XXXX.XXXX.XXXX.XXXX
            parts = [
                prefix,
                self._generate_hex_segment(4),
                self._generate_hex_segment(4),
                self._generate_hex_segment(4),
                self._generate_hex_segment(4)
            ]
            return ".".join(parts)
        
        else:
            # Default dashed format
            return self.generate_key(key_type, "dashed")
    
    def _generate_hex_segment(self, length: int) -> str:
        """Generate random hex segment of specified length"""
        return secrets.token_hex(length // 2).upper()[:length]
    
    def generate_key_id(self) -> str:
        """Generate unique key identifier"""
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(4).upper()
        return f"{timestamp[-6:]}{random_part}"

class APIKeyDatabase:
    """Database manager for API keys and access logs"""
    
    def __init__(self, db_path: str = "api_key_lab.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize API key database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                key_value TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                key_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 1000,
                permissions TEXT NOT NULL,
                metadata TEXT,
                owner_id TEXT NOT NULL
            )
        """)
        
        # Access logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                log_id TEXT PRIMARY KEY,
                key_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                response_code INTEGER,
                response_time_ms REAL,
                bytes_transferred INTEGER,
                error_message TEXT,
                FOREIGN KEY (key_id) REFERENCES api_keys (key_id)
            )
        """)
        
        # Key integrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_integrations (
                integration_id TEXT PRIMARY KEY,
                key_id TEXT NOT NULL,
                service_type TEXT NOT NULL,
                service_name TEXT NOT NULL,
                configuration TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_sync TIMESTAMP,
                FOREIGN KEY (key_id) REFERENCES api_keys (key_id)
            )
        """)
        
        # Usage analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_analytics (
                analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT NOT NULL,
                date DATE NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                unique_ips INTEGER DEFAULT 0,
                FOREIGN KEY (key_id) REFERENCES api_keys (key_id)
            )
        """)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_keys_owner ON api_keys(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_keys_status ON api_keys(status)",
            "CREATE INDEX IF NOT EXISTS idx_logs_key ON access_logs(key_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON access_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_key_date ON usage_analytics(key_id, date)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        conn.commit()
        conn.close()

class APIKeyManager:
    """Main API key management system"""
    
    def __init__(self):
        self.db = APIKeyDatabase()
        self.generator = APIKeyGenerator()
        
    def create_api_key(self, name: str, key_type: APIKeyType, owner_id: str,
                      permissions: List[str], expires_days: Optional[int] = None,
                      rate_limit: int = 1000, metadata: Optional[Dict] = None) -> APIKey:
        """Create new API key"""
        
        key_id = self.generator.generate_key_id()
        key_value = self.generator.generate_key(key_type)
        
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        api_key = APIKey(
            key_id=key_id,
            key_value=key_value,
            name=name,
            key_type=key_type.value,
            status=APIKeyStatus.ACTIVE.value,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            last_used=None,
            usage_count=0,
            rate_limit=rate_limit,
            permissions=permissions,
            metadata=metadata or {},
            owner_id=owner_id
        )
        
        # Store in database
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_keys 
            (key_id, key_value, name, key_type, status, created_at, expires_at,
             last_used, usage_count, rate_limit, permissions, metadata, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            api_key.key_id, api_key.key_value, api_key.name, api_key.key_type,
            api_key.status, api_key.created_at, api_key.expires_at, api_key.last_used,
            api_key.usage_count, api_key.rate_limit, json.dumps(api_key.permissions),
            json.dumps(api_key.metadata), api_key.owner_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created API key: {key_id} for {owner_id}")
        return api_key
    
    def get_api_keys(self, owner_id: str = None, status: APIKeyStatus = None) -> List[APIKey]:
        """Get API keys with optional filtering"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM api_keys WHERE 1=1"
        params = []
        
        if owner_id:
            query += " AND owner_id = ?"
            params.append(owner_id)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        api_keys = []
        for row in rows:
            api_key = APIKey(
                key_id=row[0], key_value=row[1], name=row[2], key_type=row[3],
                status=row[4], created_at=row[5], expires_at=row[6], last_used=row[7],
                usage_count=row[8], rate_limit=row[9], 
                permissions=json.loads(row[10]), metadata=json.loads(row[11]),
                owner_id=row[12]
            )
            api_keys.append(api_key)
        
        return api_keys
    
    def log_api_access(self, key_id: str, endpoint: str, method: str,
                      ip_address: str, user_agent: str, response_code: int,
                      response_time_ms: float, bytes_transferred: int = 0,
                      error_message: str = None):
        """Log API access"""
        
        log_id = hashlib.sha256(f"{key_id}{endpoint}{time.time()}".encode()).hexdigest()[:16]
        
        access_log = AccessLog(
            log_id=log_id,
            key_id=key_id,
            timestamp=datetime.now().isoformat(),
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            response_code=response_code,
            response_time_ms=response_time_ms,
            bytes_transferred=bytes_transferred,
            error_message=error_message
        )
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Insert access log
        cursor.execute("""
            INSERT INTO access_logs 
            (log_id, key_id, timestamp, endpoint, method, ip_address, user_agent,
             response_code, response_time_ms, bytes_transferred, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            access_log.log_id, access_log.key_id, access_log.timestamp,
            access_log.endpoint, access_log.method, access_log.ip_address,
            access_log.user_agent, access_log.response_code, access_log.response_time_ms,
            access_log.bytes_transferred, access_log.error_message
        ))
        
        # Update key usage
        cursor.execute("""
            UPDATE api_keys 
            SET usage_count = usage_count + 1, last_used = ?
            WHERE key_id = ?
        """, (access_log.timestamp, key_id))
        
        conn.commit()
        conn.close()
    
    def get_access_logs(self, key_id: str = None, limit: int = 100) -> List[AccessLog]:
        """Get access logs"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM access_logs"
        params = []
        
        if key_id:
            query += " WHERE key_id = ?"
            params.append(key_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            log = AccessLog(
                log_id=row[0], key_id=row[1], timestamp=row[2], endpoint=row[3],
                method=row[4], ip_address=row[5], user_agent=row[6],
                response_code=row[7], response_time_ms=row[8], bytes_transferred=row[9],
                error_message=row[10]
            )
            logs.append(log)
        
        return logs
    
    def create_integration(self, key_id: str, service_type: str, service_name: str,
                          configuration: Dict[str, Any]) -> str:
        """Create service integration for API key"""
        
        integration_id = hashlib.sha256(f"{key_id}{service_type}{time.time()}".encode()).hexdigest()[:12]
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO key_integrations 
            (integration_id, key_id, service_type, service_name, configuration, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            integration_id, key_id, service_type, service_name,
            json.dumps(configuration), "active", datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return integration_id
    
    def get_usage_analytics(self, key_id: str, days: int = 7) -> Dict[str, Any]:
        """Get usage analytics for API key"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Daily usage stats
        cursor.execute("""
            SELECT date, total_requests, successful_requests, failed_requests,
                   avg_response_time, total_bytes, unique_ips
            FROM usage_analytics 
            WHERE key_id = ? AND date >= date('now', '-{} days')
            ORDER BY date
        """.format(days), (key_id,))
        
        daily_stats = cursor.fetchall()
        
        # Overall stats
        cursor.execute("""
            SELECT COUNT(*) as total_requests,
                   SUM(CASE WHEN response_code < 400 THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN response_code >= 400 THEN 1 ELSE 0 END) as failed,
                   AVG(response_time_ms) as avg_response_time,
                   SUM(bytes_transferred) as total_bytes,
                   COUNT(DISTINCT ip_address) as unique_ips
            FROM access_logs 
            WHERE key_id = ? AND timestamp >= datetime('now', '-{} days')
        """.format(days), (key_id,))
        
        overall_stats = cursor.fetchone()
        conn.close()
        
        return {
            "key_id": key_id,
            "period_days": days,
            "daily_stats": [
                {
                    "date": row[0],
                    "total_requests": row[1],
                    "successful_requests": row[2], 
                    "failed_requests": row[3],
                    "avg_response_time": row[4],
                    "total_bytes": row[5],
                    "unique_ips": row[6]
                } for row in daily_stats
            ],
            "overall_stats": {
                "total_requests": overall_stats[0] or 0,
                "successful_requests": overall_stats[1] or 0,
                "failed_requests": overall_stats[2] or 0,
                "avg_response_time": overall_stats[3] or 0,
                "total_bytes": overall_stats[4] or 0,
                "unique_ips": overall_stats[5] or 0,
                "success_rate": (overall_stats[1] / overall_stats[0] * 100) if overall_stats[0] else 0
            }
        }

class APIKeyLabInterface:
    """Web interface for API Key Lab"""
    
    def __init__(self):
        self.manager = APIKeyManager()
    
    def generate_lab_interface(self) -> str:
        """Generate HTML interface for API Key Lab"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - API Key Lab</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .lab-container {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: 100vh;
        }
        
        .sidebar {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .sidebar h2 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .nav-item {
            padding: 12px 16px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .nav-item:hover {
            background: rgba(0, 212, 255, 0.2);
            transform: translateX(5px);
        }
        
        .nav-item.active {
            background: rgba(0, 212, 255, 0.3);
            border-left: 4px solid #00d4ff;
        }
        
        .main-content {
            padding: 20px;
            overflow-y: auto;
        }
        
        .header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #00d4ff;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.1rem;
        }
        
        .generate-key-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #00d4ff;
            font-weight: 600;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            background: rgba(0, 0, 0, 0.3);
            color: #ffffff;
            font-size: 14px;
        }
        
        .generate-btn {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }
        
        .api-keys-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .api-key-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .api-key-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(45deg, #00d4ff, #0099cc);
        }
        
        .key-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .key-name {
            color: #00d4ff;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .key-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-active {
            background: rgba(0, 255, 127, 0.2);
            color: #00ff7f;
        }
        
        .key-value {
            font-family: 'Courier New', monospace;
            font-size: 16px;
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 6px;
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            letter-spacing: 2px;
        }
        
        .key-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.4rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 5px;
        }
        
        .integrations-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
        }
        
        .integration-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .integration-card {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .integration-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            font-size: 24px;
        }
        
        .access-logs {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 25px;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .log-table th,
        .log-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .log-table th {
            color: #00d4ff;
            font-weight: 600;
        }
        
        .response-code {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .code-success {
            background: rgba(0, 255, 127, 0.2);
            color: #00ff7f;
        }
        
        .code-error {
            background: rgba(255, 69, 0, 0.2);
            color: #ff4500;
        }
        
        .floating-stats {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 12px;
            padding: 20px;
            min-width: 250px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .generate-btn:active {
            animation: pulse 0.3s ease;
        }
        
        .copy-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .copy-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="lab-container">
        <div class="sidebar">
            <h2>🔑 API Key Lab</h2>
            <div class="nav-item active" onclick="showSection('keys')">
                📊 Key Management
            </div>
            <div class="nav-item" onclick="showSection('generate')">
                ➕ Generate Keys
            </div>
            <div class="nav-item" onclick="showSection('integrations')">
                🔗 Integrations
            </div>
            <div class="nav-item" onclick="showSection('analytics')">
                📈 Analytics
            </div>
            <div class="nav-item" onclick="showSection('logs')">
                📋 Access Logs
            </div>
        </div>
        
        <div class="main-content">
            <div class="header">
                <div>
                    <h1>API KEY LAB</h1>
                    <div class="header-subtitle">Enterprise API management with identifiers, access logs, and integrations</div>
                </div>
            </div>
            
            <div id="generate-section" class="generate-key-section">
                <h3 style="color: #00d4ff; margin-bottom: 20px;">🚀 GENERATE NEW API KEY</h3>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div class="form-group">
                        <label for="keyName">Key Name</label>
                        <input type="text" id="keyName" placeholder="Enter API key name" value="CloudService Integration">
                    </div>
                    
                    <div class="form-group">
                        <label for="keyType">Key Type</label>
                        <select id="keyType">
                            <option value="standard">Standard</option>
                            <option value="premium">Premium</option>
                            <option value="enterprise" selected>Enterprise</option>
                            <option value="analytics">Analytics Tool</option>
                            <option value="cloud_service">Cloud Service</option>
                            <option value="data_pipeline">Data Pipeline</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="rateLimit">Rate Limit (req/min)</label>
                        <input type="number" id="rateLimit" value="5000" min="100">
                    </div>
                    
                    <div class="form-group">
                        <label for="expiryDays">Expiry (days)</label>
                        <input type="number" id="expiryDays" value="365" min="1">
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="generate-btn" onclick="generateAPIKey()">
                        🔑 GENERATE KEY
                    </button>
                </div>
            </div>
            
            <div class="api-keys-grid">
                <div class="api-key-card">
                    <div class="key-header">
                        <div class="key-name">CloudService Integration</div>
                        <div class="key-status status-active">Active</div>
                    </div>
                    
                    <div class="key-value">
                        ENT-C6DI-84F9-6H11
                        <button class="copy-btn" onclick="copyToClipboard('ENT-C6DI-84F9-6H11')">Copy</button>
                    </div>
                    
                    <div class="key-stats">
                        <div class="stat-item">
                            <div class="stat-value">1,247</div>
                            <div class="stat-label">Total Requests</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">98.2%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">2h ago</div>
                            <div class="stat-label">Last Used</div>
                        </div>
                    </div>
                </div>
                
                <div class="api-key-card">
                    <div class="key-header">
                        <div class="key-name">Analytics Tool</div>
                        <div class="key-status status-active">Active</div>
                    </div>
                    
                    <div class="key-value">
                        ANL-B2F8-9A3E-7D12
                        <button class="copy-btn" onclick="copyToClipboard('ANL-B2F8-9A3E-7D12')">Copy</button>
                    </div>
                    
                    <div class="key-stats">
                        <div class="stat-item">
                            <div class="stat-value">892</div>
                            <div class="stat-label">Total Requests</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">99.1%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">5m ago</div>
                            <div class="stat-label">Last Used</div>
                        </div>
                    </div>
                </div>
                
                <div class="api-key-card">
                    <div class="key-header">
                        <div class="key-name">Data Pipeline</div>
                        <div class="key-status status-active">Active</div>
                    </div>
                    
                    <div class="key-value">
                        DPL-F4A7-2B9C-8E15
                        <button class="copy-btn" onclick="copyToClipboard('DPL-F4A7-2B9C-8E15')">Copy</button>
                    </div>
                    
                    <div class="key-stats">
                        <div class="stat-item">
                            <div class="stat-value">2,156</div>
                            <div class="stat-label">Total Requests</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">97.8%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">1m ago</div>
                            <div class="stat-label">Last Used</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="integrations-section">
                <h3 style="color: #00d4ff; margin-bottom: 20px;">🔗 SERVICE INTEGRATIONS</h3>
                
                <div class="integration-grid">
                    <div class="integration-card">
                        <div class="integration-icon">☁️</div>
                        <h4>CloudService</h4>
                        <p style="color: rgba(255,255,255,0.7); margin: 10px 0;">AWS S3 bucket integration for file storage and retrieval operations.</p>
                        <div style="color: #00ff7f; font-size: 14px;">✓ Connected</div>
                    </div>
                    
                    <div class="integration-card">
                        <div class="integration-icon">📊</div>
                        <h4>AnalyticsTool</h4>
                        <p style="color: rgba(255,255,255,0.7); margin: 10px 0;">Real-time analytics dashboard with ML insights and predictions.</p>
                        <div style="color: #00ff7f; font-size: 14px;">✓ Connected</div>
                    </div>
                    
                    <div class="integration-card">
                        <div class="integration-icon">🔄</div>
                        <h4>DataPipeline</h4>
                        <p style="color: rgba(255,255,255,0.7); margin: 10px 0;">ETL pipeline for processing and transforming data streams.</p>
                        <div style="color: #00ff7f; font-size: 14px;">✓ Connected</div>
                    </div>
                </div>
            </div>
            
            <div class="access-logs">
                <h3 style="color: #00d4ff; margin-bottom: 20px;">📋 RECENT ACCESS LOGS</h3>
                
                <table class="log-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>API Key</th>
                            <th>Endpoint</th>
                            <th>Method</th>
                            <th>Response</th>
                            <th>IP Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2025-06-20 09:15:42</td>
                            <td>ENT-C6DI-***</td>
                            <td>/api/v1/analytics/data</td>
                            <td>GET</td>
                            <td><span class="response-code code-success">200</span></td>
                            <td>192.168.1.100</td>
                        </tr>
                        <tr>
                            <td>2025-06-20 09:14:38</td>
                            <td>ANL-B2F8-***</td>
                            <td>/api/v1/cloud/upload</td>
                            <td>POST</td>
                            <td><span class="response-code code-success">201</span></td>
                            <td>10.0.0.45</td>
                        </tr>
                        <tr>
                            <td>2025-06-20 09:13:22</td>
                            <td>DPL-F4A7-***</td>
                            <td>/api/v1/pipeline/process</td>
                            <td>POST</td>
                            <td><span class="response-code code-success">200</span></td>
                            <td>172.16.0.10</td>
                        </tr>
                        <tr>
                            <td>2025-06-20 09:12:15</td>
                            <td>ENT-C6DI-***</td>
                            <td>/api/v1/analytics/metrics</td>
                            <td>GET</td>
                            <td><span class="response-code code-error">429</span></td>
                            <td>192.168.1.100</td>
                        </tr>
                        <tr>
                            <td>2025-06-20 09:11:03</td>
                            <td>ANL-B2F8-***</td>
                            <td>/api/v1/data/export</td>
                            <td>GET</td>
                            <td><span class="response-code code-success">200</span></td>
                            <td>10.0.0.45</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="floating-stats">
        <h4 style="color: #00d4ff; margin-bottom: 15px;">📊 Live Stats</h4>
        <div style="margin-bottom: 10px;">
            <strong>Active Keys:</strong> 3
        </div>
        <div style="margin-bottom: 10px;">
            <strong>Total Requests Today:</strong> 4,295
        </div>
        <div style="margin-bottom: 10px;">
            <strong>Success Rate:</strong> 98.4%
        </div>
        <div>
            <strong>Avg Response Time:</strong> 145ms
        </div>
    </div>
    
    <script>
        function generateAPIKey() {
            const keyName = document.getElementById('keyName').value;
            const keyType = document.getElementById('keyType').value;
            
            // Generate mock API key
            const prefixes = {
                'standard': 'STD',
                'premium': 'PRM',
                'enterprise': 'ENT',
                'analytics': 'ANL',
                'cloud_service': 'CLD',
                'data_pipeline': 'DPL'
            };
            
            const prefix = prefixes[keyType];
            const segments = [
                Math.random().toString(36).substr(2, 4).toUpperCase(),
                Math.random().toString(36).substr(2, 4).toUpperCase(),
                Math.random().toString(36).substr(2, 4).toUpperCase()
            ];
            
            const newKey = `${prefix}-${segments.join('-')}`;
            
            alert(`New API Key Generated:\\n\\nName: ${keyName}\\nKey: ${newKey}\\n\\nKey has been added to your dashboard.`);
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('API Key copied to clipboard!');
            });
        }
        
        function showSection(section) {
            // Update navigation
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        // Auto-refresh stats every 30 seconds
        setInterval(() => {
            const statsElement = document.querySelector('.floating-stats');
            statsElement.style.animation = 'pulse 0.5s ease';
            setTimeout(() => {
                statsElement.style.animation = '';
            }, 500);
        }, 30000);
    </script>
</body>
</html>
        """

def main():
    """Demo of API Key Lab functionality"""
    print("MITO Engine - API Key Lab Demo")
    print("=" * 50)
    
    # Initialize API Key Lab
    manager = APIKeyManager()
    
    # Create sample API keys
    sample_keys = [
        {
            "name": "CloudService Integration",
            "key_type": APIKeyType.ENTERPRISE,
            "owner_id": "user001",
            "permissions": ["read", "write", "delete"],
            "rate_limit": 5000
        },
        {
            "name": "Analytics Tool",
            "key_type": APIKeyType.ANALYTICS,
            "owner_id": "user001", 
            "permissions": ["read", "analytics"],
            "rate_limit": 3000
        },
        {
            "name": "Data Pipeline",
            "key_type": APIKeyType.DATA_PIPELINE,
            "owner_id": "user002",
            "permissions": ["read", "write", "process"],
            "rate_limit": 10000
        }
    ]
    
    print("Creating sample API keys...")
    for key_data in sample_keys:
        api_key = manager.create_api_key(**key_data)
        print(f"  ✓ Created: {api_key.name} - {api_key.key_value}")
        
        # Log some sample access
        for i in range(5):
            manager.log_api_access(
                key_id=api_key.key_id,
                endpoint=f"/api/v1/data/{i}",
                method="GET",
                ip_address="192.168.1.100",
                user_agent="MITO-Client/1.0",
                response_code=200,
                response_time_ms=150.0,
                bytes_transferred=1024
            )
    
    # Get all keys
    all_keys = manager.get_api_keys()
    print(f"\nTotal API keys: {len(all_keys)}")
    
    # Show analytics for first key
    if all_keys:
        analytics = manager.get_usage_analytics(all_keys[0].key_id)
        print(f"Analytics for {all_keys[0].name}:")
        print(f"  Total requests: {analytics['overall_stats']['total_requests']}")
        print(f"  Success rate: {analytics['overall_stats']['success_rate']:.1f}%")
    
    print("\nAPI Key Lab demo completed!")

if __name__ == "__main__":
    main()