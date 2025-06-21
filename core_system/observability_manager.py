"""
MITO Engine - Advanced Observability & Monitoring
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Live metrics, anomaly detection, and user analytics
"""

import asyncio
import websockets
import json
import time
import threading
import sqlite3
import psutil
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os

logger = logging.getLogger(__name__)

class WebSocketMetricsStreamer:
    """Low-latency WebSocket-based metrics streaming"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.clients = set()
        self.running = False
        self.metrics_history = deque(maxlen=1000)
        self.server = None
        
    async def register_client(self, websocket, path):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            # Send initial metrics burst
            for metric in list(self.metrics_history)[-10:]:
                await websocket.send(json.dumps(metric))
                
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected: {websocket.remote_address}")
            
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to all connected clients"""
        if self.clients:
            message = json.dumps(metrics)
            disconnected = set()
            
            for client in self.clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected.add(client)
                    
            # Remove disconnected clients
            self.clients -= disconnected
            
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            # Process metrics
            process_count = len(psutil.pids())
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else 0
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent,
                    'swap_total': swap.total,
                    'swap_used': swap.used,
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv,
                    'connections': network_connections
                },
                'system': {
                    'process_count': process_count,
                    'boot_time': psutil.boot_time(),
                    'uptime': time.time() - psutil.boot_time()
                }
            }
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
            
    async def start_streaming(self):
        """Start WebSocket server and metrics collection"""
        self.running = True
        
        # Start WebSocket server
        self.server = await websockets.serve(self.register_client, "localhost", self.port)
        logger.info(f"WebSocket metrics server started on port {self.port}")
        
        # Start metrics collection loop
        while self.running:
            try:
                metrics = self.collect_system_metrics()
                await self.broadcast_metrics(metrics)
                await asyncio.sleep(1)  # 1-second intervals for low latency
            except Exception as e:
                logger.error(f"Error in metrics streaming: {e}")
                await asyncio.sleep(5)
                
    def stop_streaming(self):
        """Stop metrics streaming"""
        self.running = False
        if self.server:
            self.server.close()

class AnomalyDetector:
    """ML-based anomaly detection for system metrics"""
    
    def __init__(self, model_path: str = "anomaly_model.pkl"):
        self.model_path = model_path
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.training_data = deque(maxlen=1000)
        self.anomaly_threshold = 0.1
        self.load_or_create_model()
        
    def load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.isolation_forest = model_data['model']
                    self.scaler = model_data['scaler']
                logger.info("Loaded existing anomaly detection model")
            else:
                self.isolation_forest = IsolationForest(
                    contamination=self.anomaly_threshold,
                    random_state=42,
                    n_estimators=100
                )
                logger.info("Created new anomaly detection model")
        except Exception as e:
            logger.error(f"Failed to load/create anomaly model: {e}")
            self.isolation_forest = IsolationForest(contamination=self.anomaly_threshold)
            
    def extract_features(self, metrics: Dict[str, Any]) -> List[float]:
        """Extract numerical features from metrics"""
        try:
            features = [
                metrics['cpu']['usage_percent'],
                metrics['memory']['percent'],
                metrics['disk']['percent'],
                metrics['network']['bytes_sent'] / 1024 / 1024,  # MB
                metrics['network']['bytes_recv'] / 1024 / 1024,  # MB
                metrics['system']['process_count']
            ]
            return features
        except Exception as e:
            logger.error(f"Failed to extract features: {e}")
            return [0.0] * 6
            
    def add_training_data(self, metrics: Dict[str, Any]):
        """Add metrics to training data"""
        features = self.extract_features(metrics)
        self.training_data.append(features)
        
        # Retrain model periodically
        if len(self.training_data) >= 100 and len(self.training_data) % 50 == 0:
            self.retrain_model()
            
    def retrain_model(self):
        """Retrain the anomaly detection model"""
        try:
            if len(self.training_data) < 50:
                return
                
            # Prepare training data
            X = np.array(list(self.training_data))
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.isolation_forest.fit(X_scaled)
            
            # Save model
            model_data = {
                'model': self.isolation_forest,
                'scaler': self.scaler
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"Retrained anomaly model with {len(self.training_data)} samples")
            
        except Exception as e:
            logger.error(f"Failed to retrain model: {e}")
            
    def detect_anomaly(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if metrics represent an anomaly"""
        try:
            features = self.extract_features(metrics)
            
            if self.isolation_forest is None:
                return {'is_anomaly': False, 'score': 0.0, 'reason': 'Model not trained'}
                
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict anomaly
            prediction = self.isolation_forest.predict(features_scaled)[0]
            score = self.isolation_forest.decision_function(features_scaled)[0]
            
            is_anomaly = prediction == -1
            
            # Determine reason if anomaly
            reason = ""
            if is_anomaly:
                feature_names = ['CPU', 'Memory', 'Disk', 'Network Send', 'Network Recv', 'Processes']
                # Simple rule-based reasoning
                if features[0] > 90:
                    reason = "High CPU usage"
                elif features[1] > 90:
                    reason = "High memory usage"
                elif features[2] > 95:
                    reason = "High disk usage"
                elif features[3] > 100 or features[4] > 100:
                    reason = "High network activity"
                else:
                    reason = "Unusual system behavior pattern"
                    
            return {
                'is_anomaly': is_anomaly,
                'score': float(score),
                'reason': reason,
                'timestamp': metrics.get('timestamp'),
                'features': dict(zip(['cpu', 'memory', 'disk', 'net_send', 'net_recv', 'processes'], features))
            }
            
        except Exception as e:
            logger.error(f"Failed to detect anomaly: {e}")
            return {'is_anomaly': False, 'score': 0.0, 'reason': f'Error: {e}'}

class UserAnalytics:
    """User session analytics and heatmap generation"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        self.init_analytics_db()
        
    def init_analytics_db(self):
        """Initialize user analytics database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    tab_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    duration_seconds REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_heatmaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    tab_usage TEXT NOT NULL,
                    total_duration REAL,
                    most_used_tab TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
            
    def track_interaction(self, session_id: str, user_id: str, tab_id: str, 
                         action_type: str, duration: float = 0, metadata: Dict[str, Any] = None):
        """Track user interaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_interactions 
                (session_id, user_id, tab_id, action_type, duration_seconds, metadata) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, tab_id, action_type, duration, json.dumps(metadata) if metadata else "{}"))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {e}")
            
    def generate_session_heatmap(self, session_id: str) -> Dict[str, Any]:
        """Generate heatmap for user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get interaction data for session
            cursor.execute("""
                SELECT tab_id, COUNT(*) as interaction_count, 
                       SUM(duration_seconds) as total_duration,
                       AVG(duration_seconds) as avg_duration
                FROM user_interactions 
                WHERE session_id = ? 
                GROUP BY tab_id
                ORDER BY interaction_count DESC
            """, (session_id,))
            
            tab_usage = {}
            total_interactions = 0
            total_duration = 0
            
            for row in cursor.fetchall():
                tab_id, count, duration, avg_duration = row
                tab_usage[tab_id] = {
                    'interactions': count,
                    'total_duration': duration or 0,
                    'avg_duration': avg_duration or 0,
                    'percentage': 0  # Will calculate after getting totals
                }
                total_interactions += count
                total_duration += (duration or 0)
                
            # Calculate percentages
            for tab_id in tab_usage:
                tab_usage[tab_id]['percentage'] = (tab_usage[tab_id]['interactions'] / total_interactions * 100) if total_interactions > 0 else 0
                
            most_used_tab = max(tab_usage.keys(), key=lambda x: tab_usage[x]['interactions']) if tab_usage else None
            
            heatmap_data = {
                'session_id': session_id,
                'tab_usage': tab_usage,
                'total_interactions': total_interactions,
                'total_duration': total_duration,
                'most_used_tab': most_used_tab,
                'generated_at': datetime.now().isoformat()
            }
            
            # Store heatmap
            cursor.execute("""
                INSERT OR REPLACE INTO session_heatmaps 
                (session_id, tab_usage, total_duration, most_used_tab) 
                VALUES (?, ?, ?, ?)
            """, (session_id, json.dumps(tab_usage), total_duration, most_used_tab))
            
            conn.commit()
            conn.close()
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Failed to generate session heatmap: {e}")
            return {}
            
    def get_global_usage_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get global usage analytics across all users"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Most popular tabs
            cursor.execute("""
                SELECT tab_id, COUNT(*) as usage_count 
                FROM user_interactions 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY tab_id 
                ORDER BY usage_count DESC
            """.format(days))
            
            popular_tabs = dict(cursor.fetchall())
            
            # Daily usage patterns
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as interactions
                FROM user_interactions 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY hour 
                ORDER BY hour
            """.format(days))
            
            hourly_usage = dict(cursor.fetchall())
            
            # User engagement metrics
            cursor.execute("""
                SELECT user_id, COUNT(DISTINCT session_id) as sessions,
                       COUNT(*) as total_interactions,
                       AVG(duration_seconds) as avg_interaction_time
                FROM user_interactions 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY user_id
            """.format(days))
            
            user_engagement = {}
            for row in cursor.fetchall():
                user_id, sessions, interactions, avg_time = row
                user_engagement[user_id] = {
                    'sessions': sessions,
                    'interactions': interactions,
                    'avg_interaction_time': avg_time or 0
                }
                
            conn.close()
            
            return {
                'popular_tabs': popular_tabs,
                'hourly_usage': hourly_usage,
                'user_engagement': user_engagement,
                'analysis_period_days': days,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get global analytics: {e}")
            return {}

class SystemOperationsManager:
    """Advanced system operations including command playback and rollback"""
    
    def __init__(self, db_path: str = "mito_operations.db"):
        self.db_path = db_path
        self.init_operations_db()
        
    def init_operations_db(self):
        """Initialize operations database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    working_directory TEXT,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    duration_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    environment_vars TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    snapshot_name TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    file_checksums TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT UNIQUE NOT NULL,
                    cron_expression TEXT NOT NULL,
                    command TEXT NOT NULL,
                    working_directory TEXT,
                    environment_vars TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize operations database: {e}")
            
    def record_command_execution(self, session_id: str, user_id: str, command: str, 
                               working_dir: str, exit_code: int, stdout: str, stderr: str, 
                               duration_ms: int, env_vars: Dict[str, str] = None):
        """Record command execution for playback"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO command_history 
                (session_id, user_id, command, working_directory, exit_code, 
                 stdout, stderr, duration_ms, environment_vars) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, command, working_dir, exit_code, stdout, stderr, 
                  duration_ms, json.dumps(env_vars) if env_vars else "{}"))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record command execution: {e}")
            
    def get_command_history(self, session_id: str = None, user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get command history for playback"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM command_history WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
                
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get command history: {e}")
            return []
            
    def create_session_snapshot(self, session_id: str, snapshot_name: str, 
                              state_data: Dict[str, Any], description: str = "") -> bool:
        """Create session state snapshot for rollback"""
        try:
            # Calculate file checksums for important files
            file_checksums = self._calculate_file_checksums()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO session_snapshots 
                (session_id, snapshot_name, state_data, file_checksums, description) 
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, snapshot_name, json.dumps(state_data), 
                  json.dumps(file_checksums), description))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session snapshot: {e}")
            return False
            
    def _calculate_file_checksums(self) -> Dict[str, str]:
        """Calculate checksums for important files"""
        import hashlib
        
        important_files = [
            'app.py', 'session_manager.py', 'networking_manager.py',
            'mito_sessions.db', 'mito_operations.db'
        ]
        
        checksums = {}
        for filename in important_files:
            try:
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        checksums[filename] = file_hash
            except Exception as e:
                logger.error(f"Failed to calculate checksum for {filename}: {e}")
                
        return checksums