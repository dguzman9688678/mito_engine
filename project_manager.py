"""
MITO Engine - Project Manager
Complete project management system with templates, scaffolding, and deployment
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid

class ProjectTemplate:
    """Project template definition"""
    
    def __init__(self, name: str, description: str, category: str, files: Dict[str, str], 
                 dependencies: List[str] = None, config: Dict[str, Any] = None):
        self.template_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.category = category
        self.files = files  # file_path: content
        self.dependencies = dependencies or []
        self.config = config or {}
        self.created_at = datetime.now().isoformat()

class Project:
    """Project instance"""
    
    def __init__(self, name: str, template_id: str = None, path: str = None):
        self.project_id = str(uuid.uuid4())
        self.name = name
        self.template_id = template_id
        self.path = Path(path) if path else Path(name)
        self.created_at = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.status = "active"
        self.metadata = {}

class ProjectManager:
    """Complete project management system"""
    
    def __init__(self):
        self.templates = {}
        self.projects = {}
        self.initialize_default_templates()
    
    def initialize_default_templates(self):
        """Initialize default project templates"""
        
        # Flask Web Application
        flask_template = ProjectTemplate(
            name="Flask Web Application",
            description="Complete Flask web application with authentication and database",
            category="web",
            files={
                "app.py": '''import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    return jsonify({"status": "running", "version": "1.0.0"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
''',
                "models.py": '''from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<User {self.username}>'
''',
                "templates/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Application</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center">Welcome to Flask App</h1>
        <p class="text-center">Your application is running successfully!</p>
    </div>
</body>
</html>
''',
                "requirements.txt": '''flask
flask-sqlalchemy
flask-login
gunicorn
python-dotenv
''',
                ".env": '''SESSION_SECRET=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
''',
                "README.md": '''# Flask Web Application

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in .env file
3. Run the application: `python app.py`

## Features
- Flask web framework
- SQLAlchemy database integration
- Bootstrap UI
- Environment configuration
'''
            },
            dependencies=["flask", "flask-sqlalchemy", "flask-login", "gunicorn"],
            config={"port": 5000, "framework": "flask"}
        )
        self.add_template(flask_template)
        
        # Python CLI Tool
        cli_template = ProjectTemplate(
            name="Python CLI Tool",
            description="Command-line tool with argument parsing and logging",
            category="cli",
            files={
                "main.py": '''#!/usr/bin/env python3
"""
Command Line Tool
"""

import argparse
import logging
import sys
from datetime import datetime

def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Python CLI Tool')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--config', '-c', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("CLI tool started")
    
    # Your CLI logic here
    logger.info("Processing complete")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
''',
                "config.py": '''"""
Configuration management
"""

import os
import json
from pathlib import Path

class Config:
    """Configuration class"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file or 'config.json'
        self.data = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "app_name": "CLI Tool",
            "version": "1.0.0",
            "debug": False
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.data[key] = value
        self.save_config()
''',
                "requirements.txt": '''click
colorama
python-dotenv
''',
                "README.md": '''# Python CLI Tool

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py --help
python main.py --verbose
```

## Features
- Argument parsing with argparse
- Configurable logging
- Configuration management
- Error handling
'''
            },
            dependencies=["click", "colorama"],
            config={"type": "cli"}
        )
        self.add_template(cli_template)
        
        # React Frontend
        react_template = ProjectTemplate(
            name="React Frontend",
            description="Modern React application with TypeScript and styling",
            category="frontend",
            files={
                "package.json": '''{
  "name": "react-app",
  "version": "1.0.0",
  "description": "React application",
  "main": "index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}''',
                "public/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React App</title>
</head>
<body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
</body>
</html>''',
                "src/App.tsx": '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>React Application</h1>
        <p>Welcome to your new React app!</p>
      </header>
    </div>
  );
}

export default App;
''',
                "src/index.tsx": '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',
                "src/App.css": '''.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

h1 {
  margin-bottom: 20px;
}
''',
                "src/index.css": '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}
''',
                "README.md": '''# React Application

## Available Scripts

### `npm start`
Runs the app in development mode on port 3000.

### `npm run build`
Builds the app for production.

### `npm test`
Launches the test runner.

## Features
- React 18
- TypeScript support
- Modern CSS
- Development server
'''
            },
            dependencies=["react", "react-dom", "typescript"],
            config={"framework": "react", "port": 3000}
        )
        self.add_template(react_template)
        
        # FastAPI Backend
        fastapi_template = ProjectTemplate(
            name="FastAPI Backend",
            description="FastAPI REST API with database and authentication",
            category="api",
            files={
                "main.py": '''from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="FastAPI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "FastAPI Backend is running"}

@app.get("/users/", response_model=list[UserResponse])
async def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                "requirements.txt": '''fastapi
uvicorn[standard]
sqlalchemy
pydantic
python-multipart
''',
                ".env": '''DATABASE_URL=sqlite:///./app.db
''',
                "README.md": '''# FastAPI Backend

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python main.py`
3. Visit http://localhost:8000/docs for API documentation

## Features
- FastAPI framework
- SQLAlchemy ORM
- Automatic API documentation
- CORS middleware
- Pydantic validation
'''
            },
            dependencies=["fastapi", "uvicorn", "sqlalchemy"],
            config={"framework": "fastapi", "port": 8000}
        )
        self.add_template(fastapi_template)
    
    def add_template(self, template: ProjectTemplate):
        """Add a project template"""
        self.templates[template.template_id] = template
    
    def list_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """List available project templates"""
        templates = []
        for template in self.templates.values():
            if category is None or template.category == category:
                templates.append({
                    "id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "dependencies": template.dependencies,
                    "created_at": template.created_at
                })
        return templates
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get specific template"""
        return self.templates.get(template_id)
    
    def create_project(self, name: str, template_id: str = None, path: str = None) -> Dict[str, Any]:
        """Create new project from template"""
        try:
            project = Project(name, template_id, path)
            project_path = project.path
            
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            if template_id and template_id in self.templates:
                template = self.templates[template_id]
                
                # Create files from template
                for file_path, content in template.files.items():
                    full_path = project_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Store project metadata
                metadata = {
                    "template_id": template_id,
                    "template_name": template.name,
                    "dependencies": template.dependencies,
                    "config": template.config
                }
                project.metadata = metadata
                
                # Create project config file
                project_config = {
                    "project_id": project.project_id,
                    "name": project.name,
                    "template_id": template_id,
                    "created_at": project.created_at,
                    "metadata": metadata
                }
                
                with open(project_path / ".mito-project.json", 'w') as f:
                    json.dump(project_config, f, indent=2)
            
            self.projects[project.project_id] = project
            
            return {
                "success": True,
                "project_id": project.project_id,
                "name": project.name,
                "path": str(project.path),
                "template_id": template_id,
                "message": f"Project '{name}' created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects"""
        projects = []
        for project in self.projects.values():
            projects.append({
                "id": project.project_id,
                "name": project.name,
                "path": str(project.path),
                "template_id": project.template_id,
                "created_at": project.created_at,
                "last_modified": project.last_modified,
                "status": project.status
            })
        return projects
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get specific project"""
        return self.projects.get(project_id)
    
    def delete_project(self, project_id: str, delete_files: bool = False) -> Dict[str, Any]:
        """Delete project"""
        try:
            if project_id not in self.projects:
                return {"success": False, "error": "Project not found"}
            
            project = self.projects[project_id]
            
            if delete_files and project.path.exists():
                shutil.rmtree(project.path)
            
            del self.projects[project_id]
            
            return {
                "success": True,
                "message": f"Project '{project.name}' deleted successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scaffold_feature(self, project_id: str, feature_type: str, feature_name: str) -> Dict[str, Any]:
        """Add a feature to existing project"""
        try:
            if project_id not in self.projects:
                return {"success": False, "error": "Project not found"}
            
            project = self.projects[project_id]
            
            # Define feature scaffolds
            scaffolds = {
                "api_endpoint": {
                    f"api/{feature_name}.py": f'''from flask import Blueprint, request, jsonify

{feature_name}_bp = Blueprint('{feature_name}', __name__)

@{feature_name}_bp.route('/{feature_name}', methods=['GET'])
def get_{feature_name}():
    return jsonify({{"message": "{feature_name} endpoint"}})

@{feature_name}_bp.route('/{feature_name}', methods=['POST'])
def create_{feature_name}():
    data = request.get_json()
    return jsonify({{"message": "{feature_name} created", "data": data}})
'''
                },
                "model": {
                    f"models/{feature_name}.py": f'''from app import db
from datetime import datetime

class {feature_name.title()}(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {{
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }}
    
    def __repr__(self):
        return f'<{feature_name.title()} {{self.name}}>'
'''
                },
                "component": {
                    f"components/{feature_name.title()}.tsx": f'''import React from 'react';

interface {feature_name.title()}Props {{
  // Define props here
}}

const {feature_name.title()}: React.FC<{feature_name.title()}Props> = () => {{
  return (
    <div className="{feature_name}-component">
      <h2>{feature_name.title()} Component</h2>
      {{/* Component content here */}}
    </div>
  );
}};

export default {feature_name.title()};
'''
                }
            }
            
            if feature_type not in scaffolds:
                return {"success": False, "error": f"Unknown feature type: {feature_type}"}
            
            # Create feature files
            created_files = []
            for file_path, content in scaffolds[feature_type].items():
                full_path = project.path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(file_path)
            
            project.last_modified = datetime.now().isoformat()
            
            return {
                "success": True,
                "message": f"Feature '{feature_name}' of type '{feature_type}' added to project",
                "created_files": created_files
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_project_structure(self, project_id: str) -> Dict[str, Any]:
        """Get project file structure"""
        try:
            if project_id not in self.projects:
                return {"success": False, "error": "Project not found"}
            
            project = self.projects[project_id]
            
            def build_tree(path: Path, name: str = None) -> Dict[str, Any]:
                if name is None:
                    name = path.name
                
                if path.is_file():
                    return {
                        "name": name,
                        "type": "file",
                        "size": path.stat().st_size,
                        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    }
                else:
                    children = []
                    try:
                        for child in sorted(path.iterdir()):
                            if not child.name.startswith('.'):
                                children.append(build_tree(child))
                    except PermissionError:
                        pass
                    
                    return {
                        "name": name,
                        "type": "directory",
                        "children": children
                    }
            
            structure = build_tree(project.path, project.name)
            
            return {
                "success": True,
                "project_id": project_id,
                "structure": structure
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global project manager instance
project_manager = ProjectManager()

def main():
    """Demo of project manager functionality"""
    
    # List templates
    templates = project_manager.list_templates()
    print("Available templates:")
    for template in templates:
        print(f"- {template['name']}: {template['description']}")
    
    # Create a Flask project
    if templates:
        flask_template = next((t for t in templates if "Flask" in t['name']), None)
        if flask_template:
            result = project_manager.create_project("my_flask_app", flask_template['id'])
            print(f"\nProject creation result: {result}")
            
            if result['success']:
                # Get project structure
                structure = project_manager.get_project_structure(result['project_id'])
                print(f"\nProject structure: {json.dumps(structure, indent=2)}")

if __name__ == "__main__":
    main()