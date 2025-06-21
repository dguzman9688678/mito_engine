"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    API_USAGE_WARNING = "api_usage_warning"
    API_SWITCH_SUGGESTION = "api_switch_suggestion"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    FUNCTION_START = "function_start"
    FUNCTION_COMPLETE = "function_complete"
    SYSTEM_ALERT = "system_alert"
    COST_ALERT = "cost_alert"

@dataclass
class Notification:
    id: str
    type: NotificationType
    title: str
    message: str
    timestamp: datetime
    priority: str = "medium"  # low, medium, high, urgent
    read: bool = False
    data: Optional[Dict] = None

class NotificationManager:
    """Manages all MITO notifications and alerts"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.notification_file = "mito_notifications.json"
        self.user_preferences = {
            "api_usage_threshold": 80,  # Notify at 80% usage
            "cost_threshold": 10.0,     # Notify at $10 spend
            "phase_notifications": True,
            "task_notifications": True,
            "function_notifications": False  # Can be noisy
        }
        self.load_notifications()
    
    def create_notification(self, 
                          notification_type: NotificationType,
                          title: str,
                          message: str,
                          priority: str = "medium",
                          data: Optional[Dict] = None) -> str:
        """Create a new notification"""
        notification_id = f"notif_{int(time.time())}_{len(self.notifications)}"
        
        notification = Notification(
            id=notification_id,
            type=notification_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            priority=priority,
            data=data or {}
        )
        
        self.notifications.append(notification)
        self.save_notifications()
        
        # Log high priority notifications
        if priority in ["high", "urgent"]:
            logger.warning(f"NOTIFICATION: {title} - {message}")
        else:
            logger.info(f"NOTIFICATION: {title}")
        
        return notification_id
    
    def get_recent_notifications(self, limit: int = 50) -> List[Notification]:
        """Get recent notifications, limited by count"""
        # Sort by timestamp descending and return limited results
        sorted_notifications = sorted(self.notifications, key=lambda x: x.timestamp, reverse=True)
        return sorted_notifications[:limit]
    
    def notify_api_usage(self, provider: str, usage_percent: float, requests_made: int, limit: int):
        """Notify about API usage levels"""
        if usage_percent >= self.user_preferences["api_usage_threshold"]:
            priority = "high" if usage_percent >= 90 else "medium"
            
            message = f"""
            API Usage Alert for {provider}:
            
            Current Usage: {usage_percent:.1f}%
            Requests Made: {requests_made:,}
            Limit: {limit:,}
            Remaining: {limit - requests_made:,}
            
            Consider switching to backup API if needed.
            """
            
            self.create_notification(
                NotificationType.API_USAGE_WARNING,
                f"{provider} API Usage: {usage_percent:.1f}%",
                message,
                priority,
                {
                    "provider": provider,
                    "usage_percent": usage_percent,
                    "requests_made": requests_made,
                    "limit": limit
                }
            )
    
    def suggest_api_switch(self, current_provider: str, suggested_provider: str, reason: str):
        """Suggest switching to a different API"""
        message = f"""
        API Switch Recommendation:
        
        Current: {current_provider}
        Suggested: {suggested_provider}
        Reason: {reason}
        
        Would you like MITO to automatically switch providers?
        """
        
        self.create_notification(
            NotificationType.API_SWITCH_SUGGESTION,
            f"Switch from {current_provider} to {suggested_provider}",
            message,
            "medium",
            {
                "current_provider": current_provider,
                "suggested_provider": suggested_provider,
                "reason": reason
            }
        )
    
    def notify_task_start(self, task_name: str, estimated_duration: str = None):
        """Notify when a task starts"""
        if not self.user_preferences["task_notifications"]:
            return
            
        message = f"Starting task: {task_name}"
        if estimated_duration:
            message += f"\nEstimated duration: {estimated_duration}"
        
        self.create_notification(
            NotificationType.TASK_START,
            f"Task Started: {task_name}",
            message,
            "low",
            {"task_name": task_name, "start_time": datetime.now().isoformat()}
        )
    
    def notify_task_complete(self, task_name: str, duration: str = None, success: bool = True):
        """Notify when a task completes"""
        if not self.user_preferences["task_notifications"]:
            return
            
        status = "✓ Completed" if success else "✗ Failed"
        message = f"Task {status}: {task_name}"
        if duration:
            message += f"\nDuration: {duration}"
        
        priority = "low" if success else "medium"
        
        self.create_notification(
            NotificationType.TASK_COMPLETE,
            f"Task {status}: {task_name}",
            message,
            priority,
            {
                "task_name": task_name,
                "success": success,
                "duration": duration,
                "end_time": datetime.now().isoformat()
            }
        )
    
    def notify_phase_start(self, phase_name: str, phase_number: int = None):
        """Notify when a project phase starts"""
        if not self.user_preferences["phase_notifications"]:
            return
            
        title = f"Phase {phase_number}: {phase_name}" if phase_number else f"Phase Started: {phase_name}"
        message = f"Beginning development phase: {phase_name}"
        
        self.create_notification(
            NotificationType.PHASE_START,
            title,
            message,
            "medium",
            {
                "phase_name": phase_name,
                "phase_number": phase_number,
                "start_time": datetime.now().isoformat()
            }
        )
    
    def notify_phase_complete(self, phase_name: str, phase_number: int = None, next_phase: str = None):
        """Notify when a project phase completes"""
        if not self.user_preferences["phase_notifications"]:
            return
            
        title = f"Phase {phase_number} Complete: {phase_name}" if phase_number else f"Phase Complete: {phase_name}"
        message = f"✓ Completed phase: {phase_name}"
        
        if next_phase:
            message += f"\nNext phase: {next_phase}"
        
        self.create_notification(
            NotificationType.PHASE_COMPLETE,
            title,
            message,
            "medium",
            {
                "phase_name": phase_name,
                "phase_number": phase_number,
                "next_phase": next_phase,
                "end_time": datetime.now().isoformat()
            }
        )
    
    def notify_function_start(self, function_name: str, context: str = None):
        """Notify when a function starts executing"""
        if not self.user_preferences["function_notifications"]:
            return
            
        message = f"Executing function: {function_name}"
        if context:
            message += f"\nContext: {context}"
        
        self.create_notification(
            NotificationType.FUNCTION_START,
            f"Function Started: {function_name}",
            message,
            "low",
            {"function_name": function_name, "context": context}
        )
    
    def notify_function_complete(self, function_name: str, result: str = None, success: bool = True):
        """Notify when a function completes"""
        if not self.user_preferences["function_notifications"]:
            return
            
        status = "✓ Completed" if success else "✗ Failed"
        message = f"Function {status}: {function_name}"
        if result:
            message += f"\nResult: {result}"
        
        self.create_notification(
            NotificationType.FUNCTION_COMPLETE,
            f"Function {status}: {function_name}",
            message,
            "low",
            {"function_name": function_name, "result": result, "success": success}
        )
    
    def notify_cost_alert(self, provider: str, current_cost: float, threshold: float):
        """Notify about API cost thresholds"""
        if current_cost >= threshold:
            message = f"""
            Cost Alert for {provider}:
            
            Current Spend: ${current_cost:.2f}
            Threshold: ${threshold:.2f}
            
            Consider switching to free alternatives or monitoring usage.
            """
            
            self.create_notification(
                NotificationType.COST_ALERT,
                f"Cost Alert: ${current_cost:.2f} on {provider}",
                message,
                "high",
                {
                    "provider": provider,
                    "current_cost": current_cost,
                    "threshold": threshold
                }
            )
    
    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications"""
        return [n for n in self.notifications if not n.read]
    
    def get_recent_notifications(self, hours: int = 24) -> List[Notification]:
        """Get notifications from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [n for n in self.notifications if n.timestamp >= cutoff_time]
    
    def add_notification(self, title: str, message: str, notification_type: str = "info"):
        """Add notification with simple interface for compatibility"""
        type_mapping = {
            "info": NotificationType.SYSTEM_ALERT,
            "success": NotificationType.TASK_COMPLETE,
            "warning": NotificationType.API_USAGE_WARNING,
            "error": NotificationType.SYSTEM_ALERT
        }
        
        notif_type = type_mapping.get(notification_type, NotificationType.SYSTEM_ALERT)
        priority = "high" if notification_type == "error" else "medium"
        
        return self.create_notification(notif_type, title, message, priority)
    
    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                self.save_notifications()
                break
    
    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than N days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.notifications = [n for n in self.notifications if n.timestamp >= cutoff_time]
        self.save_notifications()
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update notification preferences"""
        self.user_preferences.update(preferences)
        self.save_notifications()
    
    def save_notifications(self):
        """Save notifications to file"""
        try:
            data = {
                "notifications": [
                    {
                        "id": n.id,
                        "type": n.type.value,
                        "title": n.title,
                        "message": n.message,
                        "timestamp": n.timestamp.isoformat(),
                        "priority": n.priority,
                        "read": n.read,
                        "data": n.data
                    }
                    for n in self.notifications
                ],
                "preferences": self.user_preferences
            }
            
            with open(self.notification_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save notifications: {e}")
    
    def load_notifications(self):
        """Load notifications from file"""
        try:
            if os.path.exists(self.notification_file):
                with open(self.notification_file, 'r') as f:
                    data = json.load(f)
                
                self.user_preferences.update(data.get("preferences", {}))
                
                for n_data in data.get("notifications", []):
                    notification = Notification(
                        id=n_data["id"],
                        type=NotificationType(n_data["type"]),
                        title=n_data["title"],
                        message=n_data["message"],
                        timestamp=datetime.fromisoformat(n_data["timestamp"]),
                        priority=n_data["priority"],
                        read=n_data["read"],
                        data=n_data.get("data", {})
                    )
                    self.notifications.append(notification)
                    
        except Exception as e:
            logger.error(f"Failed to load notifications: {e}")
    
    def get_notification_summary(self) -> Dict[str, Any]:
        """Get summary of current notifications"""
        unread = self.get_unread_notifications()
        recent = self.get_recent_notifications()
        
        return {
            "total_notifications": len(self.notifications),
            "unread_count": len(unread),
            "recent_count": len(recent),
            "high_priority_unread": len([n for n in unread if n.priority in ["high", "urgent"]]),
            "latest_notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "priority": n.priority,
                    "timestamp": n.timestamp.isoformat(),
                    "read": n.read
                }
                for n in sorted(self.notifications, key=lambda x: x.timestamp, reverse=True)[:5]
            ]
        }