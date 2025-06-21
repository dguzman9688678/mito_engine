"""
MITO Engine - Authentication Manager
Complete authentication and security management system
"""

import os
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import re

class User:
    """User data model"""
    
    def __init__(self, user_id: str, username: str, email: str, password_hash: str,
                 role: str = "user", active: bool = True, created_at: str = None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.active = active
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = None
        self.login_attempts = 0
        self.locked_until = None

class Session:
    """User session data"""
    
    def __init__(self, session_id: str, user_id: str, ip_address: str, user_agent: str):
        self.session_id = session_id
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()
        self.active = True

class AuthenticationManager:
    """Complete authentication and security management"""
    
    def __init__(self, db_path: str = "auth.db", secret_key: str = None):
        self.db_path = db_path
        self.secret_key = secret_key or os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self.max_login_attempts = 5
        self.lockout_duration = 30 * 60  # 30 minutes in seconds
        
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT,
                login_attempts INTEGER DEFAULT 0,
                locked_until TEXT
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                ip_address TEXT,
                success BOOLEAN,
                timestamp TEXT NOT NULL,
                user_agent TEXT
            )
        ''')
        
        # Permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                permission TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                granted_by TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if none exists
        self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin user"""
        try:
            admin_exists = self.get_user_by_username("admin")
            if not admin_exists:
                self.register_user(
                    username="admin",
                    email="admin@mito.local",
                    password="admin123",
                    role="admin"
                )
        except:
            pass
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": "strong" if len(errors) == 0 else "weak"
        }
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """Register new user"""
        try:
            # Validate input
            if not username or not email or not password:
                return {"success": False, "error": "Username, email, and password are required"}
            
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return {"success": False, "error": "Invalid email format"}
            
            # Validate password
            password_validation = self.validate_password(password)
            if not password_validation["valid"]:
                return {"success": False, "error": "Password validation failed", "details": password_validation["errors"]}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT username, email FROM users WHERE username = ? OR email = ?", (username, email))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return {"success": False, "error": "Username or email already exists"}
            
            # Create user
            user_id = secrets.token_urlsafe(16)
            password_hash = generate_password_hash(password)
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, role, created_at))
            
            # Grant default permissions
            default_permissions = ["read_profile", "update_profile"]
            if role == "admin":
                default_permissions.extend(["admin_access", "user_management", "system_config"])
            
            for permission in default_permissions:
                cursor.execute('''
                    INSERT INTO permissions (user_id, permission, granted_at)
                    VALUES (?, ?, ?)
                ''', (user_id, permission, created_at))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "message": "User registered successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None, 
                         user_agent: str = None) -> Dict[str, Any]:
        """Authenticate user login"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Log login attempt
            cursor.execute('''
                INSERT INTO login_attempts (username, ip_address, success, timestamp, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, ip_address, False, datetime.now().isoformat(), user_agent))
            
            # Get user
            cursor.execute('''
                SELECT user_id, username, email, password_hash, role, active, login_attempts, locked_until
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))
            
            user_data = cursor.fetchone()
            if not user_data:
                conn.commit()
                conn.close()
                return {"success": False, "error": "Invalid username or password"}
            
            user_id, db_username, email, password_hash, role, active, login_attempts, locked_until = user_data
            
            # Check if user is active
            if not active:
                conn.commit()
                conn.close()
                return {"success": False, "error": "Account is disabled"}
            
            # Check if account is locked
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < lock_time:
                    conn.commit()
                    conn.close()
                    return {"success": False, "error": f"Account locked until {locked_until}"}
                else:
                    # Unlock account
                    cursor.execute('''
                        UPDATE users SET locked_until = NULL, login_attempts = 0
                        WHERE user_id = ?
                    ''', (user_id,))
                    login_attempts = 0
            
            # Verify password
            if not check_password_hash(password_hash, password):
                # Increment failed attempts
                login_attempts += 1
                
                if login_attempts >= self.max_login_attempts:
                    # Lock account
                    locked_until = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()
                    cursor.execute('''
                        UPDATE users SET login_attempts = ?, locked_until = ?
                        WHERE user_id = ?
                    ''', (login_attempts, locked_until, user_id))
                    conn.commit()
                    conn.close()
                    return {"success": False, "error": f"Account locked due to too many failed attempts"}
                else:
                    cursor.execute('''
                        UPDATE users SET login_attempts = ?
                        WHERE user_id = ?
                    ''', (login_attempts, user_id))
                    conn.commit()
                    conn.close()
                    return {"success": False, "error": "Invalid username or password"}
            
            # Successful login - reset attempts and update last login
            cursor.execute('''
                UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            # Update login attempt record
            cursor.execute('''
                UPDATE login_attempts SET success = 1
                WHERE username = ? AND timestamp = (
                    SELECT MAX(timestamp) FROM login_attempts WHERE username = ?
                )
            ''', (username, username))
            
            conn.commit()
            conn.close()
            
            # Create session
            session_result = self.create_session(user_id, ip_address, user_agent)
            if not session_result["success"]:
                return session_result
            
            # Generate JWT token
            token = self.generate_jwt_token(user_id, db_username, role)
            
            return {
                "success": True,
                "user": {
                    "user_id": user_id,
                    "username": db_username,
                    "email": email,
                    "role": role
                },
                "session_id": session_result["session_id"],
                "token": token,
                "message": "Login successful"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_session(self, user_id: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Create user session"""
        try:
            session_id = secrets.token_urlsafe(32)
            created_at = datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, ip_address, user_agent, created_at, last_activity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, ip_address, user_agent, created_at, created_at))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "session_id": session_id,
                "created_at": created_at
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate and refresh session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, s.created_at, s.last_activity, s.active,
                       u.username, u.email, u.role, u.active as user_active
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.session_id = ?
            ''', (session_id,))
            
            session_data = cursor.fetchone()
            if not session_data:
                conn.close()
                return {"success": False, "error": "Invalid session"}
            
            user_id, created_at, last_activity, session_active, username, email, role, user_active = session_data
            
            if not session_active or not user_active:
                conn.close()
                return {"success": False, "error": "Session or user is inactive"}
            
            # Check session timeout
            last_activity_time = datetime.fromisoformat(last_activity)
            if (datetime.now() - last_activity_time).total_seconds() > self.session_timeout:
                # Expire session
                cursor.execute("UPDATE sessions SET active = 0 WHERE session_id = ?", (session_id,))
                conn.commit()
                conn.close()
                return {"success": False, "error": "Session expired"}
            
            # Update last activity
            cursor.execute('''
                UPDATE sessions SET last_activity = ? WHERE session_id = ?
            ''', (datetime.now().isoformat(), session_id))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "user": {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "role": role
                },
                "session": {
                    "session_id": session_id,
                    "created_at": created_at,
                    "last_activity": last_activity
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def logout_user(self, session_id: str) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE sessions SET active = 0 WHERE session_id = ?", (session_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return {"success": False, "error": "Session not found"}
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "Logged out successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_jwt_token(self, user_id: str, username: str, role: str) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {"success": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, email, role, active, created_at, last_login
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return {
                    "user_id": user_data[0],
                    "username": user_data[1],
                    "email": user_data[2],
                    "role": user_data[3],
                    "active": bool(user_data[4]),
                    "created_at": user_data[5],
                    "last_login": user_data[6]
                }
            
            return None
            
        except Exception:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, email, role, active, created_at, last_login
                FROM users WHERE username = ?
            ''', (username,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return {
                    "user_id": user_data[0],
                    "username": user_data[1],
                    "email": user_data[2],
                    "role": user_data[3],
                    "active": bool(user_data[4]),
                    "created_at": user_data[5],
                    "last_login": user_data[6]
                }
            
            return None
            
        except Exception:
            return None
    
    def update_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Update user password"""
        try:
            # Validate new password
            password_validation = self.validate_password(new_password)
            if not password_validation["valid"]:
                return {"success": False, "error": "Password validation failed", "details": password_validation["errors"]}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {"success": False, "error": "User not found"}
            
            current_password_hash = result[0]
            
            # Verify old password
            if not check_password_hash(current_password_hash, old_password):
                conn.close()
                return {"success": False, "error": "Current password is incorrect"}
            
            # Update password
            new_password_hash = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_password_hash, user_id))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "Password updated successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT permission FROM permissions WHERE user_id = ?", (user_id,))
            permissions = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return permissions
            
        except Exception:
            return []
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions or "admin_access" in user_permissions
    
    def get_active_sessions(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get active sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT session_id, user_id, ip_address, user_agent, created_at, last_activity
                    FROM sessions WHERE user_id = ? AND active = 1
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT s.session_id, s.user_id, s.ip_address, s.user_agent, s.created_at, s.last_activity, u.username
                    FROM sessions s
                    JOIN users u ON s.user_id = u.user_id
                    WHERE s.active = 1
                ''')
            
            sessions = []
            for row in cursor.fetchall():
                session = {
                    "session_id": row[0],
                    "user_id": row[1],
                    "ip_address": row[2],
                    "user_agent": row[3],
                    "created_at": row[4],
                    "last_activity": row[5]
                }
                if len(row) > 6:
                    session["username"] = row[6]
                sessions.append(session)
            
            conn.close()
            return sessions
            
        except Exception:
            return []
    
    def get_login_history(self, username: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get login attempt history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if username:
                cursor.execute('''
                    SELECT username, ip_address, success, timestamp, user_agent
                    FROM login_attempts WHERE username = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (username, limit))
            else:
                cursor.execute('''
                    SELECT username, ip_address, success, timestamp, user_agent
                    FROM login_attempts
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "username": row[0],
                    "ip_address": row[1],
                    "success": bool(row[2]),
                    "timestamp": row[3],
                    "user_agent": row[4]
                })
            
            conn.close()
            return history
            
        except Exception:
            return []

# Global authentication manager instance
auth_manager = AuthenticationManager()

def main():
    """Demo of authentication manager functionality"""
    
    # Register a test user
    register_result = auth_manager.register_user("testuser", "test@example.com", "TestPass123!")
    print("Registration result:", register_result)
    
    if register_result["success"]:
        # Authenticate user
        auth_result = auth_manager.authenticate_user("testuser", "TestPass123!", "127.0.0.1", "Test Browser")
        print("Authentication result:", auth_result)
        
        if auth_result["success"]:
            # Validate session
            session_validation = auth_manager.validate_session(auth_result["session_id"])
            print("Session validation:", session_validation)
            
            # Get user permissions
            permissions = auth_manager.get_user_permissions(auth_result["user"]["user_id"])
            print("User permissions:", permissions)
            
            # Logout
            logout_result = auth_manager.logout_user(auth_result["session_id"])
            print("Logout result:", logout_result)

if __name__ == "__main__":
    main()