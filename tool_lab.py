#!/usr/bin/env python3
"""
MITO Engine - Tool Lab
Developer toolkit with tool list, development icons, and interface panels
"""

import os
import json
import sqlite3
import subprocess
import importlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ToolCategory(Enum):
    """Tool categories"""
    CODE_GENERATION = "code_generation"
    API_TESTING = "api_testing"
    DATABASE = "database"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SECURITY = "security"
    AI_ML = "ai_ml"
    UTILITIES = "utilities"

class ToolStatus(Enum):
    """Tool status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    BETA = "beta"

@dataclass
class Tool:
    """Development tool definition"""
    tool_id: str
    name: str
    description: str
    category: str
    version: str
    status: str
    icon: str
    command: str
    config: Dict[str, Any]
    dependencies: List[str]
    created_at: str
    last_used: Optional[str]
    usage_count: int

class ToolDatabase:
    """Database for tool management"""
    
    def __init__(self, db_path: str = "tool_lab.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize tool database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                tool_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                icon TEXT,
                command TEXT,
                config TEXT,
                dependencies TEXT,
                created_at TIMESTAMP NOT NULL,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                execution_id TEXT PRIMARY KEY,
                tool_id TEXT NOT NULL,
                user_id TEXT,
                command TEXT NOT NULL,
                arguments TEXT,
                output TEXT,
                error_output TEXT,
                exit_code INTEGER,
                execution_time REAL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                FOREIGN KEY (tool_id) REFERENCES tools (tool_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_configurations (
                config_id TEXT PRIMARY KEY,
                tool_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                config_name TEXT NOT NULL,
                config_data TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (tool_id) REFERENCES tools (tool_id)
            )
        """)
        
        conn.commit()
        conn.close()

class ToolManager:
    """Main tool management system"""
    
    def __init__(self):
        self.db = ToolDatabase()
        self.built_in_tools = self._load_built_in_tools()
        self._register_built_in_tools()
    
    def _load_built_in_tools(self) -> List[Tool]:
        """Load built-in development tools"""
        return [
            Tool(
                tool_id="code_generator",
                name="Code Generator",
                description="Generate code templates and boilerplate",
                category=ToolCategory.CODE_GENERATION.value,
                version="1.2.0",
                status=ToolStatus.ACTIVE.value,
                icon="⚡",
                command="python code_generator.py",
                config={"templates_path": "templates/", "output_path": "generated/"},
                dependencies=["jinja2"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="api_tester",
                name="API Testing Suite",
                description="REST API testing and validation",
                category=ToolCategory.API_TESTING.value,
                version="1.0.0",
                status=ToolStatus.ACTIVE.value,
                icon="🌐",
                command="python api_tester.py",
                config={"base_url": "http://localhost:5000", "timeout": 30},
                dependencies=["requests"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="db_manager",
                name="Database Manager",
                description="Database operations and migrations",
                category=ToolCategory.DATABASE.value,
                version="2.1.0",
                status=ToolStatus.ACTIVE.value,
                icon="🗄️",
                command="python db_manager.py",
                config={"db_url": "sqlite:///data.db", "backup_path": "backups/"},
                dependencies=["sqlalchemy"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="deployment_wizard",
                name="Deployment Wizard",
                description="Automated deployment and configuration",
                category=ToolCategory.DEPLOYMENT.value,
                version="1.5.0",
                status=ToolStatus.ACTIVE.value,
                icon="🚀",
                command="python deployment_wizard.py",
                config={"target_env": "production", "rollback_enabled": True},
                dependencies=["docker", "kubernetes"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="system_monitor",
                name="System Monitor",
                description="Real-time system performance monitoring",
                category=ToolCategory.MONITORING.value,
                version="1.0.0",
                status=ToolStatus.ACTIVE.value,
                icon="📊",
                command="python system_monitor.py",
                config={"refresh_interval": 5, "alert_threshold": 80},
                dependencies=["psutil"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="security_scanner",
                name="Security Scanner",
                description="Code and dependency security analysis",
                category=ToolCategory.SECURITY.value,
                version="1.3.0",
                status=ToolStatus.ACTIVE.value,
                icon="🔒",
                command="python security_scanner.py",
                config={"scan_depth": "full", "report_format": "json"},
                dependencies=["bandit", "safety"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="ml_trainer",
                name="ML Model Trainer",
                description="Machine learning model training and evaluation",
                category=ToolCategory.AI_ML.value,
                version="2.0.0",
                status=ToolStatus.BETA.value,
                icon="🤖",
                command="python ml_trainer.py",
                config={"model_type": "auto", "validation_split": 0.2},
                dependencies=["scikit-learn", "tensorflow"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="log_analyzer",
                name="Log Analyzer",
                description="Parse and analyze application logs",
                category=ToolCategory.UTILITIES.value,
                version="1.1.0",
                status=ToolStatus.ACTIVE.value,
                icon="📋",
                command="python log_analyzer.py",
                config={"log_format": "json", "aggregation": "hourly"},
                dependencies=["pandas"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="benchmark_suite",
                name="Performance Benchmark",
                description="Application performance benchmarking",
                category=ToolCategory.MONITORING.value,
                version="1.0.0",
                status=ToolStatus.ACTIVE.value,
                icon="⚡",
                command="python benchmark_suite.py",
                config={"iterations": 100, "warm_up": 10},
                dependencies=["locust"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            ),
            Tool(
                tool_id="data_validator",
                name="Data Validator",
                description="Data quality validation and cleansing",
                category=ToolCategory.UTILITIES.value,
                version="1.2.0",
                status=ToolStatus.ACTIVE.value,
                icon="✅",
                command="python data_validator.py",
                config={"validation_rules": "strict", "auto_clean": False},
                dependencies=["great_expectations"],
                created_at=datetime.now().isoformat(),
                last_used=None,
                usage_count=0
            )
        ]
    
    def _register_built_in_tools(self):
        """Register built-in tools in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for tool in self.built_in_tools:
            cursor.execute("""
                INSERT OR REPLACE INTO tools 
                (tool_id, name, description, category, version, status, icon, 
                 command, config, dependencies, created_at, last_used, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tool.tool_id, tool.name, tool.description, tool.category,
                tool.version, tool.status, tool.icon, tool.command,
                json.dumps(tool.config), json.dumps(tool.dependencies),
                tool.created_at, tool.last_used, tool.usage_count
            ))
        
        conn.commit()
        conn.close()
    
    def get_tools(self, category: Optional[ToolCategory] = None, 
                  status: Optional[ToolStatus] = None) -> List[Tool]:
        """Get tools with optional filtering"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM tools WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category.value)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        tools = []
        for row in rows:
            tool = Tool(
                tool_id=row[0], name=row[1], description=row[2], category=row[3],
                version=row[4], status=row[5], icon=row[6], command=row[7],
                config=json.loads(row[8]), dependencies=json.loads(row[9]),
                created_at=row[10], last_used=row[11], usage_count=row[12]
            )
            tools.append(tool)
        
        return tools
    
    def execute_tool(self, tool_id: str, arguments: List[str] = None, 
                    user_id: str = None) -> Dict[str, Any]:
        """Execute a tool with given arguments"""
        # Get tool
        tools = [t for t in self.get_tools() if t.tool_id == tool_id]
        if not tools:
            return {"error": "Tool not found"}
        
        tool = tools[0]
        arguments = arguments or []
        
        # Prepare command
        command_parts = tool.command.split() + arguments
        
        execution_id = f"exec_{int(datetime.now().timestamp())}"
        started_at = datetime.now()
        
        try:
            # Execute command
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            completed_at = datetime.now()
            execution_time = (completed_at - started_at).total_seconds()
            
            # Log execution
            self._log_execution(
                execution_id, tool_id, user_id, " ".join(command_parts),
                json.dumps(arguments), result.stdout, result.stderr,
                result.returncode, execution_time, started_at, completed_at
            )
            
            # Update tool usage
            self._update_tool_usage(tool_id)
            
            return {
                "execution_id": execution_id,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Tool execution timed out"}
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
    
    def _log_execution(self, execution_id: str, tool_id: str, user_id: str,
                      command: str, arguments: str, output: str, error_output: str,
                      exit_code: int, execution_time: float, started_at: datetime,
                      completed_at: datetime):
        """Log tool execution"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tool_executions
            (execution_id, tool_id, user_id, command, arguments, output, 
             error_output, exit_code, execution_time, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id, tool_id, user_id, command, arguments, output,
            error_output, exit_code, execution_time, started_at.isoformat(),
            completed_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _update_tool_usage(self, tool_id: str):
        """Update tool usage statistics"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tools 
            SET usage_count = usage_count + 1, last_used = ?
            WHERE tool_id = ?
        """, (datetime.now().isoformat(), tool_id))
        
        conn.commit()
        conn.close()
    
    def get_tool_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get tool usage statistics"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Most used tools
        cursor.execute("""
            SELECT t.name, t.usage_count, t.last_used
            FROM tools t
            ORDER BY t.usage_count DESC
            LIMIT 10
        """)
        most_used = cursor.fetchall()
        
        # Recent executions
        cursor.execute("""
            SELECT t.name, e.started_at, e.exit_code, e.execution_time
            FROM tool_executions e
            JOIN tools t ON e.tool_id = t.tool_id
            WHERE e.started_at >= datetime('now', '-{} days')
            ORDER BY e.started_at DESC
            LIMIT 20
        """.format(days))
        recent_executions = cursor.fetchall()
        
        # Category usage
        cursor.execute("""
            SELECT t.category, SUM(t.usage_count) as total_usage
            FROM tools t
            GROUP BY t.category
            ORDER BY total_usage DESC
        """)
        category_usage = cursor.fetchall()
        
        conn.close()
        
        return {
            "most_used_tools": [
                {"name": row[0], "usage_count": row[1], "last_used": row[2]}
                for row in most_used
            ],
            "recent_executions": [
                {
                    "tool_name": row[0],
                    "started_at": row[1],
                    "exit_code": row[2],
                    "execution_time": row[3]
                }
                for row in recent_executions
            ],
            "category_usage": [
                {"category": row[0], "total_usage": row[1]}
                for row in category_usage
            ]
        }

class ToolLabInterface:
    """Web interface for Tool Lab"""
    
    def __init__(self):
        self.manager = ToolManager()
    
    def generate_lab_interface(self) -> str:
        """Generate HTML interface for Tool Lab"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - Tool Lab</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .lab-container {
            display: grid;
            grid-template-columns: 280px 1fr;
            height: 100vh;
        }
        
        .sidebar {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            overflow-y: auto;
        }
        
        .sidebar h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .category-section {
            margin-bottom: 20px;
        }
        
        .category-header {
            color: #667eea;
            font-size: 1.1rem;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .tool-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tool-item:hover {
            background: rgba(102, 126, 234, 0.3);
            transform: translateX(5px);
        }
        
        .tool-icon {
            font-size: 1.2rem;
            margin-right: 10px;
            width: 24px;
        }
        
        .tool-name {
            flex: 1;
            font-size: 0.9rem;
        }
        
        .tool-status {
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 10px;
            background: rgba(0, 255, 127, 0.2);
            color: #00ff7f;
        }
        
        .main-content {
            padding: 20px;
            overflow-y: auto;
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.1rem;
        }
        
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .tool-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
            transition: all 0.3s ease;
        }
        
        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .tool-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .tool-card-icon {
            font-size: 2rem;
            margin-right: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            padding: 10px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
        }
        
        .tool-card-info h3 {
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .tool-card-info .version {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .tool-description {
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 15px;
            line-height: 1.4;
        }
        
        .tool-stats {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
        }
        
        .tool-actions {
            display: flex;
            gap: 10px;
        }
        
        .action-btn {
            flex: 1;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .run-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        
        .run-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .config-btn {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .config-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .execution-panel {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .execution-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .execution-header h3 {
            color: #667eea;
        }
        
        .clear-btn {
            background: rgba(255, 69, 0, 0.2);
            color: #ff4500;
            border: 1px solid #ff4500;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .execution-log {
            background: #000000;
            color: #00ff00;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            min-height: 200px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .quick-actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .quick-action {
            flex: 1;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .quick-action:hover {
            background: rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }
        
        .quick-action-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .floating-console {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            max-height: 300px;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            display: none;
        }
        
        .console-header {
            padding: 10px 15px;
            background: rgba(102, 126, 234, 0.3);
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .console-content {
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #00ff00;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .running {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="lab-container">
        <div class="sidebar">
            <h2>🛠️ Tool Lab</h2>
            
            <div class="category-section">
                <div class="category-header">🔧 Code Generation</div>
                <div class="tool-item" onclick="selectTool('code_generator')">
                    <span class="tool-icon">⚡</span>
                    <span class="tool-name">Code Generator</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">🌐 API Testing</div>
                <div class="tool-item" onclick="selectTool('api_tester')">
                    <span class="tool-icon">🌐</span>
                    <span class="tool-name">API Tester</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">🗄️ Database</div>
                <div class="tool-item" onclick="selectTool('db_manager')">
                    <span class="tool-icon">🗄️</span>
                    <span class="tool-name">DB Manager</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">🚀 Deployment</div>
                <div class="tool-item" onclick="selectTool('deployment_wizard')">
                    <span class="tool-icon">🚀</span>
                    <span class="tool-name">Deploy Wizard</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">📊 Monitoring</div>
                <div class="tool-item" onclick="selectTool('system_monitor')">
                    <span class="tool-icon">📊</span>
                    <span class="tool-name">System Monitor</span>
                    <span class="tool-status">Active</span>
                </div>
                <div class="tool-item" onclick="selectTool('benchmark_suite')">
                    <span class="tool-icon">⚡</span>
                    <span class="tool-name">Benchmark</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">🔒 Security</div>
                <div class="tool-item" onclick="selectTool('security_scanner')">
                    <span class="tool-icon">🔒</span>
                    <span class="tool-name">Security Scanner</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">🤖 AI/ML</div>
                <div class="tool-item" onclick="selectTool('ml_trainer')">
                    <span class="tool-icon">🤖</span>
                    <span class="tool-name">ML Trainer</span>
                    <span class="tool-status">Beta</span>
                </div>
            </div>
            
            <div class="category-section">
                <div class="category-header">⚙️ Utilities</div>
                <div class="tool-item" onclick="selectTool('log_analyzer')">
                    <span class="tool-icon">📋</span>
                    <span class="tool-name">Log Analyzer</span>
                    <span class="tool-status">Active</span>
                </div>
                <div class="tool-item" onclick="selectTool('data_validator')">
                    <span class="tool-icon">✅</span>
                    <span class="tool-name">Data Validator</span>
                    <span class="tool-status">Active</span>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>TOOL LAB</h1>
                <div class="header-subtitle">Developer toolkit with tool list, development icons, and interface panels</div>
            </div>
            
            <div class="quick-actions">
                <div class="quick-action" onclick="runQuickAction('generate')">
                    <div class="quick-action-icon">⚡</div>
                    <div>Quick Generate</div>
                </div>
                <div class="quick-action" onclick="runQuickAction('test')">
                    <div class="quick-action-icon">🧪</div>
                    <div>Run Tests</div>
                </div>
                <div class="quick-action" onclick="runQuickAction('deploy')">
                    <div class="quick-action-icon">🚀</div>
                    <div>Deploy</div>
                </div>
                <div class="quick-action" onclick="runQuickAction('monitor')">
                    <div class="quick-action-icon">📊</div>
                    <div>Monitor</div>
                </div>
            </div>
            
            <div class="tools-grid">
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">⚡</div>
                        <div class="tool-card-info">
                            <h3>Code Generator</h3>
                            <div class="version">v1.2.0</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Generate code templates and boilerplate for various frameworks and languages.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">847</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">98.3%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">1.2s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('code_generator')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('code_generator')">Configure</button>
                    </div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">🌐</div>
                        <div class="tool-card-info">
                            <h3>API Testing Suite</h3>
                            <div class="version">v1.0.0</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Comprehensive REST API testing and validation with automated test generation.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">523</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">95.7%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">3.5s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('api_tester')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('api_tester')">Configure</button>
                    </div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">🗄️</div>
                        <div class="tool-card-info">
                            <h3>Database Manager</h3>
                            <div class="version">v2.1.0</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Database operations, migrations, and schema management with backup capabilities.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">312</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">99.1%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">0.8s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('db_manager')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('db_manager')">Configure</button>
                    </div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">🚀</div>
                        <div class="tool-card-info">
                            <h3>Deployment Wizard</h3>
                            <div class="version">v1.5.0</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Automated deployment and configuration with rollback capabilities.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">89</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">97.8%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">45.2s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('deployment_wizard')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('deployment_wizard')">Configure</button>
                    </div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">🔒</div>
                        <div class="tool-card-info">
                            <h3>Security Scanner</h3>
                            <div class="version">v1.3.0</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Code and dependency security analysis with vulnerability detection.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">156</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">94.2%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">12.4s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('security_scanner')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('security_scanner')">Configure</button>
                    </div>
                </div>
                
                <div class="tool-card">
                    <div class="tool-card-header">
                        <div class="tool-card-icon">🤖</div>
                        <div class="tool-card-info">
                            <h3>ML Model Trainer</h3>
                            <div class="version">v2.0.0 Beta</div>
                        </div>
                    </div>
                    <div class="tool-description">
                        Machine learning model training and evaluation with automated hyperparameter tuning.
                    </div>
                    <div class="tool-stats">
                        <div class="stat-item">
                            <div class="stat-value">43</div>
                            <div class="stat-label">Executions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">91.3%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">127s</div>
                            <div class="stat-label">Avg Time</div>
                        </div>
                    </div>
                    <div class="tool-actions">
                        <button class="action-btn run-btn" onclick="runTool('ml_trainer')">Run Tool</button>
                        <button class="action-btn config-btn" onclick="configureTool('ml_trainer')">Configure</button>
                    </div>
                </div>
            </div>
            
            <div class="execution-panel">
                <div class="execution-header">
                    <h3>🖥️ Execution Console</h3>
                    <button class="clear-btn" onclick="clearConsole()">Clear</button>
                </div>
                <div class="execution-log" id="executionLog">
                    Welcome to MITO Tool Lab Console
                    Ready to execute development tools...
                    
                    $ tool-lab --status
                    Tool Lab Status: Online
                    Available Tools: 10
                    Active Executions: 0
                    System Status: Operational
                    
                    $ _
                </div>
            </div>
        </div>
    </div>
    
    <div class="floating-console" id="floatingConsole">
        <div class="console-header">
            <span>🛠️ Tool Output</span>
            <button onclick="hideFloatingConsole()" style="background: none; border: none; color: white; cursor: pointer;">✕</button>
        </div>
        <div class="console-content" id="floatingConsoleContent">
            Ready...
        </div>
    </div>
    
    <script>
        let selectedTool = null;
        
        function selectTool(toolId) {
            selectedTool = toolId;
            document.querySelectorAll('.tool-item').forEach(item => {
                item.style.background = 'rgba(255, 255, 255, 0.1)';
            });
            event.target.closest('.tool-item').style.background = 'rgba(102, 126, 234, 0.3)';
            
            logToConsole(`Selected tool: ${toolId}`);
        }
        
        function runTool(toolId) {
            const toolCard = event.target.closest('.tool-card');
            toolCard.classList.add('running');
            
            logToConsole(`Starting ${toolId}...`);
            showFloatingConsole();
            
            // Simulate tool execution
            setTimeout(() => {
                const outputs = {
                    'code_generator': [
                        'Initializing code generator...',
                        'Loading templates...',
                        'Generating boilerplate code...',
                        'Writing files to output directory...',
                        'Code generation completed successfully!'
                    ],
                    'api_tester': [
                        'Starting API test suite...',
                        'Loading test configurations...',
                        'Running endpoint tests...',
                        'Validating responses...',
                        'All tests passed - 15/15 endpoints validated'
                    ],
                    'db_manager': [
                        'Connecting to database...',
                        'Checking schema integrity...',
                        'Running migrations...',
                        'Updating indexes...',
                        'Database operations completed successfully'
                    ]
                };
                
                const toolOutputs = outputs[toolId] || ['Tool executed successfully'];
                let i = 0;
                
                const interval = setInterval(() => {
                    if (i < toolOutputs.length) {
                        addToFloatingConsole(toolOutputs[i]);
                        logToConsole(toolOutputs[i]);
                        i++;
                    } else {
                        clearInterval(interval);
                        toolCard.classList.remove('running');
                        logToConsole(`${toolId} execution completed\\n`);
                    }
                }, 800);
            }, 1000);
        }
        
        function configureTool(toolId) {
            logToConsole(`Opening configuration for ${toolId}...`);
            alert(`Configuration panel for ${toolId} would open here.`);
        }
        
        function runQuickAction(action) {
            const actions = {
                'generate': 'Running quick code generation...',
                'test': 'Executing test suite...',
                'deploy': 'Initiating deployment...',
                'monitor': 'Opening monitoring dashboard...'
            };
            
            logToConsole(actions[action]);
            event.target.classList.add('running');
            
            setTimeout(() => {
                event.target.classList.remove('running');
                logToConsole(`${action} completed\\n`);
            }, 2000);
        }
        
        function logToConsole(message) {
            const log = document.getElementById('executionLog');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `\\n[${timestamp}] ${message}`;
            log.scrollTop = log.scrollHeight;
        }
        
        function clearConsole() {
            document.getElementById('executionLog').innerHTML = 'Console cleared...\\n$ _';
        }
        
        function showFloatingConsole() {
            document.getElementById('floatingConsole').style.display = 'block';
        }
        
        function hideFloatingConsole() {
            document.getElementById('floatingConsole').style.display = 'none';
        }
        
        function addToFloatingConsole(message) {
            const content = document.getElementById('floatingConsoleContent');
            content.innerHTML += message + '\\n';
            content.scrollTop = content.scrollHeight;
        }
        
        // Auto-update console every 5 seconds
        setInterval(() => {
            const timestamp = new Date().toLocaleTimeString();
            // logToConsole(`System heartbeat: ${timestamp}`);
        }, 30000);
    </script>
</body>
</html>
        """

def main():
    """Demo of Tool Lab functionality"""
    print("MITO Engine - Tool Lab Demo")
    print("=" * 50)
    
    # Initialize Tool Lab
    manager = ToolManager()
    
    # Get all tools
    tools = manager.get_tools()
    print(f"Available tools: {len(tools)}")
    
    for tool in tools[:5]:  # Show first 5 tools
        print(f"  ✓ {tool.name} ({tool.category}) - v{tool.version}")
    
    # Get usage statistics
    stats = manager.get_tool_usage_stats()
    print(f"\\nUsage Statistics:")
    print(f"  Most used tools: {len(stats['most_used_tools'])}")
    print(f"  Recent executions: {len(stats['recent_executions'])}")
    print(f"  Categories: {len(stats['category_usage'])}")
    
    print("\\nTool Lab demo completed!")

if __name__ == "__main__":
    main()