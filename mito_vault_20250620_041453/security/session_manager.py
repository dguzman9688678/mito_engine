"""
MITO Engine - Session and Profile Management
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Session persistence and profile-based customization
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from flask import session, request
import sqlite3
import hashlib

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions, preferences, and workspace states"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize session database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_data TEXT,
                    workspace_state TEXT,
                    tab_states TEXT,
                    preferences TEXT
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    role TEXT DEFAULT 'developer',
                    tool_permissions TEXT,
                    custom_layout TEXT,
                    theme_preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit trail table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    user_id TEXT,
                    action_type TEXT,
                    action_details TEXT,
                    tab_context TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Session database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize session database: {e}")
            
    def get_session_id(self) -> str:
        """Get or create session ID"""
        if 'mito_session_id' not in session:
            session['mito_session_id'] = hashlib.md5(
                f"{time.time()}{request.remote_addr}".encode()
            ).hexdigest()
        return session['mito_session_id']
        
    def save_tab_state(self, session_id: str, tab_id: str, state: Dict[str, Any]):
        """Save tab state for session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing tab states
            cursor.execute("SELECT tab_states FROM user_sessions WHERE session_id = ?", (session_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                tab_states = json.loads(result[0])
            else:
                tab_states = {}
                
            tab_states[tab_id] = {
                'state': state,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update or insert session
            cursor.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (session_id, tab_states, last_activity) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (session_id, json.dumps(tab_states)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save tab state: {e}")
            
    def get_tab_states(self, session_id: str) -> Dict[str, Any]:
        """Get all tab states for session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT tab_states FROM user_sessions WHERE session_id = ?", (session_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get tab states: {e}")
            return {}
            
    def save_workspace_state(self, session_id: str, workspace_data: Dict[str, Any]):
        """Save workspace state"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (session_id, workspace_state, last_activity) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (session_id, json.dumps(workspace_data)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save workspace state: {e}")
            
    def get_workspace_state(self, session_id: str) -> Dict[str, Any]:
        """Get workspace state for session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT workspace_state FROM user_sessions WHERE session_id = ?", (session_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get workspace state: {e}")
            return {}

class ProfileManager:
    """Manages user profiles and role-based tool access"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        self.role_permissions = {
            'developer': [
                'workspace', 'ai-chat', 'code-editor', 'file-browser', 
                'project-tools', 'analytics', 'advanced'
            ],
            'operations': [
                'workspace', 'analytics', 'advanced', 'networking', 
                'monitoring', 'deployment'
            ],
            'analyst': [
                'workspace', 'ai-chat', 'analytics', 'reporting', 
                'data-tools'
            ],
            'admin': [
                'workspace', 'ai-chat', 'code-editor', 'file-browser',
                'project-tools', 'analytics', 'advanced', 'networking',
                'monitoring', 'deployment', 'security', 'audit'
            ]
        }
        
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile and permissions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, tool_permissions, custom_layout, theme_preferences 
                FROM user_profiles WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                role, permissions, layout, theme = result
                return {
                    'role': role,
                    'permissions': json.loads(permissions) if permissions else self.role_permissions.get(role, []),
                    'layout': json.loads(layout) if layout else {},
                    'theme': json.loads(theme) if theme else {}
                }
            else:
                # Default profile for new users
                return {
                    'role': 'developer',
                    'permissions': self.role_permissions['developer'],
                    'layout': {},
                    'theme': {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {'role': 'developer', 'permissions': self.role_permissions['developer'], 'layout': {}, 'theme': {}}
            
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update user profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles 
                (user_id, role, tool_permissions, custom_layout, theme_preferences, updated_at) 
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                profile_data.get('role', 'developer'),
                json.dumps(profile_data.get('permissions', [])),
                json.dumps(profile_data.get('layout', {})),
                json.dumps(profile_data.get('theme', {}))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")

class AuditTrail:
    """Tracks user actions and system changes"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        
    def log_action(self, session_id: str, user_id: str, action_type: str, 
                   action_details: str, tab_context: str = None):
        """Log user action to audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_trail 
                (session_id, user_id, action_type, action_details, tab_context, ip_address, user_agent) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                action_type,
                action_details,
                tab_context,
                request.remote_addr if request else None,
                request.headers.get('User-Agent') if request else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log action to audit trail: {e}")
            
    def get_audit_log(self, session_id: str = None, user_id: str = None, 
                      days: int = 7) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            where_clause = "WHERE timestamp >= datetime('now', '-{} days')".format(days)
            params = []
            
            if session_id:
                where_clause += " AND session_id = ?"
                params.append(session_id)
                
            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)
                
            cursor.execute(f"""
                SELECT * FROM audit_trail {where_clause} 
                ORDER BY timestamp DESC LIMIT 1000
            """, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            conn.close()
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get audit log: {e}")
            return []

class TelemetryStreamer:
    """Streams real-time system metrics and logs"""
    
    def __init__(self):
        self.active_streams = {}
        
    def start_stream(self, session_id: str, stream_type: str):
        """Start telemetry stream for session"""
        if session_id not in self.active_streams:
            self.active_streams[session_id] = []
            
        if stream_type not in self.active_streams[session_id]:
            self.active_streams[session_id].append(stream_type)
            
    def stop_stream(self, session_id: str, stream_type: str = None):
        """Stop telemetry stream"""
        if session_id in self.active_streams:
            if stream_type:
                if stream_type in self.active_streams[session_id]:
                    self.active_streams[session_id].remove(stream_type)
            else:
                del self.active_streams[session_id]
                
    def get_live_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'disk_usage': (disk.used / disk.total) * 100,
                'disk_free': disk.free,
                'network_sent': network.bytes_sent,
                'network_received': network.bytes_recv,
                'active_sessions': len(self.active_streams)
            }
            
        except Exception as e:
            logger.error(f"Failed to get live metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

class ReportGenerator:
    """Generates exportable reports and certificates"""
    
    def __init__(self, db_path: str = "mito_sessions.db"):
        self.db_path = db_path
        
    def generate_audit_report(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        audit_trail = AuditTrail(self.db_path)
        audit_data = audit_trail.get_audit_log(user_id=user_id, days=days)
        
        # Analyze audit data
        action_counts = {}
        tab_usage = {}
        hourly_activity = {}
        
        for entry in audit_data:
            action_type = entry['action_type']
            tab_context = entry['tab_context']
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            hour = timestamp.hour
            
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            if tab_context:
                tab_usage[tab_context] = tab_usage.get(tab_context, 0) + 1
                
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
            
        return {
            'report_id': hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest(),
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'total_actions': len(audit_data),
            'action_breakdown': action_counts,
            'tab_usage': tab_usage,
            'hourly_activity': hourly_activity,
            'raw_data': audit_data
        }
        
    def generate_system_report(self) -> Dict[str, Any]:
        """Generate system status and performance report"""
        telemetry = TelemetryStreamer()
        metrics = telemetry.get_live_metrics()
        
        # Additional system information
        import platform
        import psutil
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'total_memory': psutil.virtual_memory().total,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        return {
            'report_id': hashlib.md5(f"system{time.time()}".encode()).hexdigest(),
            'generated_at': datetime.now().isoformat(),
            'system_info': system_info,
            'current_metrics': metrics,
            'mito_version': '1.2.0'
        }
        
    def export_to_pdf(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Export report to PDF format"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            filename = f"mito_{report_type}_report_{report_data['report_id']}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.darkblue
            )
            story.append(Paragraph(f"MITO Engine {report_type.title()} Report", title_style))
            story.append(Spacer(1, 12))
            
            # Report metadata
            story.append(Paragraph(f"Report ID: {report_data['report_id']}", styles['Normal']))
            story.append(Paragraph(f"Generated: {report_data['generated_at']}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Report content based on type
            if report_type == 'audit':
                story.append(Paragraph("Audit Summary", styles['Heading2']))
                story.append(Paragraph(f"Total Actions: {report_data['total_actions']}", styles['Normal']))
                story.append(Paragraph(f"Period: {report_data['period_days']} days", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Action breakdown table
                if report_data['action_breakdown']:
                    story.append(Paragraph("Action Breakdown", styles['Heading3']))
                    action_data = [['Action Type', 'Count']]
                    for action, count in report_data['action_breakdown'].items():
                        action_data.append([action, str(count)])
                    
                    action_table = Table(action_data)
                    action_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(action_table)
                    
            elif report_type == 'system':
                story.append(Paragraph("System Information", styles['Heading2']))
                for key, value in report_data['system_info'].items():
                    story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", styles['Normal']))
                story.append(Spacer(1, 12))
                
                story.append(Paragraph("Current Metrics", styles['Heading2']))
                for key, value in report_data['current_metrics'].items():
                    if key != 'timestamp':
                        story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", styles['Normal']))
            
            doc.build(story)
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return None
            
    def export_to_csv(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Export report to CSV format"""
        try:
            import csv
            
            filename = f"mito_{report_type}_report_{report_data['report_id']}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                if report_type == 'audit' and 'raw_data' in report_data:
                    # Write audit data
                    if report_data['raw_data']:
                        headers = list(report_data['raw_data'][0].keys())
                        writer.writerow(headers)
                        
                        for entry in report_data['raw_data']:
                            writer.writerow([entry.get(header, '') for header in headers])
                            
                elif report_type == 'system':
                    # Write system metrics
                    writer.writerow(['Metric', 'Value'])
                    for key, value in report_data['current_metrics'].items():
                        writer.writerow([key, value])
                        
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return None