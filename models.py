"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    tech_stack = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # JSON fields for complex data
    structure = db.Column(db.Text)  # JSON string
    files = db.Column(db.Text)      # JSON string
    deployment = db.Column(db.Text) # JSON string
    documentation = db.Column(db.Text) # JSON string
    ai_generated_code = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.project_type,
            'tech_stack': self.tech_stack,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'structure': json.loads(self.structure) if self.structure else [],
            'files': json.loads(self.files) if self.files else {},
            'deployment': json.loads(self.deployment) if self.deployment else {},
            'documentation': json.loads(self.documentation) if self.documentation else {},
            'ai_generated_code': self.ai_generated_code
        }
    
    @classmethod
    def from_dict(cls, data):
        project = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            project_type=data['type'],
            tech_stack=data['tech_stack'],
            structure=json.dumps(data.get('structure', [])),
            files=json.dumps(data.get('files', {})),
            deployment=json.dumps(data.get('deployment', {})),
            documentation=json.dumps(data.get('documentation', {})),
            ai_generated_code=data.get('ai_generated_code', '')
        )
        return project


class CodeGeneration(db.Model):
    __tablename__ = 'code_generations'
    
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    generated_code = db.Column(db.Text, nullable=False)
    file_structure = db.Column(db.Text)  # JSON string
    documentation = db.Column(db.Text)   # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'prompt': self.prompt,
            'language': self.language,
            'code': self.generated_code,
            'file_structure': json.loads(self.file_structure) if self.file_structure else [],
            'documentation': json.loads(self.documentation) if self.documentation else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Deployment(db.Model):
    __tablename__ = 'deployments'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    deployment_url = db.Column(db.String(500))
    cdn_url = db.Column(db.String(500))
    api_url = db.Column(db.String(500))
    database_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='deployed')
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    project = db.relationship('Project', backref=db.backref('deployments', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'deployment_url': self.deployment_url,
            'cdn_url': self.cdn_url,
            'api_url': self.api_url,
            'database_url': self.database_url,
            'status': self.status,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None
        }


class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'details': self.details,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }