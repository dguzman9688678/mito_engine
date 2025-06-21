#!/usr/bin/env python3
"""
MITO Engine - Deployment Matrix
Holographic sphere managing global deployments with real-time monitoring and orchestration
"""

import os
import json
import sqlite3
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    STOPPED = "stopped"
    SCALING = "scaling"

class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    PREVIEW = "preview"

class Region(Enum):
    """Global regions"""
    US_EAST = "us-east-1"
    US_WEST = "us-west-2"
    EU_WEST = "eu-west-1"
    EU_CENTRAL = "eu-central-1"
    ASIA_PACIFIC = "ap-southeast-1"
    ASIA_NORTHEAST = "ap-northeast-1"

class DeploymentStrategy(Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"
    A_B_TESTING = "a_b_testing"

@dataclass
class Deployment:
    """Deployment configuration"""
    deployment_id: str
    name: str
    application: str
    version: str
    environment: str
    region: str
    status: str
    strategy: str
    config: Dict[str, Any]
    resources: Dict[str, Any]
    health_checks: List[Dict[str, Any]]
    created_at: str
    deployed_at: Optional[str]
    last_update: str
    metadata: Dict[str, Any]

@dataclass
class DeploymentMetrics:
    """Deployment performance metrics"""
    deployment_id: str
    cpu_usage: float
    memory_usage: float
    network_io: float
    disk_io: float
    request_count: int
    error_rate: float
    response_time: float
    availability: float
    last_updated: str

@dataclass
class GlobalNode:
    """Global deployment node"""
    node_id: str
    region: str
    environment: str
    status: str
    coordinates: Tuple[float, float, float]  # 3D coordinates for visualization
    deployments: List[str]
    capacity: Dict[str, float]
    utilization: Dict[str, float]
    last_heartbeat: str

class DeploymentDatabase:
    """Database for deployment management"""
    
    def __init__(self, db_path: str = "deployment_matrix.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize deployment database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                application TEXT NOT NULL,
                version TEXT NOT NULL,
                environment TEXT NOT NULL,
                region TEXT NOT NULL,
                status TEXT NOT NULL,
                strategy TEXT NOT NULL,
                config TEXT NOT NULL,
                resources TEXT NOT NULL,
                health_checks TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                deployed_at TIMESTAMP,
                last_update TIMESTAMP NOT NULL,
                metadata TEXT
            )
        """)
        
        # Deployment metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT NOT NULL,
                cpu_usage REAL NOT NULL,
                memory_usage REAL NOT NULL,
                network_io REAL NOT NULL,
                disk_io REAL NOT NULL,
                request_count INTEGER NOT NULL,
                error_rate REAL NOT NULL,
                response_time REAL NOT NULL,
                availability REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (deployment_id) REFERENCES deployments (deployment_id)
            )
        """)
        
        # Global nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_nodes (
                node_id TEXT PRIMARY KEY,
                region TEXT NOT NULL,
                environment TEXT NOT NULL,
                status TEXT NOT NULL,
                coordinates TEXT NOT NULL,
                deployments TEXT NOT NULL,
                capacity TEXT NOT NULL,
                utilization TEXT NOT NULL,
                last_heartbeat TIMESTAMP NOT NULL
            )
        """)
        
        # Deployment events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_events (
                event_id TEXT PRIMARY KEY,
                deployment_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                FOREIGN KEY (deployment_id) REFERENCES deployments (deployment_id)
            )
        """)
        
        # Release pipeline table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS release_pipelines (
                pipeline_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                application TEXT NOT NULL,
                stages TEXT NOT NULL,
                triggers TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_run TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

class DeploymentOrchestrator:
    """Deployment orchestration system"""
    
    def __init__(self, db: DeploymentDatabase):
        self.db = db
        self._initialize_global_nodes()
        self._initialize_sample_deployments()
    
    def _initialize_global_nodes(self):
        """Initialize global deployment nodes"""
        nodes = [
            {
                "node_id": "us-east-prod-01",
                "region": Region.US_EAST.value,
                "environment": Environment.PRODUCTION.value,
                "status": "healthy",
                "coordinates": [40.7128, -74.0060, 0],  # New York
                "capacity": {"cpu": 100, "memory": 512, "storage": 2048},
                "utilization": {"cpu": 45.2, "memory": 62.8, "storage": 23.1}
            },
            {
                "node_id": "us-west-prod-01",
                "region": Region.US_WEST.value,
                "environment": Environment.PRODUCTION.value,
                "status": "healthy",
                "coordinates": [37.7749, -122.4194, 0],  # San Francisco
                "capacity": {"cpu": 100, "memory": 512, "storage": 2048},
                "utilization": {"cpu": 38.7, "memory": 55.3, "storage": 19.8}
            },
            {
                "node_id": "eu-west-prod-01",
                "region": Region.EU_WEST.value,
                "environment": Environment.PRODUCTION.value,
                "status": "healthy",
                "coordinates": [51.5074, -0.1278, 0],  # London
                "capacity": {"cpu": 100, "memory": 512, "storage": 2048},
                "utilization": {"cpu": 52.1, "memory": 68.9, "storage": 31.4}
            },
            {
                "node_id": "asia-prod-01",
                "region": Region.ASIA_PACIFIC.value,
                "environment": Environment.PRODUCTION.value,
                "status": "healthy",
                "coordinates": [1.3521, 103.8198, 0],  # Singapore
                "capacity": {"cpu": 100, "memory": 512, "storage": 2048},
                "utilization": {"cpu": 41.6, "memory": 59.2, "storage": 26.7}
            },
            {
                "node_id": "us-east-staging-01",
                "region": Region.US_EAST.value,
                "environment": Environment.STAGING.value,
                "status": "healthy",
                "coordinates": [40.7128, -74.0060, 1],  # New York (staging layer)
                "capacity": {"cpu": 50, "memory": 256, "storage": 1024},
                "utilization": {"cpu": 23.8, "memory": 34.5, "storage": 15.2}
            }
        ]
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for node_data in nodes:
            cursor.execute("""
                INSERT OR REPLACE INTO global_nodes
                (node_id, region, environment, status, coordinates, deployments,
                 capacity, utilization, last_heartbeat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node_data["node_id"], node_data["region"], node_data["environment"],
                node_data["status"], json.dumps(node_data["coordinates"]), json.dumps([]),
                json.dumps(node_data["capacity"]), json.dumps(node_data["utilization"]),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _initialize_sample_deployments(self):
        """Initialize sample deployments"""
        deployments = [
            {
                "name": "MITO Engine API",
                "application": "mito-api",
                "version": "1.2.0",
                "environment": Environment.PRODUCTION.value,
                "region": Region.US_EAST.value,
                "strategy": DeploymentStrategy.BLUE_GREEN.value,
                "config": {
                    "replicas": 3,
                    "port": 5000,
                    "health_check_path": "/health"
                },
                "resources": {
                    "cpu": "2000m",
                    "memory": "4Gi",
                    "storage": "20Gi"
                },
                "health_checks": [
                    {"type": "http", "path": "/health", "interval": 30},
                    {"type": "tcp", "port": 5000, "interval": 10}
                ]
            },
            {
                "name": "Agent Lab Service",
                "application": "agent-lab",
                "version": "2.1.0",
                "environment": Environment.PRODUCTION.value,
                "region": Region.EU_WEST.value,
                "strategy": DeploymentStrategy.ROLLING.value,
                "config": {
                    "replicas": 2,
                    "port": 8080,
                    "auto_scaling": True
                },
                "resources": {
                    "cpu": "1500m",
                    "memory": "3Gi",
                    "storage": "15Gi"
                },
                "health_checks": [
                    {"type": "http", "path": "/api/health", "interval": 30}
                ]
            },
            {
                "name": "Analytics Engine",
                "application": "analytics",
                "version": "1.5.2",
                "environment": Environment.PRODUCTION.value,
                "region": Region.ASIA_PACIFIC.value,
                "strategy": DeploymentStrategy.CANARY.value,
                "config": {
                    "replicas": 4,
                    "port": 9000,
                    "canary_percentage": 10
                },
                "resources": {
                    "cpu": "3000m",
                    "memory": "8Gi",
                    "storage": "50Gi"
                },
                "health_checks": [
                    {"type": "http", "path": "/metrics", "interval": 15}
                ]
            }
        ]
        
        for dep_data in deployments:
            self.create_deployment(**dep_data)
    
    def create_deployment(self, name: str, application: str, version: str,
                         environment: Environment, region: Region,
                         strategy: DeploymentStrategy, config: Dict[str, Any],
                         resources: Dict[str, Any], health_checks: List[Dict[str, Any]],
                         metadata: Dict[str, Any] = None) -> str:
        """Create new deployment"""
        
        deployment_id = f"deploy_{int(time.time())}_{hashlib.sha256(name.encode()).hexdigest()[:8]}"
        
        deployment = Deployment(
            deployment_id=deployment_id,
            name=name,
            application=application,
            version=version,
            environment=environment if isinstance(environment, str) else environment.value,
            region=region if isinstance(region, str) else region.value,
            status=DeploymentStatus.PENDING.value,
            strategy=strategy if isinstance(strategy, str) else strategy.value,
            config=config,
            resources=resources,
            health_checks=health_checks,
            created_at=datetime.now().isoformat(),
            deployed_at=None,
            last_update=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO deployments
            (deployment_id, name, application, version, environment, region,
             status, strategy, config, resources, health_checks, created_at,
             deployed_at, last_update, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deployment.deployment_id, deployment.name, deployment.application,
            deployment.version, deployment.environment, deployment.region,
            deployment.status, deployment.strategy, json.dumps(deployment.config),
            json.dumps(deployment.resources), json.dumps(deployment.health_checks),
            deployment.created_at, deployment.deployed_at, deployment.last_update,
            json.dumps(deployment.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        # Simulate deployment process
        self._simulate_deployment(deployment_id)
        
        logger.info(f"Created deployment: {name} in {region}")
        return deployment_id
    
    def _simulate_deployment(self, deployment_id: str):
        """Simulate deployment process"""
        import threading
        
        def deployment_thread():
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Update to deploying
            cursor.execute("""
                UPDATE deployments 
                SET status = ?, last_update = ?
                WHERE deployment_id = ?
            """, (DeploymentStatus.DEPLOYING.value, datetime.now().isoformat(), deployment_id))
            
            conn.commit()
            
            # Simulate deployment time
            time.sleep(2)
            
            # Update to deployed
            cursor.execute("""
                UPDATE deployments 
                SET status = ?, deployed_at = ?, last_update = ?
                WHERE deployment_id = ?
            """, (
                DeploymentStatus.DEPLOYED.value, 
                datetime.now().isoformat(),
                datetime.now().isoformat(), 
                deployment_id
            ))
            
            conn.commit()
            conn.close()
            
            # Start metrics generation
            self._generate_metrics(deployment_id)
        
        thread = threading.Thread(target=deployment_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_metrics(self, deployment_id: str):
        """Generate realistic deployment metrics"""
        import threading
        
        def metrics_thread():
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            base_metrics = {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "network_io": 1024.0,
                "disk_io": 512.0,
                "request_count": 1000,
                "error_rate": 0.5,
                "response_time": 150.0,
                "availability": 99.9
            }
            
            for _ in range(10):  # Generate 10 metric points
                # Add some variance
                metrics = {
                    key: max(0, value + (hash(f"{deployment_id}{time.time()}") % 20 - 10))
                    for key, value in base_metrics.items()
                }
                
                cursor.execute("""
                    INSERT INTO deployment_metrics
                    (deployment_id, cpu_usage, memory_usage, network_io, disk_io,
                     request_count, error_rate, response_time, availability, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deployment_id, metrics["cpu_usage"], metrics["memory_usage"],
                    metrics["network_io"], metrics["disk_io"], metrics["request_count"],
                    metrics["error_rate"], metrics["response_time"], metrics["availability"],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                time.sleep(1)
            
            conn.close()
        
        thread = threading.Thread(target=metrics_thread)
        thread.daemon = True
        thread.start()
    
    def get_deployments(self, environment: Environment = None, region: Region = None) -> List[Deployment]:
        """Get deployments with optional filtering"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM deployments WHERE 1=1"
        params = []
        
        if environment:
            query += " AND environment = ?"
            params.append(environment.value)
        
        if region:
            query += " AND region = ?"
            params.append(region.value)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        deployments = []
        for row in rows:
            deployment = Deployment(
                deployment_id=row[0], name=row[1], application=row[2], version=row[3],
                environment=row[4], region=row[5], status=row[6], strategy=row[7],
                config=json.loads(row[8]), resources=json.loads(row[9]),
                health_checks=json.loads(row[10]), created_at=row[11],
                deployed_at=row[12], last_update=row[13], metadata=json.loads(row[14] or '{}')
            )
            deployments.append(deployment)
        
        return deployments
    
    def get_global_status(self) -> Dict[str, Any]:
        """Get global deployment status"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Deployment counts by status
        cursor.execute("SELECT status, COUNT(*) FROM deployments GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # Regional distribution
        cursor.execute("SELECT region, COUNT(*) FROM deployments GROUP BY region")
        regional_counts = dict(cursor.fetchall())
        
        # Environment distribution
        cursor.execute("SELECT environment, COUNT(*) FROM deployments GROUP BY environment")
        env_counts = dict(cursor.fetchall())
        
        # Global nodes status
        cursor.execute("SELECT region, status, COUNT(*) FROM global_nodes GROUP BY region, status")
        node_status = {}
        for region, status, count in cursor.fetchall():
            if region not in node_status:
                node_status[region] = {}
            node_status[region][status] = count
        
        # Recent metrics
        cursor.execute("""
            SELECT AVG(cpu_usage), AVG(memory_usage), AVG(availability)
            FROM deployment_metrics 
            WHERE timestamp >= datetime('now', '-1 hour')
        """)
        avg_metrics = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_deployments": sum(status_counts.values()),
            "status_distribution": status_counts,
            "regional_distribution": regional_counts,
            "environment_distribution": env_counts,
            "node_status": node_status,
            "global_metrics": {
                "avg_cpu_usage": avg_metrics[0] or 0,
                "avg_memory_usage": avg_metrics[1] or 0,
                "avg_availability": avg_metrics[2] or 0
            },
            "last_updated": datetime.now().isoformat()
        }

class DeploymentMatrixInterface:
    """Web interface for Deployment Matrix"""
    
    def __init__(self):
        self.db = DeploymentDatabase()
        self.orchestrator = DeploymentOrchestrator(self.db)
    
    def generate_matrix_interface(self) -> str:
        """Generate HTML interface for Deployment Matrix"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - Deployment Matrix</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: radial-gradient(ellipse at center, #000428 0%, #004e92 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow: hidden;
        }
        
        .matrix-container {
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            padding: 20px;
            text-align: center;
            background: rgba(0, 0, 0, 0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header h1 {
            color: #00d4ff;
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.2rem;
        }
        
        .holographic-sphere {
            position: relative;
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            perspective: 1000px;
        }
        
        .sphere-container {
            position: relative;
            width: 500px;
            height: 500px;
            transform-style: preserve-3d;
            animation: rotate-sphere 20s linear infinite;
        }
        
        .sphere {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, rgba(0, 212, 255, 0.8), rgba(0, 150, 255, 0.3), transparent);
            box-shadow: 
                0 0 100px rgba(0, 212, 255, 0.4),
                inset 0 0 100px rgba(0, 212, 255, 0.2);
            border: 2px solid rgba(0, 212, 255, 0.6);
        }
        
        .sphere::before {
            content: '';
            position: absolute;
            top: 10%;
            left: 10%;
            width: 30%;
            height: 30%;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.8), transparent);
            filter: blur(10px);
        }
        
        .deployment-node {
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: radial-gradient(circle, #00ff7f, #32cd32);
            box-shadow: 0 0 15px #00ff7f;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 10;
        }
        
        .deployment-node:hover {
            transform: scale(1.5);
            box-shadow: 0 0 25px #00ff7f;
        }
        
        .deployment-node.warning {
            background: radial-gradient(circle, #ffa500, #ff6b35);
            box-shadow: 0 0 15px #ffa500;
        }
        
        .deployment-node.error {
            background: radial-gradient(circle, #ff4500, #dc143c);
            box-shadow: 0 0 15px #ff4500;
        }
        
        .node-label {
            position: absolute;
            top: -30px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8rem;
            color: #00d4ff;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .deployment-node:hover .node-label {
            opacity: 1;
        }
        
        .connection-line {
            position: absolute;
            height: 2px;
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.8), rgba(0, 212, 255, 0.2));
            transform-origin: left center;
            animation: pulse-line 3s infinite ease-in-out;
        }
        
        .orbital-ring {
            position: absolute;
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 50%;
            animation: rotate-ring 15s linear infinite;
        }
        
        .ring-1 {
            width: 550px;
            height: 550px;
            top: -25px;
            left: -25px;
        }
        
        .ring-2 {
            width: 600px;
            height: 600px;
            top: -50px;
            left: -50px;
            animation-duration: 25s;
            animation-direction: reverse;
        }
        
        .data-stream {
            position: absolute;
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #00ff7f;
            box-shadow: 0 0 10px #00ff7f;
            animation: stream-flow 2s linear infinite;
        }
        
        .control-panel {
            position: absolute;
            top: 100px;
            left: 50px;
            width: 300px;
            background: rgba(0, 0, 0, 0.6);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .panel-section {
            margin-bottom: 20px;
        }
        
        .panel-title {
            color: #00d4ff;
            font-size: 1.1rem;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 5px;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .metric-value {
            color: #00ff7f;
            font-weight: bold;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        
        .status-healthy {
            background: #00ff7f;
            box-shadow: 0 0 8px #00ff7f;
        }
        
        .status-warning {
            background: #ffa500;
            box-shadow: 0 0 8px #ffa500;
        }
        
        .status-error {
            background: #ff4500;
            box-shadow: 0 0 8px #ff4500;
        }
        
        .deployment-info {
            position: absolute;
            top: 100px;
            right: 50px;
            width: 350px;
            background: rgba(0, 0, 0, 0.6);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .deployment-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #00d4ff;
        }
        
        .deployment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .deployment-name {
            color: #00d4ff;
            font-weight: 600;
        }
        
        .deployment-status {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        
        .status-deployed {
            background: rgba(0, 255, 127, 0.2);
            color: #00ff7f;
        }
        
        .status-deploying {
            background: rgba(255, 165, 0, 0.2);
            color: #ffa500;
        }
        
        .deployment-details {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .action-buttons {
            position: absolute;
            bottom: 50px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 20px;
        }
        
        .action-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .deploy-btn {
            background: linear-gradient(45deg, #00ff7f, #32cd32);
            color: #000;
        }
        
        .rollback-btn {
            background: linear-gradient(45deg, #ff4500, #dc143c);
            color: #fff;
        }
        
        .scale-btn {
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            color: #fff;
        }
        
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .floating-stats {
            position: absolute;
            bottom: 50px;
            right: 50px;
            background: rgba(0, 0, 0, 0.8);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .global-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            text-align: center;
        }
        
        .stat-item {
            font-size: 0.9rem;
        }
        
        .stat-number {
            font-size: 1.4rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        @keyframes rotate-sphere {
            0% { transform: rotateY(0deg) rotateX(0deg); }
            50% { transform: rotateY(180deg) rotateX(10deg); }
            100% { transform: rotateY(360deg) rotateX(0deg); }
        }
        
        @keyframes rotate-ring {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        @keyframes pulse-line {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }
        
        @keyframes stream-flow {
            0% { transform: translateY(0) scale(1); opacity: 1; }
            50% { transform: translateY(-50px) scale(1.2); opacity: 0.7; }
            100% { transform: translateY(-100px) scale(0.8); opacity: 0; }
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 10px;
            border-radius: 6px;
            font-size: 0.9rem;
            pointer-events: none;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="matrix-container">
        <div class="header">
            <h1>DEPLOYMENT MATRIX</h1>
            <div class="header-subtitle">Holographic sphere managing global deployments</div>
        </div>
        
        <div class="holographic-sphere">
            <div class="sphere-container">
                <div class="sphere"></div>
                
                <!-- Orbital rings -->
                <div class="orbital-ring ring-1"></div>
                <div class="orbital-ring ring-2"></div>
                
                <!-- Deployment nodes positioned around sphere -->
                <div class="deployment-node" style="top: 20%; left: 30%;" onclick="selectDeployment('us-east')">
                    <div class="node-label">US East</div>
                </div>
                
                <div class="deployment-node" style="top: 25%; right: 25%;" onclick="selectDeployment('us-west')">
                    <div class="node-label">US West</div>
                </div>
                
                <div class="deployment-node" style="top: 15%; left: 60%;" onclick="selectDeployment('eu-west')">
                    <div class="node-label">EU West</div>
                </div>
                
                <div class="deployment-node" style="bottom: 25%; right: 35%;" onclick="selectDeployment('asia-pacific')">
                    <div class="node-label">Asia Pacific</div>
                </div>
                
                <div class="deployment-node warning" style="bottom: 30%; left: 20%;" onclick="selectDeployment('eu-central')">
                    <div class="node-label">EU Central</div>
                </div>
                
                <!-- Connection lines -->
                <div class="connection-line" style="top: 25%; left: 35%; width: 150px; transform: rotate(15deg);"></div>
                <div class="connection-line" style="top: 20%; left: 45%; width: 100px; transform: rotate(45deg);"></div>
                <div class="connection-line" style="bottom: 35%; left: 40%; width: 120px; transform: rotate(-30deg);"></div>
                
                <!-- Data streams -->
                <div class="data-stream" style="top: 30%; left: 40%; animation-delay: 0s;"></div>
                <div class="data-stream" style="top: 40%; right: 30%; animation-delay: 0.5s;"></div>
                <div class="data-stream" style="bottom: 40%; left: 35%; animation-delay: 1s;"></div>
                <div class="data-stream" style="bottom: 35%; right: 40%; animation-delay: 1.5s;"></div>
            </div>
        </div>
        
        <div class="control-panel">
            <div class="panel-section">
                <div class="panel-title">🌐 Global Status</div>
                <div class="metric-row">
                    <span>Total Deployments</span>
                    <span class="metric-value">12</span>
                </div>
                <div class="metric-row">
                    <span>Active Regions</span>
                    <span class="metric-value">5</span>
                </div>
                <div class="metric-row">
                    <span>Global Uptime</span>
                    <span class="metric-value">99.97%</span>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="panel-title">🚀 Deployment Health</div>
                <div class="metric-row">
                    <span><span class="status-indicator status-healthy"></span>Healthy</span>
                    <span class="metric-value">10</span>
                </div>
                <div class="metric-row">
                    <span><span class="status-indicator status-warning"></span>Warning</span>
                    <span class="metric-value">2</span>
                </div>
                <div class="metric-row">
                    <span><span class="status-indicator status-error"></span>Error</span>
                    <span class="metric-value">0</span>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="panel-title">📊 Resource Usage</div>
                <div class="metric-row">
                    <span>CPU Average</span>
                    <span class="metric-value">45.8%</span>
                </div>
                <div class="metric-row">
                    <span>Memory Average</span>
                    <span class="metric-value">62.3%</span>
                </div>
                <div class="metric-row">
                    <span>Network I/O</span>
                    <span class="metric-value">1.2 GB/s</span>
                </div>
            </div>
        </div>
        
        <div class="deployment-info">
            <div class="panel-title">🎯 Active Deployments</div>
            
            <div class="deployment-card">
                <div class="deployment-header">
                    <div class="deployment-name">MITO Engine API</div>
                    <div class="deployment-status status-deployed">Deployed</div>
                </div>
                <div class="deployment-details">
                    Version: 1.2.0 | Region: US East<br>
                    Strategy: Blue-Green | Replicas: 3
                </div>
            </div>
            
            <div class="deployment-card">
                <div class="deployment-header">
                    <div class="deployment-name">Agent Lab Service</div>
                    <div class="deployment-status status-deployed">Deployed</div>
                </div>
                <div class="deployment-details">
                    Version: 2.1.0 | Region: EU West<br>
                    Strategy: Rolling | Replicas: 2
                </div>
            </div>
            
            <div class="deployment-card">
                <div class="deployment-header">
                    <div class="deployment-name">Analytics Engine</div>
                    <div class="deployment-status status-deploying">Deploying</div>
                </div>
                <div class="deployment-details">
                    Version: 1.5.2 | Region: Asia Pacific<br>
                    Strategy: Canary | Progress: 75%
                </div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="action-btn deploy-btn" onclick="deployGlobal()">Deploy</button>
            <button class="action-btn scale-btn" onclick="scaleDeployments()">Scale</button>
            <button class="action-btn rollback-btn" onclick="rollbackDeployment()">Rollback</button>
        </div>
        
        <div class="floating-stats">
            <div class="global-stats">
                <div class="stat-item">
                    <div class="stat-number">47.2K</div>
                    <div>Requests/min</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">1.2ms</div>
                    <div>Avg Latency</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">99.9%</div>
                    <div>Availability</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        let selectedRegion = null;
        
        function selectDeployment(region) {
            selectedRegion = region;
            
            // Highlight selected node
            document.querySelectorAll('.deployment-node').forEach(node => {
                node.style.transform = 'scale(1)';
            });
            event.target.style.transform = 'scale(1.8)';
            
            console.log(`Selected deployment region: ${region}`);
            
            // Update deployment info panel with region-specific data
            updateDeploymentInfo(region);
        }
        
        function updateDeploymentInfo(region) {
            // In a real application, this would fetch actual deployment data
            const regionData = {
                'us-east': {
                    deployments: ['MITO Engine API', 'User Management Service'],
                    health: 'healthy',
                    cpu: '42.3%',
                    memory: '58.7%'
                },
                'eu-west': {
                    deployments: ['Agent Lab Service', 'Analytics Dashboard'],
                    health: 'healthy', 
                    cpu: '39.1%',
                    memory: '61.2%'
                },
                'asia-pacific': {
                    deployments: ['Analytics Engine', 'ML Training Service'],
                    health: 'deploying',
                    cpu: '51.8%',
                    memory: '67.4%'
                }
            };
            
            // Update control panel with region-specific metrics
            console.log(`Updated info for ${region}:`, regionData[region]);
        }
        
        function deployGlobal() {
            // Simulate global deployment
            const btn = event.target;
            btn.style.background = 'linear-gradient(45deg, #ffa500, #ff6b35)';
            btn.textContent = 'DEPLOYING...';
            
            // Add deployment animation to sphere
            document.querySelector('.sphere').style.animation = 'rotate-sphere 5s linear infinite';
            
            setTimeout(() => {
                btn.style.background = 'linear-gradient(45deg, #00ff7f, #32cd32)';
                btn.textContent = 'DEPLOYED!';
                
                setTimeout(() => {
                    btn.textContent = 'DEPLOY';
                    btn.style.background = 'linear-gradient(45deg, #00ff7f, #32cd32)';
                }, 2000);
            }, 3000);
        }
        
        function scaleDeployments() {
            if (!selectedRegion) {
                alert('Please select a deployment region first');
                return;
            }
            
            const replicas = prompt(`Enter number of replicas for ${selectedRegion}:`, '3');
            if (replicas) {
                alert(`Scaling ${selectedRegion} to ${replicas} replicas...`);
                
                // Visual feedback
                const nodes = document.querySelectorAll('.deployment-node');
                nodes.forEach(node => {
                    node.style.animation = 'pulse-line 1s infinite';
                });
                
                setTimeout(() => {
                    nodes.forEach(node => {
                        node.style.animation = '';
                    });
                }, 3000);
            }
        }
        
        function rollbackDeployment() {
            if (!selectedRegion) {
                alert('Please select a deployment region first');
                return;
            }
            
            const confirmed = confirm(`Rollback deployment in ${selectedRegion}?`);
            if (confirmed) {
                alert(`Rolling back ${selectedRegion} deployment...`);
                
                // Change selected node to warning state temporarily
                const selectedNode = document.querySelector('.deployment-node[style*="scale(1.8)"]');
                if (selectedNode) {
                    selectedNode.classList.add('warning');
                    setTimeout(() => {
                        selectedNode.classList.remove('warning');
                    }, 5000);
                }
            }
        }
        
        // Real-time metrics updates
        setInterval(() => {
            // Update CPU usage
            const cpuElement = document.querySelector('.metric-row:nth-child(1) .metric-value');
            if (cpuElement && cpuElement.textContent.includes('%')) {
                const currentCpu = parseFloat(cpuElement.textContent);
                const newCpu = Math.max(20, Math.min(80, currentCpu + (Math.random() - 0.5) * 2));
                cpuElement.textContent = `${newCpu.toFixed(1)}%`;
            }
            
            // Update requests/min
            const reqElement = document.querySelector('.stat-number');
            if (reqElement) {
                const current = parseFloat(reqElement.textContent);
                const variance = (Math.random() - 0.5) * 5;
                reqElement.textContent = `${(current + variance).toFixed(1)}K`;
            }
        }, 5000);
        
        // Mouse tracking for 3D effect
        document.addEventListener('mousemove', (e) => {
            const sphere = document.querySelector('.sphere-container');
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;
            
            const mouseX = (e.clientX - centerX) / centerX;
            const mouseY = (e.clientY - centerY) / centerY;
            
            sphere.style.transform = `rotateY(${mouseX * 10}deg) rotateX(${-mouseY * 10}deg)`;
        });
        
        // Tooltip functionality
        document.querySelectorAll('.deployment-node').forEach(node => {
            node.addEventListener('mouseenter', (e) => {
                const tooltip = document.getElementById('tooltip');
                const label = node.querySelector('.node-label').textContent;
                tooltip.textContent = `${label} - Click for details`;
                tooltip.style.opacity = '1';
            });
            
            node.addEventListener('mouseleave', () => {
                document.getElementById('tooltip').style.opacity = '0';
            });
        });
        
        document.addEventListener('mousemove', (e) => {
            const tooltip = document.getElementById('tooltip');
            tooltip.style.left = e.clientX + 10 + 'px';
            tooltip.style.top = e.clientY - 30 + 'px';
        });
    </script>
</body>
</html>
        """

def main():
    """Demo of Deployment Matrix functionality"""
    print("MITO Engine - Deployment Matrix Demo")
    print("=" * 50)
    
    # Initialize Deployment Matrix
    interface = DeploymentMatrixInterface()
    
    # Get all deployments
    deployments = interface.orchestrator.get_deployments()
    print(f"Active deployments: {len(deployments)}")
    
    for deployment in deployments:
        print(f"  🚀 {deployment.name} v{deployment.version}")
        print(f"     Region: {deployment.region}, Environment: {deployment.environment}")
        print(f"     Status: {deployment.status}, Strategy: {deployment.strategy}")
    
    # Get global status
    status = interface.orchestrator.get_global_status()
    print(f"\nGlobal Status:")
    print(f"  Total deployments: {status['total_deployments']}")
    print(f"  Status distribution: {status['status_distribution']}")
    print(f"  Regional distribution: {status['regional_distribution']}")
    print(f"  Avg CPU usage: {status['global_metrics']['avg_cpu_usage']:.1f}%")
    print(f"  Avg availability: {status['global_metrics']['avg_availability']:.1f}%")
    
    print("\nDeployment Matrix demo completed!")

if __name__ == "__main__":
    main()