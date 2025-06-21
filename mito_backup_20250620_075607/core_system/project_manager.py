#!/usr/bin/env python3
"""
Project Management Integration for MITO Engine
Connects with Jira, Trello, Asana, and other project management platforms
"""

import os
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import requests
from urllib.parse import urljoin
import hashlib
import base64

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Represents a project task"""
    id: str
    title: str
    description: str
    status: str
    priority: str
    assignee: str
    project_id: str
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    labels: List[str] = None
    comments: List[Dict] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.comments is None:
            self.comments = []

@dataclass
class Project:
    """Represents a project"""
    id: str
    name: str
    description: str
    status: str
    owner: str
    created_at: str
    team_members: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.team_members is None:
            self.team_members = []
        if self.tags is None:
            self.tags = []

class ProjectDatabase:
    """Database for project management data"""
    
    def __init__(self, db_path: str = "project_management.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize project management database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                owner TEXT NOT NULL,
                team_members TEXT,
                tags TEXT,
                external_id TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT,
                assignee TEXT,
                project_id TEXT NOT NULL,
                labels TEXT,
                comments TEXT,
                external_id TEXT,
                platform TEXT,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                api_endpoint TEXT NOT NULL,
                auth_token TEXT,
                auth_type TEXT,
                config TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

class JiraIntegration:
    """Jira integration client"""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (username, api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def test_connection(self) -> bool:
        """Test Jira connection"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/myself")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Jira connection test failed: {e}")
            return False
            
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all Jira projects"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/project")
            response.raise_for_status()
            
            projects = []
            for project in response.json():
                projects.append({
                    'id': project['key'],
                    'external_id': project['id'],
                    'name': project['name'],
                    'description': project.get('description', ''),
                    'status': 'active',
                    'owner': project.get('lead', {}).get('displayName', 'Unknown'),
                    'created_at': datetime.now().isoformat(),
                    'platform': 'jira'
                })
                
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get Jira projects: {e}")
            return []
            
    def get_tasks(self, project_key: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get tasks (issues) from Jira project"""
        try:
            jql = f"project = {project_key} ORDER BY updated DESC"
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,assignee,created,updated,duedate,labels,comment'
            }
            
            response = self.session.get(f"{self.base_url}/rest/api/3/search", params=params)
            response.raise_for_status()
            
            tasks = []
            for issue in response.json().get('issues', []):
                fields = issue['fields']
                
                # Extract comments
                comments = []
                if fields.get('comment', {}).get('comments'):
                    for comment in fields['comment']['comments'][:5]:  # Last 5 comments
                        comments.append({
                            'author': comment['author']['displayName'],
                            'body': comment['body'],
                            'created': comment['created']
                        })
                
                tasks.append({
                    'id': issue['key'],
                    'external_id': issue['id'],
                    'title': fields['summary'],
                    'description': fields.get('description', ''),
                    'status': fields['status']['name'],
                    'priority': fields.get('priority', {}).get('name', 'Medium'),
                    'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
                    'project_id': project_key,
                    'labels': [label for label in fields.get('labels', [])],
                    'comments': comments,
                    'due_date': fields.get('duedate'),
                    'created_at': fields['created'],
                    'updated_at': fields['updated'],
                    'platform': 'jira'
                })
                
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get Jira tasks for project {project_key}: {e}")
            return []
            
    def create_task(self, project_key: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new Jira issue"""
        try:
            issue_data = {
                'fields': {
                    'project': {'key': project_key},
                    'summary': task_data['title'],
                    'description': task_data.get('description', ''),
                    'issuetype': {'name': 'Task'},
                    'priority': {'name': task_data.get('priority', 'Medium')}
                }
            }
            
            if task_data.get('assignee'):
                issue_data['fields']['assignee'] = {'name': task_data['assignee']}
                
            if task_data.get('due_date'):
                issue_data['fields']['duedate'] = task_data['due_date']
                
            response = self.session.post(f"{self.base_url}/rest/api/3/issue", json=issue_data)
            response.raise_for_status()
            
            return response.json()['key']
            
        except Exception as e:
            logger.error(f"Failed to create Jira task: {e}")
            return None

class TrelloIntegration:
    """Trello integration client"""
    
    def __init__(self, api_key: str, token: str):
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"
        self.session = requests.Session()
        
    def test_connection(self) -> bool:
        """Test Trello connection"""
        try:
            params = {'key': self.api_key, 'token': self.token}
            response = self.session.get(f"{self.base_url}/members/me", params=params)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Trello connection test failed: {e}")
            return False
            
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all Trello boards as projects"""
        try:
            params = {'key': self.api_key, 'token': self.token}
            response = self.session.get(f"{self.base_url}/members/me/boards", params=params)
            response.raise_for_status()
            
            projects = []
            for board in response.json():
                projects.append({
                    'id': board['id'],
                    'external_id': board['id'],
                    'name': board['name'],
                    'description': board.get('desc', ''),
                    'status': 'open' if not board['closed'] else 'closed',
                    'owner': 'Unknown',  # Trello doesn't provide direct owner info
                    'created_at': datetime.now().isoformat(),
                    'platform': 'trello'
                })
                
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get Trello boards: {e}")
            return []
            
    def get_tasks(self, board_id: str) -> List[Dict[str, Any]]:
        """Get cards from Trello board"""
        try:
            params = {
                'key': self.api_key, 
                'token': self.token,
                'cards': 'open',
                'card_fields': 'name,desc,due,labels,dateLastActivity'
            }
            
            response = self.session.get(f"{self.base_url}/boards/{board_id}/cards", params=params)
            response.raise_for_status()
            
            tasks = []
            for card in response.json():
                tasks.append({
                    'id': card['id'],
                    'external_id': card['id'],
                    'title': card['name'],
                    'description': card.get('desc', ''),
                    'status': 'open',  # Trello cards are either open or archived
                    'priority': 'Medium',  # Trello doesn't have built-in priority
                    'assignee': 'Unassigned',  # Would need additional API call
                    'project_id': board_id,
                    'labels': [label['name'] for label in card.get('labels', [])],
                    'comments': [],  # Would need additional API call
                    'due_date': card.get('due'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': card.get('dateLastActivity'),
                    'platform': 'trello'
                })
                
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get Trello cards for board {board_id}: {e}")
            return []

class AsanaIntegration:
    """Asana integration client"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://app.asana.com/api/1.0"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        })
        
    def test_connection(self) -> bool:
        """Test Asana connection"""
        try:
            response = self.session.get(f"{self.base_url}/users/me")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Asana connection test failed: {e}")
            return False
            
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all Asana projects"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            response.raise_for_status()
            
            projects = []
            for project in response.json()['data']:
                projects.append({
                    'id': project['gid'],
                    'external_id': project['gid'],
                    'name': project['name'],
                    'description': project.get('notes', ''),
                    'status': project.get('archived', False) and 'archived' or 'active',
                    'owner': project.get('owner', {}).get('name', 'Unknown'),
                    'created_at': project.get('created_at', datetime.now().isoformat()),
                    'platform': 'asana'
                })
                
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get Asana projects: {e}")
            return []
            
    def get_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Get tasks from Asana project"""
        try:
            params = {
                'project': project_id,
                'opt_fields': 'name,notes,completed,assignee.name,due_on,tags.name,created_at,modified_at'
            }
            
            response = self.session.get(f"{self.base_url}/tasks", params=params)
            response.raise_for_status()
            
            tasks = []
            for task in response.json()['data']:
                tasks.append({
                    'id': task['gid'],
                    'external_id': task['gid'],
                    'title': task['name'],
                    'description': task.get('notes', ''),
                    'status': 'completed' if task.get('completed') else 'in_progress',
                    'priority': 'Medium',  # Asana doesn't have built-in priority in basic API
                    'assignee': task.get('assignee', {}).get('name', 'Unassigned'),
                    'project_id': project_id,
                    'labels': [tag['name'] for tag in task.get('tags', [])],
                    'comments': [],  # Would need additional API call
                    'due_date': task.get('due_on'),
                    'created_at': task.get('created_at'),
                    'updated_at': task.get('modified_at'),
                    'platform': 'asana'
                })
                
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get Asana tasks for project {project_id}: {e}")
            return []

class ProjectManager:
    """Main project management integration system"""
    
    def __init__(self):
        self.db = ProjectDatabase()
        self.integrations = {}
        self.load_integrations()
        
    def load_integrations(self):
        """Load configured integrations"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM integrations WHERE enabled = TRUE")
            
            for row in cursor.fetchall():
                platform, api_endpoint, auth_token, auth_type, config_str = row[1:6]
                config = json.loads(config_str) if config_str else {}
                
                if platform == 'jira':
                    self.integrations['jira'] = JiraIntegration(
                        api_endpoint,
                        config.get('username'),
                        auth_token
                    )
                elif platform == 'trello':
                    self.integrations['trello'] = TrelloIntegration(
                        config.get('api_key'),
                        auth_token
                    )
                elif platform == 'asana':
                    self.integrations['asana'] = AsanaIntegration(auth_token)
                    
            conn.close()
            logger.info(f"Loaded {len(self.integrations)} integrations")
            
        except Exception as e:
            logger.error(f"Failed to load integrations: {e}")
            
    def add_integration(self, platform: str, config: Dict[str, Any]) -> bool:
        """Add a new integration"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO integrations 
                (platform, api_endpoint, auth_token, auth_type, config)
                VALUES (?, ?, ?, ?, ?)
            """, (
                platform,
                config.get('api_endpoint', ''),
                config.get('auth_token', ''),
                config.get('auth_type', 'bearer'),
                json.dumps(config)
            ))
            
            conn.commit()
            conn.close()
            
            # Reload integrations
            self.load_integrations()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add integration {platform}: {e}")
            return False
            
    def sync_projects(self, platform: str = None) -> Dict[str, Any]:
        """Sync projects from external platforms"""
        results = {}
        platforms = [platform] if platform else self.integrations.keys()
        
        for platform_name in platforms:
            if platform_name not in self.integrations:
                continue
                
            try:
                integration = self.integrations[platform_name]
                projects = integration.get_projects()
                
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
                synced_count = 0
                for project_data in projects:
                    cursor.execute("""
                        INSERT OR REPLACE INTO projects 
                        (id, name, description, status, owner, external_id, platform, synced_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        project_data['id'],
                        project_data['name'],
                        project_data['description'],
                        project_data['status'],
                        project_data['owner'],
                        project_data['external_id'],
                        platform_name
                    ))
                    synced_count += 1
                    
                conn.commit()
                conn.close()
                
                results[platform_name] = {
                    'success': True,
                    'projects_synced': synced_count
                }
                
                self._log_sync_action(platform_name, 'sync_projects', 'project', '', True)
                
            except Exception as e:
                logger.error(f"Failed to sync projects from {platform_name}: {e}")
                results[platform_name] = {
                    'success': False,
                    'error': str(e)
                }
                self._log_sync_action(platform_name, 'sync_projects', 'project', '', False, str(e))
                
        return results
        
    def sync_tasks(self, project_id: str = None, platform: str = None) -> Dict[str, Any]:
        """Sync tasks from external platforms"""
        results = {}
        
        # Get projects to sync
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            projects = cursor.fetchall()
        else:
            query = "SELECT * FROM projects"
            params = []
            if platform:
                query += " WHERE platform = ?"
                params.append(platform)
            cursor.execute(query, params)
            projects = cursor.fetchall()
            
        conn.close()
        
        for project in projects:
            project_id, name, desc, status, owner, team_members, tags, external_id, platform_name = project[:9]
            
            if platform_name not in self.integrations:
                continue
                
            try:
                integration = self.integrations[platform_name]
                tasks = integration.get_tasks(external_id or project_id)
                
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
                synced_count = 0
                for task_data in tasks:
                    cursor.execute("""
                        INSERT OR REPLACE INTO tasks 
                        (id, title, description, status, priority, assignee, project_id,
                         labels, comments, external_id, platform, due_date, synced_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        task_data['id'],
                        task_data['title'],
                        task_data['description'],
                        task_data['status'],
                        task_data['priority'],
                        task_data['assignee'],
                        project_id,
                        json.dumps(task_data['labels']),
                        json.dumps(task_data['comments']),
                        task_data['external_id'],
                        platform_name,
                        task_data['due_date']
                    ))
                    synced_count += 1
                    
                conn.commit()
                conn.close()
                
                results[f"{platform_name}:{project_id}"] = {
                    'success': True,
                    'tasks_synced': synced_count
                }
                
                self._log_sync_action(platform_name, 'sync_tasks', 'task', project_id, True)
                
            except Exception as e:
                logger.error(f"Failed to sync tasks for project {project_id} from {platform_name}: {e}")
                results[f"{platform_name}:{project_id}"] = {
                    'success': False,
                    'error': str(e)
                }
                self._log_sync_action(platform_name, 'sync_tasks', 'task', project_id, False, str(e))
                
        return results
        
    def get_projects(self, platform: str = None) -> List[Dict[str, Any]]:
        """Get projects from database"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            if platform:
                cursor.execute("SELECT * FROM projects WHERE platform = ? ORDER BY updated_at DESC", (platform,))
            else:
                cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
                
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'status': row[3],
                    'owner': row[4],
                    'team_members': json.loads(row[5]) if row[5] else [],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'external_id': row[7],
                    'platform': row[8],
                    'created_at': row[9],
                    'updated_at': row[10],
                    'synced_at': row[11]
                })
                
            conn.close()
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []
            
    def get_tasks(self, project_id: str = None, status: str = None, assignee: str = None) -> List[Dict[str, Any]]:
        """Get tasks from database"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if assignee:
                query += " AND assignee = ?"
                params.append(assignee)
                
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'status': row[3],
                    'priority': row[4],
                    'assignee': row[5],
                    'project_id': row[6],
                    'labels': json.loads(row[7]) if row[7] else [],
                    'comments': json.loads(row[8]) if row[8] else [],
                    'external_id': row[9],
                    'platform': row[10],
                    'due_date': row[11],
                    'created_at': row[12],
                    'updated_at': row[13],
                    'synced_at': row[14]
                })
                
            conn.close()
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
            
    def create_task(self, project_id: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Create a new task"""
        try:
            # Get project info
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT platform, external_id FROM projects WHERE id = ?", (project_id,))
            project_info = cursor.fetchone()
            
            if not project_info:
                return None
                
            platform, external_id = project_info
            
            # Create task in external platform if integration exists
            external_task_id = None
            if platform in self.integrations:
                integration = self.integrations[platform]
                if hasattr(integration, 'create_task'):
                    external_task_id = integration.create_task(external_id or project_id, task_data)
                    
            # Create task in local database
            task_id = external_task_id or f"local_{hashlib.md5(f\"{project_id}_{task_data['title']}_{datetime.now().isoformat()}\".encode()).hexdigest()[:8]}"
            
            cursor.execute("""
                INSERT INTO tasks 
                (id, title, description, status, priority, assignee, project_id,
                 labels, external_id, platform)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                task_data['title'],
                task_data.get('description', ''),
                task_data.get('status', 'todo'),
                task_data.get('priority', 'Medium'),
                task_data.get('assignee', ''),
                project_id,
                json.dumps(task_data.get('labels', [])),
                external_task_id,
                platform
            ))
            
            conn.commit()
            conn.close()
            
            self._log_sync_action(platform, 'create_task', 'task', task_id, True)
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            self._log_sync_action('local', 'create_task', 'task', '', False, str(e))
            return None
            
    def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get project analytics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Task status distribution
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM tasks 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY status
            """.format(days))
            status_distribution = dict(cursor.fetchall())
            
            # Tasks by priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM tasks 
                WHERE created_at >= datetime('now', '-{} days')
                GROUP BY priority
            """.format(days))
            priority_distribution = dict(cursor.fetchall())
            
            # Tasks by assignee
            cursor.execute("""
                SELECT assignee, COUNT(*) as count 
                FROM tasks 
                WHERE created_at >= datetime('now', '-{} days')
                AND assignee != 'Unassigned'
                GROUP BY assignee
                ORDER BY count DESC
                LIMIT 10
            """.format(days))
            assignee_distribution = dict(cursor.fetchall())
            
            # Overdue tasks
            cursor.execute("""
                SELECT COUNT(*) FROM tasks 
                WHERE due_date < date('now') 
                AND status NOT IN ('completed', 'done', 'closed')
            """)
            overdue_tasks = cursor.fetchone()[0]
            
            # Platform distribution
            cursor.execute("""
                SELECT platform, COUNT(*) as count 
                FROM projects 
                GROUP BY platform
            """)
            platform_distribution = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'period_days': days,
                'status_distribution': status_distribution,
                'priority_distribution': priority_distribution,
                'assignee_distribution': assignee_distribution,
                'overdue_tasks': overdue_tasks,
                'platform_distribution': platform_distribution,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}
            
    def _log_sync_action(self, platform: str, action: str, resource_type: str, 
                        resource_id: str, success: bool, error_message: str = None):
        """Log synchronization action"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sync_history 
                (platform, action, resource_type, resource_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (platform, action, resource_type, resource_id, success, error_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log sync action: {e}")

def main():
    """Demo of project management integration"""
    print("Project Management Integration Demo")
    print("=" * 40)
    
    pm = ProjectManager()
    
    # Demo configuration (would come from environment in real usage)
    demo_configs = {
        'jira': {
            'api_endpoint': 'https://your-domain.atlassian.net',
            'username': 'your-email@domain.com',
            'auth_token': 'your-api-token',
            'auth_type': 'basic'
        },
        'trello': {
            'api_key': 'your-trello-api-key',
            'auth_token': 'your-trello-token',
            'auth_type': 'key_token'
        },
        'asana': {
            'auth_token': 'your-asana-access-token',
            'auth_type': 'bearer'
        }
    }
    
    print("\n1. Integration Setup:")
    for platform, config in demo_configs.items():
        if pm.add_integration(platform, config):
            print(f"   ✓ {platform} integration configured")
        else:
            print(f"   ✗ {platform} integration failed")
    
    print("\n2. Available Projects:")
    projects = pm.get_projects()
    for project in projects[:5]:  # Show first 5
        print(f"   {project['name']} ({project['platform']}) - {project['status']}")
    
    print(f"\n   Total projects: {len(projects)}")
    
    print("\n3. Recent Tasks:")
    tasks = pm.get_tasks()
    for task in tasks[:5]:  # Show first 5
        print(f"   {task['title']} - {task['status']} ({task['platform']})")
        print(f"      Assigned to: {task['assignee']}, Priority: {task['priority']}")
    
    print(f"\n   Total tasks: {len(tasks)}")
    
    print("\n4. Analytics:")
    analytics = pm.get_analytics(30)
    
    if analytics.get('status_distribution'):
        print("   Task Status Distribution:")
        for status, count in analytics['status_distribution'].items():
            print(f"     {status}: {count}")
    
    if analytics.get('platform_distribution'):
        print("   Platform Distribution:")
        for platform, count in analytics['platform_distribution'].items():
            print(f"     {platform}: {count} projects")
    
    print(f"\n   Overdue tasks: {analytics.get('overdue_tasks', 0)}")

if __name__ == "__main__":
    main()