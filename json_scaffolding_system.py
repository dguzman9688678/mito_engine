#!/usr/bin/env python3
"""
MITO Engine - JSON Scaffolding System
Automated project scaffolding using JSON configuration templates
"""

import os
import json
import time
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MITOScaffoldingEngine:
    """JSON-based scaffolding system for rapid project creation"""
    
    def __init__(self):
        self.templates_dir = "workspace_templates"
        self.scaffolds_dir = "generated_scaffolds"
        self.ensure_directories()
        self.load_default_templates()
    
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.scaffolds_dir, exist_ok=True)
    
    def load_default_templates(self):
        """Load default JSON scaffolding templates"""
        
        # Flask Web Application Template
        flask_template = {
            "name": "flask_web_app",
            "description": "Complete Flask web application with authentication and database",
            "version": "1.0.0",
            "structure": {
                "app.py": {
                    "type": "file",
                    "content": """from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users')
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email} for u in users])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
                },
                "templates/": {
                    "type": "directory",
                    "files": {
                        "base.html": {
                            "type": "file",
                            "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Flask App{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">Flask App</a>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
                        },
                        "index.html": {
                            "type": "file",
                            "content": """{% extends "base.html" %}

{% block title %}Home - Flask App{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8">
        <h1>Welcome to Flask App</h1>
        <p class="lead">Your application is ready to use.</p>
        <button class="btn btn-primary" onclick="loadUsers()">Load Users</button>
    </div>
</div>

<div id="users-list" class="mt-4"></div>

<script>
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();
        
        const usersList = document.getElementById('users-list');
        usersList.innerHTML = '<h3>Users</h3><ul class="list-group">' + 
            users.map(user => `<li class="list-group-item">${user.username} (${user.email})</li>`).join('') +
            '</ul>';
    } catch (error) {
        console.error('Error loading users:', error);
    }
}
</script>
{% endblock %}"""
                        }
                    }
                },
                "static/": {
                    "type": "directory",
                    "files": {
                        "css/": {
                            "type": "directory",
                            "files": {
                                "app.css": {
                                    "type": "file",
                                    "content": """/* Custom styles */
.navbar-brand {
    font-weight: bold;
}

.btn-primary {
    background-color: #007bff;
    border-color: #007bff;
}

.list-group-item {
    border: 1px solid #dee2e6;
}"""
                                }
                            }
                        },
                        "js/": {
                            "type": "directory",
                            "files": {
                                "app.js": {
                                    "type": "file",
                                    "content": """// Application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Flask App loaded');
});"""
                                }
                            }
                        }
                    }
                },
                "requirements.txt": {
                    "type": "file",
                    "content": """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.7
python-dotenv==1.0.0"""
                },
                ".env": {
                    "type": "file",
                    "content": """SESSION_SECRET=your-secret-key-here
DATABASE_URL=sqlite:///app.db
FLASK_ENV=development
FLASK_DEBUG=True"""
                },
                "README.md": {
                    "type": "file",
                    "content": """# Flask Web Application

A complete Flask web application with authentication and database support.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables in `.env`

3. Run the application:
   ```bash
   python app.py
   ```

## Features

- Flask web framework
- SQLAlchemy database integration
- Bootstrap UI components
- User management
- API endpoints

## API Endpoints

- `GET /` - Home page
- `GET /api/users` - Get all users

## Configuration

Edit `.env` file to configure:
- SESSION_SECRET
- DATABASE_URL
- FLASK_ENV
- FLASK_DEBUG
"""
                }
            }
        }
        
        # Next.js React Application Template
        nextjs_template = {
            "name": "nextjs_react_app",
            "description": "Modern Next.js React application with TypeScript",
            "version": "1.0.0",
            "structure": {
                "package.json": {
                    "type": "file",
                    "content": """{
  "name": "nextjs-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18",
    "react-dom": "^18",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5"
  },
  "devDependencies": {
    "eslint": "^8",
    "eslint-config-next": "14.0.0"
  }
}"""
                },
                "tsconfig.json": {
                    "type": "file",
                    "content": """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""
                },
                "next.config.js": {
                    "type": "file",
                    "content": """/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig"""
                },
                "app/": {
                    "type": "directory",
                    "files": {
                        "layout.tsx": {
                            "type": "file",
                            "content": """import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Next.js App',
  description: 'Generated by MITO Engine',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-blue-600 text-white p-4">
          <div className="container mx-auto">
            <h1 className="text-xl font-bold">Next.js App</h1>
          </div>
        </nav>
        <main className="container mx-auto p-4">
          {children}
        </main>
      </body>
    </html>
  )
}"""
                        },
                        "page.tsx": {
                            "type": "file",
                            "content": """'use client'

import { useState, useEffect } from 'react'

export default function Home() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    setMessage('Welcome to Next.js with TypeScript!')
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">
        {message}
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-3">Features</h2>
          <ul className="space-y-2 text-gray-600">
            <li>• Next.js 14</li>
            <li>• TypeScript</li>
            <li>• Tailwind CSS</li>
            <li>• App Router</li>
          </ul>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-3">Getting Started</h2>
          <p className="text-gray-600">
            Edit app/page.tsx to modify this page.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-3">Deploy</h2>
          <p className="text-gray-600">
            Deploy your Next.js app with Vercel, Netlify, or any hosting platform.
          </p>
        </div>
      </div>
    </div>
  )
}"""
                        },
                        "globals.css": {
                            "type": "file",
                            "content": """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

@media (prefers-color-scheme: dark) {
  :root {
    --foreground-rgb: 255, 255, 255;
    --background-start-rgb: 0, 0, 0;
    --background-end-rgb: 0, 0, 0;
  }
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}"""
                        }
                    }
                },
                "README.md": {
                    "type": "file",
                    "content": """# Next.js React Application

A modern Next.js application with TypeScript and Tailwind CSS.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Responsive design
- Modern React patterns

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Deployment

Deploy easily on Vercel, Netlify, or any modern hosting platform.
"""
                }
            }
        }
        
        # Express.js API Template
        express_template = {
            "name": "express_api",
            "description": "RESTful API with Express.js, MongoDB, and authentication",
            "version": "1.0.0",
            "structure": {
                "package.json": {
                    "type": "file",
                    "content": """{
  "name": "express-api",
  "version": "1.0.0",
  "description": "RESTful API with Express.js",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "dotenv": "^16.3.1",
    "express-rate-limit": "^6.10.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1",
    "jest": "^29.6.2",
    "supertest": "^6.3.3"
  }
}"""
                },
                "server.js": {
                    "type": "file",
                    "content": """const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/expressapi', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/users', require('./routes/users'));

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Something went wrong!',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});

module.exports = app;"""
                },
                "models/": {
                    "type": "directory",
                    "files": {
                        "User.js": {
                            "type": "file",
                            "content": """const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    minlength: 3,
    maxlength: 30
  },
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true
  },
  password: {
    type: String,
    required: true,
    minlength: 6
  },
  role: {
    type: String,
    enum: ['user', 'admin'],
    default: 'user'
  },
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model('User', userSchema);"""
                        }
                    }
                },
                "routes/": {
                    "type": "directory",
                    "files": {
                        "auth.js": {
                            "type": "file",
                            "content": """const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const router = express.Router();

// Register
router.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    
    // Check if user exists
    const existingUser = await User.findOne({ 
      $or: [{ email }, { username }] 
    });
    
    if (existingUser) {
      return res.status(400).json({ 
        error: 'User already exists' 
      });
    }
    
    // Create user
    const user = new User({ username, email, password });
    await user.save();
    
    // Generate JWT
    const token = jwt.sign(
      { userId: user._id }, 
      process.env.JWT_SECRET || 'fallback-secret',
      { expiresIn: '7d' }
    );
    
    res.status(201).json({
      message: 'User created successfully',
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    // Find user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Check password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Generate JWT
    const token = jwt.sign(
      { userId: user._id }, 
      process.env.JWT_SECRET || 'fallback-secret',
      { expiresIn: '7d' }
    );
    
    res.json({
      message: 'Login successful',
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;"""
                        },
                        "users.js": {
                            "type": "file",
                            "content": """const express = require('express');
const User = require('../models/User');
const auth = require('../middleware/auth');
const router = express.Router();

// Get all users (protected)
router.get('/', auth, async (req, res) => {
  try {
    const users = await User.find({}, '-password');
    res.json(users);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get user profile (protected)
router.get('/profile', auth, async (req, res) => {
  try {
    const user = await User.findById(req.userId, '-password');
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update user profile (protected)
router.put('/profile', auth, async (req, res) => {
  try {
    const { username, email } = req.body;
    
    const user = await User.findByIdAndUpdate(
      req.userId,
      { username, email },
      { new: true, select: '-password' }
    );
    
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;"""
                        }
                    }
                },
                "middleware/": {
                    "type": "directory",
                    "files": {
                        "auth.js": {
                            "type": "file",
                            "content": """const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
  const token = req.header('Authorization')?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ error: 'Access denied. No token provided.' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'fallback-secret');
    req.userId = decoded.userId;
    next();
  } catch (error) {
    res.status(400).json({ error: 'Invalid token.' });
  }
};"""
                        }
                    }
                },
                ".env": {
                    "type": "file",
                    "content": """NODE_ENV=development
PORT=3000
MONGODB_URI=mongodb://localhost:27017/expressapi
JWT_SECRET=your-super-secret-jwt-key-here
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100"""
                },
                "README.md": {
                    "type": "file",
                    "content": """# Express.js REST API

A complete RESTful API built with Express.js, MongoDB, and JWT authentication.

## Features

- User registration and authentication
- JWT token-based security
- Password hashing with bcrypt
- Rate limiting
- CORS support
- MongoDB integration
- Input validation
- Error handling

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables in `.env`

3. Start MongoDB service

4. Run the application:
   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Users (Protected)
- `GET /api/users` - Get all users
- `GET /api/users/profile` - Get current user profile
- `PUT /api/users/profile` - Update user profile

### Health Check
- `GET /health` - API health status

## Testing

Use tools like Postman or curl to test the endpoints:

```bash
# Register
curl -X POST http://localhost:3000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:3000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@example.com","password":"password123"}'
```
"""
                }
            }
        }
        
        # Save templates
        templates = [flask_template, nextjs_template, express_template]
        
        for template in templates:
            template_path = os.path.join(self.templates_dir, f"{template['name']}.json")
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
        
        logger.info(f"Loaded {len(templates)} default scaffolding templates")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        templates = []
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.join(self.templates_dir, filename)
                try:
                    with open(template_path, 'r') as f:
                        template = json.load(f)
                        templates.append({
                            'file': filename,
                            'name': template.get('name', 'Unknown'),
                            'description': template.get('description', 'No description'),
                            'version': template.get('version', '1.0.0')
                        })
                except Exception as e:
                    logger.error(f"Error loading template {filename}: {e}")
        
        return templates
    
    def generate_project(self, template_name: str, project_name: str, 
                        output_dir: str = None, variables: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate a new project from template"""
        
        # Load template
        template_path = os.path.join(self.templates_dir, f"{template_name}.json")
        if not os.path.exists(template_path):
            return {
                'success': False,
                'error': f'Template {template_name} not found'
            }
        
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f'Error loading template: {e}'
            }
        
        # Set output directory
        if not output_dir:
            output_dir = os.path.join(self.scaffolds_dir, project_name)
        
        # Prepare variables for substitution
        template_vars = {
            'PROJECT_NAME': project_name,
            'PROJECT_NAME_LOWER': project_name.lower(),
            'PROJECT_NAME_UPPER': project_name.upper(),
            'CURRENT_DATE': datetime.now().strftime('%Y-%m-%d'),
            'CURRENT_YEAR': str(datetime.now().year),
            'TIMESTAMP': str(int(time.time()))
        }
        
        if variables:
            template_vars.update(variables)
        
        # Generate project structure
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            files_created = []
            dirs_created = []
            
            self._create_structure(
                template['structure'], 
                output_dir, 
                template_vars,
                files_created,
                dirs_created
            )
            
            # Create project manifest
            manifest = {
                'project_name': project_name,
                'template_used': template_name,
                'template_version': template.get('version', '1.0.0'),
                'generated_at': datetime.now().isoformat(),
                'files_created': files_created,
                'directories_created': dirs_created,
                'variables_used': template_vars
            }
            
            manifest_path = os.path.join(output_dir, '.mito_project.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return {
                'success': True,
                'project_path': output_dir,
                'files_created': len(files_created),
                'directories_created': len(dirs_created),
                'manifest': manifest
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating project: {e}'
            }
    
    def _create_structure(self, structure: Dict[str, Any], base_path: str, 
                         variables: Dict[str, str], files_created: List[str], 
                         dirs_created: List[str]):
        """Recursively create project structure"""
        
        for name, config in structure.items():
            item_path = os.path.join(base_path, name)
            
            if config['type'] == 'directory':
                os.makedirs(item_path, exist_ok=True)
                dirs_created.append(item_path)
                
                if 'files' in config:
                    self._create_structure(
                        config['files'], 
                        item_path, 
                        variables,
                        files_created,
                        dirs_created
                    )
            
            elif config['type'] == 'file':
                content = config.get('content', '')
                
                # Variable substitution
                for var_name, var_value in variables.items():
                    content = content.replace(f'{{{var_name}}}', var_value)
                
                with open(item_path, 'w') as f:
                    f.write(content)
                
                files_created.append(item_path)
    
    def create_custom_template(self, name: str, description: str, 
                              structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom template"""
        
        template = {
            'name': name,
            'description': description,
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'structure': structure
        }
        
        template_path = os.path.join(self.templates_dir, f"{name}.json")
        
        try:
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            return {
                'success': True,
                'template_path': template_path,
                'message': f'Template {name} created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error creating template: {e}'
            }
    
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """Get information about a generated project"""
        
        manifest_path = os.path.join(project_path, '.mito_project.json')
        
        if not os.path.exists(manifest_path):
            return {
                'success': False,
                'error': 'Not a MITO generated project'
            }
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            return {
                'success': True,
                'project_info': manifest
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error reading project manifest: {e}'
            }


# Global scaffolding engine instance
_scaffolding_engine = None

def get_scaffolding_engine() -> MITOScaffoldingEngine:
    """Get or create global scaffolding engine instance"""
    global _scaffolding_engine
    if _scaffolding_engine is None:
        _scaffolding_engine = MITOScaffoldingEngine()
    return _scaffolding_engine


if __name__ == "__main__":
    # Test scaffolding system
    print("Testing MITO JSON Scaffolding System...")
    
    engine = MITOScaffoldingEngine()
    
    # List templates
    templates = engine.list_templates()
    print(f"Available templates: {len(templates)}")
    for template in templates:
        print(f"  - {template['name']}: {template['description']}")
    
    # Generate a test project
    result = engine.generate_project(
        'flask_web_app',
        'test_flask_project',
        variables={'AUTHOR': 'MITO Engine', 'EMAIL': 'mito@example.com'}
    )
    
    if result['success']:
        print(f"\n✓ Project generated successfully!")
        print(f"  Path: {result['project_path']}")
        print(f"  Files created: {result['files_created']}")
        print(f"  Directories created: {result['directories_created']}")
    else:
        print(f"\n✗ Project generation failed: {result['error']}")
    
    print("\n✓ JSON Scaffolding System test completed")