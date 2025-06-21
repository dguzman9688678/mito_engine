#!/usr/bin/env python3
"""
MITO Engine - Comprehensive Audit System
Tracks all system activities, user interactions, security events, and compliance monitoring
"""

import os
import json
import sqlite3
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import time
from pathlib import Path
import traceback
import psutil
import platform

logger = logging.getLogger(__name__)

class AuditLevel(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"

class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    SYSTEM_OPERATION = "system_operation"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    SECURITY_EVENT = "security_event"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    ERROR = "error"

@dataclass
class AuditEvent:
    """Represents a single audit event"""
    id: str
    timestamp: str
    level: str
    category: str
    action: str
    user_id: Optional[str]
    session_id: Optional[str]
    resource: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    duration_ms: Optional[float]
    system_info: Dict[str, Any]

@dataclass
class ComplianceRule:
    """Defines a compliance monitoring rule"""
    id: str
    name: str
    description: str
    category: str
    rule_type: str
    conditions: Dict[str, Any]
    severity: str
    enabled: bool
    created_at: str

class AuditDatabase:
    """Database manager for audit logs"""
    
    def __init__(self, db_path: str = "audit_logs.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize audit database with proper indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main audit events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                duration_ms REAL,
                system_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Compliance rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_rules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                conditions TEXT NOT NULL,
                severity TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Compliance violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES compliance_rules (id),
                FOREIGN KEY (event_id) REFERENCES audit_events (id)
            )
        """)
        
        # Security incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_resources TEXT,
                attack_vector TEXT,
                source_ip TEXT,
                user_id TEXT,
                status TEXT DEFAULT 'investigating',
                assigned_to TEXT,
                resolved_at TIMESTAMP,
                resolution_summary TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Audit statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                level TEXT NOT NULL,
                count INTEGER NOT NULL,
                avg_duration_ms REAL,
                success_rate REAL,
                unique_users INTEGER,
                unique_sessions INTEGER,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_events(category)",
            "CREATE INDEX IF NOT EXISTS idx_audit_level ON audit_events(level)",
            "CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_events(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_rule ON compliance_violations(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_status ON compliance_violations(status)",
            "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON security_incidents(severity)",
            "CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        conn.commit()
        conn.close()

class AuditLogger:
    """Centralized audit logging system"""
    
    def __init__(self, db: AuditDatabase):
        self.db = db
        self.event_queue = queue.Queue()
        self.processing_thread = None
        self.running = False
        self.batch_size = 100
        self.flush_interval = 5  # seconds
        self.start_processor()
        
    def start_processor(self):
        """Start background event processor"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self.processing_thread.start()
        logger.info("Audit event processor started")
        
    def stop_processor(self):
        """Stop background event processor"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        self._flush_remaining_events()
        
    def log_event(self, level: AuditLevel, category: AuditCategory, action: str,
                  user_id: str = None, session_id: str = None, resource: str = None,
                  details: Dict[str, Any] = None, ip_address: str = None,
                  user_agent: str = None, success: bool = True,
                  duration_ms: float = None) -> str:
        """Log an audit event"""
        
        event_id = hashlib.sha256(
            f"{datetime.now().isoformat()}_{action}_{user_id}_{session_id}".encode()
        ).hexdigest()[:16]
        
        system_info = self._get_system_info()
        
        event = AuditEvent(
            id=event_id,
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            action=action,
            user_id=user_id,
            session_id=session_id,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            duration_ms=duration_ms,
            system_info=system_info
        )
        
        # Queue event for processing
        self.event_queue.put(event)
        
        return event_id
        
    def log_authentication(self, user_id: str, action: str, success: bool,
                          ip_address: str = None, details: Dict[str, Any] = None):
        """Log authentication events"""
        return self.log_event(
            level=AuditLevel.SECURITY if not success else AuditLevel.INFO,
            category=AuditCategory.AUTHENTICATION,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=success
        )
        
    def log_authorization(self, user_id: str, resource: str, action: str,
                         success: bool, details: Dict[str, Any] = None):
        """Log authorization events"""
        return self.log_event(
            level=AuditLevel.WARNING if not success else AuditLevel.INFO,
            category=AuditCategory.AUTHORIZATION,
            action=action,
            user_id=user_id,
            resource=resource,
            details=details,
            success=success
        )
        
    def log_data_access(self, user_id: str, resource: str, action: str,
                       session_id: str = None, details: Dict[str, Any] = None):
        """Log data access events"""
        return self.log_event(
            level=AuditLevel.INFO,
            category=AuditCategory.DATA_ACCESS,
            action=action,
            user_id=user_id,
            session_id=session_id,
            resource=resource,
            details=details
        )
        
    def log_api_call(self, endpoint: str, method: str, user_id: str = None,
                    session_id: str = None, response_code: int = 200,
                    duration_ms: float = None, ip_address: str = None):
        """Log API call events"""
        success = 200 <= response_code < 400
        level = AuditLevel.ERROR if response_code >= 500 else AuditLevel.INFO
        
        return self.log_event(
            level=level,
            category=AuditCategory.API_CALL,
            action=f"{method} {endpoint}",
            user_id=user_id,
            session_id=session_id,
            resource=endpoint,
            details={"method": method, "response_code": response_code},
            ip_address=ip_address,
            success=success,
            duration_ms=duration_ms
        )
        
    def log_security_event(self, event_type: str, severity: AuditLevel,
                          user_id: str = None, ip_address: str = None,
                          details: Dict[str, Any] = None):
        """Log security events"""
        return self.log_event(
            level=severity,
            category=AuditCategory.SECURITY_EVENT,
            action=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=False
        )
        
    def log_system_operation(self, operation: str, success: bool,
                           details: Dict[str, Any] = None,
                           duration_ms: float = None):
        """Log system operations"""
        level = AuditLevel.ERROR if not success else AuditLevel.INFO
        return self.log_event(
            level=level,
            category=AuditCategory.SYSTEM_OPERATION,
            action=operation,
            details=details,
            success=success,
            duration_ms=duration_ms
        )
        
    def _process_events(self):
        """Background event processor"""
        events_batch = []
        last_flush = time.time()
        
        while self.running or not self.event_queue.empty():
            try:
                # Get event with timeout
                try:
                    event = self.event_queue.get(timeout=1.0)
                    events_batch.append(event)
                except queue.Empty:
                    continue
                
                # Flush batch if full or time elapsed
                current_time = time.time()
                if (len(events_batch) >= self.batch_size or 
                    current_time - last_flush >= self.flush_interval):
                    
                    self._flush_events_batch(events_batch)
                    events_batch = []
                    last_flush = current_time
                    
            except Exception as e:
                logger.error(f"Error processing audit events: {e}")
                
        # Flush remaining events
        if events_batch:
            self._flush_events_batch(events_batch)
            
    def _flush_events_batch(self, events: List[AuditEvent]):
        """Flush batch of events to database"""
        if not events:
            return
            
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            for event in events:
                cursor.execute("""
                    INSERT INTO audit_events 
                    (id, timestamp, level, category, action, user_id, session_id,
                     resource, details, ip_address, user_agent, success,
                     duration_ms, system_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id, event.timestamp, event.level, event.category,
                    event.action, event.user_id, event.session_id, event.resource,
                    json.dumps(event.details), event.ip_address, event.user_agent,
                    event.success, event.duration_ms, json.dumps(event.system_info)
                ))
                
            conn.commit()
            conn.close()
            
            logger.debug(f"Flushed {len(events)} audit events to database")
            
        except Exception as e:
            logger.error(f"Failed to flush audit events: {e}")
            
    def _flush_remaining_events(self):
        """Flush any remaining events in queue"""
        remaining_events = []
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                remaining_events.append(event)
            except queue.Empty:
                break
                
        if remaining_events:
            self._flush_events_batch(remaining_events)
            
    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "process_id": os.getpid()
            }
        except Exception:
            return {"error": "Unable to collect system info"}

class ComplianceMonitor:
    """Monitors audit events for compliance violations"""
    
    def __init__(self, db: AuditDatabase):
        self.db = db
        self.rules = {}
        self.load_rules()
        
    def load_rules(self):
        """Load compliance rules from database"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM compliance_rules WHERE enabled = TRUE")
            rows = cursor.fetchall()
            
            for row in rows:
                rule = ComplianceRule(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    category=row[3],
                    rule_type=row[4],
                    conditions=json.loads(row[5]),
                    severity=row[6],
                    enabled=row[7],
                    created_at=row[8]
                )
                self.rules[rule.id] = rule
                
            conn.close()
            logger.info(f"Loaded {len(self.rules)} compliance rules")
            
        except Exception as e:
            logger.error(f"Failed to load compliance rules: {e}")
            
    def add_rule(self, rule: ComplianceRule) -> bool:
        """Add new compliance rule"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO compliance_rules
                (id, name, description, category, rule_type, conditions, severity, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.id, rule.name, rule.description, rule.category,
                rule.rule_type, json.dumps(rule.conditions), rule.severity, rule.enabled
            ))
            
            conn.commit()
            conn.close()
            
            self.rules[rule.id] = rule
            logger.info(f"Added compliance rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add compliance rule: {e}")
            return False
            
    def check_event_compliance(self, event: AuditEvent) -> List[str]:
        """Check if event violates any compliance rules"""
        violations = []
        
        for rule_id, rule in self.rules.items():
            if self._evaluate_rule(rule, event):
                violation_id = self._record_violation(rule_id, event)
                violations.append(violation_id)
                
        return violations
        
    def _evaluate_rule(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Evaluate if event violates the rule"""
        conditions = rule.conditions
        
        try:
            # Category-based rules
            if rule.rule_type == "category_frequency":
                return self._check_frequency_violation(rule, event)
            elif rule.rule_type == "failed_attempts":
                return self._check_failed_attempts(rule, event)
            elif rule.rule_type == "privileged_access":
                return self._check_privileged_access(rule, event)
            elif rule.rule_type == "data_access_pattern":
                return self._check_data_access_pattern(rule, event)
            elif rule.rule_type == "time_based":
                return self._check_time_based_violation(rule, event)
                
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")
            return False
            
    def _check_frequency_violation(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Check for frequency-based violations"""
        conditions = rule.conditions
        category = conditions.get("category")
        max_count = conditions.get("max_count", 100)
        time_window = conditions.get("time_window_minutes", 60)
        
        if event.category != category:
            return False
            
        # Check frequency in time window
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM audit_events 
            WHERE category = ? AND user_id = ? 
            AND timestamp >= datetime('now', '-{} minutes')
        """.format(time_window), (category, event.user_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > max_count
        
    def _check_failed_attempts(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Check for repeated failed attempts"""
        conditions = rule.conditions
        max_failures = conditions.get("max_failures", 5)
        time_window = conditions.get("time_window_minutes", 15)
        
        if event.success or event.category != "authentication":
            return False
            
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM audit_events 
            WHERE category = 'authentication' AND success = FALSE
            AND user_id = ? AND timestamp >= datetime('now', '-{} minutes')
        """.format(time_window), (event.user_id,))
        
        failures = cursor.fetchone()[0]
        conn.close()
        
        return failures >= max_failures
        
    def _check_privileged_access(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Check for unauthorized privileged access"""
        conditions = rule.conditions
        privileged_actions = conditions.get("privileged_actions", [])
        authorized_roles = conditions.get("authorized_roles", [])
        
        if event.action not in privileged_actions:
            return False
            
        # Check if user has authorized role (would need role system)
        user_roles = event.details.get("user_roles", [])
        return not any(role in authorized_roles for role in user_roles)
        
    def _check_data_access_pattern(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Check for suspicious data access patterns"""
        conditions = rule.conditions
        sensitive_resources = conditions.get("sensitive_resources", [])
        max_resources = conditions.get("max_resources_per_hour", 50)
        
        if event.category != "data_access":
            return False
            
        if event.resource not in sensitive_resources:
            return False
            
        # Check access frequency
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(DISTINCT resource) FROM audit_events 
            WHERE category = 'data_access' AND user_id = ?
            AND timestamp >= datetime('now', '-1 hour')
        """, (event.user_id,))
        
        resource_count = cursor.fetchone()[0]
        conn.close()
        
        return resource_count > max_resources
        
    def _check_time_based_violation(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Check for time-based access violations"""
        conditions = rule.conditions
        allowed_hours = conditions.get("allowed_hours", [])  # 24-hour format
        
        if not allowed_hours:
            return False
            
        current_hour = datetime.now().hour
        return current_hour not in allowed_hours
        
    def _record_violation(self, rule_id: str, event: AuditEvent) -> str:
        """Record compliance violation"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            rule = self.rules[rule_id]
            
            cursor.execute("""
                INSERT INTO compliance_violations
                (rule_id, event_id, violation_type, severity, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_id, event.id, rule.rule_type, rule.severity,
                f"Compliance violation: {rule.name}"
            ))
            
            violation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.warning(f"Compliance violation recorded: {rule.name} (ID: {violation_id})")
            return str(violation_id)
            
        except Exception as e:
            logger.error(f"Failed to record compliance violation: {e}")
            return None

class SecurityIncidentManager:
    """Manages security incidents and automated responses"""
    
    def __init__(self, db: AuditDatabase):
        self.db = db
        self.incident_threshold = {
            "failed_login_attempts": 5,
            "suspicious_data_access": 10,
            "privilege_escalation": 1,
            "malware_detection": 1
        }
        
    def create_incident(self, incident_type: str, severity: str, description: str,
                       affected_resources: List[str] = None, source_ip: str = None,
                       user_id: str = None) -> int:
        """Create new security incident"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO security_incidents
                (incident_type, severity, description, affected_resources,
                 source_ip, user_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'investigating')
            """, (
                incident_type, severity, description,
                json.dumps(affected_resources or []), source_ip, user_id
            ))
            
            incident_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.critical(f"Security incident created: {incident_type} (ID: {incident_id})")
            return incident_id
            
        except Exception as e:
            logger.error(f"Failed to create security incident: {e}")
            return None
            
    def auto_respond_to_threat(self, incident_type: str, user_id: str = None,
                              ip_address: str = None):
        """Automatic threat response"""
        if incident_type == "failed_login_attempts" and user_id:
            self._lock_user_account(user_id)
        elif incident_type == "suspicious_ip" and ip_address:
            self._block_ip_address(ip_address)
        elif incident_type == "privilege_escalation" and user_id:
            self._revoke_user_permissions(user_id)
            
    def _lock_user_account(self, user_id: str):
        """Lock user account temporarily"""
        logger.warning(f"Auto-response: Locking user account {user_id}")
        # Implementation would integrate with user management system
        
    def _block_ip_address(self, ip_address: str):
        """Block suspicious IP address"""
        logger.warning(f"Auto-response: Blocking IP address {ip_address}")
        # Implementation would integrate with firewall/security system
        
    def _revoke_user_permissions(self, user_id: str):
        """Revoke elevated permissions"""
        logger.warning(f"Auto-response: Revoking permissions for user {user_id}")
        # Implementation would integrate with authorization system

class AuditAnalytics:
    """Provides analytics and reporting on audit data"""
    
    def __init__(self, db: AuditDatabase):
        self.db = db
        
    def generate_daily_statistics(self, date: str = None) -> Dict[str, Any]:
        """Generate daily audit statistics"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Total events by category
            cursor.execute("""
                SELECT category, level, COUNT(*), AVG(duration_ms),
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate,
                       COUNT(DISTINCT user_id), COUNT(DISTINCT session_id)
                FROM audit_events 
                WHERE DATE(timestamp) = ?
                GROUP BY category, level
            """, (date,))
            
            stats = {}
            for row in cursor.fetchall():
                category, level, count, avg_duration, success_rate, unique_users, unique_sessions = row
                
                if category not in stats:
                    stats[category] = {}
                    
                stats[category][level] = {
                    "count": count,
                    "avg_duration_ms": avg_duration,
                    "success_rate": success_rate,
                    "unique_users": unique_users,
                    "unique_sessions": unique_sessions
                }
                
            # Security incidents
            cursor.execute("""
                SELECT severity, COUNT(*) FROM security_incidents 
                WHERE DATE(detected_at) = ?
                GROUP BY severity
            """, (date,))
            
            security_incidents = dict(cursor.fetchall())
            
            # Compliance violations
            cursor.execute("""
                SELECT severity, COUNT(*) FROM compliance_violations 
                WHERE DATE(detected_at) = ?
                GROUP BY severity
            """, (date,))
            
            compliance_violations = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "date": date,
                "statistics": stats,
                "security_incidents": security_incidents,
                "compliance_violations": compliance_violations,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate daily statistics: {e}")
            return {}
            
    def get_user_activity_summary(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Activity by category
            cursor.execute("""
                SELECT category, COUNT(*), 
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM audit_events 
                WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
                GROUP BY category
            """.format(days), (user_id,))
            
            activity_by_category = {}
            for category, count, success_rate in cursor.fetchall():
                activity_by_category[category] = {
                    "count": count,
                    "success_rate": success_rate
                }
                
            # Recent failures
            cursor.execute("""
                SELECT action, COUNT(*) FROM audit_events 
                WHERE user_id = ? AND success = FALSE 
                AND timestamp >= datetime('now', '-{} days')
                GROUP BY action
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """.format(days), (user_id,))
            
            recent_failures = dict(cursor.fetchall())
            
            # Compliance violations
            cursor.execute("""
                SELECT cv.severity, COUNT(*) FROM compliance_violations cv
                JOIN audit_events ae ON cv.event_id = ae.id
                WHERE ae.user_id = ? AND cv.detected_at >= datetime('now', '-{} days')
                GROUP BY cv.severity
            """.format(days), (user_id,))
            
            violations = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "user_id": user_id,
                "period_days": days,
                "activity_by_category": activity_by_category,
                "recent_failures": recent_failures,
                "compliance_violations": violations,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {e}")
            return {}

class MITOAuditSystem:
    """Main MITO Audit System"""
    
    def __init__(self):
        self.db = AuditDatabase()
        self.logger = AuditLogger(self.db)
        self.compliance_monitor = ComplianceMonitor(self.db)
        self.incident_manager = SecurityIncidentManager(self.db)
        self.analytics = AuditAnalytics(self.db)
        self.init_default_compliance_rules()
        
    def init_default_compliance_rules(self):
        """Initialize default compliance rules"""
        default_rules = [
            ComplianceRule(
                id="failed_login_limit",
                name="Failed Login Attempts Limit",
                description="Alert on excessive failed login attempts",
                category="authentication",
                rule_type="failed_attempts",
                conditions={"max_failures": 5, "time_window_minutes": 15},
                severity="high",
                enabled=True,
                created_at=datetime.now().isoformat()
            ),
            ComplianceRule(
                id="privileged_access_control",
                name="Privileged Access Control",
                description="Monitor privileged operations",
                category="authorization",
                rule_type="privileged_access",
                conditions={
                    "privileged_actions": ["admin_login", "user_create", "permission_modify"],
                    "authorized_roles": ["admin", "system"]
                },
                severity="critical",
                enabled=True,
                created_at=datetime.now().isoformat()
            ),
            ComplianceRule(
                id="data_access_frequency",
                name="Excessive Data Access",
                description="Alert on unusual data access patterns",
                category="data_access",
                rule_type="data_access_pattern",
                conditions={
                    "sensitive_resources": ["user_data", "financial_data", "personal_info"],
                    "max_resources_per_hour": 50
                },
                severity="medium",
                enabled=True,
                created_at=datetime.now().isoformat()
            )
        ]
        
        for rule in default_rules:
            self.compliance_monitor.add_rule(rule)
            
    def shutdown(self):
        """Gracefully shutdown audit system"""
        logger.info("Shutting down MITO Audit System")
        self.logger.stop_processor()

def main():
    """Demo of audit system capabilities"""
    print("MITO Engine - Comprehensive Audit System Demo")
    print("=" * 50)
    
    # Initialize audit system
    audit_system = MITOAuditSystem()
    
    print("\n1. Logging sample audit events...")
    
    # Sample authentication events
    audit_system.logger.log_authentication(
        user_id="user123",
        action="login_attempt",
        success=True,
        ip_address="192.168.1.100",
        details={"method": "password", "browser": "Chrome"}
    )
    
    # Sample failed login
    for i in range(6):  # Trigger compliance rule
        audit_system.logger.log_authentication(
            user_id="user456",
            action="login_attempt",
            success=False,
            ip_address="192.168.1.200",
            details={"method": "password", "reason": "invalid_password"}
        )
    
    # Sample API calls
    audit_system.logger.log_api_call(
        endpoint="/api/users",
        method="GET",
        user_id="user123",
        response_code=200,
        duration_ms=45.2
    )
    
    # Sample data access
    audit_system.logger.log_data_access(
        user_id="user123",
        resource="user_data",
        action="read",
        details={"record_count": 50}
    )
    
    # Sample security event
    audit_system.logger.log_security_event(
        event_type="suspicious_activity",
        severity=AuditLevel.WARNING,
        ip_address="192.168.1.200",
        details={"pattern": "repeated_failed_logins"}
    )
    
    print("   ✓ Sample events logged")
    
    # Wait for processing
    time.sleep(2)
    
    print("\n2. Generating analytics...")
    
    # Daily statistics
    daily_stats = audit_system.analytics.generate_daily_statistics()
    print(f"   ✓ Daily statistics: {len(daily_stats.get('statistics', {}))} categories")
    
    # User activity
    user_activity = audit_system.analytics.get_user_activity_summary("user123", days=1)
    print(f"   ✓ User activity: {len(user_activity.get('activity_by_category', {}))} categories")
    
    print("\n3. Compliance monitoring...")
    print(f"   ✓ Active rules: {len(audit_system.compliance_monitor.rules)}")
    
    print("\n4. Security incidents...")
    # Create sample incident
    incident_id = audit_system.incident_manager.create_incident(
        incident_type="failed_login_attempts",
        severity="high",
        description="Excessive failed login attempts detected",
        source_ip="192.168.1.200",
        user_id="user456"
    )
    print(f"   ✓ Created security incident: {incident_id}")
    
    print("\nAudit system demo completed successfully!")
    
    # Cleanup
    audit_system.shutdown()

if __name__ == "__main__":
    main()