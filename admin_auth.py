"""
MITO Engine - Admin Authentication System
Protects administrative functions with password authentication
"""

import os
import hashlib
from functools import wraps
from flask import session, request, jsonify, redirect, url_for


class AdminAuth:
    """Handles admin authentication for MITO Engine"""

    def __init__(self):
        # Default admin password - change this in production
        self.admin_password_hash = self._hash_password(
            os.getenv("ADMIN_PASSWORD", "mito_admin_2025"))

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verify admin password"""
        return self._hash_password(password) == self.admin_password_hash

    def is_admin_logged_in(self) -> bool:
        """Check if admin is currently logged in"""
        return session.get('admin_authenticated', False)

    def login_admin(self, password: str) -> bool:
        """Attempt admin login"""
        if self.verify_password(password):
            session['admin_authenticated'] = True
            session.permanent = True
            return True
        return False

    def logout_admin(self):
        """Logout admin"""
        session.pop('admin_authenticated', None)

    def require_admin(self, f):
        """Decorator to require admin authentication"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.is_admin_logged_in():
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Admin authentication required',
                        'redirect': '/admin-login'
                    }), 401
                else:
                    return redirect(url_for('admin_login'))
            return f(*args, **kwargs)

        return decorated_function


# Global admin auth instance
admin_auth = AdminAuth()

# Admin login template
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Admin Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 1rem;
        }
        
        .subtitle {
            color: #6b7280;
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #374151;
            font-weight: 500;
        }
        
        input[type="password"] {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .login-btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
        }
        
        .error {
            color: #ef4444;
            margin-top: 1rem;
            font-size: 0.9rem;
        }
        
        .back-link {
            margin-top: 2rem;
            display: block;
            color: #667eea;
            text-decoration: none;
            font-size: 0.9rem;
        }
        
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">MITO</div>
        <div class="subtitle">Admin Access Required</div>
        
        <form method="POST" action="/admin-login">
            <div class="form-group">
                <label for="password">Admin Password</label>
                <input type="password" id="password" name="password" required autofocus>
            </div>
            
            <button type="submit" class="login-btn">Access Admin Panel</button>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </form>
        
        <a href="/" class="back-link">← Back to MITO Dashboard</a>
    </div>
</body>
</html>
"""
