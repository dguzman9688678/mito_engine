#!/usr/bin/env python3
"""
MITO Engine - Agent Lab
AI agent creation interface with 3D wireframe visualization, datasets, model training, and agent creation
"""

import os
import json
import sqlite3
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of AI agents"""
    CONVERSATIONAL = "conversational"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    TASK_AUTOMATION = "task_automation"
    DATA_PROCESSING = "data_processing"
    DECISION_MAKING = "decision_making"
    MONITORING = "monitoring"
    CUSTOM = "custom"

class TrainingStatus(Enum):
    """Training status"""
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ModelArchitecture(Enum):
    """Model architectures"""
    TRANSFORMER = "transformer"
    LSTM = "lstm"
    CNN = "cnn"
    HYBRID = "hybrid"
    ENSEMBLE = "ensemble"

@dataclass
class Agent:
    """AI agent definition"""
    agent_id: str
    name: str
    description: str
    agent_type: str
    model_architecture: str
    training_status: str
    current_epoch: int
    total_epochs: int
    accuracy: float
    loss: float
    dataset_id: str
    config: Dict[str, Any]
    capabilities: List[str]
    created_at: str
    trained_at: Optional[str]
    last_active: Optional[str]

@dataclass
class Dataset:
    """Training dataset"""
    dataset_id: str
    name: str
    description: str
    data_type: str
    size: int
    features: int
    labels: List[str]
    split_ratio: Dict[str, float]
    preprocessing: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str

@dataclass
class TrainingSession:
    """Model training session"""
    session_id: str
    agent_id: str
    dataset_id: str
    start_time: str
    end_time: Optional[str]
    current_epoch: int
    total_epochs: int
    best_accuracy: float
    current_loss: float
    training_metrics: Dict[str, List[float]]
    hyperparameters: Dict[str, Any]
    status: str

class AgentDatabase:
    """Database for agent management"""
    
    def __init__(self, db_path: str = "agent_lab.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize agent database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                agent_type TEXT NOT NULL,
                model_architecture TEXT NOT NULL,
                training_status TEXT NOT NULL,
                current_epoch INTEGER DEFAULT 0,
                total_epochs INTEGER DEFAULT 100,
                accuracy REAL DEFAULT 0.0,
                loss REAL DEFAULT 0.0,
                dataset_id TEXT,
                config TEXT,
                capabilities TEXT,
                created_at TIMESTAMP NOT NULL,
                trained_at TIMESTAMP,
                last_active TIMESTAMP
            )
        """)
        
        # Datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                data_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                features INTEGER NOT NULL,
                labels TEXT,
                split_ratio TEXT,
                preprocessing TEXT,
                metadata TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Training sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_sessions (
                session_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                dataset_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                current_epoch INTEGER DEFAULT 0,
                total_epochs INTEGER NOT NULL,
                best_accuracy REAL DEFAULT 0.0,
                current_loss REAL DEFAULT 0.0,
                training_metrics TEXT,
                hyperparameters TEXT,
                status TEXT NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id),
                FOREIGN KEY (dataset_id) REFERENCES datasets (dataset_id)
            )
        """)
        
        # Agent interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_interactions (
                interaction_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                input_text TEXT,
                output_text TEXT,
                confidence REAL,
                response_time REAL,
                feedback_score INTEGER,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        """)
        
        conn.commit()
        conn.close()

class AgentTrainer:
    """AI agent training system"""
    
    def __init__(self, db: AgentDatabase):
        self.db = db
        
    def create_training_session(self, agent_id: str, dataset_id: str, 
                              hyperparameters: Dict[str, Any]) -> str:
        """Create new training session"""
        session_id = f"train_{int(time.time())}"
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO training_sessions
            (session_id, agent_id, dataset_id, start_time, total_epochs,
             hyperparameters, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, agent_id, dataset_id, datetime.now().isoformat(),
            hyperparameters.get('epochs', 100), json.dumps(hyperparameters),
            TrainingStatus.PENDING.value
        ))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def start_training(self, session_id: str) -> bool:
        """Start training session"""
        try:
            # Update session status
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE training_sessions 
                SET status = ?, start_time = ?
                WHERE session_id = ?
            """, (TrainingStatus.TRAINING.value, datetime.now().isoformat(), session_id))
            
            # Get session details
            cursor.execute("""
                SELECT agent_id, dataset_id, total_epochs, hyperparameters
                FROM training_sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            session_data = cursor.fetchone()
            if not session_data:
                conn.close()
                return False
            
            agent_id, dataset_id, total_epochs, hyperparams = session_data
            hyperparameters = json.loads(hyperparams)
            
            # Update agent status
            cursor.execute("""
                UPDATE agents 
                SET training_status = ?, current_epoch = 0, total_epochs = ?
                WHERE agent_id = ?
            """, (TrainingStatus.TRAINING.value, total_epochs, agent_id))
            
            conn.commit()
            conn.close()
            
            # Simulate training process
            self._simulate_training(session_id, agent_id, total_epochs, hyperparameters)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            return False
    
    def _simulate_training(self, session_id: str, agent_id: str, 
                          total_epochs: int, hyperparameters: Dict[str, Any]):
        """Simulate training process with realistic metrics"""
        import threading
        
        def training_thread():
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Initialize metrics
            metrics = {
                'loss': [],
                'accuracy': [],
                'val_loss': [],
                'val_accuracy': []
            }
            
            learning_rate = hyperparameters.get('learning_rate', 0.001)
            batch_size = hyperparameters.get('batch_size', 32)
            
            for epoch in range(1, total_epochs + 1):
                # Simulate realistic training metrics
                base_loss = 2.5 * (0.95 ** epoch) + 0.1
                noise = (hash(f"{epoch}{session_id}") % 100) / 1000
                loss = max(0.01, base_loss + noise)
                
                accuracy = min(0.99, 1.0 - (loss * 0.4) + (epoch * 0.002))
                val_loss = loss * 1.1 + (noise * 0.5)
                val_accuracy = accuracy * 0.95
                
                metrics['loss'].append(loss)
                metrics['accuracy'].append(accuracy)
                metrics['val_loss'].append(val_loss)
                metrics['val_accuracy'].append(val_accuracy)
                
                # Update session
                cursor.execute("""
                    UPDATE training_sessions 
                    SET current_epoch = ?, current_loss = ?, 
                        best_accuracy = ?, training_metrics = ?
                    WHERE session_id = ?
                """, (
                    epoch, loss, max(metrics['accuracy']), 
                    json.dumps(metrics), session_id
                ))
                
                # Update agent
                cursor.execute("""
                    UPDATE agents 
                    SET current_epoch = ?, accuracy = ?, loss = ?
                    WHERE agent_id = ?
                """, (epoch, accuracy, loss, agent_id))
                
                conn.commit()
                
                # Simulate training time
                time.sleep(0.1)  # Quick simulation
                
                if epoch % 10 == 0:
                    logger.info(f"Training epoch {epoch}/{total_epochs}, Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            
            # Complete training
            cursor.execute("""
                UPDATE training_sessions 
                SET status = ?, end_time = ?
                WHERE session_id = ?
            """, (TrainingStatus.COMPLETED.value, datetime.now().isoformat(), session_id))
            
            cursor.execute("""
                UPDATE agents 
                SET training_status = ?, trained_at = ?
                WHERE agent_id = ?
            """, (TrainingStatus.COMPLETED.value, datetime.now().isoformat(), agent_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Training completed for agent {agent_id}")
        
        # Start training in background
        thread = threading.Thread(target=training_thread)
        thread.daemon = True
        thread.start()

class AgentManager:
    """Main agent management system"""
    
    def __init__(self):
        self.db = AgentDatabase()
        self.trainer = AgentTrainer(self.db)
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize sample datasets and agents"""
        # Create sample datasets
        sample_datasets = [
            Dataset(
                dataset_id="ds_conversational_001",
                name="Conversational Training Data",
                description="Large-scale conversational AI training dataset",
                data_type="text",
                size=50000,
                features=768,
                labels=["intent", "sentiment", "entity"],
                split_ratio={"train": 0.8, "val": 0.1, "test": 0.1},
                preprocessing={"tokenization": "bert", "max_length": 512},
                metadata={"language": "en", "domain": "general"},
                created_at=datetime.now().isoformat()
            ),
            Dataset(
                dataset_id="ds_analytical_001",
                name="Business Analytics Dataset",
                description="Time series and tabular data for business analytics",
                data_type="tabular",
                size=25000,
                features=42,
                labels=["prediction", "category", "risk_score"],
                split_ratio={"train": 0.7, "val": 0.2, "test": 0.1},
                preprocessing={"normalization": "standard", "encoding": "one_hot"},
                metadata={"temporal": True, "categorical_features": 8},
                created_at=datetime.now().isoformat()
            ),
            Dataset(
                dataset_id="ds_creative_001",
                name="Creative Content Dataset",
                description="Multimodal dataset for creative content generation",
                data_type="multimodal",
                size=15000,
                features=1024,
                labels=["style", "genre", "quality"],
                split_ratio={"train": 0.8, "val": 0.15, "test": 0.05},
                preprocessing={"image_size": [256, 256], "text_tokenizer": "gpt2"},
                metadata={"modalities": ["text", "image"], "creativity_score": True},
                created_at=datetime.now().isoformat()
            )
        ]
        
        # Store datasets
        for dataset in sample_datasets:
            self._store_dataset(dataset)
        
        # Create sample agents
        sample_agents = [
            Agent(
                agent_id="agent_conv_001",
                name="ConversaBot Pro",
                description="Advanced conversational agent for customer support",
                agent_type=AgentType.CONVERSATIONAL.value,
                model_architecture=ModelArchitecture.TRANSFORMER.value,
                training_status=TrainingStatus.COMPLETED.value,
                current_epoch=75,
                total_epochs=100,
                accuracy=0.947,
                loss=0.124,
                dataset_id="ds_conversational_001",
                config={"temperature": 0.7, "max_tokens": 512, "top_p": 0.9},
                capabilities=["dialogue", "context_awareness", "emotion_detection"],
                created_at=datetime.now().isoformat(),
                trained_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            ),
            Agent(
                agent_id="agent_anal_001",
                name="DataMind Analytics",
                description="Business intelligence and predictive analytics agent",
                agent_type=AgentType.ANALYTICAL.value,
                model_architecture=ModelArchitecture.ENSEMBLE.value,
                training_status=TrainingStatus.TRAINING.value,
                current_epoch=25,
                total_epochs=50,
                accuracy=0.823,
                loss=0.287,
                dataset_id="ds_analytical_001",
                config={"ensemble_size": 5, "feature_selection": "auto"},
                capabilities=["forecasting", "anomaly_detection", "pattern_recognition"],
                created_at=datetime.now().isoformat(),
                trained_at=None,
                last_active=None
            ),
            Agent(
                agent_id="agent_creative_001",
                name="CreativeGenius AI",
                description="Multimodal creative content generation agent",
                agent_type=AgentType.CREATIVE.value,
                model_architecture=ModelArchitecture.HYBRID.value,
                training_status=TrainingStatus.PENDING.value,
                current_epoch=0,
                total_epochs=200,
                accuracy=0.0,
                loss=0.0,
                dataset_id="ds_creative_001",
                config={"creativity_boost": 1.2, "style_transfer": True},
                capabilities=["text_generation", "image_synthesis", "style_transfer"],
                created_at=datetime.now().isoformat(),
                trained_at=None,
                last_active=None
            )
        ]
        
        # Store agents
        for agent in sample_agents:
            self._store_agent(agent)
    
    def _store_dataset(self, dataset: Dataset):
        """Store dataset in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO datasets
            (dataset_id, name, description, data_type, size, features, labels,
             split_ratio, preprocessing, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dataset.dataset_id, dataset.name, dataset.description, dataset.data_type,
            dataset.size, dataset.features, json.dumps(dataset.labels),
            json.dumps(dataset.split_ratio), json.dumps(dataset.preprocessing),
            json.dumps(dataset.metadata), dataset.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def _store_agent(self, agent: Agent):
        """Store agent in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO agents
            (agent_id, name, description, agent_type, model_architecture,
             training_status, current_epoch, total_epochs, accuracy, loss,
             dataset_id, config, capabilities, created_at, trained_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.agent_id, agent.name, agent.description, agent.agent_type,
            agent.model_architecture, agent.training_status, agent.current_epoch,
            agent.total_epochs, agent.accuracy, agent.loss, agent.dataset_id,
            json.dumps(agent.config), json.dumps(agent.capabilities),
            agent.created_at, agent.trained_at, agent.last_active
        ))
        
        conn.commit()
        conn.close()
    
    def create_agent(self, name: str, description: str, agent_type: AgentType,
                    model_architecture: ModelArchitecture, dataset_id: str,
                    capabilities: List[str], config: Dict[str, Any]) -> Agent:
        """Create new AI agent"""
        
        agent_id = f"agent_{int(time.time())}"
        
        agent = Agent(
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=agent_type.value,
            model_architecture=model_architecture.value,
            training_status=TrainingStatus.PENDING.value,
            current_epoch=0,
            total_epochs=config.get('epochs', 100),
            accuracy=0.0,
            loss=0.0,
            dataset_id=dataset_id,
            config=config,
            capabilities=capabilities,
            created_at=datetime.now().isoformat(),
            trained_at=None,
            last_active=None
        )
        
        self._store_agent(agent)
        
        logger.info(f"Created agent: {name} ({agent_id})")
        return agent
    
    def get_agents(self, agent_type: Optional[AgentType] = None) -> List[Agent]:
        """Get agents with optional filtering"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM agents"
        params = []
        
        if agent_type:
            query += " WHERE agent_type = ?"
            params.append(agent_type.value)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        agents = []
        for row in rows:
            agent = Agent(
                agent_id=row[0], name=row[1], description=row[2], agent_type=row[3],
                model_architecture=row[4], training_status=row[5], current_epoch=row[6],
                total_epochs=row[7], accuracy=row[8], loss=row[9], dataset_id=row[10],
                config=json.loads(row[11]), capabilities=json.loads(row[12]),
                created_at=row[13], trained_at=row[14], last_active=row[15]
            )
            agents.append(agent)
        
        return agents
    
    def get_datasets(self) -> List[Dataset]:
        """Get all available datasets"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        datasets = []
        for row in rows:
            dataset = Dataset(
                dataset_id=row[0], name=row[1], description=row[2], data_type=row[3],
                size=row[4], features=row[5], labels=json.loads(row[6]),
                split_ratio=json.loads(row[7]), preprocessing=json.loads(row[8]),
                metadata=json.loads(row[9]), created_at=row[10]
            )
            datasets.append(dataset)
        
        return datasets
    
    def start_training(self, agent_id: str, hyperparameters: Optional[Dict[str, Any]] = None) -> str:
        """Start training for an agent"""
        # Get agent details
        agents = [a for a in self.get_agents() if a.agent_id == agent_id]
        if not agents:
            raise ValueError("Agent not found")
        
        agent = agents[0]
        hyperparameters = hyperparameters or {
            'epochs': agent.total_epochs,
            'learning_rate': 0.001,
            'batch_size': 32,
            'optimizer': 'adam'
        }
        
        # Create training session
        session_id = self.trainer.create_training_session(
            agent_id, agent.dataset_id, hyperparameters
        )
        
        # Start training
        if self.trainer.start_training(session_id):
            return session_id
        else:
            raise RuntimeError("Failed to start training")

class AgentLabInterface:
    """Web interface for Agent Lab"""
    
    def __init__(self):
        self.manager = AgentManager()
    
    def generate_lab_interface(self) -> str:
        """Generate HTML interface for Agent Lab"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - Agent Lab</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .lab-container {
            display: grid;
            grid-template-columns: 320px 1fr;
            height: 100vh;
        }
        
        .sidebar {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            overflow-y: auto;
        }
        
        .sidebar h2 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
        }
        
        .sidebar h2::before {
            content: '🤖';
            margin-right: 10px;
            font-size: 1.8rem;
        }
        
        .agent-section {
            margin-bottom: 25px;
        }
        
        .section-header {
            color: #00d4ff;
            font-size: 1.1rem;
            margin-bottom: 15px;
            padding: 10px 0;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
        }
        
        .agent-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid transparent;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .agent-item:hover {
            background: rgba(0, 212, 255, 0.1);
            border-left-color: #00d4ff;
            transform: translateX(5px);
        }
        
        .agent-name {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .agent-type {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 8px;
        }
        
        .agent-status {
            font-size: 0.8rem;
            padding: 4px 8px;
            border-radius: 12px;
            display: inline-block;
        }
        
        .status-training {
            background: rgba(255, 165, 0, 0.2);
            color: #ffa500;
        }
        
        .status-completed {
            background: rgba(0, 255, 127, 0.2);
            color: #00ff7f;
        }
        
        .status-pending {
            background: rgba(128, 128, 128, 0.2);
            color: #808080;
        }
        
        .main-content {
            padding: 20px;
            overflow-y: auto;
        }
        
        .header {
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #00d4ff;
            font-size: 2.8rem;
            margin-bottom: 10px;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.2rem;
        }
        
        .agent-workspace {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .wireframe-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            position: relative;
            min-height: 400px;
        }
        
        .wireframe-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .wireframe-header h3 {
            color: #00d4ff;
            margin-bottom: 10px;
        }
        
        .wireframe-3d {
            position: relative;
            width: 100%;
            height: 300px;
            background: radial-gradient(circle at center, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .head-wireframe {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 150px;
            height: 180px;
        }
        
        .wireframe-line {
            position: absolute;
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            opacity: 0.8;
        }
        
        /* 3D Head wireframe lines */
        .line-1 { width: 100px; height: 2px; top: 20px; left: 25px; transform: skew(-10deg); }
        .line-2 { width: 2px; height: 80px; top: 20px; left: 25px; }
        .line-3 { width: 2px; height: 80px; top: 20px; right: 25px; }
        .line-4 { width: 100px; height: 2px; bottom: 80px; left: 25px; transform: skew(10deg); }
        .line-5 { width: 80px; height: 2px; top: 50px; left: 35px; }
        .line-6 { width: 60px; height: 2px; top: 70px; left: 45px; }
        .line-7 { width: 40px; height: 2px; top: 90px; left: 55px; }
        .line-8 { width: 2px; height: 40px; top: 40px; left: 50px; }
        .line-9 { width: 2px; height: 40px; top: 40px; right: 50px; }
        .line-10 { width: 20px; height: 2px; top: 60px; left: 40px; }
        .line-11 { width: 20px; height: 2px; top: 60px; right: 40px; }
        
        .neural-nodes {
            position: absolute;
            width: 100%;
            height: 100%;
        }
        
        .node {
            position: absolute;
            width: 8px;
            height: 8px;
            background: #00d4ff;
            border-radius: 50%;
            box-shadow: 0 0 10px #00d4ff;
        }
        
        .control-panel {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .control-section {
            margin-bottom: 25px;
        }
        
        .control-section h4 {
            color: #00d4ff;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.9rem;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(0, 0, 0, 0.3);
            color: #ffffff;
            font-size: 14px;
        }
        
        .training-metrics {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .epoch-progress {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            height: 8px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .epoch-bar {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #0099cc);
            transition: width 0.3s ease;
        }
        
        .epoch-text {
            text-align: center;
            margin-top: 10px;
            font-size: 1.2rem;
            font-weight: bold;
            color: #00d4ff;
        }
        
        .create-agent-btn {
            width: 100%;
            background: linear-gradient(45deg, #00d4ff, #0099cc);
            border: none;
            padding: 15px;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .create-agent-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
        }
        
        .datasets-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
        }
        
        .datasets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .dataset-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .dataset-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .dataset-name {
            color: #00d4ff;
            font-weight: 600;
        }
        
        .dataset-type {
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        
        .dataset-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        
        .dataset-stat {
            text-align: center;
        }
        
        .stat-value {
            font-weight: bold;
            color: #00d4ff;
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
        }
        
        @keyframes pulse-glow {
            0% { box-shadow: 0 0 5px #00d4ff; }
            50% { box-shadow: 0 0 20px #00d4ff, 0 0 30px #0099cc; }
            100% { box-shadow: 0 0 5px #00d4ff; }
        }
        
        .training-active {
            animation: pulse-glow 2s infinite;
        }
        
        @keyframes wireframe-animate {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }
        
        .wireframe-line {
            animation: wireframe-animate 3s infinite ease-in-out;
        }
        
        .floating-chart {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            height: 200px;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 10px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            padding: 15px;
            display: none;
        }
        
        .chart-header {
            color: #00d4ff;
            margin-bottom: 10px;
            font-size: 0.9rem;
        }
        
        .chart-area {
            height: 150px;
            background: linear-gradient(to top, rgba(0, 212, 255, 0.1) 0%, transparent 100%);
            border-radius: 5px;
            position: relative;
        }
    </style>
</head>
<body>
    <div class="lab-container">
        <div class="sidebar">
            <h2>Agent Lab</h2>
            
            <div class="agent-section">
                <div class="section-header">🤖 Active Agents</div>
                
                <div class="agent-item" onclick="selectAgent('agent_conv_001')">
                    <div class="agent-name">ConversaBot Pro</div>
                    <div class="agent-type">Conversational</div>
                    <div class="agent-status status-completed">Trained</div>
                </div>
                
                <div class="agent-item" onclick="selectAgent('agent_anal_001')">
                    <div class="agent-name">DataMind Analytics</div>
                    <div class="agent-type">Analytical</div>
                    <div class="agent-status status-training">Training</div>
                </div>
                
                <div class="agent-item" onclick="selectAgent('agent_creative_001')">
                    <div class="agent-name">CreativeGenius AI</div>
                    <div class="agent-type">Creative</div>
                    <div class="agent-status status-pending">Pending</div>
                </div>
            </div>
            
            <div class="agent-section">
                <div class="section-header">📊 Training Queue</div>
                
                <div style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.6);">
                    • DataMind Analytics - Epoch 25/50
                    <br>• CreativeGenius AI - Waiting
                    <br>• TaskBot v2 - Scheduled
                </div>
            </div>
            
            <div class="agent-section">
                <div class="section-header">🎯 Quick Actions</div>
                
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <button style="background: rgba(0, 212, 255, 0.2); border: 1px solid #00d4ff; color: white; padding: 8px; border-radius: 4px; cursor: pointer;">
                        Start Training
                    </button>
                    <button style="background: rgba(255, 165, 0, 0.2); border: 1px solid #ffa500; color: white; padding: 8px; border-radius: 4px; cursor: pointer;">
                        Pause Training
                    </button>
                    <button style="background: rgba(0, 255, 127, 0.2); border: 1px solid #00ff7f; color: white; padding: 8px; border-radius: 4px; cursor: pointer;">
                        Deploy Agent
                    </button>
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>AGENT LAB</h1>
                <div class="header-subtitle">AI agent creation interface with 3D wireframe visualization, datasets, and model training</div>
            </div>
            
            <div class="agent-workspace">
                <div class="wireframe-container">
                    <div class="wireframe-header">
                        <h3>3D Agent Visualization</h3>
                        <div style="color: rgba(255, 255, 255, 0.6);">Neural Architecture: Transformer</div>
                    </div>
                    
                    <div class="wireframe-3d">
                        <div class="head-wireframe">
                            <div class="wireframe-line line-1"></div>
                            <div class="wireframe-line line-2"></div>
                            <div class="wireframe-line line-3"></div>
                            <div class="wireframe-line line-4"></div>
                            <div class="wireframe-line line-5"></div>
                            <div class="wireframe-line line-6"></div>
                            <div class="wireframe-line line-7"></div>
                            <div class="wireframe-line line-8"></div>
                            <div class="wireframe-line line-9"></div>
                            <div class="wireframe-line line-10"></div>
                            <div class="wireframe-line line-11"></div>
                        </div>
                        
                        <div class="neural-nodes">
                            <div class="node" style="top: 20%; left: 20%;"></div>
                            <div class="node" style="top: 20%; right: 20%;"></div>
                            <div class="node" style="top: 40%; left: 30%;"></div>
                            <div class="node" style="top: 40%; right: 30%;"></div>
                            <div class="node" style="top: 60%; left: 25%;"></div>
                            <div class="node" style="top: 60%; right: 25%;"></div>
                            <div class="node" style="top: 80%; left: 35%;"></div>
                            <div class="node" style="top: 80%; right: 35%;"></div>
                        </div>
                    </div>
                </div>
                
                <div class="control-panel">
                    <div class="control-section">
                        <h4>🎯 Agent Configuration</h4>
                        
                        <div class="form-group">
                            <label>Agent Name</label>
                            <input type="text" placeholder="Enter agent name" value="ConversaBot Pro">
                        </div>
                        
                        <div class="form-group">
                            <label>Agent Type</label>
                            <select>
                                <option>Conversational</option>
                                <option>Analytical</option>
                                <option>Creative</option>
                                <option>Task Automation</option>
                                <option>Data Processing</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Model Architecture</label>
                            <select>
                                <option>Transformer</option>
                                <option>LSTM</option>
                                <option>CNN</option>
                                <option>Hybrid</option>
                                <option>Ensemble</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="control-section">
                        <h4>📊 Training Parameters</h4>
                        
                        <div class="training-metrics">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <div class="metric-value">94.7%</div>
                                    <div class="metric-label">Accuracy</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value">0.124</div>
                                    <div class="metric-label">Loss</div>
                                </div>
                            </div>
                            
                            <div class="epoch-progress">
                                <div class="epoch-bar" style="width: 75%"></div>
                            </div>
                            <div class="epoch-text">EPOCH 25/100</div>
                        </div>
                        
                        <div class="form-group">
                            <label>Learning Rate</label>
                            <input type="number" value="0.001" step="0.0001">
                        </div>
                        
                        <div class="form-group">
                            <label>Batch Size</label>
                            <input type="number" value="32">
                        </div>
                    </div>
                    
                    <button class="create-agent-btn" onclick="createAgent()">
                        CREATE AGENT
                    </button>
                </div>
            </div>
            
            <div class="datasets-section">
                <h3 style="color: #00d4ff; margin-bottom: 20px;">📊 AVAILABLE DATASETS</h3>
                
                <div class="datasets-grid">
                    <div class="dataset-card">
                        <div class="dataset-header">
                            <div class="dataset-name">Conversational Training Data</div>
                            <div class="dataset-type">Text</div>
                        </div>
                        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-bottom: 15px;">
                            Large-scale conversational AI training dataset with multi-turn dialogues
                        </div>
                        <div class="dataset-stats">
                            <div class="dataset-stat">
                                <div class="stat-value">50K</div>
                                <div class="stat-label">Samples</div>
                            </div>
                            <div class="dataset-stat">
                                <div class="stat-value">768</div>
                                <div class="stat-label">Features</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dataset-card">
                        <div class="dataset-header">
                            <div class="dataset-name">Business Analytics Dataset</div>
                            <div class="dataset-type">Tabular</div>
                        </div>
                        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-bottom: 15px;">
                            Time series and tabular data for business intelligence and forecasting
                        </div>
                        <div class="dataset-stats">
                            <div class="dataset-stat">
                                <div class="stat-value">25K</div>
                                <div class="stat-label">Samples</div>
                            </div>
                            <div class="dataset-stat">
                                <div class="stat-value">42</div>
                                <div class="stat-label">Features</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dataset-card">
                        <div class="dataset-header">
                            <div class="dataset-name">Creative Content Dataset</div>
                            <div class="dataset-type">Multimodal</div>
                        </div>
                        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-bottom: 15px;">
                            Multimodal dataset for creative content generation and style transfer
                        </div>
                        <div class="dataset-stats">
                            <div class="dataset-stat">
                                <div class="stat-value">15K</div>
                                <div class="stat-label">Samples</div>
                            </div>
                            <div class="dataset-stat">
                                <div class="stat-value">1024</div>
                                <div class="stat-label">Features</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="floating-chart" id="trainingChart">
        <div class="chart-header">📈 Training Progress</div>
        <div class="chart-area">
            <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 60%; background: linear-gradient(to right, #00d4ff, #0099cc); opacity: 0.3; border-radius: 3px;"></div>
        </div>
    </div>
    
    <script>
        let selectedAgent = null;
        let trainingActive = false;
        
        function selectAgent(agentId) {
            selectedAgent = agentId;
            
            // Update UI based on selected agent
            const agents = {
                'agent_conv_001': {
                    name: 'ConversaBot Pro',
                    accuracy: '94.7%',
                    loss: '0.124',
                    epoch: 75,
                    total: 100
                },
                'agent_anal_001': {
                    name: 'DataMind Analytics',
                    accuracy: '82.3%',
                    loss: '0.287',
                    epoch: 25,
                    total: 50
                },
                'agent_creative_001': {
                    name: 'CreativeGenius AI',
                    accuracy: '0.0%',
                    loss: '0.0',
                    epoch: 0,
                    total: 200
                }
            };
            
            const agent = agents[agentId];
            if (agent) {
                // Update metrics
                document.querySelector('.metric-value').textContent = agent.accuracy;
                document.querySelectorAll('.metric-value')[1].textContent = agent.loss;
                document.querySelector('.epoch-text').textContent = `EPOCH ${agent.epoch}/${agent.total}`;
                document.querySelector('.epoch-bar').style.width = `${(agent.epoch / agent.total) * 100}%`;
                
                // Update form
                document.querySelector('input[type="text"]').value = agent.name;
            }
            
            // Highlight selected agent
            document.querySelectorAll('.agent-item').forEach(item => {
                item.style.borderLeftColor = 'transparent';
            });
            event.target.closest('.agent-item').style.borderLeftColor = '#00d4ff';
            
            console.log(`Selected agent: ${agentId}`);
        }
        
        function createAgent() {
            const agentName = document.querySelector('input[type="text"]').value;
            const agentType = document.querySelector('select').value;
            const architecture = document.querySelectorAll('select')[1].value;
            
            if (!agentName.trim()) {
                alert('Please enter an agent name');
                return;
            }
            
            // Start creation animation
            const btn = document.querySelector('.create-agent-btn');
            btn.style.background = 'linear-gradient(45deg, #ffa500, #ff6b35)';
            btn.textContent = 'CREATING AGENT...';
            
            // Simulate agent creation
            setTimeout(() => {
                btn.style.background = 'linear-gradient(45deg, #00ff7f, #32cd32)';
                btn.textContent = 'AGENT CREATED!';
                
                setTimeout(() => {
                    btn.style.background = 'linear-gradient(45deg, #00d4ff, #0099cc)';
                    btn.textContent = 'CREATE AGENT';
                    
                    alert(`Agent "${agentName}" has been created successfully!\\n\\nType: ${agentType}\\nArchitecture: ${architecture}\\n\\nThe agent is now ready for training.`);
                }, 2000);
            }, 3000);
        }
        
        function startTraining() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            trainingActive = true;
            document.querySelector('.wireframe-container').classList.add('training-active');
            document.getElementById('trainingChart').style.display = 'block';
            
            // Simulate training progress
            let epoch = 0;
            const maxEpochs = 100;
            
            const trainingInterval = setInterval(() => {
                epoch++;
                const progress = (epoch / maxEpochs) * 100;
                const accuracy = Math.min(99, 60 + (epoch * 0.4) + Math.random() * 2);
                const loss = Math.max(0.01, 2.5 * Math.exp(-epoch * 0.05) + Math.random() * 0.1);
                
                // Update UI
                document.querySelector('.epoch-text').textContent = `EPOCH ${epoch}/${maxEpochs}`;
                document.querySelector('.epoch-bar').style.width = `${progress}%`;
                document.querySelector('.metric-value').textContent = `${accuracy.toFixed(1)}%`;
                document.querySelectorAll('.metric-value')[1].textContent = loss.toFixed(3);
                
                if (epoch >= maxEpochs) {
                    clearInterval(trainingInterval);
                    trainingActive = false;
                    document.querySelector('.wireframe-container').classList.remove('training-active');
                    alert('Training completed successfully!');
                }
            }, 200);
        }
        
        // Auto-update wireframe animation
        setInterval(() => {
            if (trainingActive) {
                document.querySelectorAll('.node').forEach((node, index) => {
                    const intensity = Math.random() * 0.5 + 0.5;
                    node.style.boxShadow = `0 0 ${intensity * 20}px #00d4ff`;
                });
            }
        }, 1000);
        
        // Initialize with first agent selected
        setTimeout(() => {
            document.querySelector('.agent-item').click();
        }, 500);
    </script>
</body>
</html>
        """

def main():
    """Demo of Agent Lab functionality"""
    print("MITO Engine - Agent Lab Demo")
    print("=" * 50)
    
    # Initialize Agent Lab
    manager = AgentManager()
    
    # Get all agents
    agents = manager.get_agents()
    print(f"Available agents: {len(agents)}")
    
    for agent in agents:
        print(f"  ✓ {agent.name} ({agent.agent_type}) - {agent.training_status}")
        print(f"    Accuracy: {agent.accuracy:.1%}, Epoch: {agent.current_epoch}/{agent.total_epochs}")
    
    # Get datasets
    datasets = manager.get_datasets()
    print(f"\nAvailable datasets: {len(datasets)}")
    
    for dataset in datasets:
        print(f"  📊 {dataset.name} - {dataset.size:,} samples, {dataset.features} features")
    
    # Start training for pending agent
    pending_agents = [a for a in agents if a.training_status == TrainingStatus.PENDING.value]
    if pending_agents:
        agent = pending_agents[0]
        print(f"\nStarting training for: {agent.name}")
        try:
            session_id = manager.start_training(agent.agent_id)
            print(f"Training session started: {session_id}")
        except Exception as e:
            print(f"Failed to start training: {e}")
    
    print("\nAgent Lab demo completed!")

if __name__ == "__main__":
    main()