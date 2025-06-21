#!/usr/bin/env python3
"""
Machine Learning Analytics Engine for MITO
Predictive analytics, anomaly detection, and personalized recommendations
"""

import os
import json
import sqlite3
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neural_network import MLPRegressor, MLPClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class MLModel:
    """Represents a trained ML model"""
    id: str
    name: str
    model_type: str
    algorithm: str
    features: List[str]
    target: str
    accuracy: float
    created_at: str
    model_path: str
    metadata: Dict[str, Any]

@dataclass
class Prediction:
    """Represents a prediction result"""
    model_id: str
    input_features: Dict[str, Any]
    prediction: Union[float, str, List]
    confidence: float
    timestamp: str
    explanation: Optional[str] = None

@dataclass
class Anomaly:
    """Represents an anomaly detection result"""
    id: str
    data_point: Dict[str, Any]
    anomaly_score: float
    severity: str
    detected_at: str
    context: Dict[str, Any]

class MLDatabase:
    """Database for ML models and results"""
    
    def __init__(self, db_path: str = "ml_analytics.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize ML database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                features TEXT NOT NULL,
                target TEXT,
                accuracy REAL,
                model_path TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                input_features TEXT NOT NULL,
                prediction TEXT NOT NULL,
                confidence REAL,
                explanation TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES ml_models (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                data_point TEXT NOT NULL,
                anomaly_score REAL NOT NULL,
                severity TEXT NOT NULL,
                context TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                outcome TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                score REAL NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicked BOOLEAN DEFAULT FALSE,
                feedback INTEGER
            )
        """)
        
        conn.commit()
        conn.close()

class PredictiveAnalytics:
    """Predictive analytics system"""
    
    def __init__(self, db: MLDatabase):
        self.db = db
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
    def train_regression_model(self, data: pd.DataFrame, target_column: str, 
                             features: List[str], model_name: str) -> MLModel:
        """Train a regression model"""
        try:
            # Prepare data
            X = data[features].copy()
            y = data[target_column]
            
            # Handle categorical variables
            categorical_features = X.select_dtypes(include=['object']).columns
            for col in categorical_features:
                encoder = LabelEncoder()
                X[col] = encoder.fit_transform(X[col].astype(str))
                self.encoders[f"{model_name}_{col}"] = encoder
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers[model_name] = scaler
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Try multiple algorithms
            algorithms = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression(),
                'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            }
            
            best_model = None
            best_score = -float('inf')
            best_algorithm = None
            
            for name, model in algorithms.items():
                # Train model
                model.fit(X_train, y_train)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                avg_score = cv_scores.mean()
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
                    best_algorithm = name
            
            # Save model
            model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = f"models/{model_id}.joblib"
            os.makedirs("models", exist_ok=True)
            
            joblib.dump({
                'model': best_model,
                'scaler': self.scalers[model_name],
                'encoders': {k: v for k, v in self.encoders.items() if k.startswith(model_name)}
            }, model_path)
            
            # Test accuracy
            test_predictions = best_model.predict(X_test)
            from sklearn.metrics import r2_score
            accuracy = r2_score(y_test, test_predictions)
            
            # Create ML model record
            ml_model = MLModel(
                id=model_id,
                name=model_name,
                model_type="regression",
                algorithm=best_algorithm,
                features=features,
                target=target_column,
                accuracy=accuracy,
                created_at=datetime.now().isoformat(),
                model_path=model_path,
                metadata={
                    'cv_score': best_score,
                    'test_r2': accuracy,
                    'feature_count': len(features),
                    'training_samples': len(X_train)
                }
            )
            
            # Store in database
            self._store_model(ml_model)
            self.models[model_id] = best_model
            
            logger.info(f"Trained regression model {model_name} with R² score: {accuracy:.4f}")
            return ml_model
            
        except Exception as e:
            logger.error(f"Failed to train regression model: {e}")
            raise
            
    def train_classification_model(self, data: pd.DataFrame, target_column: str,
                                 features: List[str], model_name: str) -> MLModel:
        """Train a classification model"""
        try:
            # Prepare data
            X = data[features].copy()
            y = data[target_column]
            
            # Handle categorical variables
            categorical_features = X.select_dtypes(include=['object']).columns
            for col in categorical_features:
                encoder = LabelEncoder()
                X[col] = encoder.fit_transform(X[col].astype(str))
                self.encoders[f"{model_name}_{col}"] = encoder
            
            # Encode target if categorical
            target_encoder = None
            if y.dtype == 'object':
                target_encoder = LabelEncoder()
                y = target_encoder.fit_transform(y)
                self.encoders[f"{model_name}_target"] = target_encoder
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers[model_name] = scaler
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Try multiple algorithms
            algorithms = {
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
                'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            }
            
            best_model = None
            best_score = -float('inf')
            best_algorithm = None
            
            for name, model in algorithms.items():
                # Train model
                model.fit(X_train, y_train)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                avg_score = cv_scores.mean()
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
                    best_algorithm = name
            
            # Save model
            model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = f"models/{model_id}.joblib"
            
            joblib.dump({
                'model': best_model,
                'scaler': self.scalers[model_name],
                'encoders': {k: v for k, v in self.encoders.items() if k.startswith(model_name)}
            }, model_path)
            
            # Test accuracy
            test_predictions = best_model.predict(X_test)
            accuracy = accuracy_score(y_test, test_predictions)
            
            # Create ML model record
            ml_model = MLModel(
                id=model_id,
                name=model_name,
                model_type="classification",
                algorithm=best_algorithm,
                features=features,
                target=target_column,
                accuracy=accuracy,
                created_at=datetime.now().isoformat(),
                model_path=model_path,
                metadata={
                    'cv_score': best_score,
                    'test_accuracy': accuracy,
                    'feature_count': len(features),
                    'training_samples': len(X_train),
                    'classes': len(np.unique(y))
                }
            )
            
            # Store in database
            self._store_model(ml_model)
            self.models[model_id] = best_model
            
            logger.info(f"Trained classification model {model_name} with accuracy: {accuracy:.4f}")
            return ml_model
            
        except Exception as e:
            logger.error(f"Failed to train classification model: {e}")
            raise
            
    def predict(self, model_id: str, input_data: Dict[str, Any]) -> Prediction:
        """Make prediction using trained model"""
        try:
            # Load model if not in memory
            if model_id not in self.models:
                self._load_model(model_id)
            
            # Get model info
            model_info = self._get_model_info(model_id)
            if not model_info:
                raise ValueError(f"Model {model_id} not found")
            
            # Prepare input data
            input_df = pd.DataFrame([input_data])
            
            # Apply same preprocessing
            for col in model_info['features']:
                if col in input_df.columns and f"{model_info['name']}_{col}" in self.encoders:
                    encoder = self.encoders[f"{model_info['name']}_{col}"]
                    input_df[col] = encoder.transform(input_df[col].astype(str))
            
            # Scale features
            if model_info['name'] in self.scalers:
                scaler = self.scalers[model_info['name']]
                input_scaled = scaler.transform(input_df[model_info['features']])
            else:
                input_scaled = input_df[model_info['features']].values
            
            # Make prediction
            model = self.models[model_id]
            prediction = model.predict(input_scaled)[0]
            
            # Calculate confidence
            confidence = 0.8  # Default confidence
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(input_scaled)[0]
                confidence = float(np.max(proba))
            elif hasattr(model, 'decision_function'):
                decision = model.decision_function(input_scaled)[0]
                confidence = float(1 / (1 + np.exp(-abs(decision))))
            
            # Create prediction record
            prediction_record = Prediction(
                model_id=model_id,
                input_features=input_data,
                prediction=float(prediction) if isinstance(prediction, (int, float)) else str(prediction),
                confidence=confidence,
                timestamp=datetime.now().isoformat()
            )
            
            # Store prediction
            self._store_prediction(prediction_record)
            
            return prediction_record
            
        except Exception as e:
            logger.error(f"Failed to make prediction: {e}")
            raise
            
    def _store_model(self, model: MLModel):
        """Store model in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ml_models 
            (id, name, model_type, algorithm, features, target, accuracy, model_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model.id, model.name, model.model_type, model.algorithm,
            json.dumps(model.features), model.target, model.accuracy,
            model.model_path, json.dumps(model.metadata)
        ))
        
        conn.commit()
        conn.close()
        
    def _store_prediction(self, prediction: Prediction):
        """Store prediction in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions 
            (model_id, input_features, prediction, confidence, explanation)
            VALUES (?, ?, ?, ?, ?)
        """, (
            prediction.model_id,
            json.dumps(prediction.input_features),
            json.dumps(prediction.prediction),
            prediction.confidence,
            prediction.explanation
        ))
        
        conn.commit()
        conn.close()
        
    def _get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information from database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ml_models WHERE id = ?", (model_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'model_type': result[2],
                'algorithm': result[3],
                'features': json.loads(result[4]),
                'target': result[5],
                'accuracy': result[6],
                'model_path': result[7],
                'metadata': json.loads(result[8]) if result[8] else {}
            }
        
        conn.close()
        return None
        
    def _load_model(self, model_id: str):
        """Load model from disk"""
        model_info = self._get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found")
        
        model_data = joblib.load(model_info['model_path'])
        self.models[model_id] = model_data['model']
        self.scalers[model_info['name']] = model_data['scaler']
        self.encoders.update(model_data['encoders'])

class AnomalyDetection:
    """Anomaly detection system"""
    
    def __init__(self, db: MLDatabase):
        self.db = db
        self.detectors = {}
        
    def train_anomaly_detector(self, data: pd.DataFrame, features: List[str], 
                             detector_name: str, contamination: float = 0.1) -> str:
        """Train anomaly detection model"""
        try:
            # Prepare data
            X = data[features].copy()
            
            # Handle categorical variables
            categorical_features = X.select_dtypes(include=['object']).columns
            encoders = {}
            for col in categorical_features:
                encoder = LabelEncoder()
                X[col] = encoder.fit_transform(X[col].astype(str))
                encoders[col] = encoder
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train Isolation Forest
            detector = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            detector.fit(X_scaled)
            
            # Save detector
            detector_id = f"{detector_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = f"models/{detector_id}_anomaly.joblib"
            
            joblib.dump({
                'detector': detector,
                'scaler': scaler,
                'encoders': encoders,
                'features': features
            }, model_path)
            
            self.detectors[detector_id] = {
                'detector': detector,
                'scaler': scaler,
                'encoders': encoders,
                'features': features
            }
            
            # Store model info
            ml_model = MLModel(
                id=detector_id,
                name=detector_name,
                model_type="anomaly_detection",
                algorithm="isolation_forest",
                features=features,
                target="anomaly_score",
                accuracy=1.0 - contamination,  # Expected normal rate
                created_at=datetime.now().isoformat(),
                model_path=model_path,
                metadata={
                    'contamination': contamination,
                    'feature_count': len(features),
                    'training_samples': len(X)
                }
            )
            
            self._store_model(ml_model)
            
            logger.info(f"Trained anomaly detector {detector_name}")
            return detector_id
            
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {e}")
            raise
            
    def detect_anomalies(self, detector_id: str, data: pd.DataFrame) -> List[Anomaly]:
        """Detect anomalies in data"""
        try:
            # Load detector if not in memory
            if detector_id not in self.detectors:
                self._load_detector(detector_id)
            
            detector_info = self.detectors[detector_id]
            
            # Prepare data
            X = data[detector_info['features']].copy()
            
            # Apply same preprocessing
            for col, encoder in detector_info['encoders'].items():
                if col in X.columns:
                    X[col] = encoder.transform(X[col].astype(str))
            
            # Scale features
            X_scaled = detector_info['scaler'].transform(X)
            
            # Detect anomalies
            anomaly_scores = detector_info['detector'].decision_function(X_scaled)
            predictions = detector_info['detector'].predict(X_scaled)
            
            anomalies = []
            for i, (score, prediction) in enumerate(zip(anomaly_scores, predictions)):
                if prediction == -1:  # Anomaly detected
                    severity = "high" if score < -0.5 else "medium" if score < -0.2 else "low"
                    
                    anomaly = Anomaly(
                        id=f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                        data_point=data.iloc[i].to_dict(),
                        anomaly_score=float(score),
                        severity=severity,
                        detected_at=datetime.now().isoformat(),
                        context={
                            'detector_id': detector_id,
                            'row_index': i,
                            'feature_values': X.iloc[i].to_dict()
                        }
                    )
                    
                    anomalies.append(anomaly)
                    self._store_anomaly(anomaly)
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            raise
            
    def _store_model(self, model: MLModel):
        """Store model in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ml_models 
            (id, name, model_type, algorithm, features, target, accuracy, model_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model.id, model.name, model.model_type, model.algorithm,
            json.dumps(model.features), model.target, model.accuracy,
            model.model_path, json.dumps(model.metadata)
        ))
        
        conn.commit()
        conn.close()
        
    def _store_anomaly(self, anomaly: Anomaly):
        """Store anomaly in database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO anomalies 
            (id, data_point, anomaly_score, severity, context)
            VALUES (?, ?, ?, ?, ?)
        """, (
            anomaly.id,
            json.dumps(anomaly.data_point),
            anomaly.anomaly_score,
            anomaly.severity,
            json.dumps(anomaly.context)
        ))
        
        conn.commit()
        conn.close()
        
    def _load_detector(self, detector_id: str):
        """Load detector from disk"""
        model_info = self._get_model_info(detector_id)
        if not model_info:
            raise ValueError(f"Detector {detector_id} not found")
        
        detector_data = joblib.load(model_info['model_path'])
        self.detectors[detector_id] = detector_data
        
    def _get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model information from database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ml_models WHERE id = ?", (model_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'model_type': result[2],
                'algorithm': result[3],
                'features': json.loads(result[4]),
                'target': result[5],
                'accuracy': result[6],
                'model_path': result[7],
                'metadata': json.loads(result[8]) if result[8] else {}
            }
        
        conn.close()
        return None

class RecommendationEngine:
    """Personalized recommendation system"""
    
    def __init__(self, db: MLDatabase):
        self.db = db
        self.user_profiles = {}
        
    def track_user_interaction(self, user_id: str, action: str, context: Dict[str, Any],
                             session_id: str = None, outcome: str = None):
        """Track user interaction for learning"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_interactions 
                (user_id, action, context, session_id, outcome)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, action, json.dumps(context), session_id, outcome))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to track user interaction: {e}")
            
    def generate_recommendations(self, user_id: str, recommendation_type: str,
                               count: int = 5) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        try:
            # Get user interaction history
            user_interactions = self._get_user_interactions(user_id, days=30)
            
            if not user_interactions:
                return self._get_default_recommendations(recommendation_type, count)
            
            # Analyze user patterns
            user_profile = self._build_user_profile(user_interactions)
            
            # Generate recommendations based on type
            if recommendation_type == "code_templates":
                return self._recommend_code_templates(user_profile, count)
            elif recommendation_type == "project_tools":
                return self._recommend_project_tools(user_profile, count)
            elif recommendation_type == "learning_resources":
                return self._recommend_learning_resources(user_profile, count)
            else:
                return self._get_default_recommendations(recommendation_type, count)
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []
            
    def _get_user_interactions(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user interaction history"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT action, context, outcome, timestamp 
            FROM user_interactions 
            WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        """.format(days), (user_id,))
        
        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                'action': row[0],
                'context': json.loads(row[1]) if row[1] else {},
                'outcome': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        return interactions
        
    def _build_user_profile(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build user profile from interactions"""
        profile = {
            'preferred_languages': {},
            'preferred_frameworks': {},
            'activity_patterns': {},
            'success_rate': 0.0,
            'expertise_level': 'beginner',
            'interests': {}
        }
        
        total_interactions = len(interactions)
        successful_interactions = 0
        
        for interaction in interactions:
            # Track programming languages
            context = interaction['context']
            if 'language' in context:
                lang = context['language']
                profile['preferred_languages'][lang] = profile['preferred_languages'].get(lang, 0) + 1
                
            # Track frameworks
            if 'framework' in context:
                framework = context['framework']
                profile['preferred_frameworks'][framework] = profile['preferred_frameworks'].get(framework, 0) + 1
                
            # Track activity types
            action = interaction['action']
            profile['activity_patterns'][action] = profile['activity_patterns'].get(action, 0) + 1
            
            # Track success rate
            if interaction['outcome'] in ['success', 'completed']:
                successful_interactions += 1
        
        # Calculate success rate
        if total_interactions > 0:
            profile['success_rate'] = successful_interactions / total_interactions
            
        # Determine expertise level
        if profile['success_rate'] > 0.8 and total_interactions > 20:
            profile['expertise_level'] = 'expert'
        elif profile['success_rate'] > 0.6 and total_interactions > 10:
            profile['expertise_level'] = 'intermediate'
        
        return profile
        
    def _recommend_code_templates(self, user_profile: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Recommend code templates based on user profile"""
        recommendations = []
        
        # Get preferred languages
        preferred_languages = sorted(user_profile['preferred_languages'].items(), 
                                   key=lambda x: x[1], reverse=True)
        
        template_suggestions = {
            'python': [
                {'name': 'Flask REST API', 'score': 0.9, 'reason': 'Popular web framework'},
                {'name': 'ML Pipeline', 'score': 0.8, 'reason': 'Data science workflow'},
                {'name': 'Python Class', 'score': 0.7, 'reason': 'OOP best practices'}
            ],
            'javascript': [
                {'name': 'React Component', 'score': 0.9, 'reason': 'Modern frontend development'},
                {'name': 'Node.js Express API', 'score': 0.8, 'reason': 'Backend development'},
                {'name': 'JavaScript Module', 'score': 0.7, 'reason': 'Modular code structure'}
            ],
            'docker': [
                {'name': 'Microservice Setup', 'score': 0.9, 'reason': 'Containerization best practices'},
                {'name': 'Multi-stage Dockerfile', 'score': 0.8, 'reason': 'Optimized builds'}
            ]
        }
        
        # Recommend based on preferred languages
        for lang, usage_count in preferred_languages[:3]:  # Top 3 languages
            if lang in template_suggestions:
                for template in template_suggestions[lang]:
                    template['language'] = lang
                    template['score'] *= (usage_count / max(user_profile['preferred_languages'].values()))
                    recommendations.append(template)
        
        # Add general recommendations if user is beginner
        if user_profile['expertise_level'] == 'beginner':
            recommendations.extend([
                {
                    'name': 'Basic Web Template',
                    'language': 'html',
                    'score': 0.6,
                    'reason': 'Good for learning web development'
                },
                {
                    'name': 'Simple Python Script',
                    'language': 'python',
                    'score': 0.5,
                    'reason': 'Great for beginners'
                }
            ])
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:count]
        
    def _recommend_project_tools(self, user_profile: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Recommend project management tools"""
        recommendations = []
        
        activity_patterns = user_profile['activity_patterns']
        
        # Analyze user's workflow patterns
        if activity_patterns.get('code_generation', 0) > 5:
            recommendations.append({
                'name': 'Advanced Code Generator',
                'type': 'development_tool',
                'score': 0.9,
                'reason': 'Frequently uses code generation'
            })
            
        if activity_patterns.get('project_management', 0) > 3:
            recommendations.append({
                'name': 'Jira Integration',
                'type': 'project_tool',
                'score': 0.8,
                'reason': 'Active in project management'
            })
            
        if user_profile['expertise_level'] == 'expert':
            recommendations.extend([
                {
                    'name': 'CI/CD Pipeline Setup',
                    'type': 'devops_tool',
                    'score': 0.9,
                    'reason': 'Expert-level automation'
                },
                {
                    'name': 'Security Audit Tools',
                    'type': 'security_tool',
                    'score': 0.8,
                    'reason': 'Advanced security practices'
                }
            ])
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:count]
        
    def _recommend_learning_resources(self, user_profile: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Recommend learning resources"""
        recommendations = []
        
        expertise_level = user_profile['expertise_level']
        preferred_languages = user_profile['preferred_languages']
        
        if expertise_level == 'beginner':
            recommendations.extend([
                {
                    'name': 'Python Fundamentals',
                    'type': 'course',
                    'score': 0.9,
                    'reason': 'Essential programming skills'
                },
                {
                    'name': 'Web Development Basics',
                    'type': 'tutorial',
                    'score': 0.8,
                    'reason': 'Modern web technologies'
                }
            ])
        elif expertise_level == 'intermediate':
            recommendations.extend([
                {
                    'name': 'Advanced Design Patterns',
                    'type': 'course',
                    'score': 0.9,
                    'reason': 'Level up architecture skills'
                },
                {
                    'name': 'DevOps Best Practices',
                    'type': 'guide',
                    'score': 0.8,
                    'reason': 'Production deployment skills'
                }
            ])
        else:  # expert
            recommendations.extend([
                {
                    'name': 'System Architecture Mastery',
                    'type': 'advanced_course',
                    'score': 0.9,
                    'reason': 'Expert-level system design'
                },
                {
                    'name': 'ML Engineering Practices',
                    'type': 'specialization',
                    'score': 0.8,
                    'reason': 'Cutting-edge AI development'
                }
            ])
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:count]
        
    def _get_default_recommendations(self, recommendation_type: str, count: int) -> List[Dict[str, Any]]:
        """Get default recommendations for new users"""
        defaults = {
            'code_templates': [
                {'name': 'Python Script Template', 'score': 0.8, 'reason': 'Popular starting point'},
                {'name': 'Web API Template', 'score': 0.7, 'reason': 'Common project type'},
                {'name': 'Docker Setup', 'score': 0.6, 'reason': 'Modern deployment'}
            ],
            'project_tools': [
                {'name': 'Project Organizer', 'score': 0.8, 'reason': 'Essential for productivity'},
                {'name': 'Code Quality Tools', 'score': 0.7, 'reason': 'Maintain high standards'},
                {'name': 'Documentation Generator', 'score': 0.6, 'reason': 'Good practices'}
            ],
            'learning_resources': [
                {'name': 'Getting Started Guide', 'score': 0.9, 'reason': 'Perfect for new users'},
                {'name': 'Best Practices Tutorial', 'score': 0.8, 'reason': 'Learn the right way'},
                {'name': 'Community Examples', 'score': 0.7, 'reason': 'Learn from others'}
            ]
        }
        
        return defaults.get(recommendation_type, [])[:count]

class MLAnalyticsEngine:
    """Main ML analytics engine"""
    
    def __init__(self):
        self.db = MLDatabase()
        self.predictive_analytics = PredictiveAnalytics(self.db)
        self.anomaly_detection = AnomalyDetection(self.db)
        self.recommendation_engine = RecommendationEngine(self.db)
        
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Model statistics
            cursor.execute("SELECT model_type, COUNT(*) FROM ml_models GROUP BY model_type")
            model_stats = dict(cursor.fetchall())
            
            # Recent predictions
            cursor.execute("""
                SELECT COUNT(*) FROM predictions 
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            recent_predictions = cursor.fetchone()[0]
            
            # Anomaly statistics
            cursor.execute("""
                SELECT severity, COUNT(*) FROM anomalies 
                WHERE detected_at >= datetime('now', '-7 days')
                GROUP BY severity
            """)
            anomaly_stats = dict(cursor.fetchall())
            
            # User engagement
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) FROM user_interactions 
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            active_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'model_statistics': model_stats,
                'recent_predictions': recent_predictions,
                'anomaly_statistics': anomaly_stats,
                'active_users': active_users,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate analytics dashboard: {e}")
            return {}

def main():
    """Demo of ML analytics capabilities"""
    print("ML Analytics Engine Demo")
    print("=" * 30)
    
    # Initialize engine
    ml_engine = MLAnalyticsEngine()
    
    # Create sample data for demonstration
    np.random.seed(42)
    
    # Sample data for regression (predicting project completion time)
    project_data = pd.DataFrame({
        'team_size': np.random.randint(2, 10, 100),
        'complexity_score': np.random.uniform(1, 10, 100),
        'experience_level': np.random.choice(['junior', 'mid', 'senior'], 100),
        'technology_stack': np.random.choice(['python', 'javascript', 'java'], 100),
        'completion_time': np.random.uniform(1, 20, 100)  # weeks
    })
    
    print("\n1. Training Predictive Models:")
    
    # Train regression model
    try:
        regression_model = ml_engine.predictive_analytics.train_regression_model(
            data=project_data,
            target_column='completion_time',
            features=['team_size', 'complexity_score', 'experience_level', 'technology_stack'],
            model_name='project_completion_predictor'
        )
        print(f"   ✓ Regression model trained with R² score: {regression_model.accuracy:.4f}")
    except Exception as e:
        print(f"   ✗ Regression model training failed: {e}")
    
    # Sample data for classification (predicting project success)
    project_data['success'] = (project_data['completion_time'] <= 15).astype(int)
    
    try:
        classification_model = ml_engine.predictive_analytics.train_classification_model(
            data=project_data,
            target_column='success',
            features=['team_size', 'complexity_score', 'experience_level', 'technology_stack'],
            model_name='project_success_predictor'
        )
        print(f"   ✓ Classification model trained with accuracy: {classification_model.accuracy:.4f}")
    except Exception as e:
        print(f"   ✗ Classification model training failed: {e}")
    
    print("\n2. Anomaly Detection:")
    
    # Train anomaly detector
    try:
        anomaly_detector_id = ml_engine.anomaly_detection.train_anomaly_detector(
            data=project_data,
            features=['team_size', 'complexity_score', 'completion_time'],
            detector_name='project_anomaly_detector',
            contamination=0.1
        )
        print(f"   ✓ Anomaly detector trained: {anomaly_detector_id}")
        
        # Detect anomalies in sample data
        anomalies = ml_engine.anomaly_detection.detect_anomalies(
            detector_id=anomaly_detector_id,
            data=project_data.sample(20)
        )
        print(f"   ✓ Detected {len(anomalies)} anomalies in sample data")
        
    except Exception as e:
        print(f"   ✗ Anomaly detection failed: {e}")
    
    print("\n3. Recommendation System:")
    
    # Simulate user interactions
    user_id = "demo_user"
    ml_engine.recommendation_engine.track_user_interaction(
        user_id=user_id,
        action="code_generation",
        context={"language": "python", "framework": "flask"},
        outcome="success"
    )
    
    # Generate recommendations
    try:
        recommendations = ml_engine.recommendation_engine.generate_recommendations(
            user_id=user_id,
            recommendation_type="code_templates",
            count=3
        )
        print(f"   ✓ Generated {len(recommendations)} recommendations:")
        for rec in recommendations:
            print(f"     - {rec['name']} (score: {rec['score']:.2f})")
    except Exception as e:
        print(f"   ✗ Recommendation generation failed: {e}")
    
    print("\n4. Analytics Dashboard:")
    dashboard = ml_engine.get_analytics_dashboard()
    if dashboard:
        print(f"   Model Statistics: {dashboard.get('model_statistics', {})}")
        print(f"   Recent Predictions: {dashboard.get('recent_predictions', 0)}")
        print(f"   Active Users: {dashboard.get('active_users', 0)}")
    
    print("\nML Analytics Engine demo completed successfully!")

if __name__ == "__main__":
    main()