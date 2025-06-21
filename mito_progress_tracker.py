#!/usr/bin/env python3
"""
MITO Engine - Live Progress Tracker
Real-time progress monitoring for autonomous agent tasks and functions
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Real-time progress tracking for MITO autonomous operations"""
    
    def __init__(self, db_path: str = "mito_progress.db"):
        self.db_path = db_path
        self.active_tasks = {}
        self.function_progress = {}
        self.system_metrics = {}
        self.init_database()
        
    def init_database(self):
        """Initialize progress tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Task progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                estimated_duration INTEGER DEFAULT 60,
                current_step TEXT,
                progress_percent REAL DEFAULT 0.0,
                status TEXT DEFAULT 'running',
                steps_completed INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 1,
                last_update TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Function metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS function_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT NOT NULL,
                execution_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_duration REAL DEFAULT 0.0,
                last_execution TEXT,
                status TEXT DEFAULT 'idle'
            )
        """)
        
        conn.commit()
        conn.close()
        
    def start_task(self, task_id: str, task_name: str, estimated_duration: int = 60, total_steps: int = 1):
        """Start tracking a new task"""
        task_data = {
            "task_id": task_id,
            "task_name": task_name,
            "start_time": datetime.now().isoformat(),
            "estimated_duration": estimated_duration,
            "current_step": "Initializing",
            "progress_percent": 0.0,
            "status": "running",
            "steps_completed": 0,
            "total_steps": total_steps,
            "last_update": datetime.now().isoformat()
        }
        
        self.active_tasks[task_id] = task_data
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO task_progress 
            (task_id, task_name, start_time, estimated_duration, current_step, total_steps)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, task_name, task_data["start_time"], estimated_duration, "Initializing", total_steps))
        conn.commit()
        conn.close()
        
    def update_task_progress(self, task_id: str, step_name: str, progress_percent: float, steps_completed: int = None):
        """Update task progress"""
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        task["current_step"] = step_name
        task["progress_percent"] = min(100.0, max(0.0, progress_percent))
        task["last_update"] = datetime.now().isoformat()
        
        if steps_completed is not None:
            task["steps_completed"] = steps_completed
            if task["total_steps"] > 0:
                task["progress_percent"] = (steps_completed / task["total_steps"]) * 100
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE task_progress 
            SET current_step = ?, progress_percent = ?, steps_completed = ?, last_update = ?
            WHERE task_id = ?
        """, (step_name, task["progress_percent"], task["steps_completed"], task["last_update"], task_id))
        conn.commit()
        conn.close()
        
    def complete_task(self, task_id: str, success: bool = True):
        """Mark task as completed"""
        if task_id not in self.active_tasks:
            return
            
        task = self.active_tasks[task_id]
        task["status"] = "completed" if success else "failed"
        task["progress_percent"] = 100.0 if success else task["progress_percent"]
        task["last_update"] = datetime.now().isoformat()
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE task_progress 
            SET status = ?, progress_percent = ?, last_update = ?
            WHERE task_id = ?
        """, (task["status"], task["progress_percent"], task["last_update"], task_id))
        conn.commit()
        conn.close()
        
        # Remove from active tasks after a delay
        def cleanup():
            time.sleep(5)  # Keep completed tasks visible for 5 seconds
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
        
        threading.Thread(target=cleanup, daemon=True).start()
        
    def update_function_metrics(self, function_name: str, execution_time: float, success: bool):
        """Update function execution metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current metrics
        cursor.execute("SELECT * FROM function_metrics WHERE function_name = ?", (function_name,))
        result = cursor.fetchone()
        
        if result:
            # Update existing metrics
            execution_count = result[2] + 1
            success_count = result[3] + (1 if success else 0)
            failure_count = result[4] + (0 if success else 1)
            avg_duration = ((result[5] * result[2]) + execution_time) / execution_count
            
            cursor.execute("""
                UPDATE function_metrics 
                SET execution_count = ?, success_count = ?, failure_count = ?, 
                    avg_duration = ?, last_execution = ?, status = ?
                WHERE function_name = ?
            """, (execution_count, success_count, failure_count, avg_duration, 
                  datetime.now().isoformat(), "completed", function_name))
        else:
            # Create new metrics
            cursor.execute("""
                INSERT INTO function_metrics 
                (function_name, execution_count, success_count, failure_count, 
                 avg_duration, last_execution, status)
                VALUES (?, 1, ?, ?, ?, ?, 'completed')
            """, (function_name, 1 if success else 0, 0 if success else 1, 
                  execution_time, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    def get_live_progress_report(self) -> Dict[str, Any]:
        """Get comprehensive live progress report"""
        # Get active tasks
        active_tasks_list = []
        for task_id, task in self.active_tasks.items():
            start_time = datetime.fromisoformat(task["start_time"])
            elapsed = (datetime.now() - start_time).total_seconds()
            estimated_remaining = max(0, task["estimated_duration"] - elapsed)
            
            active_tasks_list.append({
                "task_id": task_id,
                "task_name": task["task_name"],
                "current_step": task["current_step"],
                "progress_percent": round(task["progress_percent"], 1),
                "steps_completed": task["steps_completed"],
                "total_steps": task["total_steps"],
                "elapsed_seconds": round(elapsed, 1),
                "estimated_remaining": round(estimated_remaining, 1),
                "status": task["status"]
            })
        
        # Get function metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT function_name, execution_count, success_count, failure_count, 
                   avg_duration, last_execution, status
            FROM function_metrics 
            ORDER BY last_execution DESC
        """)
        
        function_metrics = []
        for row in cursor.fetchall():
            success_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
            function_metrics.append({
                "function_name": row[0],
                "execution_count": row[1],
                "success_count": row[2],
                "failure_count": row[3],
                "success_rate": round(success_rate, 1),
                "avg_duration": round(row[4], 2),
                "last_execution": row[5],
                "status": row[6]
            })
        
        conn.close()
        
        # System metrics
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "active_tasks_count": len(active_tasks_list),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "active_tasks": active_tasks_list,
            "function_metrics": function_metrics,
            "system_metrics": system_metrics,
            "report_timestamp": datetime.now().isoformat()
        }
        
    def get_progress_summary(self) -> str:
        """Get formatted progress summary"""
        report = self.get_live_progress_report()
        
        summary = ["🔄 MITO Live Progress Report", "=" * 40]
        
        # Active tasks
        if report["active_tasks"]:
            summary.append("\n📋 Active Tasks:")
            for task in report["active_tasks"]:
                progress_bar = "█" * int(task["progress_percent"] / 10) + "░" * (10 - int(task["progress_percent"] / 10))
                summary.append(f"  {task['task_name']}")
                summary.append(f"    Step: {task['current_step']}")
                summary.append(f"    Progress: [{progress_bar}] {task['progress_percent']}%")
                summary.append(f"    Remaining: {task['estimated_remaining']}s")
                summary.append("")
        else:
            summary.append("\n✅ No active tasks - MITO is monitoring")
        
        # Top functions
        if report["function_metrics"]:
            summary.append("\n⚡ Function Performance:")
            for func in report["function_metrics"][:5]:
                summary.append(f"  {func['function_name']}: {func['success_rate']}% success, {func['avg_duration']}s avg")
        
        # System status
        summary.append(f"\n🖥️  System: CPU {report['system_metrics']['cpu_percent']}%, RAM {report['system_metrics']['memory_percent']}%")
        
        return "\n".join(summary)

# Global progress tracker instance
progress_tracker = ProgressTracker()