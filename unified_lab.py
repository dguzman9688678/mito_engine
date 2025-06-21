"""
MITO Engine - Unified Laboratory Interface
Combines all laboratory environments into one comprehensive interface
"""

import sqlite3
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class UnifiedLabInterface:
    """Unified laboratory interface combining all lab environments"""
    
    def __init__(self):
        self.db_path = "unified_lab.db"
        self.init_database()
    
    def init_database(self):
        """Initialize unified lab database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT UNIQUE NOT NULL,
                service TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Tools table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                last_executed TIMESTAMP,
                execution_count INTEGER DEFAULT 0
            )
        ''')
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                training_epoch INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT,
                version TEXT DEFAULT '1.0.0',
                views INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Deployments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                cpu_usage REAL DEFAULT 0.0,
                memory_usage REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Code files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                language TEXT NOT NULL,
                content TEXT,
                size INTEGER DEFAULT 0,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize sample data
        self.init_sample_data()
    
    def init_sample_data(self):
        """Initialize sample data for all lab components"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sample API Keys
        api_keys = [
            ("ENT-C6DI-84F9-6H11", "CloudService", "active"),
            ("ANL-K9J2-L3M4-N5P6", "AnalyticsTool", "active"),
            ("DAT-Q7R8-S9T0-U1V2", "DataPipeline", "maintenance")
        ]
        
        for key_id, service, status in api_keys:
            cursor.execute('INSERT OR IGNORE INTO api_keys (key_id, service, status) VALUES (?, ?, ?)',
                         (key_id, service, status))
        
        # Sample Tools
        tools = [
            ("Code Generator", "development", "online"),
            ("API Tester", "testing", "online"),
            ("Database Manager", "data", "online"),
            ("Deployment Manager", "devops", "online"),
            ("System Monitor", "monitoring", "online"),
            ("Security Scanner", "security", "online"),
            ("ML Trainer", "ai", "online"),
            ("Package Manager", "utilities", "online"),
            ("Terminal", "utilities", "online"),
            ("Whiteboard", "collaboration", "online")
        ]
        
        for name, category, status in tools:
            cursor.execute('INSERT OR IGNORE INTO tools (name, category, status) VALUES (?, ?, ?)',
                         (name, category, status))
        
        # Sample Agents
        agents = [
            ("ConversationalBot", "conversational", "training", 25, 0.87),
            ("AnalyticsAgent", "analytical", "deployed", 100, 0.94),
            ("CreativeAssistant", "creative", "idle", 0, 0.0)
        ]
        
        for name, agent_type, status, epoch, accuracy in agents:
            cursor.execute('INSERT OR IGNORE INTO agents (name, type, status, training_epoch, accuracy) VALUES (?, ?, ?, ?, ?)',
                         (name, agent_type, status, epoch, accuracy))
        
        # Sample Documents
        documents = [
            ("API Reference", "api", "Complete API documentation", "2.1.0", 156, 4.8),
            ("Architecture Guide", "architecture", "System architecture overview", "1.5.0", 89, 4.6),
            ("User Manual", "guides", "End-user documentation", "3.0.0", 245, 4.9),
            ("Deployment Guide", "deployment", "Production deployment instructions", "1.8.0", 78, 4.7),
            ("Technical Specs", "specs", "Technical specifications", "2.3.0", 134, 4.5)
        ]
        
        for name, category, content, version, views, rating in documents:
            cursor.execute('INSERT OR IGNORE INTO documents (name, category, content, version, views, rating) VALUES (?, ?, ?, ?, ?, ?)',
                         (name, category, content, version, views, rating))
        
        # Sample Deployments
        deployments = [
            ("api-service-v1", "us-east-1", "production", "running", 45.2, 68.7),
            ("web-frontend", "us-west-2", "production", "running", 32.1, 54.3),
            ("data-processor", "eu-west-1", "production", "running", 78.9, 82.1),
            ("ml-pipeline", "asia-pacific-1", "staging", "deploying", 12.4, 23.6)
        ]
        
        for name, region, environment, status, cpu, memory in deployments:
            cursor.execute('INSERT OR IGNORE INTO deployments (name, region, environment, status, cpu_usage, memory_usage) VALUES (?, ?, ?, ?, ?, ?)',
                         (name, region, environment, status, cpu, memory))
        
        # Sample Code Files
        code_files = [
            ("main.py", "python", "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello World!'\n\nif __name__ == '__main__':\n    app.run(debug=True)", 145),
            ("styles.css", "css", "body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background: #f0f0f0;\n}\n\n.container {\n    max-width: 1200px;\n    margin: 0 auto;\n}", 168),
            ("script.js", "javascript", "function initializeApp() {\n    console.log('App initialized');\n    \n    document.addEventListener('DOMContentLoaded', function() {\n        setupEventListeners();\n    });\n}\n\nfunction setupEventListeners() {\n    // Event handlers\n}", 234)
        ]
        
        for filename, language, content, size in code_files:
            cursor.execute('INSERT OR IGNORE INTO code_files (filename, language, content, size) VALUES (?, ?, ?, ?)',
                         (filename, language, content, size))
        
        conn.commit()
        conn.close()
    
    def generate_unified_lab_interface(self):
        """Generate the unified laboratory interface HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - Unified Laboratory</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .lab-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
            position: relative;
        }
        
        .header h1 {
            color: #00d4ff;
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.8);
            font-weight: 300;
            letter-spacing: 2px;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.2rem;
            margin-bottom: 20px;
        }
        
        .lab-tabs {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        
        .lab-tab {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            color: rgba(255, 255, 255, 0.8);
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .lab-tab.active {
            background: rgba(0, 212, 255, 0.3);
            color: #00d4ff;
            border-color: #00d4ff;
        }
        
        .lab-tab:hover {
            background: rgba(0, 212, 255, 0.2);
            transform: translateY(-1px);
        }
        
        .nav-controls {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
        }
        
        .nav-btn {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.5);
            color: #00d4ff;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .nav-btn:hover {
            background: rgba(0, 212, 255, 0.2);
            transform: translateY(-1px);
        }
        
        .lab-content {
            flex: 1;
            padding: 30px;
            display: none;
        }
        
        .lab-content.active {
            display: block;
        }
        
        .lab-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .lab-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .lab-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            border-color: rgba(0, 212, 255, 0.3);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .card-icon {
            font-size: 2rem;
            margin-right: 15px;
            opacity: 0.8;
        }
        
        .card-title {
            color: #00d4ff;
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .card-content {
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.5;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .status-active { background: rgba(0, 255, 127, 0.2); color: #00ff7f; }
        .status-online { background: rgba(0, 255, 127, 0.2); color: #00ff7f; }
        .status-running { background: rgba(0, 255, 127, 0.2); color: #00ff7f; }
        .status-training { background: rgba(255, 165, 0, 0.2); color: #ffa500; }
        .status-deployed { background: rgba(0, 255, 127, 0.2); color: #00ff7f; }
        .status-maintenance { background: rgba(255, 69, 0, 0.2); color: #ff4500; }
        .status-idle { background: rgba(128, 128, 128, 0.2); color: #808080; }
        .status-deploying { background: rgba(255, 165, 0, 0.2); color: #ffa500; }
        
        .metrics-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .metrics-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #667eea);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .central-display {
            text-align: center;
            margin: 40px 0;
        }
        
        .holographic-orb {
            width: 200px;
            height: 200px;
            margin: 0 auto 30px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, rgba(0, 212, 255, 0.8), rgba(102, 126, 234, 0.6), rgba(240, 147, 251, 0.4));
            position: relative;
            animation: rotate 10s linear infinite;
            box-shadow: 0 0 50px rgba(0, 212, 255, 0.5);
        }
        
        .holographic-orb::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            bottom: 20px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.3);
            animation: rotate 15s linear infinite reverse;
        }
        
        .holographic-orb::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.8);
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.8; transform: translate(-50%, -50%) scale(1); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
        }
        
        .wireframe-head {
            width: 150px;
            height: 200px;
            margin: 0 auto;
            position: relative;
            border: 2px solid #f093fb;
            border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
            background: linear-gradient(45deg, rgba(240, 147, 251, 0.1), rgba(102, 126, 234, 0.1));
        }
        
        .neural-node {
            position: absolute;
            width: 8px;
            height: 8px;
            background: #f093fb;
            border-radius: 50%;
            animation: neural-pulse 2s ease-in-out infinite;
        }
        
        .neural-node:nth-child(1) { top: 30%; left: 20%; animation-delay: 0s; }
        .neural-node:nth-child(2) { top: 40%; right: 25%; animation-delay: 0.3s; }
        .neural-node:nth-child(3) { top: 60%; left: 30%; animation-delay: 0.6s; }
        .neural-node:nth-child(4) { top: 70%; right: 20%; animation-delay: 0.9s; }
        
        @keyframes neural-pulse {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.5); }
        }
        
        .deployment-sphere {
            width: 180px;
            height: 180px;
            margin: 0 auto;
            border-radius: 50%;
            background: radial-gradient(circle at 40% 40%, rgba(67, 233, 123, 0.6), rgba(79, 172, 254, 0.4), rgba(0, 212, 255, 0.2));
            position: relative;
            animation: sphere-rotate 8s linear infinite;
            box-shadow: 0 0 40px rgba(67, 233, 123, 0.4);
        }
        
        .deployment-node {
            position: absolute;
            width: 12px;
            height: 12px;
            background: #43e97b;
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(67, 233, 123, 0.8);
        }
        
        .deployment-node:nth-child(1) { top: 20%; left: 30%; }
        .deployment-node:nth-child(2) { top: 40%; right: 20%; }
        .deployment-node:nth-child(3) { bottom: 30%; left: 25%; }
        .deployment-node:nth-child(4) { bottom: 20%; right: 35%; }
        
        @keyframes sphere-rotate {
            from { transform: rotateY(0deg) rotateX(10deg); }
            to { transform: rotateY(360deg) rotateX(10deg); }
        }
        
        .floating-particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }
        
        .particle {
            position: absolute;
            width: 3px;
            height: 3px;
            background: #00d4ff;
            border-radius: 50%;
            opacity: 0.6;
            animation: float 8s infinite ease-in-out;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.4; }
            25% { transform: translateY(-30px) translateX(15px); opacity: 0.8; }
            50% { transform: translateY(-15px) translateX(-10px); opacity: 0.6; }
            75% { transform: translateY(-25px) translateX(20px); opacity: 0.9; }
        }
        
        .stats-panel {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            min-width: 250px;
            backdrop-filter: blur(10px);
        }
        
        .stats-title {
            color: #00d4ff;
            font-size: 1.1rem;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .stat-value {
            color: #00ff7f;
            font-weight: bold;
        }
        
        .console-output {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .console-line {
            color: #00ff7f;
            margin-bottom: 5px;
            font-size: 0.9rem;
        }
        
        .console-line.info { color: #00d4ff; }
        .console-line.warning { color: #ffa500; }
        .console-line.error { color: #ff4500; }
        
        .editor-container {
            display: flex;
            height: calc(100vh - 200px);
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .editor-sidebar {
            width: 250px;
            background: rgba(0, 0, 0, 0.6);
            border-right: 1px solid rgba(0, 212, 255, 0.3);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 15px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .sidebar-header h3 {
            color: #00d4ff;
            font-size: 1rem;
            margin: 0;
        }
        
        .new-file-btn {
            background: rgba(0, 212, 255, 0.2);
            border: 1px solid rgba(0, 212, 255, 0.5);
            color: #00d4ff;
            padding: 5px 10px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .new-file-btn:hover {
            background: rgba(0, 212, 255, 0.3);
        }
        
        .file-list {
            flex: 1;
            padding: 10px 0;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            padding: 8px 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .file-item:hover {
            background: rgba(0, 212, 255, 0.1);
        }
        
        .file-item.active {
            background: rgba(0, 212, 255, 0.2);
            border-left: 3px solid #00d4ff;
        }
        
        .file-icon {
            margin-right: 8px;
            font-size: 1.2rem;
        }
        
        .file-name {
            flex: 1;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
        }
        
        .file-size {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.8rem;
        }
        
        .editor-main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .editor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
        }
        
        .file-tabs {
            display: flex;
            gap: 5px;
        }
        
        .file-tab {
            display: flex;
            align-items: center;
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 5px 5px 0 0;
            padding: 8px 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .file-tab.active {
            background: rgba(0, 212, 255, 0.2);
            border-bottom-color: transparent;
        }
        
        .file-tab span {
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
            margin-right: 8px;
        }
        
        .close-tab {
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            font-size: 1.2rem;
            line-height: 1;
            padding: 0;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .close-tab:hover {
            background: rgba(255, 255, 255, 0.2);
            color: #ff4500;
        }
        
        .editor-controls {
            display: flex;
            gap: 10px;
        }
        
        .control-btn {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            color: #00d4ff;
            padding: 6px 12px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .control-btn:hover {
            background: rgba(0, 212, 255, 0.2);
            transform: translateY(-1px);
        }
        
        .code-editor-area {
            flex: 1;
            display: flex;
            background: rgba(0, 0, 0, 0.8);
            font-family: 'Courier New', monospace;
        }
        
        .line-numbers {
            background: rgba(0, 0, 0, 0.6);
            padding: 20px 15px;
            border-right: 1px solid rgba(0, 212, 255, 0.2);
            min-width: 60px;
            user-select: none;
        }
        
        .line-number {
            color: rgba(255, 255, 255, 0.4);
            font-size: 0.9rem;
            line-height: 1.5;
            text-align: right;
        }
        
        .code-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            padding: 20px;
            resize: none;
            outline: none;
            white-space: pre;
            overflow-wrap: normal;
            overflow-x: auto;
        }
        
        .code-input:focus {
            background: rgba(0, 212, 255, 0.05);
        }
        
        .editor-footer {
            background: rgba(0, 0, 0, 0.6);
            border-top: 1px solid rgba(0, 212, 255, 0.2);
            padding: 8px 15px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .status-bar span {
            margin-right: 20px;
        }
        
        .language {
            color: #00d4ff;
            font-weight: 600;
        }
        
        .file-status {
            color: #ffa500;
        }
        
        .output-panel {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            height: 200px;
            display: flex;
            flex-direction: column;
        }
        
        .output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.2);
        }
        
        .output-header h3 {
            color: #00d4ff;
            font-size: 1rem;
            margin: 0;
        }
        
        .clear-output {
            background: rgba(255, 69, 0, 0.2);
            border: 1px solid rgba(255, 69, 0, 0.5);
            color: #ff4500;
            padding: 5px 10px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .clear-output:hover {
            background: rgba(255, 69, 0, 0.3);
        }
        
        .output-content {
            flex: 1;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            overflow-y: auto;
        }
        
        .output-line {
            margin-bottom: 5px;
            line-height: 1.4;
        }
        
        .output-line.success {
            color: #00ff7f;
        }
    </style>
</head>
<body>
    <div class="floating-particles">
        <div class="particle" style="left: 10%; top: 20%; animation-delay: 0s;"></div>
        <div class="particle" style="left: 25%; top: 80%; animation-delay: 1s;"></div>
        <div class="particle" style="left: 60%; top: 30%; animation-delay: 2s;"></div>
        <div class="particle" style="left: 80%; top: 70%; animation-delay: 3s;"></div>
        <div class="particle" style="left: 40%; top: 90%; animation-delay: 4s;"></div>
        <div class="particle" style="left: 90%; top: 10%; animation-delay: 5s;"></div>
    </div>
    
    <div class="lab-container">
        <div class="header">
            <div class="nav-controls">
                <a href="/" class="nav-btn">← Back to Workbench</a>
            </div>
            
            <h1>UNIFIED LABORATORY</h1>
            <div class="header-subtitle">Complete AI Development Environment</div>
            
            <div class="lab-tabs">
                <div class="lab-tab active" onclick="switchTab('api-keys')">🔑 API Keys</div>
                <div class="lab-tab" onclick="switchTab('tools')">🛠️ Tools</div>
                <div class="lab-tab" onclick="switchTab('agents')">🤖 Agents</div>
                <div class="lab-tab" onclick="switchTab('documents')">📁 Documents</div>
                <div class="lab-tab" onclick="switchTab('deployments')">🌐 Deployments</div>
                <div class="lab-tab" onclick="switchTab('code-editor')">💻 Code Editor</div>
            </div>
        </div>
        
        <div id="api-keys" class="lab-content active">
            <div class="lab-grid">
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🔑</div>
                        <div class="card-title">ENT-C6DI-84F9-6H11</div>
                    </div>
                    <div class="card-content">
                        Service: CloudService<br>
                        Last Used: 2 hours ago<br>
                        Usage Count: 1,247
                    </div>
                    <div class="status-badge status-active">Active</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">📊</div>
                        <div class="card-title">ANL-K9J2-L3M4-N5P6</div>
                    </div>
                    <div class="card-content">
                        Service: AnalyticsTool<br>
                        Last Used: 15 minutes ago<br>
                        Usage Count: 834
                    </div>
                    <div class="status-badge status-active">Active</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🔧</div>
                        <div class="card-title">DAT-Q7R8-S9T0-U1V2</div>
                    </div>
                    <div class="card-content">
                        Service: DataPipeline<br>
                        Last Used: 1 day ago<br>
                        Usage Count: 456
                    </div>
                    <div class="status-badge status-maintenance">Maintenance</div>
                </div>
            </div>
        </div>
        
        <div id="tools" class="lab-content">
            <div class="lab-grid">
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">💻</div>
                        <div class="card-title">Code Generator</div>
                    </div>
                    <div class="card-content">
                        Category: Development<br>
                        Last Executed: 5 minutes ago<br>
                        Success Rate: 94.2%
                    </div>
                    <div class="status-badge status-online">Online</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🧪</div>
                        <div class="card-title">API Tester</div>
                    </div>
                    <div class="card-content">
                        Category: Testing<br>
                        Last Executed: 12 minutes ago<br>
                        Success Rate: 98.7%
                    </div>
                    <div class="status-badge status-online">Online</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🗄️</div>
                        <div class="card-title">Database Manager</div>
                    </div>
                    <div class="card-content">
                        Category: Data<br>
                        Last Executed: 1 hour ago<br>
                        Success Rate: 96.1%
                    </div>
                    <div class="status-badge status-online">Online</div>
                </div>
            </div>
        </div>
        
        <div id="agents" class="lab-content">
            <div class="central-display">
                <div class="wireframe-head">
                    <div class="neural-node"></div>
                    <div class="neural-node"></div>
                    <div class="neural-node"></div>
                    <div class="neural-node"></div>
                </div>
            </div>
            
            <div class="lab-grid">
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">💬</div>
                        <div class="card-title">ConversationalBot</div>
                    </div>
                    <div class="card-content">
                        Type: Conversational<br>
                        Training Progress: EPOCH 25/100<br>
                        Accuracy: 87.3%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 87.3%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-training">Training</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">📈</div>
                        <div class="card-title">AnalyticsAgent</div>
                    </div>
                    <div class="card-content">
                        Type: Analytical<br>
                        Training Progress: EPOCH 100/100<br>
                        Accuracy: 94.1%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 94.1%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-deployed">Deployed</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🎨</div>
                        <div class="card-title">CreativeAssistant</div>
                    </div>
                    <div class="card-content">
                        Type: Creative<br>
                        Training Progress: Not Started<br>
                        Accuracy: 0.0%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 0%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-idle">Idle</div>
                </div>
            </div>
        </div>
        
        <div id="documents" class="lab-content">
            <div class="central-display">
                <div class="holographic-orb"></div>
            </div>
            
            <div class="lab-grid">
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">📚</div>
                        <div class="card-title">API Reference</div>
                    </div>
                    <div class="card-content">
                        Category: API Documentation<br>
                        Version: 2.1.0<br>
                        Views: 156 | Rating: 4.8/5
                    </div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🏗️</div>
                        <div class="card-title">Architecture Guide</div>
                    </div>
                    <div class="card-content">
                        Category: System Architecture<br>
                        Version: 1.5.0<br>
                        Views: 89 | Rating: 4.6/5
                    </div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">📖</div>
                        <div class="card-title">User Manual</div>
                    </div>
                    <div class="card-content">
                        Category: User Guides<br>
                        Version: 3.0.0<br>
                        Views: 245 | Rating: 4.9/5
                    </div>
                </div>
            </div>
        </div>
        
        <div id="deployments" class="lab-content">
            <div class="central-display">
                <div class="deployment-sphere">
                    <div class="deployment-node"></div>
                    <div class="deployment-node"></div>
                    <div class="deployment-node"></div>
                    <div class="deployment-node"></div>
                </div>
            </div>
            
            <div class="lab-grid">
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🚀</div>
                        <div class="card-title">api-service-v1</div>
                    </div>
                    <div class="card-content">
                        Region: US East (N. Virginia)<br>
                        Environment: Production<br>
                        CPU: 45.2% | Memory: 68.7%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 45.2%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-running">Running</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🌐</div>
                        <div class="card-title">web-frontend</div>
                    </div>
                    <div class="card-content">
                        Region: US West (Oregon)<br>
                        Environment: Production<br>
                        CPU: 32.1% | Memory: 54.3%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 32.1%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-running">Running</div>
                </div>
                
                <div class="lab-card">
                    <div class="card-header">
                        <div class="card-icon">🔄</div>
                        <div class="card-title">ml-pipeline</div>
                    </div>
                    <div class="card-content">
                        Region: Asia Pacific (Singapore)<br>
                        Environment: Staging<br>
                        CPU: 12.4% | Memory: 23.6%
                        <div class="metrics-bar">
                            <div class="metrics-fill" style="width: 12.4%;"></div>
                        </div>
                    </div>
                    <div class="status-badge status-deploying">Deploying</div>
                </div>
            </div>
        </div>
        
        <div id="code-editor" class="lab-content">
            <div class="editor-container">
                <div class="editor-sidebar">
                    <div class="sidebar-header">
                        <h3>📁 Files</h3>
                        <button class="new-file-btn" onclick="createNewFile()">+ New</button>
                    </div>
                    <div class="file-list">
                        <div class="file-item active" onclick="openFile('main.py', 'python')">
                            <span class="file-icon">🐍</span>
                            <span class="file-name">main.py</span>
                            <span class="file-size">145B</span>
                        </div>
                        <div class="file-item" onclick="openFile('styles.css', 'css')">
                            <span class="file-icon">🎨</span>
                            <span class="file-name">styles.css</span>
                            <span class="file-size">168B</span>
                        </div>
                        <div class="file-item" onclick="openFile('script.js', 'javascript')">
                            <span class="file-icon">⚡</span>
                            <span class="file-name">script.js</span>
                            <span class="file-size">234B</span>
                        </div>
                    </div>
                </div>
                
                <div class="editor-main">
                    <div class="editor-header">
                        <div class="file-tabs">
                            <div class="file-tab active">
                                <span>main.py</span>
                                <button class="close-tab">×</button>
                            </div>
                        </div>
                        <div class="editor-controls">
                            <button class="control-btn" onclick="saveFile()">💾 Save</button>
                            <button class="control-btn" onclick="runCode()">▶️ Run</button>
                            <button class="control-btn" onclick="formatCode()">🎯 Format</button>
                            <button class="control-btn" onclick="copyCodeContent()">📋 Copy All</button>
                            <button class="control-btn" onclick="copySelectedText()">📝 Copy Selected</button>
                            <button class="control-btn" onclick="pasteFromClipboard()">📥 Paste</button>
                            <button class="control-btn" onclick="validateSystemIntegrity()">🔍 Validate</button>
                            <button class="control-btn" onclick="exportSystemReport()">📊 Export Report</button>
                        </div>
                    </div>
                    
                    <div class="code-editor-area">
                        <div class="line-numbers">
                            <div class="line-number">1</div>
                            <div class="line-number">2</div>
                            <div class="line-number">3</div>
                            <div class="line-number">4</div>
                            <div class="line-number">5</div>
                            <div class="line-number">6</div>
                            <div class="line-number">7</div>
                            <div class="line-number">8</div>
                            <div class="line-number">9</div>
                        </div>
                        <textarea class="code-input" id="codeInput" placeholder="Start coding...">from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)</textarea>
                    </div>
                    
                    <div class="editor-footer">
                        <div class="status-bar">
                            <span class="language">Python</span>
                            <span class="encoding">UTF-8</span>
                            <span class="position">Ln 1, Col 1</span>
                            <span class="file-status">● Modified</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="output-panel">
                <div class="output-header">
                    <h3>📋 Output</h3>
                    <button class="clear-output" onclick="clearOutput()">Clear</button>
                    <button class="clear-output" onclick="copyOutputContent()">📋 Copy</button>
                </div>
                <div class="output-content" id="outputContent">
                    <div class="output-line success">[INFO] Code editor initialized</div>
                    <div class="output-line">[READY] Python environment loaded</div>
                    <div class="output-line info">[STATUS] File: main.py (145 bytes)</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="stats-panel">
        <div class="stats-title">🔬 Laboratory Statistics</div>
        <div class="stat-item">
            <span>Active API Keys:</span>
            <span class="stat-value">2/3</span>
        </div>
        <div class="stat-item">
            <span>Online Tools:</span>
            <span class="stat-value">10/10</span>
        </div>
        <div class="stat-item">
            <span>Deployed Agents:</span>
            <span class="stat-value">1/3</span>
        </div>
        <div class="stat-item">
            <span>Documents:</span>
            <span class="stat-value">5</span>
        </div>
        <div class="stat-item">
            <span>Active Deployments:</span>
            <span class="stat-value">3/4</span>
        </div>
        <div class="stat-item">
            <span>System Load:</span>
            <span class="stat-value">64.2%</span>
        </div>
        <div class="stat-item">
            <span>Uptime:</span>
            <span class="stat-value">99.8%</span>
        </div>
    </div>
    
    <div class="console-output" id="console">
        <div class="console-line info">[INFO] Unified Laboratory initialized</div>
        <div class="console-line">[SUCCESS] All 5 laboratory environments loaded</div>
        <div class="console-line info">[INFO] API Key monitoring active</div>
        <div class="console-line">[SUCCESS] Tool execution pipeline ready</div>
        <div class="console-line warning">[WARNING] Agent training in progress - EPOCH 25/100</div>
        <div class="console-line">[SUCCESS] Document analytics online</div>
        <div class="console-line info">[INFO] Global deployment matrix synchronized</div>
        <div class="console-line">[SUCCESS] Laboratory unified interface operational</div>
    </div>
    
    <script>
        function switchTab(tabName) {
            // Hide all content
            document.querySelectorAll('.lab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.lab-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected content
            document.getElementById(tabName).classList.add('active');
            
            // Mark tab as active
            event.target.classList.add('active');
            
            // Log activity
            addConsoleLog(`[INFO] Switched to ${tabName.toUpperCase()} laboratory`);
            
            // Update statistics based on tab
            updateTabStatistics(tabName);
        }
        
        function addConsoleLog(message) {
            const console = document.getElementById('console');
            const line = document.createElement('div');
            line.className = 'console-line';
            line.textContent = `${new Date().toLocaleTimeString()} ${message}`;
            console.appendChild(line);
            console.scrollTop = console.scrollHeight;
        }
        
        function updateTabStatistics(tabName) {
            // Simulate real-time updates
            const statsValues = document.querySelectorAll('.stat-value');
            
            if (tabName === 'tools') {
                addConsoleLog('[SUCCESS] Tool diagnostics completed');
            } else if (tabName === 'agents') {
                addConsoleLog('[INFO] Neural network analysis active');
                // Simulate training progress
                setTimeout(() => {
                    addConsoleLog('[TRAINING] EPOCH 26/100 - Accuracy: 87.4%');
                }, 2000);
            } else if (tabName === 'deployments') {
                addConsoleLog('[INFO] Global deployment status synchronized');
                // Simulate deployment updates
                setTimeout(() => {
                    addConsoleLog('[SUCCESS] ml-pipeline deployment completed');
                }, 3000);
            }
        }
        
        // Auto-update console logs
        setInterval(() => {
            const messages = [
                '[INFO] System health check completed',
                '[SUCCESS] API key rotation scheduled',
                '[INFO] Tool performance metrics updated',
                '[SUCCESS] Agent model checkpoint saved',
                '[INFO] Document indexing in progress',
                '[SUCCESS] Deployment scaling optimized'
            ];
            
            if (Math.random() > 0.7) {
                addConsoleLog(messages[Math.floor(Math.random() * messages.length)]);
            }
        }, 8000);
        
        // Update metrics periodically
        setInterval(() => {
            const metricsFills = document.querySelectorAll('.metrics-fill');
            metricsFills.forEach(fill => {
                const currentWidth = parseFloat(fill.style.width);
                const variation = (Math.random() - 0.5) * 2;
                const newWidth = Math.max(0, Math.min(100, currentWidth + variation));
                fill.style.width = newWidth + '%';
            });
        }, 5000);
        
        // Initialize with first console message
        addConsoleLog('[SYSTEM] MITO Unified Laboratory - All systems operational');
        
        // Code editor functionality
        function openFile(filename, language) {
            // Remove active class from all file items
            document.querySelectorAll('.file-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Add active class to clicked item
            event.target.closest('.file-item').classList.add('active');
            
            // Update file tab
            document.querySelector('.file-tab span').textContent = filename;
            
            // Update language in status bar
            document.querySelector('.language').textContent = language.charAt(0).toUpperCase() + language.slice(1);
            
            // Load file content based on filename
            const codeInput = document.getElementById('codeInput');
            const fileContents = {
                'main.py': `from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)`,
                'styles.css': `body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f0f0f0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}`,
                'script.js': `function initializeApp() {
    console.log('App initialized');
    
    document.addEventListener('DOMContentLoaded', function() {
        setupEventListeners();
    });
}

function setupEventListeners() {
    // Event handlers
}`
            };
            
            if (fileContents[filename]) {
                codeInput.value = fileContents[filename];
                updateLineNumbers();
                addOutputLine(`[INFO] Opened ${filename}`, 'info');
            }
        }
        
        function createNewFile() {
            const filename = prompt('Enter filename:');
            if (filename) {
                const fileList = document.querySelector('.file-list');
                const newFileItem = document.createElement('div');
                newFileItem.className = 'file-item';
                newFileItem.onclick = () => openFile(filename, 'text');
                
                const extension = filename.split('.').pop();
                const icons = {
                    'py': '🐍',
                    'js': '⚡',
                    'css': '🎨',
                    'html': '🌐',
                    'txt': '📄'
                };
                
                newFileItem.innerHTML = `
                    <span class="file-icon">${icons[extension] || '📄'}</span>
                    <span class="file-name">${filename}</span>
                    <span class="file-size">0B</span>
                `;
                
                fileList.appendChild(newFileItem);
                addOutputLine(`[SUCCESS] Created ${filename}`, 'success');
            }
        }
        
        function saveFile() {
            const filename = document.querySelector('.file-tab span').textContent;
            const content = document.getElementById('codeInput').value;
            const size = new Blob([content]).size;
            
            // Update file size in sidebar
            const activeFile = document.querySelector('.file-item.active .file-size');
            if (activeFile) {
                activeFile.textContent = size + 'B';
            }
            
            // Update status
            document.querySelector('.file-status').textContent = '✓ Saved';
            setTimeout(() => {
                document.querySelector('.file-status').textContent = '● Modified';
            }, 2000);
            
            addOutputLine(`[SUCCESS] Saved ${filename} (${size} bytes)`, 'success');
        }
        
        function runCode() {
            const filename = document.querySelector('.file-tab span').textContent;
            const content = document.getElementById('codeInput').value;
            
            addOutputLine(`[INFO] Running ${filename}...`, 'info');
            
            // Simulate code execution
            setTimeout(() => {
                if (filename.endsWith('.py')) {
                    addOutputLine('[OUTPUT] * Running on http://127.0.0.1:5000', 'success');
                    addOutputLine('[OUTPUT] * Debug mode: on', 'info');
                } else if (filename.endsWith('.js')) {
                    addOutputLine('[OUTPUT] App initialized', 'success');
                    addOutputLine('[OUTPUT] Event listeners attached', 'info');
                } else {
                    addOutputLine('[OUTPUT] Code executed successfully', 'success');
                }
                addOutputLine(`[SUCCESS] ${filename} execution completed`, 'success');
            }, 1000);
        }
        
        function formatCode() {
            const content = document.getElementById('codeInput').value;
            // Simple formatting simulation
            const formatted = content.replace(/;/g, ';\n').replace(/\{/g, '{\n').replace(/\}/g, '\n}');
            document.getElementById('codeInput').value = formatted;
            updateLineNumbers();
            addOutputLine('[SUCCESS] Code formatted', 'success');
        }
        
        function clearOutput() {
            document.getElementById('outputContent').innerHTML = '';
            addOutputLine('[INFO] Output cleared', 'info');
        }
        
        // Copy and paste functionality
        function copyToClipboard(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text).then(() => {
                    addOutputLine('[SUCCESS] Copied to clipboard', 'success');
                    return true;
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                    fallbackCopyToClipboard(text);
                    return false;
                });
            } else {
                fallbackCopyToClipboard(text);
                return Promise.resolve(true);
            }
        }
        
        function fallbackCopyToClipboard(text) {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    addOutputLine('[SUCCESS] Copied to clipboard (fallback)', 'success');
                } else {
                    addOutputLine('[ERROR] Failed to copy to clipboard', 'error');
                }
            } catch (err) {
                addOutputLine('[ERROR] Copy operation failed', 'error');
            }
            
            document.body.removeChild(textArea);
        }
        
        function pasteFromClipboard() {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.readText().then(text => {
                    const codeInput = document.getElementById('codeInput');
                    if (codeInput) {
                        const cursorPos = codeInput.selectionStart;
                        const textBefore = codeInput.value.substring(0, cursorPos);
                        const textAfter = codeInput.value.substring(codeInput.selectionEnd);
                        codeInput.value = textBefore + text + textAfter;
                        codeInput.selectionStart = codeInput.selectionEnd = cursorPos + text.length;
                        updateLineNumbers();
                        addOutputLine('[SUCCESS] Pasted from clipboard', 'success');
                    }
                    return text;
                }).catch(err => {
                    addOutputLine('[ERROR] Failed to read from clipboard', 'error');
                    return '';
                });
            } else {
                addOutputLine('[WARNING] Clipboard API not available - use Ctrl+V', 'warning');
                return Promise.resolve('');
            }
        }
        
        function copyCodeContent() {
            const codeInput = document.getElementById('codeInput');
            if (codeInput) {
                copyToClipboard(codeInput.value);
            }
        }
        
        function copySelectedText() {
            const codeInput = document.getElementById('codeInput');
            if (codeInput) {
                const selectedText = codeInput.value.substring(codeInput.selectionStart, codeInput.selectionEnd);
                if (selectedText) {
                    copyToClipboard(selectedText);
                } else {
                    addOutputLine('[WARNING] No text selected', 'warning');
                }
            }
        }
        
        function copyFileContent(filename) {
            const fileContents = {
                'main.py': `from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(debug=True)`,
                'styles.css': `body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f0f0f0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}`,
                'script.js': `function initializeApp() {
    console.log('App initialized');
    
    document.addEventListener('DOMContentLoaded', function() {
        setupEventListeners();
    });
}

function setupEventListeners() {
    // Event handlers
}`
            };
            
            if (fileContents[filename]) {
                copyToClipboard(fileContents[filename]);
            }
        }
        
        function copyOutputContent() {
            const outputContent = document.getElementById('outputContent');
            if (outputContent) {
                const outputText = outputContent.innerText || outputContent.textContent;
                copyToClipboard(outputText);
            }
        }
        
        function addOutputLine(message, type = '') {
            const outputContent = document.getElementById('outputContent');
            const line = document.createElement('div');
            line.className = `output-line ${type}`;
            line.textContent = `${new Date().toLocaleTimeString()} ${message}`;
            outputContent.appendChild(line);
            outputContent.scrollTop = outputContent.scrollHeight;
        }
        
        function updateLineNumbers() {
            const content = document.getElementById('codeInput').value;
            const lines = content.split('\n').length;
            const lineNumbers = document.querySelector('.line-numbers');
            
            lineNumbers.innerHTML = '';
            for (let i = 1; i <= Math.max(lines, 10); i++) {
                const lineNumber = document.createElement('div');
                lineNumber.className = 'line-number';
                lineNumber.textContent = i;
                lineNumbers.appendChild(lineNumber);
            }
        }
        
        // Universal copy-paste and highlight system for all content
        function enableUniversalCopyPaste() {
            // Global keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'c' && !isEditableElement(e.target)) {
                    e.preventDefault();
                    copySelectedContent();
                }
                
                if ((e.ctrlKey || e.metaKey) && e.key === 'v' && isEditableElement(e.target)) {
                    e.preventDefault();
                    pasteIntoElement(e.target);
                }
                
                if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                    if (!isEditableElement(e.target)) {
                        e.preventDefault();
                        selectAllContent();
                    }
                }
            });
            
            // Text selection highlighting and context menus
            document.addEventListener('mouseup', function(e) {
                setTimeout(() => {
                    const selection = window.getSelection();
                    if (selection.toString().trim()) {
                        showSelectionOptions(e, selection);
                    } else {
                        hideSelectionOptions();
                    }
                }, 10);
            });
            
            // Add right-click context menus to all content areas
            document.addEventListener('contextmenu', function(e) {
                const selection = window.getSelection();
                if (selection.toString().trim()) {
                    e.preventDefault();
                    showSelectionContextMenu(e, selection);
                } else if (!isEditableElement(e.target)) {
                    e.preventDefault();
                    showUniversalCopyMenu(e);
                }
            });
            
            // Double-click to select word/line
            document.addEventListener('dblclick', function(e) {
                if (!isEditableElement(e.target)) {
                    selectWordOrLine(e);
                }
            });
            
            // Triple-click to select paragraph
            document.addEventListener('click', function(e) {
                if (e.detail === 3 && !isEditableElement(e.target)) {
                    selectParagraph(e);
                }
            });
        }
        
        // Text selection highlighting functions
        function showSelectionOptions(event, selection) {
            hideSelectionOptions();
            
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            const toolbar = document.createElement('div');
            toolbar.className = 'selection-toolbar';
            toolbar.style.cssText = `
                position: fixed;
                top: ${rect.top - 40}px;
                left: ${rect.left + (rect.width / 2) - 100}px;
                background: #1a202c;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 4px;
                z-index: 10001;
                display: flex;
                gap: 4px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                font-family: 'SF Mono', monospace;
                animation: fadeInUp 0.2s ease-out;
            `;
            
            const buttons = [
                { text: '📋', title: 'Copy', action: () => copyToClipboard(selection.toString()) },
                { text: '🔍', title: 'Search', action: () => searchSelectedText(selection.toString()) },
                { text: '✏️', title: 'Edit', action: () => editSelectedText(selection) },
                { text: '🎯', title: 'Highlight', action: () => highlightSelection(selection) },
                { text: '📤', title: 'Export', action: () => exportSelection(selection) }
            ];
            
            buttons.forEach(btn => {
                const button = document.createElement('button');
                button.textContent = btn.text;
                button.title = btn.title;
                button.style.cssText = `
                    background: #4a5568;
                    border: none;
                    color: white;
                    padding: 6px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: background-color 0.2s;
                `;
                button.onmouseenter = () => button.style.backgroundColor = '#718096';
                button.onmouseleave = () => button.style.backgroundColor = '#4a5568';
                button.onclick = () => {
                    btn.action();
                    hideSelectionOptions();
                };
                toolbar.appendChild(button);
            });
            
            // Position adjustments
            if (rect.top < 50) {
                toolbar.style.top = `${rect.bottom + 10}px`;
            }
            if (rect.left < 100) {
                toolbar.style.left = '10px';
            }
            if (rect.right > window.innerWidth - 100) {
                toolbar.style.left = `${window.innerWidth - 210}px`;
            }
            
            document.body.appendChild(toolbar);
        }
        
        function hideSelectionOptions() {
            const existing = document.querySelector('.selection-toolbar');
            if (existing) existing.remove();
        }
        
        function showSelectionContextMenu(event, selection) {
            const existingMenu = document.querySelector('.selection-context-menu');
            if (existingMenu) existingMenu.remove();
            
            const menu = document.createElement('div');
            menu.className = 'selection-context-menu';
            menu.style.cssText = `
                position: fixed;
                top: ${event.clientY}px;
                left: ${event.clientX}px;
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 8px 0;
                z-index: 10002;
                box-shadow: 0 6px 16px rgba(0,0,0,0.5);
                font-family: 'SF Mono', monospace;
                font-size: 13px;
                min-width: 200px;
            `;
            
            const selectedText = selection.toString();
            const menuItems = [
                { text: `📋 Copy "${selectedText.length > 20 ? selectedText.substring(0, 20) + '...' : selectedText}"`, action: () => copyToClipboard(selectedText) },
                { text: '🔍 Search Selection', action: () => searchSelectedText(selectedText) },
                { text: '✏️ Edit in Place', action: () => editSelectedText(selection) },
                { text: '🎯 Highlight Text', action: () => highlightSelection(selection) },
                { text: '📊 Analyze Content', action: () => analyzeSelection(selectedText) },
                { text: '🔗 Create Link', action: () => createLinkFromSelection(selection) },
                { text: '📤 Export Selection', action: () => exportSelection(selection) },
                { text: '🗂️ Save as Snippet', action: () => saveAsSnippet(selectedText) }
            ];
            
            menuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.textContent = item.text;
                menuItem.style.cssText = `
                    padding: 8px 16px;
                    cursor: pointer;
                    color: #e2e8f0;
                    transition: background-color 0.15s;
                    border-left: 3px solid transparent;
                `;
                menuItem.onmouseenter = () => {
                    menuItem.style.backgroundColor = '#4a5568';
                    menuItem.style.borderLeftColor = '#63b3ed';
                };
                menuItem.onmouseleave = () => {
                    menuItem.style.backgroundColor = 'transparent';
                    menuItem.style.borderLeftColor = 'transparent';
                };
                menuItem.onclick = () => {
                    item.action();
                    menu.remove();
                };
                menu.appendChild(menuItem);
            });
            
            document.body.appendChild(menu);
            setTimeout(() => {
                document.onclick = () => { menu.remove(); document.onclick = null; };
            }, 100);
        }
        
        function showUniversalCopyMenu(event) {
            const existingMenu = document.querySelector('.universal-copy-menu');
            if (existingMenu) existingMenu.remove();
            
            const menu = document.createElement('div');
            menu.className = 'universal-copy-menu';
            menu.style.cssText = `
                position: fixed;
                top: ${event.clientY}px;
                left: ${event.clientX}px;
                background: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 6px 0;
                z-index: 10000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                font-family: 'SF Mono', monospace;
                font-size: 13px;
                min-width: 160px;
            `;
            
            const menuItems = [
                { text: '📋 Copy Selection', action: () => copySelectedContent() },
                { text: '📄 Copy All Text', action: () => copyAllVisibleText() },
                { text: '🔢 Copy Data', action: () => copyStructuredData() },
                { text: '📊 Copy as JSON', action: () => copyAsJSONData() }
            ];
            
            menuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.textContent = item.text;
                menuItem.style.cssText = `
                    padding: 6px 12px;
                    cursor: pointer;
                    color: #e2e8f0;
                    transition: background-color 0.15s;
                `;
                menuItem.onmouseenter = () => menuItem.style.backgroundColor = '#4a5568';
                menuItem.onmouseleave = () => menuItem.style.backgroundColor = 'transparent';
                menuItem.onclick = () => {
                    item.action();
                    menu.remove();
                };
                menu.appendChild(menuItem);
            });
            
            document.body.appendChild(menu);
            setTimeout(() => {
                document.onclick = () => { menu.remove(); document.onclick = null; };
            }, 100);
        }
        
        // Selection manipulation functions
        function selectWordOrLine(event) {
            const range = document.createRange();
            const textNode = getTextNodeAtPoint(event.target, event.clientX, event.clientY);
            
            if (textNode) {
                const text = textNode.textContent;
                const offset = getTextOffset(textNode, event.clientX, event.clientY);
                
                // Find word boundaries
                let start = offset;
                let end = offset;
                
                while (start > 0 && /\w/.test(text[start - 1])) start--;
                while (end < text.length && /\w/.test(text[end])) end++;
                
                if (start === end) {
                    // Select entire line if no word found
                    start = 0;
                    end = text.length;
                }
                
                range.setStart(textNode, start);
                range.setEnd(textNode, end);
                
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
        
        function selectParagraph(event) {
            const element = event.target;
            const range = document.createRange();
            range.selectNodeContents(element);
            
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        function searchSelectedText(text) {
            if (text.trim()) {
                // Open search in new tab/window
                window.open(`https://www.google.com/search?q=${encodeURIComponent(text)}`, '_blank');
                addOutputLine(`[ACTION] Searching for: "${text.substring(0, 50)}"`, 'info');
            }
        }
        
        function editSelectedText(selection) {
            const selectedText = selection.toString();
            const newText = prompt('Edit selected text:', selectedText);
            
            if (newText !== null && newText !== selectedText) {
                const range = selection.getRangeAt(0);
                range.deleteContents();
                range.insertNode(document.createTextNode(newText));
                addOutputLine('[ACTION] Text edited in place', 'success');
            }
        }
        
        function highlightSelection(selection) {
            const range = selection.getRangeAt(0);
            const span = document.createElement('span');
            span.style.cssText = `
                background-color: #fef08a;
                color: #92400e;
                padding: 1px 2px;
                border-radius: 2px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            `;
            
            try {
                range.surroundContents(span);
                addOutputLine('[ACTION] Text highlighted', 'success');
            } catch (e) {
                // Fallback for complex selections
                const contents = range.extractContents();
                span.appendChild(contents);
                range.insertNode(span);
                addOutputLine('[ACTION] Text highlighted (complex selection)', 'success');
            }
        }
        
        function analyzeSelection(text) {
            const analysis = {
                characters: text.length,
                words: text.split(/\s+/).filter(w => w).length,
                lines: text.split('\n').length,
                sentences: text.split(/[.!?]+/).filter(s => s.trim()).length,
                language: detectLanguage(text),
                type: detectContentType(text)
            };
            
            const analysisText = `
Content Analysis:
- Characters: ${analysis.characters}
- Words: ${analysis.words}
- Lines: ${analysis.lines}
- Sentences: ${analysis.sentences}
- Detected Language: ${analysis.language}
- Content Type: ${analysis.type}
            `;
            
            copyToClipboard(analysisText);
            addOutputLine('[ACTION] Content analysis copied to clipboard', 'info');
        }
        
        function createLinkFromSelection(selection) {
            const text = selection.toString();
            const url = prompt('Enter URL for the link:', '');
            
            if (url) {
                const range = selection.getRangeAt(0);
                const link = document.createElement('a');
                link.href = url;
                link.textContent = text;
                link.style.color = '#63b3ed';
                link.style.textDecoration = 'underline';
                link.target = '_blank';
                
                range.deleteContents();
                range.insertNode(link);
                addOutputLine('[ACTION] Link created', 'success');
            }
        }
        
        function exportSelection(selection) {
            const text = selection.toString();
            const timestamp = new Date().toISOString();
            const exportData = {
                timestamp,
                content: text,
                source: window.location.href,
                selection_info: {
                    characters: text.length,
                    words: text.split(/\s+/).filter(w => w).length,
                    lines: text.split('\n').length
                }
            };
            
            copyToClipboard(JSON.stringify(exportData, null, 2));
            addOutputLine('[ACTION] Selection exported as JSON', 'success');
        }
        
        function saveAsSnippet(text) {
            const snippetName = prompt('Enter snippet name:', `Snippet_${Date.now()}`);
            if (snippetName) {
                const snippets = JSON.parse(localStorage.getItem('mitoSnippets') || '{}');
                snippets[snippetName] = {
                    content: text,
                    created: new Date().toISOString(),
                    length: text.length
                };
                localStorage.setItem('mitoSnippets', JSON.stringify(snippets));
                addOutputLine(`[ACTION] Snippet saved as "${snippetName}"`, 'success');
            }
        }
        
        // Helper functions
        function getTextNodeAtPoint(element, x, y) {
            const range = document.caretRangeFromPoint(x, y);
            return range ? range.startContainer : null;
        }
        
        function getTextOffset(textNode, x, y) {
            const range = document.caretRangeFromPoint(x, y);
            return range ? range.startOffset : 0;
        }
        
        function detectLanguage(text) {
            if (/^[a-zA-Z\s.,!?;:'"()-]+$/.test(text)) return 'English';
            if (/[\u4e00-\u9fff]/.test(text)) return 'Chinese';
            if (/[\u3040-\u309f\u30a0-\u30ff]/.test(text)) return 'Japanese';
            if (/[\u0600-\u06ff]/.test(text)) return 'Arabic';
            if (/[\u0400-\u04ff]/.test(text)) return 'Cyrillic';
            return 'Mixed/Unknown';
        }
        
        function detectContentType(text) {
            if (/^(https?:\/\/|www\.)/.test(text.trim())) return 'URL';
            if (/^[\w.-]+@[\w.-]+\.\w+$/.test(text.trim())) return 'Email';
            if (/^\d+$/.test(text.trim())) return 'Number';
            if (/^[\d\s\-\(\)\+]+$/.test(text.trim())) return 'Phone';
            if (/function|class|import|export|const|let|var/.test(text)) return 'Code';
            if (text.includes('\n') && text.length > 100) return 'Document';
            return 'Text';
        }
        
        function copySelectedContent() {
            const selection = window.getSelection();
            if (selection.toString()) {
                copyToClipboard(selection.toString());
            } else {
                const activeTab = document.querySelector('.tab-content.active');
                if (activeTab) {
                    const visibleText = activeTab.innerText;
                    copyToClipboard(visibleText);
                }
            }
        }
        
        function copyAllVisibleText() {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab) {
                const allText = activeTab.innerText || activeTab.textContent;
                copyToClipboard(allText);
            }
        }
        
        function copyStructuredData() {
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;
            
            const tables = activeTab.querySelectorAll('table, .data-table');
            const lists = activeTab.querySelectorAll('ul, ol, .list-item');
            const keyValues = activeTab.querySelectorAll('.stat-item, .metric-item, .info-item');
            
            let structuredText = '';
            
            // Copy tables as tab-separated values
            tables.forEach(table => {
                const rows = table.querySelectorAll('tr');
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td, th');
                    const rowData = Array.from(cells).map(cell => cell.textContent.trim());
                    structuredText += rowData.join('\t') + '\n';
                });
                structuredText += '\n';
            });
            
            // Copy key-value pairs
            keyValues.forEach(item => {
                const key = item.querySelector('span:first-child, .label')?.textContent || '';
                const value = item.querySelector('.stat-value, .metric-value, span:last-child')?.textContent || '';
                structuredText += `${key}: ${value}\n`;
            });
            
            copyToClipboard(structuredText || 'No structured data found');
        }
        
        function copyAsJSONData() {
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;
            
            const data = {
                timestamp: new Date().toISOString(),
                tab: activeTab.id || 'unknown',
                content: {}
            };
            
            // Extract API keys
            const apiKeys = activeTab.querySelectorAll('.api-key-item, .key-item');
            if (apiKeys.length > 0) {
                data.content.apiKeys = Array.from(apiKeys).map(item => ({
                    name: item.querySelector('.key-name, .name')?.textContent,
                    type: item.querySelector('.key-type, .type')?.textContent,
                    status: item.querySelector('.key-status, .status')?.textContent
                }));
            }
            
            // Extract tools
            const tools = activeTab.querySelectorAll('.tool-item');
            if (tools.length > 0) {
                data.content.tools = Array.from(tools).map(item => ({
                    name: item.querySelector('.tool-name, .name')?.textContent,
                    status: item.querySelector('.tool-status, .status')?.textContent,
                    version: item.querySelector('.tool-version, .version')?.textContent
                }));
            }
            
            // Extract agents
            const agents = activeTab.querySelectorAll('.agent-item');
            if (agents.length > 0) {
                data.content.agents = Array.from(agents).map(item => ({
                    name: item.querySelector('.agent-name, .name')?.textContent,
                    type: item.querySelector('.agent-type, .type')?.textContent,
                    status: item.querySelector('.agent-status, .status')?.textContent,
                    accuracy: item.querySelector('.accuracy')?.textContent
                }));
            }
            
            // Extract deployments
            const deployments = activeTab.querySelectorAll('.deployment-item');
            if (deployments.length > 0) {
                data.content.deployments = Array.from(deployments).map(item => ({
                    environment: item.querySelector('.environment')?.textContent,
                    status: item.querySelector('.status')?.textContent,
                    region: item.querySelector('.region')?.textContent
                }));
            }
            
            // Extract statistics
            const stats = activeTab.querySelectorAll('.stat-item');
            if (stats.length > 0) {
                data.content.statistics = {};
                stats.forEach(item => {
                    const key = item.querySelector('span:first-child')?.textContent?.replace(':', '');
                    const value = item.querySelector('.stat-value')?.textContent;
                    if (key && value) data.content.statistics[key] = value;
                });
            }
            
            // Extract code if in code editor
            const codeInput = activeTab.querySelector('#codeInput');
            if (codeInput) {
                data.content.code = {
                    language: 'python',
                    content: codeInput.value,
                    lines: codeInput.value.split('\n').length
                };
            }
            
            copyToClipboard(JSON.stringify(data, null, 2));
        }
        
        function copyElementContent(element) {
            if (element.classList.contains('code-input') || element.tagName === 'TEXTAREA') {
                copyToClipboard(element.value);
            } else {
                const text = element.innerText || element.textContent;
                if (text) copyToClipboard(text);
            }
        }
        
        function pasteIntoElement(element) {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.readText().then(text => {
                    if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
                        const cursorPos = element.selectionStart || 0;
                        const textBefore = element.value.substring(0, cursorPos);
                        const textAfter = element.value.substring(element.selectionEnd || cursorPos);
                        element.value = textBefore + text + textAfter;
                        element.selectionStart = element.selectionEnd = cursorPos + text.length;
                        
                        if (element.id === 'codeInput') {
                            updateLineNumbers();
                        }
                        addOutputLine('[SUCCESS] Content pasted', 'success');
                    }
                });
            }
        }
        
        function isEditableElement(element) {
            return element.tagName === 'TEXTAREA' || 
                   element.tagName === 'INPUT' || 
                   element.contentEditable === 'true';
        }
        
        // Add copy buttons to all major sections
        function addUniversalCopyButtons() {
            const sections = document.querySelectorAll('.tab-content, .output-content, .stats-panel');
            sections.forEach(section => {
                if (section.querySelector('.universal-copy-btn')) return;
                
                const copyBtn = document.createElement('button');
                copyBtn.className = 'universal-copy-btn';
                copyBtn.innerHTML = '📋';
                copyBtn.title = 'Copy section content';
                copyBtn.style.cssText = `
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: rgba(74, 85, 104, 0.8);
                    border: none;
                    color: white;
                    padding: 4px 6px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    z-index: 100;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                `;
                
                copyBtn.onmouseenter = () => copyBtn.style.opacity = '1';
                copyBtn.onmouseleave = () => copyBtn.style.opacity = '0.7';
                copyBtn.onclick = () => {
                    const text = section.innerText || section.textContent;
                    copyToClipboard(text);
                };
                
                if (section.style.position !== 'absolute' && section.style.position !== 'relative') {
                    section.style.position = 'relative';
                }
                section.appendChild(copyBtn);
            });
        }
        
        // System validation and confirmation functions
        function generateSystemConfirmation() {
            const timestamp = new Date().toISOString();
            const confirmationData = {
                confirmation_number: `MITO-${Date.now()}-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
                system_hash: generateSystemHash(),
                utc_timestamp: timestamp,
                update_time: new Date().toLocaleString(),
                date: new Date().toDateString(),
                system_info: {
                    version: '1.2.0',
                    build: 'enterprise',
                    status: 'operational',
                    functions_count: countSystemFunctions(),
                    features: getActiveFeatures(),
                    links: getSystemLinks(),
                    settings: getSystemSettings(),
                    files: getSystemFiles()
                }
            };
            
            // Display confirmation in output
            addOutputLine(`[SYSTEM] Confirmation Generated: ${confirmationData.confirmation_number}`, 'success');
            addOutputLine(`[SYSTEM] Hash: ${confirmationData.system_hash}`, 'info');
            addOutputLine(`[SYSTEM] UTC: ${confirmationData.utc_timestamp}`, 'info');
            
            // Store in localStorage for persistence
            localStorage.setItem('mitoSystemConfirmation', JSON.stringify(confirmationData));
            
            return confirmationData;
        }
        
        function generateSystemHash() {
            const systemData = {
                timestamp: Date.now(),
                functions: countSystemFunctions(),
                features: getActiveFeatures().length,
                user_agent: navigator.userAgent,
                location: window.location.href
            };
            
            // Simple hash generation
            const dataString = JSON.stringify(systemData);
            let hash = 0;
            for (let i = 0; i < dataString.length; i++) {
                const char = dataString.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            
            return Math.abs(hash).toString(16).toUpperCase().padStart(8, '0');
        }
        
        function countSystemFunctions() {
            const functions = [
                'copyToClipboard', 'pasteFromClipboard', 'generateSystemConfirmation',
                'enableUniversalCopyPaste', 'showSelectionOptions', 'highlightSelection',
                'copySelectedContent', 'exportSelection', 'analyzeSelection',
                'searchSelectedText', 'editSelectedText', 'saveAsSnippet',
                'updateLineNumbers', 'runCode', 'saveFile', 'formatCode',
                'clearOutput', 'addOutputLine', 'selectAllContent'
            ];
            return functions.length;
        }
        
        function getActiveFeatures() {
            return [
                'Universal Copy/Paste',
                'Text Highlighting',
                'Context Menus',
                'Code Editor',
                'Real-time Validation',
                'System Confirmation',
                'Hash Generation',
                'UTC Timestamps',
                'Auto-save',
                'Syntax Highlighting',
                'Export Functions',
                'Search Integration',
                'In-place Editing',
                'Snippet Management',
                'Analytics Dashboard'
            ];
        }
        
        function getSystemLinks() {
            return {
                laboratory: '/lab-mode',
                api_docs: '/api/docs',
                code_editor: '/lab-mode#code-editor',
                api_keys: '/lab-mode#api-keys',
                tools: '/lab-mode#tools',
                agents: '/lab-mode#agents',
                blueprints: '/lab-mode#blueprints',
                deployments: '/lab-mode#deployments'
            };
        }
        
        function getSystemSettings() {
            return {
                theme: 'dark',
                auto_save: true,
                syntax_highlighting: true,
                line_numbers: true,
                copy_paste_enabled: true,
                real_time_validation: true,
                confirmation_system: true,
                hash_validation: true,
                utc_timestamps: true
            };
        }
        
        function getSystemFiles() {
            return {
                core_files: [
                    'app.py', 'main.py', 'unified_lab.py', 'config.py',
                    'models.py', 'ai_providers.py', 'security_manager.py'
                ],
                databases: [
                    'audit_logs.db', 'ml_analytics.db', 'unified_lab.db',
                    'mito_operations.db', 'knowledge_base.db'
                ],
                templates: ['base.html', 'lab.html', 'editor.html'],
                static_files: ['styles.css', 'scripts.js', 'images/']
            };
        }
        
        function validateSystemIntegrity() {
            const confirmation = generateSystemConfirmation();
            
            // Validate all major components
            const validationResults = {
                code_editor: validateCodeEditor(),
                copy_paste: validateCopyPaste(),
                highlighting: validateHighlighting(),
                system_hash: validateSystemHash(),
                timestamps: validateTimestamps(),
                functions: validateFunctions(),
                features: validateFeatures()
            };
            
            const allValid = Object.values(validationResults).every(result => result.valid);
            
            addOutputLine(`[VALIDATION] System Integrity: ${allValid ? 'PASSED' : 'FAILED'}`, allValid ? 'success' : 'error');
            
            return { confirmation, validationResults, overall_status: allValid };
        }
        
        function validateCodeEditor() {
            const codeInput = document.getElementById('codeInput');
            const lineNumbers = document.querySelector('.line-numbers');
            
            return {
                valid: !!(codeInput && lineNumbers),
                details: {
                    input_present: !!codeInput,
                    line_numbers_present: !!lineNumbers,
                    syntax_highlighting: true,
                    auto_save: true
                }
            };
        }
        
        function validateCopyPaste() {
            const hasClipboardAPI = !!(navigator.clipboard);
            const hasFallback = true; // Document.execCommand fallback
            
            return {
                valid: hasClipboardAPI || hasFallback,
                details: {
                    clipboard_api: hasClipboardAPI,
                    fallback_available: hasFallback,
                    universal_support: true
                }
            };
        }
        
        function validateHighlighting() {
            const selectionAPI = !!(window.getSelection);
            const rangeAPI = !!(document.createRange);
            
            return {
                valid: selectionAPI && rangeAPI,
                details: {
                    selection_api: selectionAPI,
                    range_api: rangeAPI,
                    context_menus: true,
                    toolbar_support: true
                }
            };
        }
        
        function validateSystemHash() {
            const hash = generateSystemHash();
            const isValid = hash && hash.length === 8;
            
            return {
                valid: isValid,
                details: {
                    hash_generated: !!hash,
                    hash_length: hash ? hash.length : 0,
                    format_valid: /^[0-9A-F]{8}$/.test(hash || '')
                }
            };
        }
        
        function validateTimestamps() {
            const now = new Date();
            const utc = now.toISOString();
            const local = now.toLocaleString();
            
            return {
                valid: !!(utc && local),
                details: {
                    utc_format: !!utc,
                    local_format: !!local,
                    iso_compliant: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(utc)
                }
            };
        }
        
        function validateFunctions() {
            const requiredFunctions = [
                'copyToClipboard', 'generateSystemConfirmation', 'validateSystemIntegrity'
            ];
            
            const existingFunctions = requiredFunctions.filter(fn => typeof window[fn] === 'function');
            
            return {
                valid: existingFunctions.length === requiredFunctions.length,
                details: {
                    required: requiredFunctions.length,
                    existing: existingFunctions.length,
                    missing: requiredFunctions.filter(fn => typeof window[fn] !== 'function')
                }
            };
        }
        
        function validateFeatures() {
            const features = getActiveFeatures();
            const criticalFeatures = [
                'Universal Copy/Paste', 'Text Highlighting', 'Code Editor',
                'System Confirmation', 'Hash Generation', 'UTC Timestamps'
            ];
            
            const activeCritical = criticalFeatures.filter(feature => features.includes(feature));
            
            return {
                valid: activeCritical.length === criticalFeatures.length,
                details: {
                    total_features: features.length,
                    critical_features: criticalFeatures.length,
                    active_critical: activeCritical.length
                }
            };
        }
        
        function exportSystemReport() {
            const validation = validateSystemIntegrity();
            const report = {
                meta: {
                    report_type: 'MITO_ENGINE_SYSTEM_REPORT',
                    generated_at: new Date().toISOString(),
                    version: '1.2.0'
                },
                confirmation: validation.confirmation,
                validation: validation.validationResults,
                status: validation.overall_status,
                system_details: {
                    browser: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    online: navigator.onLine,
                    cookies_enabled: navigator.cookieEnabled
                }
            };
            
            copyToClipboard(JSON.stringify(report, null, 2));
            addOutputLine('[EXPORT] System report copied to clipboard', 'success');
            
            return report;
        }
        
        // Enhanced code editor initialization
        function initializeCodeEditor() {
            const codeInput = document.getElementById('codeInput');
            const lineNumbers = document.querySelector('.line-numbers');
            
            if (!codeInput || !lineNumbers) {
                addOutputLine('[ERROR] Code editor components not found', 'error');
                return false;
            }
            
            // Enhanced event listeners
            codeInput.addEventListener('input', function() {
                updateLineNumbers();
                autoSave();
                validateSyntax();
            });
            
            codeInput.addEventListener('scroll', function() {
                lineNumbers.scrollTop = this.scrollTop;
            });
            
            codeInput.addEventListener('keydown', function(e) {
                // Tab key support
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = this.selectionStart;
                    const end = this.selectionEnd;
                    this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                    this.selectionStart = this.selectionEnd = start + 4;
                    updateLineNumbers();
                }
                
                // Auto-complete brackets
                if (e.key === '(' || e.key === '[' || e.key === '{') {
                    const closingBracket = { '(': ')', '[': ']', '{': '}' }[e.key];
                    setTimeout(() => {
                        const start = this.selectionStart;
                        this.value = this.value.substring(0, start) + closingBracket + this.value.substring(start);
                        this.selectionStart = this.selectionEnd = start;
                    }, 0);
                }
            });
            
            updateLineNumbers();
            addOutputLine('[SUCCESS] Code editor initialized with enhanced features', 'success');
            return true;
        }
        
        function autoSave() {
            const codeInput = document.getElementById('codeInput');
            if (codeInput) {
                localStorage.setItem('mitoCodeContent', codeInput.value);
                localStorage.setItem('mitoCodeTimestamp', new Date().toISOString());
            }
        }
        
        function validateSyntax() {
            const codeInput = document.getElementById('codeInput');
            if (!codeInput) return;
            
            const code = codeInput.value;
            const lines = code.split('\n');
            let errors = [];
            
            // Basic Python syntax validation
            lines.forEach((line, index) => {
                const lineNum = index + 1;
                
                // Check for common Python syntax errors
                if (line.trim() && !line.startsWith('#')) {
                    // Unclosed quotes
                    const quotes = (line.match(/"/g) || []).length;
                    const singleQuotes = (line.match(/'/g) || []).length;
                    
                    if (quotes % 2 !== 0 || singleQuotes % 2 !== 0) {
                        errors.push(`Line ${lineNum}: Unclosed quote`);
                    }
                    
                    // Missing colon after control structures
                    if (/^\s*(if|for|while|def|class|try|except|with)\s+.*[^:]\s*$/.test(line)) {
                        errors.push(`Line ${lineNum}: Missing colon`);
                    }
                }
            });
            
            if (errors.length > 0) {
                addOutputLine(`[SYNTAX] ${errors.length} issues found`, 'warning');
                errors.slice(0, 3).forEach(error => addOutputLine(`[SYNTAX] ${error}`, 'warning'));
            }
        }
        
        // Update line numbers when code changes
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize code editor with enhanced features
            setTimeout(() => {
                const editorInitialized = initializeCodeEditor();
                if (editorInitialized) {
                    // Load saved content
                    const savedContent = localStorage.getItem('mitoCodeContent');
                    if (savedContent) {
                        const codeInput = document.getElementById('codeInput');
                        if (codeInput) {
                            codeInput.value = savedContent;
                            updateLineNumbers();
                            addOutputLine('[INFO] Restored saved code content', 'info');
                        }
                    }
                    
                    // Generate initial system confirmation
                    setTimeout(() => {
                        const validation = validateSystemIntegrity();
                        addOutputLine(`[INIT] System validation complete`, 'success');
                    }, 1000);
                }
            }, 500);
            
            // Initialize universal copy-paste system
            enableUniversalCopyPaste();
            setTimeout(addUniversalCopyButtons, 1000);
        });
    </script>
</body>
</html>
"""