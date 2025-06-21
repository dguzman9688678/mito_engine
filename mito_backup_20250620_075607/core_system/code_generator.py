#!/usr/bin/env python3
"""
Advanced Code Generation Engine for MITO
Comprehensive templates, design patterns, and best practices implementation
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import re
import yaml
from dataclasses import dataclass, asdict
from jinja2 import Template, Environment, FileSystemLoader
import ast

logger = logging.getLogger(__name__)

@dataclass
class CodeTemplate:
    """Represents a code generation template"""
    name: str
    language: str
    category: str
    description: str
    template_content: str
    variables: List[Dict[str, str]]
    dependencies: List[str]
    tags: List[str]
    author: str = "MITO Engine"
    version: str = "1.0.0"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class GeneratedCode:
    """Represents generated code output"""
    template_name: str
    language: str
    code: str
    files: Dict[str, str]
    dependencies: List[str]
    instructions: str
    generated_at: str
    parameters: Dict[str, Any]

class TemplateDatabase:
    """Database for code templates and generation history"""
    
    def __init__(self, db_path: str = "code_templates.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize template database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                language TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                template_content TEXT NOT NULL,
                variables TEXT,
                dependencies TEXT,
                tags TEXT,
                author TEXT,
                version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                parameters TEXT,
                generated_files TEXT,
                user_id TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                user_id TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
    def save_template(self, template: CodeTemplate) -> bool:
        """Save a code template"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO templates 
                (name, language, category, description, template_content, 
                 variables, dependencies, tags, author, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.name, template.language, template.category,
                template.description, template.template_content,
                json.dumps(template.variables), json.dumps(template.dependencies),
                json.dumps(template.tags), template.author, template.version
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
            return False
            
    def get_template(self, name: str) -> Optional[CodeTemplate]:
        """Get a template by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM templates WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                return CodeTemplate(
                    name=result[1],
                    language=result[2],
                    category=result[3],
                    description=result[4],
                    template_content=result[5],
                    variables=json.loads(result[6]),
                    dependencies=json.loads(result[7]),
                    tags=json.loads(result[8]),
                    author=result[9],
                    version=result[10],
                    created_at=result[11]
                )
                
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get template {name}: {e}")
            return None
            
    def list_templates(self, language: str = None, category: str = None) -> List[Dict[str, Any]]:
        """List available templates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT name, language, category, description, tags, usage_count FROM templates"
            params = []
            
            conditions = []
            if language:
                conditions.append("language = ?")
                params.append(language)
            if category:
                conditions.append("category = ?")
                params.append(category)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY usage_count DESC, name"
            
            cursor.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                results.append({
                    'name': row[0],
                    'language': row[1],
                    'category': row[2],
                    'description': row[3],
                    'tags': json.loads(row[4]),
                    'usage_count': row[5]
                })
                
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

class CodeGenerator:
    """Main code generation engine"""
    
    def __init__(self):
        self.db = TemplateDatabase()
        self.jinja_env = Environment(loader=FileSystemLoader('.'))
        self.init_builtin_templates()
        
    def init_builtin_templates(self):
        """Initialize built-in code templates"""
        builtin_templates = [
            self._create_flask_api_template(),
            self._create_react_component_template(),
            self._create_python_class_template(),
            self._create_microservice_template(),
            self._create_database_model_template(),
            self._create_ml_pipeline_template(),
            self._create_docker_template(),
            self._create_terraform_template(),
            self._create_github_workflow_template(),
            self._create_test_suite_template()
        ]
        
        for template in builtin_templates:
            self.db.save_template(template)
            
        logger.info(f"Initialized {len(builtin_templates)} built-in templates")
        
    def _create_flask_api_template(self) -> CodeTemplate:
        """Create Flask API template"""
        template_content = """from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = '{{ database_url }}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '{{ secret_key }}'

db = SQLAlchemy(app)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class {{ model_name }}(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    {% for field in fields -%}
    {{ field.name }} = db.Column(db.{{ field.type }}, {{ field.constraints }})
    {% endfor -%}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            {% for field in fields -%}
            '{{ field.name }}': self.{{ field.name }},
            {% endfor -%}
            'created_at': self.created_at.isoformat()
        }

# Routes
@app.route('/api/{{ endpoint_prefix }}', methods=['GET'])
def get_{{ endpoint_prefix }}():
    try:
        items = {{ model_name }}.query.all()
        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        logger.error(f"Error fetching {{ endpoint_prefix }}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/{{ endpoint_prefix }}', methods=['POST'])
def create_{{ endpoint_prefix[:-1] }}():
    try:
        data = request.get_json()
        item = {{ model_name }}(
            {% for field in fields -%}
            {{ field.name }}=data.get('{{ field.name }}'),
            {% endfor -%}
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating {{ endpoint_prefix[:-1] }}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/{{ endpoint_prefix }}/<int:item_id>', methods=['GET'])
def get_{{ endpoint_prefix[:-1] }}(item_id):
    try:
        item = {{ model_name }}.query.get_or_404(item_id)
        return jsonify(item.to_dict())
    except Exception as e:
        logger.error(f"Error fetching {{ endpoint_prefix[:-1] }} {item_id}: {e}")
        return jsonify({'error': 'Not found'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug={{ debug_mode }})"""

        return CodeTemplate(
            name="flask_rest_api",
            language="python",
            category="web_framework",
            description="Complete Flask REST API with SQLAlchemy models and CRUD operations",
            template_content=template_content,
            variables=[
                {"name": "database_url", "type": "string", "description": "Database connection URL"},
                {"name": "secret_key", "type": "string", "description": "Flask secret key"},
                {"name": "model_name", "type": "string", "description": "Main model class name"},
                {"name": "endpoint_prefix", "type": "string", "description": "API endpoint prefix"},
                {"name": "fields", "type": "array", "description": "Model fields configuration"},
                {"name": "debug_mode", "type": "boolean", "description": "Enable debug mode"}
            ],
            dependencies=["flask", "flask-cors", "flask-sqlalchemy"],
            tags=["web", "api", "rest", "flask", "database"]
        )
        
    def _create_react_component_template(self) -> CodeTemplate:
        """Create React component template"""
        template_content = """import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
{% if use_styled_components -%}
import styled from 'styled-components';
{% endif -%}
{% if api_integration -%}
import axios from 'axios';
{% endif -%}

{% if use_styled_components -%}
const Container = styled.div`
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
`;

const Title = styled.h2`
  color: #333;
  margin-bottom: 16px;
`;
{% endif -%}

const {{ component_name }} = ({ {% for prop in props %}{{ prop.name }}{% if not loop.last %}, {% endif %}{% endfor %} }) => {
  {% for state in state_variables -%}
  const [{{ state.name }}, set{{ state.name|title }}] = useState({{ state.initial_value }});
  {% endfor -%}
  
  {% if api_integration -%}
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('{{ api_endpoint }}');
        setData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to load data');
      }
    };
    
    fetchData();
  }, []);
  {% endif -%}
  
  {% for method in methods -%}
  const {{ method.name }} = ({{ method.params }}) => {
    {{ method.body }}
  };
  
  {% endfor -%}
  
  return (
    {% if use_styled_components -%}
    <Container>
      <Title>{{ component_name }}</Title>
      {/* Component content */}
      {% for prop in props -%}
      <div>{{ prop.name }}: {{{ prop.name }}}</div>
      {% endfor -%}
    </Container>
    {% else -%}
    <div className="{{ css_class }}">
      <h2>{{ component_name }}</h2>
      {/* Component content */}
      {% for prop in props -%}
      <div>{{ prop.name }}: {{{ prop.name }}}</div>
      {% endfor -%}
    </div>
    {% endif -%}
  );
};

{{ component_name }}.propTypes = {
  {% for prop in props -%}
  {{ prop.name }}: PropTypes.{{ prop.type }}{% if prop.required %}.isRequired{% endif %},
  {% endfor -%}
};

{{ component_name }}.defaultProps = {
  {% for prop in props -%}
  {% if prop.default_value -%}
  {{ prop.name }}: {{ prop.default_value }},
  {% endif -%}
  {% endfor -%}
};

export default {{ component_name }};"""

        return CodeTemplate(
            name="react_component",
            language="javascript",
            category="frontend",
            description="Modern React functional component with hooks and best practices",
            template_content=template_content,
            variables=[
                {"name": "component_name", "type": "string", "description": "Component name (PascalCase)"},
                {"name": "props", "type": "array", "description": "Component props configuration"},
                {"name": "state_variables", "type": "array", "description": "State variables configuration"},
                {"name": "methods", "type": "array", "description": "Component methods"},
                {"name": "use_styled_components", "type": "boolean", "description": "Use styled-components"},
                {"name": "api_integration", "type": "boolean", "description": "Include API integration"},
                {"name": "api_endpoint", "type": "string", "description": "API endpoint URL"},
                {"name": "css_class", "type": "string", "description": "CSS class name"}
            ],
            dependencies=["react", "prop-types"],
            tags=["react", "component", "frontend", "javascript"]
        )
        
    def _create_python_class_template(self) -> CodeTemplate:
        """Create Python class template"""
        template_content = """#!/usr/bin/env python3
\"\"\"
{{ class_name }} - {{ description }}
{% if author -%}
Author: {{ author }}
{% endif -%}
Created: {{ created_date }}
\"\"\"

import logging
from typing import {{ type_imports }}
from datetime import datetime
{% for import in additional_imports -%}
{{ import }}
{% endfor %}

logger = logging.getLogger(__name__)

class {{ class_name }}{% if base_classes %}({{ base_classes|join(', ') }}){% endif %}:
    \"\"\"{{ description }}\"\"\"
    
    def __init__(self{% for param in constructor_params %}, {{ param.name }}: {{ param.type }}{% if param.default %} = {{ param.default }}{% endif %}{% endfor %}):
        \"\"\"Initialize {{ class_name }}
        
        Args:
        {% for param in constructor_params -%}
            {{ param.name }}: {{ param.description }}
        {% endfor -%}
        \"\"\"
        {% if base_classes -%}
        super().__init__()
        {% endif -%}
        {% for param in constructor_params -%}
        self.{{ param.name }} = {{ param.name }}
        {% endfor -%}
        {% for attr in instance_attributes -%}
        self.{{ attr.name }} = {{ attr.initial_value }}
        {% endfor -%}
        
        logger.info(f"{{ class_name }} initialized")
    
    {% for method in methods -%}
    def {{ method.name }}(self{% for param in method.params %}, {{ param.name }}: {{ param.type }}{% if param.default %} = {{ param.default }}{% endif %}{% endfor %}){% if method.return_type %} -> {{ method.return_type }}{% endif %}:
        \"\"\"{{ method.description }}
        
        Args:
        {% for param in method.params -%}
            {{ param.name }}: {{ param.description }}
        {% endfor -%}
        {% if method.return_type -%}
        
        Returns:
            {{ method.return_description }}
        {% endif -%}
        \"\"\"
        try:
            {{ method.body|indent(12) }}
        except Exception as e:
            logger.error(f"Error in {{ method.name }}: {e}")
            {% if method.error_handling -%}
            {{ method.error_handling|indent(12) }}
            {% else -%}
            raise
            {% endif -%}
    
    {% endfor -%}
    {% if include_repr -%}
    def __repr__(self) -> str:
        \"\"\"String representation of {{ class_name }}\"\"\"
        return f"{{ class_name }}({% for param in constructor_params %}{{ param.name }}={self.{{ param.name }}!r}{% if not loop.last %}, {% endif %}{% endfor %})"
    
    {% endif -%}
    {% if include_str -%}
    def __str__(self) -> str:
        \"\"\"Human-readable string representation\"\"\"
        return f"{{ class_name }}: {{ str_format }}"
    
    {% endif -%}
    {% if include_context_manager -%}
    def __enter__(self):
        \"\"\"Context manager entry\"\"\"
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        \"\"\"Context manager exit\"\"\"
        # Cleanup code here
        pass
    {% endif -%}

{% if include_factory -%}
class {{ class_name }}Factory:
    \"\"\"Factory for creating {{ class_name }} instances\"\"\"
    
    @staticmethod
    def create(config: Dict[str, Any]) -> {{ class_name }}:
        \"\"\"Create {{ class_name }} from configuration\"\"\"
        return {{ class_name }}(
            {% for param in constructor_params -%}
            {{ param.name }}=config.get('{{ param.name }}', {{ param.default or 'None' }}),
            {% endfor -%}
        )
{% endif -%}

def main():
    \"\"\"Example usage of {{ class_name }}\"\"\"
    # Example instantiation
    instance = {{ class_name }}(
        {% for param in constructor_params -%}
        {{ param.name }}={{ param.example_value or param.default or '...' }},
        {% endfor -%}
    )
    
    logger.info(f"Created: {instance}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()"""

        return CodeTemplate(
            name="python_class",
            language="python",
            category="oop",
            description="Comprehensive Python class with logging, type hints, and best practices",
            template_content=template_content,
            variables=[
                {"name": "class_name", "type": "string", "description": "Class name (PascalCase)"},
                {"name": "description", "type": "string", "description": "Class description"},
                {"name": "author", "type": "string", "description": "Author name"},
                {"name": "created_date", "type": "string", "description": "Creation date"},
                {"name": "base_classes", "type": "array", "description": "Base classes to inherit from"},
                {"name": "constructor_params", "type": "array", "description": "Constructor parameters"},
                {"name": "instance_attributes", "type": "array", "description": "Instance attributes"},
                {"name": "methods", "type": "array", "description": "Class methods"},
                {"name": "type_imports", "type": "string", "description": "Type imports needed"},
                {"name": "additional_imports", "type": "array", "description": "Additional imports"},
                {"name": "include_repr", "type": "boolean", "description": "Include __repr__ method"},
                {"name": "include_str", "type": "boolean", "description": "Include __str__ method"},
                {"name": "include_context_manager", "type": "boolean", "description": "Include context manager methods"},
                {"name": "include_factory", "type": "boolean", "description": "Include factory class"},
                {"name": "str_format", "type": "string", "description": "String format for __str__ method"}
            ],
            dependencies=[],
            tags=["python", "class", "oop", "best-practices"]
        )
        
    def _create_microservice_template(self) -> CodeTemplate:
        """Create microservice template"""
        template_content = """# {{ service_name }} Microservice
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE {{ port }}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{{ port }}/health || exit 1

CMD ["python", "app.py"]

---
# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
from datetime import datetime
import redis
from prometheus_client import Counter, Histogram, generate_latest
import time

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter('{{ service_name }}_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('{{ service_name }}_request_duration_seconds', 'Request latency')

# Redis connection
try:
    redis_client = redis.from_url(app.config['REDIS_URL'])
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.endpoint).inc()
    if hasattr(request, 'start_time'):
        REQUEST_LATENCY.observe(time.time() - request.start_time)
    return response

@app.route('/health', methods=['GET'])
def health_check():
    \"\"\"Health check endpoint\"\"\"
    health_status = {
        'service': '{{ service_name }}',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '{{ version }}'
    }
    
    # Check dependencies
    if redis_client:
        try:
            redis_client.ping()
            health_status['redis'] = 'connected'
        except:
            health_status['redis'] = 'disconnected'
            health_status['status'] = 'degraded'
    
    return jsonify(health_status)

@app.route('/metrics', methods=['GET'])
def metrics():
    \"\"\"Prometheus metrics endpoint\"\"\"
    return generate_latest()

{% for endpoint in endpoints -%}
@app.route('{{ endpoint.path }}', methods={{ endpoint.methods }})
def {{ endpoint.function_name }}({% if endpoint.path_params %}{{ endpoint.path_params|join(', ') }}{% endif %}):
    \"\"\"{{ endpoint.description }}\"\"\"
    try:
        {% if 'POST' in endpoint.methods or 'PUT' in endpoint.methods -%}
        data = request.get_json()
        {% endif -%}
        
        # Business logic here
        result = {
            'message': '{{ endpoint.description }}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(result), {{ endpoint.success_code }}
        
    except Exception as e:
        logger.error(f"Error in {{ endpoint.function_name }}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

{% endfor -%}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', {{ port }}))
    app.run(host='0.0.0.0', port=port, debug=False)

---
# requirements.txt
Flask==2.3.3
Flask-CORS==4.0.0
redis==4.6.0
prometheus-client==0.17.1
gunicorn==21.2.0

---
# docker-compose.yml
version: '3.8'

services:
  {{ service_name }}:
    build: .
    ports:
      - "{{ port }}:{{ port }}"
    environment:
      - SECRET_KEY={{ secret_key }}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

---
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: '{{ service_name }}'
    static_configs:
      - targets: ['{{ service_name }}:{{ port }}']"""

        return CodeTemplate(
            name="microservice",
            language="python",
            category="architecture",
            description="Complete microservice with Docker, monitoring, and health checks",
            template_content=template_content,
            variables=[
                {"name": "service_name", "type": "string", "description": "Microservice name"},
                {"name": "port", "type": "integer", "description": "Service port"},
                {"name": "version", "type": "string", "description": "Service version"},
                {"name": "secret_key", "type": "string", "description": "Secret key"},
                {"name": "endpoints", "type": "array", "description": "API endpoints configuration"}
            ],
            dependencies=["flask", "redis", "prometheus-client"],
            tags=["microservice", "docker", "monitoring", "api"]
        )
        
    def _create_database_model_template(self) -> CodeTemplate:
        """Create database model template"""
        template_content = """from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import json

Base = declarative_base()

{% if many_to_many_tables -%}
# Many-to-many association tables
{% for table in many_to_many_tables -%}
{{ table.name }} = Table(
    '{{ table.name }}',
    Base.metadata,
    Column('{{ table.left_column }}', Integer, ForeignKey('{{ table.left_table }}.id')),
    Column('{{ table.right_column }}', Integer, ForeignKey('{{ table.right_table }}.id'))
)

{% endfor -%}
{% endif -%}

class {{ model_name }}(Base):
    \"\"\"{{ description }}\"\"\"
    __tablename__ = '{{ table_name }}'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Fields
    {% for field in fields -%}
    {% if field.type == 'string' -%}
    {{ field.name }} = Column(String({{ field.length or 255 }}){% if field.nullable == false %}, nullable=False{% endif %}{% if field.unique %}, unique=True{% endif %})
    {% elif field.type == 'text' -%}
    {{ field.name }} = Column(Text{% if field.nullable == false %}, nullable=False{% endif %})
    {% elif field.type == 'integer' -%}
    {{ field.name }} = Column(Integer{% if field.nullable == false %}, nullable=False{% endif %})
    {% elif field.type == 'boolean' -%}
    {{ field.name }} = Column(Boolean, default={{ field.default or 'False' }}{% if field.nullable == false %}, nullable=False{% endif %})
    {% elif field.type == 'datetime' -%}
    {{ field.name }} = Column(DateTime{% if field.default == 'now' %}, default=datetime.utcnow{% endif %}{% if field.nullable == false %}, nullable=False{% endif %})
    {% endif -%}
    {% endfor -%}
    
    # Relationships
    {% for rel in relationships -%}
    {% if rel.type == 'one_to_many' -%}
    {{ rel.name }} = relationship("{{ rel.related_model }}", back_populates="{{ rel.back_populates }}")
    {% elif rel.type == 'many_to_one' -%}
    {{ rel.foreign_key_field }} = Column(Integer, ForeignKey('{{ rel.related_table }}.id'))
    {{ rel.name }} = relationship("{{ rel.related_model }}", back_populates="{{ rel.back_populates }}")
    {% elif rel.type == 'many_to_many' -%}
    {{ rel.name }} = relationship("{{ rel.related_model }}", secondary={{ rel.association_table }}, back_populates="{{ rel.back_populates }}")
    {% endif -%}
    {% endfor -%}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        \"\"\"Initialize {{ model_name }}\"\"\"
        {% for field in fields -%}
        self.{{ field.name }} = kwargs.get('{{ field.name }}')
        {% endfor -%}
    
    def to_dict(self, include_relationships=False):
        \"\"\"Convert model to dictionary\"\"\"
        result = {
            'id': self.id,
            {% for field in fields -%}
            '{{ field.name }}': self.{{ field.name }},
            {% endfor -%}
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relationships:
            {% for rel in relationships -%}
            if hasattr(self, '{{ rel.name }}') and self.{{ rel.name }}:
                {% if rel.type == 'one_to_many' or rel.type == 'many_to_many' -%}
                result['{{ rel.name }}'] = [item.to_dict() for item in self.{{ rel.name }}]
                {% else -%}
                result['{{ rel.name }}'] = self.{{ rel.name }}.to_dict()
                {% endif -%}
            {% endfor -%}
        
        return result
    
    def update(self, **kwargs):
        \"\"\"Update model attributes\"\"\"
        {% for field in fields -%}
        if '{{ field.name }}' in kwargs:
            self.{{ field.name }} = kwargs['{{ field.name }}']
        {% endfor -%}
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<{{ model_name }}(id={self.id}{% for field in fields[:2] %}, {{ field.name }}={self.{{ field.name }}!r}{% endfor %})>"

class {{ model_name }}Repository:
    \"\"\"Repository pattern for {{ model_name }}\"\"\"
    
    def __init__(self, session):
        self.session = session
    
    def create(self, **kwargs) -> {{ model_name }}:
        \"\"\"Create new {{ model_name }}\"\"\"
        instance = {{ model_name }}(**kwargs)
        self.session.add(instance)
        self.session.commit()
        return instance
    
    def get_by_id(self, id: int) -> {{ model_name }}:
        \"\"\"Get {{ model_name }} by ID\"\"\"
        return self.session.query({{ model_name }}).filter({{ model_name }}.id == id).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[{{ model_name }}]:
        \"\"\"Get all {{ model_name }} records\"\"\"
        return self.session.query({{ model_name }}).offset(offset).limit(limit).all()
    
    def update(self, id: int, **kwargs) -> {{ model_name }}:
        \"\"\"Update {{ model_name }}\"\"\"
        instance = self.get_by_id(id)
        if instance:
            instance.update(**kwargs)
            self.session.commit()
        return instance
    
    def delete(self, id: int) -> bool:
        \"\"\"Delete {{ model_name }}\"\"\"
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False
    
    {% for field in fields -%}
    {% if field.indexed or field.unique -%}
    def get_by_{{ field.name }}(self, {{ field.name }}) -> {{ model_name }}:
        \"\"\"Get {{ model_name }} by {{ field.name }}\"\"\"
        return self.session.query({{ model_name }}).filter({{ model_name }}.{{ field.name }} == {{ field.name }}).first()
    
    {% endif -%}
    {% endfor -%}

# Database setup
def create_database_engine(database_url: str):
    \"\"\"Create database engine\"\"\"
    engine = create_engine(database_url, echo={{ debug_mode }})
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    \"\"\"Get database session\"\"\"
    Session = sessionmaker(bind=engine)
    return Session()"""

        return CodeTemplate(
            name="database_model",
            language="python",
            category="database",
            description="SQLAlchemy model with repository pattern and relationships",
            template_content=template_content,
            variables=[
                {"name": "model_name", "type": "string", "description": "Model class name"},
                {"name": "table_name", "type": "string", "description": "Database table name"},
                {"name": "description", "type": "string", "description": "Model description"},
                {"name": "fields", "type": "array", "description": "Model fields configuration"},
                {"name": "relationships", "type": "array", "description": "Model relationships"},
                {"name": "many_to_many_tables", "type": "array", "description": "Many-to-many association tables"},
                {"name": "debug_mode", "type": "boolean", "description": "Enable SQLAlchemy debug mode"}
            ],
            dependencies=["sqlalchemy"],
            tags=["database", "sqlalchemy", "orm", "repository"]
        )
        
    def _create_ml_pipeline_template(self) -> CodeTemplate:
        """Create ML pipeline template"""
        template_content = """#!/usr/bin/env python3
\"\"\"
{{ pipeline_name }} - Machine Learning Pipeline
{{ description }}
\"\"\"

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import {{ metrics|join(', ') }}
{% for model in models -%}
from sklearn.{{ model.module }} import {{ model.class_name }}
{% endfor -%}
import joblib
import logging
from datetime import datetime
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {{ pipeline_name }}Pipeline:
    \"\"\"{{ description }}\"\"\"
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        self.target_name = '{{ target_column }}'
        
    def load_data(self, data_path: str) -> pd.DataFrame:
        \"\"\"Load and validate data\"\"\"
        logger.info(f"Loading data from {data_path}")
        
        if data_path.endswith('.csv'):
            data = pd.read_csv(data_path)
        elif data_path.endswith('.json'):
            data = pd.read_json(data_path)
        elif data_path.endswith('.parquet'):
            data = pd.read_parquet(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path}")
        
        logger.info(f"Loaded {len(data)} rows, {len(data.columns)} columns")
        return data
    
    def preprocess_data(self, data: pd.DataFrame) -> tuple:
        \"\"\"Preprocess data for training\"\"\"
        logger.info("Preprocessing data")
        
        # Handle missing values
        {% if missing_value_strategy == 'drop' -%}
        data = data.dropna()
        {% elif missing_value_strategy == 'fill_mean' -%}
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].mean())
        {% elif missing_value_strategy == 'fill_median' -%}
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data[numeric_columns] = data[numeric_columns].fillna(data[numeric_columns].median())
        {% endif -%}
        
        # Separate features and target
        X = data.drop(columns=[self.target_name])
        y = data[self.target_name]
        
        # Encode categorical variables
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            encoder = LabelEncoder()
            X[col] = encoder.fit_transform(X[col].astype(str))
            self.encoders[col] = encoder
        
        # Scale numerical features
        {% if scaling_method == 'standard' -%}
        scaler = StandardScaler()
        {% elif scaling_method == 'minmax' -%}
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        {% elif scaling_method == 'robust' -%}
        from sklearn.preprocessing import RobustScaler
        scaler = RobustScaler()
        {% endif -%}
        
        {% if scaling_method != 'none' -%}
        X_scaled = scaler.fit_transform(X)
        X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        self.scalers['features'] = scaler
        {% endif -%}
        
        self.feature_names = X.columns.tolist()
        logger.info(f"Preprocessed {len(X)} samples, {len(X.columns)} features")
        
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series) -> dict:
        \"\"\"Train multiple models and compare performance\"\"\"
        logger.info("Training models")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size={{ test_size }}, random_state=42, stratify=y
        )
        
        models_config = {
            {% for model in models -%}
            '{{ model.name }}': {{ model.class_name }}({{ model.params }}),
            {% endfor -%}
        }
        
        results = {}
        
        for name, model in models_config.items():
            logger.info(f"Training {name}")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = {}
            {% if problem_type == 'classification' -%}
            metrics['accuracy'] = accuracy_score(y_test, y_pred)
            metrics['precision'] = precision_score(y_test, y_pred, average='weighted')
            metrics['recall'] = recall_score(y_test, y_pred, average='weighted')
            metrics['f1'] = f1_score(y_test, y_pred, average='weighted')
            {% elif problem_type == 'regression' -%}
            metrics['mse'] = mean_squared_error(y_test, y_pred)
            metrics['mae'] = mean_absolute_error(y_test, y_pred)
            metrics['r2'] = r2_score(y_test, y_pred)
            {% endif -%}
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            metrics['cv_mean'] = cv_scores.mean()
            metrics['cv_std'] = cv_scores.std()
            
            results[name] = {
                'model': model,
                'metrics': metrics,
                'predictions': y_pred
            }
            
            logger.info(f"{name} - CV Score: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std'] * 2:.4f})")
        
        # Select best model
        {% if problem_type == 'classification' -%}
        best_model_name = max(results.keys(), key=lambda x: results[x]['metrics']['accuracy'])
        {% elif problem_type == 'regression' -%}
        best_model_name = min(results.keys(), key=lambda x: results[x]['metrics']['mse'])
        {% endif -%}
        
        self.models['best'] = results[best_model_name]['model']
        self.models['all'] = {name: result['model'] for name, result in results.items()}
        
        logger.info(f"Best model: {best_model_name}")
        
        return results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        \"\"\"Make predictions using the best model\"\"\"
        if 'best' not in self.models:
            raise ValueError("No trained model available. Train the pipeline first.")
        
        # Apply same preprocessing
        X_processed = X.copy()
        
        # Encode categorical variables
        for col, encoder in self.encoders.items():
            if col in X_processed.columns:
                X_processed[col] = encoder.transform(X_processed[col].astype(str))
        
        # Scale features
        if 'features' in self.scalers:
            X_processed = pd.DataFrame(
                self.scalers['features'].transform(X_processed),
                columns=X_processed.columns,
                index=X_processed.index
            )
        
        return self.models['best'].predict(X_processed)
    
    def save_pipeline(self, path: str):
        \"\"\"Save the trained pipeline\"\"\"
        pipeline_data = {
            'models': self.models,
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'config': self.config,
            'saved_at': datetime.now().isoformat()
        }
        
        joblib.dump(pipeline_data, path)
        logger.info(f"Pipeline saved to {path}")
    
    def load_pipeline(self, path: str):
        \"\"\"Load a saved pipeline\"\"\"
        pipeline_data = joblib.load(path)
        
        self.models = pipeline_data['models']
        self.scalers = pipeline_data['scalers']
        self.encoders = pipeline_data['encoders']
        self.feature_names = pipeline_data['feature_names']
        self.target_name = pipeline_data['target_name']
        self.config = pipeline_data['config']
        
        logger.info(f"Pipeline loaded from {path}")

def main():
    \"\"\"Example usage\"\"\"
    # Initialize pipeline
    pipeline = {{ pipeline_name }}Pipeline()
    
    # Load and preprocess data
    data = pipeline.load_data('{{ data_path }}')
    X, y = pipeline.preprocess_data(data)
    
    # Train models
    results = pipeline.train_models(X, y)
    
    # Print results
    for name, result in results.items():
        print(f"\\n{name} Results:")
        for metric, value in result['metrics'].items():
            print(f"  {metric}: {value:.4f}")
    
    # Save pipeline
    pipeline.save_pipeline('{{ pipeline_name }}_pipeline.joblib')

if __name__ == "__main__":
    main()"""

        return CodeTemplate(
            name="ml_pipeline",
            language="python",
            category="machine_learning",
            description="Complete ML pipeline with preprocessing, training, and evaluation",
            template_content=template_content,
            variables=[
                {"name": "pipeline_name", "type": "string", "description": "Pipeline class name"},
                {"name": "description", "type": "string", "description": "Pipeline description"},
                {"name": "target_column", "type": "string", "description": "Target column name"},
                {"name": "problem_type", "type": "string", "description": "classification or regression"},
                {"name": "models", "type": "array", "description": "Models to train and compare"},
                {"name": "metrics", "type": "array", "description": "Evaluation metrics"},
                {"name": "test_size", "type": "float", "description": "Test set size (0-1)"},
                {"name": "missing_value_strategy", "type": "string", "description": "How to handle missing values"},
                {"name": "scaling_method", "type": "string", "description": "Feature scaling method"},
                {"name": "data_path", "type": "string", "description": "Path to training data"}
            ],
            dependencies=["scikit-learn", "pandas", "numpy", "joblib"],
            tags=["machine-learning", "pipeline", "scikit-learn"]
        )
        
    def _create_docker_template(self) -> CodeTemplate:
        """Create Docker template"""
        template_content = """# Multi-stage Dockerfile for {{ app_name }}
# Stage 1: Build stage
FROM {{ base_image }} AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
{% if language == 'python' -%}
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
{% elif language == 'node' -%}
COPY package*.json ./
RUN npm ci --only=production
{% elif language == 'go' -%}
COPY go.mod go.sum ./
RUN go mod download
{% endif -%}

# Stage 2: Runtime stage
FROM {{ runtime_image }}

# Create app user
RUN addgroup --system --gid 1001 {{ app_name }} && \\
    adduser --system --uid 1001 --gid 1001 {{ app_name }}

# Set working directory
WORKDIR /app

# Copy dependencies from builder stage
{% if language == 'python' -%}
COPY --from=builder /root/.local /home/{{ app_name }}/.local
ENV PATH=/home/{{ app_name }}/.local/bin:$PATH
{% elif language == 'node' -%}
COPY --from=builder /app/node_modules ./node_modules
{% endif -%}

# Copy application code
COPY --chown={{ app_name }}:{{ app_name }} . .

# Set environment variables
ENV NODE_ENV=production
ENV PORT={{ port }}
{% for env_var in environment_variables -%}
ENV {{ env_var.name }}={{ env_var.default_value }}
{% endfor -%}

# Create necessary directories
{% for dir in directories -%}
RUN mkdir -p {{ dir }} && chown {{ app_name }}:{{ app_name }} {{ dir }}
{% endfor -%}

# Switch to non-root user
USER {{ app_name }}

# Expose port
EXPOSE {{ port }}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD {{ health_check_command }}

# Start command
{% if language == 'python' -%}
CMD ["python", "{{ entry_point }}"]
{% elif language == 'node' -%}
CMD ["node", "{{ entry_point }}"]
{% elif language == 'go' -%}
CMD ["./{{ entry_point }}"]
{% else -%}
CMD {{ start_command }}
{% endif -%}

---
# docker-compose.yml
version: '3.8'

services:
  {{ app_name }}:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "{{ port }}:{{ port }}"
    environment:
      {% for env_var in environment_variables -%}
      - {{ env_var.name }}={{ env_var.value }}
      {% endfor -%}
    volumes:
      {% for volume in volumes -%}
      - {{ volume.host_path }}:{{ volume.container_path }}{% if volume.read_only %}:ro{% endif %}
      {% endfor -%}
    {% if dependencies -%}
    depends_on:
      {% for dep in dependencies -%}
      - {{ dep }}
      {% endfor -%}
    {% endif -%}
    restart: unless-stopped
    networks:
      - {{ app_name }}_network

  {% if include_database -%}
  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB={{ database_name }}
      - POSTGRES_USER={{ database_user }}
      - POSTGRES_PASSWORD={{ database_password }}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - {{ app_name }}_network
    restart: unless-stopped
  {% endif -%}

  {% if include_redis -%}
  redis:
    image: redis:7-alpine
    networks:
      - {{ app_name }}_network
    restart: unless-stopped
  {% endif -%}

networks:
  {{ app_name }}_network:
    driver: bridge

{% if include_database -%}
volumes:
  postgres_data:
{% endif -%}

---
# .dockerignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.pytest_cache
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.idea
.vscode
.DS_Store
Thumbs.db"""

        return CodeTemplate(
            name="docker_setup",
            language="dockerfile",
            category="containerization",
            description="Multi-stage Docker setup with security best practices",
            template_content=template_content,
            variables=[
                {"name": "app_name", "type": "string", "description": "Application name"},
                {"name": "language", "type": "string", "description": "Programming language"},
                {"name": "base_image", "type": "string", "description": "Base Docker image"},
                {"name": "runtime_image", "type": "string", "description": "Runtime Docker image"},
                {"name": "port", "type": "integer", "description": "Application port"},
                {"name": "entry_point", "type": "string", "description": "Application entry point"},
                {"name": "environment_variables", "type": "array", "description": "Environment variables"},
                {"name": "volumes", "type": "array", "description": "Volume mounts"},
                {"name": "dependencies", "type": "array", "description": "Service dependencies"},
                {"name": "directories", "type": "array", "description": "Directories to create"},
                {"name": "health_check_command", "type": "string", "description": "Health check command"},
                {"name": "include_database", "type": "boolean", "description": "Include PostgreSQL"},
                {"name": "include_redis", "type": "boolean", "description": "Include Redis"},
                {"name": "database_name", "type": "string", "description": "Database name"},
                {"name": "database_user", "type": "string", "description": "Database user"},
                {"name": "database_password", "type": "string", "description": "Database password"}
            ],
            dependencies=[],
            tags=["docker", "containerization", "deployment"]
        )
        
    def _create_terraform_template(self) -> CodeTemplate:
        """Create Terraform infrastructure template"""
        template_content = """# {{ project_name }} Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  {% if use_remote_state -%}
  backend "s3" {
    bucket = "{{ state_bucket }}"
    key    = "{{ project_name }}/terraform.tfstate"
    region = "{{ aws_region }}"
  }
  {% endif -%}
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "{{ project_name }}"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "{{ aws_region }}"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "{{ environment }}"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

{% for var in custom_variables -%}
variable "{{ var.name }}" {
  description = "{{ var.description }}"
  type        = {{ var.type }}
  {% if var.default -%}
  default     = {{ var.default }}
  {% endif -%}
}

{% endfor -%}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "{{ project_name }}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "{{ project_name }}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = {{ public_subnet_count }}
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "{{ project_name }}-public-${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = {{ private_subnet_count }}
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "{{ project_name }}-private-${count.index + 1}"
    Type = "Private"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "{{ project_name }}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Groups
resource "aws_security_group" "web" {
  name_prefix = "{{ project_name }}-web-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "{{ project_name }}-web-sg"
  }
}

{% if include_alb -%}
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "{{ project_name }}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = false
  
  tags = {
    Name = "{{ project_name }}-alb"
  }
}

resource "aws_lb_target_group" "main" {
  name     = "{{ project_name }}-tg"
  port     = {{ app_port }}
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "{{ project_name }}-tg"
  }
}

resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}
{% endif -%}

{% if include_rds -%}
# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "{{ project_name }}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "{{ project_name }}-db-subnet-group"
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "{{ project_name }}-rds-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  tags = {
    Name = "{{ project_name }}-rds-sg"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = "{{ project_name }}-db"
  engine         = "postgres"
  engine_version = "{{ db_version }}"
  instance_class = "{{ db_instance_class }}"
  
  allocated_storage     = {{ db_storage }}
  max_allocated_storage = {{ db_max_storage }}
  storage_type          = "gp2"
  storage_encrypted     = true
  
  db_name  = "{{ db_name }}"
  username = "{{ db_username }}"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "{{ project_name }}-final-snapshot"
  
  tags = {
    Name = "{{ project_name }}-db"
  }
}
{% endif -%}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

{% if include_alb -%}
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}
{% endif -%}

{% if include_rds -%}
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
{% endif -%}"""

        return CodeTemplate(
            name="terraform_aws_infrastructure",
            language="hcl",
            category="infrastructure",
            description="Complete AWS infrastructure with VPC, subnets, security groups, and optional services",
            template_content=template_content,
            variables=[
                {"name": "project_name", "type": "string", "description": "Project name"},
                {"name": "aws_region", "type": "string", "description": "AWS region"},
                {"name": "environment", "type": "string", "description": "Environment (dev/staging/prod)"},
                {"name": "public_subnet_count", "type": "integer", "description": "Number of public subnets"},
                {"name": "private_subnet_count", "type": "integer", "description": "Number of private subnets"},
                {"name": "include_alb", "type": "boolean", "description": "Include Application Load Balancer"},
                {"name": "include_rds", "type": "boolean", "description": "Include RDS database"},
                {"name": "app_port", "type": "integer", "description": "Application port"},
                {"name": "db_version", "type": "string", "description": "Database version"},
                {"name": "db_instance_class", "type": "string", "description": "Database instance class"},
                {"name": "db_storage", "type": "integer", "description": "Database storage size"},
                {"name": "db_max_storage", "type": "integer", "description": "Maximum database storage"},
                {"name": "db_name", "type": "string", "description": "Database name"},
                {"name": "db_username", "type": "string", "description": "Database username"},
                {"name": "custom_variables", "type": "array", "description": "Custom Terraform variables"},
                {"name": "use_remote_state", "type": "boolean", "description": "Use remote state backend"},
                {"name": "state_bucket", "type": "string", "description": "S3 bucket for state"}
            ],
            dependencies=[],
            tags=["terraform", "aws", "infrastructure", "iac"]
        )
        
    def _create_github_workflow_template(self) -> CodeTemplate:
        """Create GitHub Actions workflow template"""
        template_content = """# {{ workflow_name }}
name: {{ workflow_name }}

on:
  {% for trigger in triggers -%}
  {{ trigger.type }}:
    {% if trigger.branches -%}
    branches: {{ trigger.branches }}
    {% endif -%}
    {% if trigger.paths -%}
    paths: {{ trigger.paths }}
    {% endif -%}
  {% endfor -%}
  workflow_dispatch:

env:
  {% for env_var in environment_variables -%}
  {{ env_var.name }}: {{ env_var.value }}
  {% endfor -%}

jobs:
  {% for job in jobs -%}
  {{ job.name }}:
    runs-on: {{ job.runs_on }}
    {% if job.timeout -%}
    timeout-minutes: {{ job.timeout }}
    {% endif -%}
    {% if job.strategy -%}
    strategy:
      matrix:
        {{ job.strategy.matrix_key }}: {{ job.strategy.matrix_values }}
    {% endif -%}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        {% if job.fetch_depth -%}
        with:
          fetch-depth: {{ job.fetch_depth }}
        {% endif -%}
      
      {% if job.setup_language -%}
      {% if job.setup_language == 'python' -%}
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: {{ job.language_version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          {% if job.dev_dependencies -%}
          pip install -r requirements-dev.txt
          {% endif -%}
      {% elif job.setup_language == 'node' -%}
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: {{ job.language_version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      {% elif job.setup_language == 'go' -%}
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: {{ job.language_version }}
          cache: true
      
      - name: Download dependencies
        run: go mod download
      {% endif -%}
      {% endif -%}
      
      {% for step in job.custom_steps -%}
      - name: {{ step.name }}
        {% if step.uses -%}
        uses: {{ step.uses }}
        {% if step.with -%}
        with:
          {% for key, value in step.with.items() -%}
          {{ key }}: {{ value }}
          {% endfor -%}
        {% endif -%}
        {% else -%}
        run: |
          {{ step.run|indent(10) }}
        {% endif -%}
        {% if step.env -%}
        env:
          {% for key, value in step.env.items() -%}
          {{ key }}: {{ value }}
          {% endfor -%}
        {% endif -%}
      
      {% endfor -%}
      {% if job.include_tests -%}
      - name: Run tests
        run: |
          {% if job.setup_language == 'python' -%}
          pytest --cov=. --cov-report=xml
          {% elif job.setup_language == 'node' -%}
          npm test
          {% elif job.setup_language == 'go' -%}
          go test -v ./...
          {% endif -%}
      
      {% if job.upload_coverage -%}
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      {% endif -%}
      {% endif -%}
      
      {% if job.include_lint -%}
      - name: Run linter
        run: |
          {% if job.setup_language == 'python' -%}
          flake8 .
          black --check .
          {% elif job.setup_language == 'node' -%}
          npm run lint
          {% elif job.setup_language == 'go' -%}
          golangci-lint run
          {% endif -%}
      {% endif -%}
      
      {% if job.include_security_scan -%}
      - name: Run security scan
        run: |
          {% if job.setup_language == 'python' -%}
          safety check
          bandit -r .
          {% elif job.setup_language == 'node' -%}
          npm audit
          {% elif job.setup_language == 'go' -%}
          gosec ./...
          {% endif -%}
      {% endif -%}
      
      {% if job.build_docker -%}
      - name: Build Docker image
        run: |
          docker build -t {{ job.docker_image_name }}:${{ github.sha }} .
          docker tag {{ job.docker_image_name }}:${{ github.sha }} {{ job.docker_image_name }}:latest
      
      {% if job.push_docker -%}
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Push Docker image
        run: |
          docker push {{ job.docker_image_name }}:${{ github.sha }}
          docker push {{ job.docker_image_name }}:latest
      {% endif -%}
      {% endif -%}
      
      {% if job.deploy -%}
      - name: Deploy to {{ job.deploy.environment }}
        {% if job.deploy.method == 'aws' -%}
        run: |
          aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws configure set aws_secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws configure set default.region {{ job.deploy.region }}
          
          # Deploy using your preferred method (ECS, Lambda, etc.)
          {{ job.deploy.commands|join('\n          ') }}
        {% elif job.deploy.method == 'heroku' -%}
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: {{ job.deploy.app_name }}
          heroku_email: {{ job.deploy.email }}
        {% endif -%}
        {% if job.deploy.only_on_main -%}
        if: github.ref == 'refs/heads/main'
        {% endif -%}
      {% endif -%}
      
      {% if job.notify -%}
      - name: Notify {{ job.notify.service }}
        if: always()
        {% if job.notify.service == 'slack' -%}
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: {{ job.notify.channel }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        {% elif job.notify.service == 'discord' -%}
        uses: sarisia/actions-status-discord@v1
        with:
          webhook: ${{ secrets.DISCORD_WEBHOOK }}
        {% endif -%}
      {% endif -%}

  {% endfor -%}"""

        return CodeTemplate(
            name="github_workflow",
            language="yaml",
            category="ci_cd",
            description="Comprehensive GitHub Actions workflow with testing, security, and deployment",
            template_content=template_content,
            variables=[
                {"name": "workflow_name", "type": "string", "description": "Workflow name"},
                {"name": "triggers", "type": "array", "description": "Workflow triggers"},
                {"name": "environment_variables", "type": "array", "description": "Environment variables"},
                {"name": "jobs", "type": "array", "description": "Jobs configuration"}
            ],
            dependencies=[],
            tags=["github-actions", "ci-cd", "automation"]
        )
        
    def _create_test_suite_template(self) -> CodeTemplate:
        """Create comprehensive test suite template"""
        template_content = """#!/usr/bin/env python3
\"\"\"
Comprehensive test suite for {{ module_name }}
Includes unit tests, integration tests, and performance tests
\"\"\"

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import asyncio
from datetime import datetime, timedelta
import json
import time
import sys
import os
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from {{ module_name }} import {{ main_class }}
{% for import_item in additional_imports -%}
{{ import_item }}
{% endfor %}

class Test{{ main_class }}(unittest.TestCase):
    \"\"\"Unit tests for {{ main_class }}\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        {% for fixture in test_fixtures -%}
        self.{{ fixture.name }} = {{ fixture.value }}
        {% endfor -%}
        self.{{ main_class|lower }} = {{ main_class }}({{ constructor_args }})
    
    def tearDown(self):
        \"\"\"Clean up after tests\"\"\"
        # Cleanup code here
        pass
    
    {% for method in test_methods -%}
    def test_{{ method.name }}(self):
        \"\"\"Test {{ method.description }}\"\"\"
        # Arrange
        {{ method.arrange|indent(8) }}
        
        # Act
        {% if method.expected_exception -%}
        with self.assertRaises({{ method.expected_exception }}):
            result = {{ method.action }}
        {% else -%}
        result = {{ method.action }}
        {% endif -%}
        
        # Assert
        {% if not method.expected_exception -%}
        {{ method.assertions|indent(8) }}
        {% endif -%}
    
    {% endfor -%}
    {% if include_mock_tests -%}
    @patch('{{ module_name }}.{{ dependency_to_mock }}')
    def test_{{ main_class|lower }}_with_mock(self, mock_{{ dependency_to_mock|lower }}):
        \"\"\"Test {{ main_class }} with mocked dependencies\"\"\"
        # Arrange
        mock_{{ dependency_to_mock|lower }}.return_value = {{ mock_return_value }}
        
        # Act
        result = self.{{ main_class|lower }}.{{ method_to_test }}({{ test_parameters }})
        
        # Assert
        self.assertEqual(result, {{ expected_result }})
        mock_{{ dependency_to_mock|lower }}.assert_called_once_with({{ expected_call_args }})
    {% endif -%}

{% if include_async_tests -%}
class TestAsync{{ main_class }}(unittest.TestCase):
    \"\"\"Async tests for {{ main_class }}\"\"\"
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.{{ main_class|lower }} = {{ main_class }}()
    
    def tearDown(self):
        self.loop.close()
    
    {% for async_method in async_test_methods -%}
    def test_{{ async_method.name }}(self):
        \"\"\"Test async {{ async_method.description }}\"\"\"
        async def run_test():
            # Arrange
            {{ async_method.arrange|indent(12) }}
            
            # Act
            result = await self.{{ main_class|lower }}.{{ async_method.method_name }}({{ async_method.parameters }})
            
            # Assert
            {{ async_method.assertions|indent(12) }}
        
        self.loop.run_until_complete(run_test())
    {% endfor -%}
{% endif -%}

{% if include_integration_tests -%}
class TestIntegration{{ main_class }}(unittest.TestCase):
    \"\"\"Integration tests for {{ main_class }}\"\"\"
    
    @classmethod
    def setUpClass(cls):
        \"\"\"Set up integration test environment\"\"\"
        {% for setup_step in integration_setup -%}
        {{ setup_step }}
        {% endfor -%}
    
    @classmethod
    def tearDownClass(cls):
        \"\"\"Clean up integration test environment\"\"\"
        {% for cleanup_step in integration_cleanup -%}
        {{ cleanup_step }}
        {% endfor -%}
    
    def setUp(self):
        self.{{ main_class|lower }} = {{ main_class }}({{ integration_constructor_args }})
    
    {% for integration_test in integration_tests -%}
    def test_{{ integration_test.name }}(self):
        \"\"\"Integration test: {{ integration_test.description }}\"\"\"
        # Test full workflow
        {{ integration_test.test_code|indent(8) }}
    {% endfor -%}
{% endif -%}

{% if include_performance_tests -%}
class TestPerformance{{ main_class }}(unittest.TestCase):
    \"\"\"Performance tests for {{ main_class }}\"\"\"
    
    def setUp(self):
        self.{{ main_class|lower }} = {{ main_class }}()
        self.performance_threshold = {{ performance_threshold }}  # seconds
    
    {% for perf_test in performance_tests -%}
    def test_{{ perf_test.name }}_performance(self):
        \"\"\"Test {{ perf_test.description }} performance\"\"\"
        start_time = time.time()
        
        # Execute performance test
        for _ in range({{ perf_test.iterations }}):
            {{ perf_test.test_code|indent(12) }}
        
        execution_time = time.time() - start_time
        avg_time = execution_time / {{ perf_test.iterations }}
        
        self.assertLess(avg_time, self.performance_threshold,
                       f"Performance test failed: {avg_time:.4f}s > {self.performance_threshold}s")
        
        print(f"Performance test {{ perf_test.name }}: {avg_time:.4f}s average")
    {% endfor -%}
{% endif -%}

{% if include_property_tests -%}
# Property-based testing with Hypothesis
from hypothesis import given, strategies as st

class TestProperties{{ main_class }}(unittest.TestCase):
    \"\"\"Property-based tests for {{ main_class }}\"\"\"
    
    def setUp(self):
        self.{{ main_class|lower }} = {{ main_class }}()
    
    {% for prop_test in property_tests -%}
    @given({{ prop_test.strategy }})
    def test_{{ prop_test.name }}_property(self, {{ prop_test.parameter }}):
        \"\"\"Property test: {{ prop_test.description }}\"\"\"
        # Property to test
        {{ prop_test.property_code|indent(8) }}
    {% endfor -%}
{% endif -%}

# Test utilities
class TestUtils:
    \"\"\"Utility functions for testing\"\"\"
    
    @staticmethod
    def create_test_data(size: int = 10) -> List[Dict[str, Any]]:
        \"\"\"Create test data\"\"\"
        return [
            {
                'id': i,
                'name': f'test_item_{i}',
                'value': i * 10,
                'timestamp': datetime.now().isoformat()
            }
            for i in range(size)
        ]
    
    @staticmethod
    def assert_dict_subset(subset: Dict, superset: Dict):
        \"\"\"Assert that subset is contained in superset\"\"\"
        for key, value in subset.items():
            assert key in superset, f"Key {key} not found in superset"
            assert superset[key] == value, f"Value mismatch for {key}: {superset[key]} != {value}"
    
    @staticmethod
    def wait_for_condition(condition, timeout: float = 5.0, interval: float = 0.1):
        \"\"\"Wait for a condition to be true\"\"\"
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition():
                return True
            time.sleep(interval)
        return False

# Test configuration
@pytest.fixture
def {{ main_class|lower }}_instance():
    \"\"\"Pytest fixture for {{ main_class }} instance\"\"\"
    return {{ main_class }}({{ constructor_args }})

{% for fixture in pytest_fixtures -%}
@pytest.fixture
def {{ fixture.name }}():
    \"\"\"{{ fixture.description }}\"\"\"
    {{ fixture.code|indent(4) }}
{% endfor -%}

# Parametrized tests
@pytest.mark.parametrize("{{ param_test.param_names }}", [
    {% for param_set in param_test.param_sets -%}
    {{ param_set }},
    {% endfor -%}
])
def test_{{ param_test.name }}({{ param_test.param_names }}):
    \"\"\"Parametrized test: {{ param_test.description }}\"\"\"
    {{ param_test.test_code }}

# Test marks
pytestmark = [
    pytest.mark.{{ test_category }},
    pytest.mark.timeout({{ test_timeout }})
]

if __name__ == '__main__':
    # Run tests with coverage
    pytest.main([
        __file__,
        '-v',
        '--cov={{ module_name }}',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--tb=short'
    ])"""

        return CodeTemplate(
            name="comprehensive_test_suite",
            language="python",
            category="testing",
            description="Complete test suite with unit, integration, performance, and property-based tests",
            template_content=template_content,
            variables=[
                {"name": "module_name", "type": "string", "description": "Module to test"},
                {"name": "main_class", "type": "string", "description": "Main class to test"},
                {"name": "constructor_args", "type": "string", "description": "Constructor arguments"},
                {"name": "test_fixtures", "type": "array", "description": "Test fixtures"},
                {"name": "test_methods", "type": "array", "description": "Unit test methods"},
                {"name": "include_mock_tests", "type": "boolean", "description": "Include mock tests"},
                {"name": "include_async_tests", "type": "boolean", "description": "Include async tests"},
                {"name": "include_integration_tests", "type": "boolean", "description": "Include integration tests"},
                {"name": "include_performance_tests", "type": "boolean", "description": "Include performance tests"},
                {"name": "include_property_tests", "type": "boolean", "description": "Include property-based tests"},
                {"name": "additional_imports", "type": "array", "description": "Additional imports"},
                {"name": "dependency_to_mock", "type": "string", "description": "Dependency to mock"},
                {"name": "async_test_methods", "type": "array", "description": "Async test methods"},
                {"name": "integration_tests", "type": "array", "description": "Integration tests"},
                {"name": "performance_tests", "type": "array", "description": "Performance tests"},
                {"name": "property_tests", "type": "array", "description": "Property-based tests"},
                {"name": "pytest_fixtures", "type": "array", "description": "Pytest fixtures"},
                {"name": "param_test", "type": "object", "description": "Parametrized test configuration"},
                {"name": "performance_threshold", "type": "float", "description": "Performance threshold in seconds"},
                {"name": "test_category", "type": "string", "description": "Test category marker"},
                {"name": "test_timeout", "type": "integer", "description": "Test timeout in seconds"}
            ],
            dependencies=["pytest", "hypothesis"],
            tags=["testing", "unit-tests", "integration-tests", "performance"]
        )
        
    def generate_code(self, template_name: str, parameters: Dict[str, Any], user_id: str = None) -> GeneratedCode:
        """Generate code from template"""
        try:
            template = self.db.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
                
            # Update usage count
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE templates SET usage_count = usage_count + 1 WHERE name = ?", (template_name,))
            conn.commit()
            conn.close()
            
            # Create Jinja template
            jinja_template = Template(template.template_content)
            
            # Generate code
            generated_code = jinja_template.render(**parameters)
            
            # Split into files if needed
            files = {}
            if "---" in generated_code:
                # Multi-file template
                file_parts = generated_code.split("---\n")
                main_file = file_parts[0].strip()
                
                # Extract filename from comments
                main_filename = self._extract_filename(main_file, template.language)
                files[main_filename] = main_file
                
                for part in file_parts[1:]:
                    if part.strip():
                        filename = self._extract_filename(part, template.language)
                        files[filename] = part.strip()
            else:
                # Single file template
                filename = self._extract_filename(generated_code, template.language)
                files[filename] = generated_code
                
            # Generate instructions
            instructions = self._generate_instructions(template, parameters)
            
            # Store generation history
            self._store_generation_history(template_name, parameters, files, user_id)
            
            return GeneratedCode(
                template_name=template_name,
                language=template.language,
                code=generated_code,
                files=files,
                dependencies=template.dependencies,
                instructions=instructions,
                generated_at=datetime.now().isoformat(),
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"Failed to generate code from template {template_name}: {e}")
            raise
            
    def _extract_filename(self, content: str, language: str) -> str:
        """Extract filename from content or generate default"""
        # Look for filename in comments
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if '# ' in line and ('.' in line or '/' in line):
                filename = line.split('# ')[-1].strip()
                if '.' in filename:
                    return filename
                    
        # Generate default filename
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'go': '.go',
            'rust': '.rs',
            'dockerfile': 'Dockerfile',
            'yaml': '.yml',
            'hcl': '.tf'
        }
        
        extension = extensions.get(language, '.txt')
        return f"main{extension}"
        
    def _generate_instructions(self, template: CodeTemplate, parameters: Dict[str, Any]) -> str:
        """Generate setup and usage instructions"""
        instructions = f"# {template.name} - Generated Code\n\n"
        instructions += f"{template.description}\n\n"
        
        if template.dependencies:
            instructions += "## Dependencies\n"
            instructions += "Install the following dependencies:\n\n"
            for dep in template.dependencies:
                instructions += f"- {dep}\n"
            instructions += "\n"
            
        instructions += "## Setup Instructions\n"
        
        if template.language == 'python':
            instructions += "1. Create a virtual environment:\n"
            instructions += "   ```bash\n"
            instructions += "   python -m venv venv\n"
            instructions += "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate\n"
            instructions += "   ```\n\n"
            instructions += "2. Install dependencies:\n"
            instructions += "   ```bash\n"
            instructions += f"   pip install {' '.join(template.dependencies)}\n"
            instructions += "   ```\n\n"
        elif template.language == 'javascript':
            instructions += "1. Initialize npm project (if not already done):\n"
            instructions += "   ```bash\n"
            instructions += "   npm init -y\n"
            instructions += "   ```\n\n"
            instructions += "2. Install dependencies:\n"
            instructions += "   ```bash\n"
            instructions += f"   npm install {' '.join(template.dependencies)}\n"
            instructions += "   ```\n\n"
            
        instructions += "## Usage\n"
        instructions += "Follow the comments in the generated code for specific usage instructions.\n\n"
        
        instructions += "## Configuration\n"
        instructions += "The following parameters were used to generate this code:\n\n"
        for key, value in parameters.items():
            instructions += f"- **{key}**: {value}\n"
            
        return instructions
        
    def _store_generation_history(self, template_name: str, parameters: Dict[str, Any], 
                                files: Dict[str, str], user_id: str = None):
        """Store code generation history"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO generation_history 
                (template_name, parameters, generated_files, user_id)
                VALUES (?, ?, ?, ?)
            """, (
                template_name,
                json.dumps(parameters),
                json.dumps(list(files.keys())),
                user_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store generation history: {e}")

def main():
    """Demo of code generation capabilities"""
    generator = CodeGenerator()
    
    print("Code Generation Engine Demo")
    print("=" * 40)
    
    # List available templates
    templates = generator.db.list_templates()
    print(f"\nAvailable templates: {len(templates)}")
    for template in templates[:5]:  # Show first 5
        print(f"- {template['name']} ({template['language']}) - {template['description'][:50]}...")
    
    # Generate a Flask API
    print("\nGenerating Flask API...")
    flask_params = {
        'database_url': 'sqlite:///app.db',
        'secret_key': 'your-secret-key-here',
        'model_name': 'User',
        'endpoint_prefix': 'users',
        'fields': [
            {'name': 'username', 'type': 'String', 'constraints': 'nullable=False, unique=True'},
            {'name': 'email', 'type': 'String', 'constraints': 'nullable=False, unique=True'},
            {'name': 'is_active', 'type': 'Boolean', 'constraints': 'default=True'}
        ],
        'debug_mode': True
    }
    
    result = generator.generate_code('flask_rest_api', flask_params)
    print(f"Generated {len(result.files)} files:")
    for filename in result.files.keys():
        print(f"- {filename}")
    
    print(f"\nDependencies: {', '.join(result.dependencies)}")

if __name__ == "__main__":
    main()