"""
MITO Engine - Development Management System
Comprehensive project management, version control, and development workflow automation
"""

import os
import json
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import shutil
from enum import Enum

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectStatus(Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Project:
    """Project data structure"""
    project_id: str
    name: str
    description: str
    status: str
    created_at: str
    updated_at: str
    owner: str
    repository_url: str = ""
    version: str = "1.0.0"
    tags: List[str] = None
    technologies: List[str] = None
    team_members: List[str] = None
    deadline: Optional[str] = None
    budget: Optional[float] = None
    progress_percentage: float = 0.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.technologies is None:
            self.technologies = []
        if self.team_members is None:
            self.team_members = []

@dataclass
class Task:
    """Task data structure"""
    task_id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: str
    assigned_to: str
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []

@dataclass
class Release:
    """Release data structure"""
    release_id: str
    project_id: str
    version: str
    name: str
    description: str
    release_date: str
    status: str
    changelog: List[str] = None
    files: List[str] = None
    
    def __post_init__(self):
        if self.changelog is None:
            self.changelog = []
        if self.files is None:
            self.files = []

class DevelopmentManager:
    """Comprehensive development management system"""
    
    def __init__(self, data_dir: str = "dev_management"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.projects_file = self.data_dir / "projects.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.releases_file = self.data_dir / "releases.json"
        
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.releases: Dict[str, Release] = {}
        
        self.load_data()
        logger.info("DevelopmentManager initialized")
    
    def load_data(self):
        """Load all data from storage"""
        try:
            # Load projects
            if self.projects_file.exists():
                with open(self.projects_file, 'r') as f:
                    data = json.load(f)
                    self.projects = {
                        pid: Project(**project_data) 
                        for pid, project_data in data.items()
                    }
            
            # Load tasks
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = {
                        tid: Task(**task_data) 
                        for tid, task_data in data.items()
                    }
            
            # Load releases
            if self.releases_file.exists():
                with open(self.releases_file, 'r') as f:
                    data = json.load(f)
                    self.releases = {
                        rid: Release(**release_data) 
                        for rid, release_data in data.items()
                    }
            
            logger.info(f"Loaded {len(self.projects)} projects, {len(self.tasks)} tasks, {len(self.releases)} releases")
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
    
    def save_data(self):
        """Save all data to storage"""
        try:
            # Save projects
            projects_data = {pid: asdict(project) for pid, project in self.projects.items()}
            with open(self.projects_file, 'w') as f:
                json.dump(projects_data, f, indent=2)
            
            # Save tasks
            tasks_data = {tid: asdict(task) for tid, task in self.tasks.items()}
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)
            
            # Save releases
            releases_data = {rid: asdict(release) for rid, release in self.releases.items()}
            with open(self.releases_file, 'w') as f:
                json.dump(releases_data, f, indent=2)
            
            logger.info("Data saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(f"{prefix}_{timestamp}_{os.urandom(4).hex()}".encode()).hexdigest()[:8]
        return f"{prefix}_{random_suffix}"
    
    def create_project(self, name: str, description: str, owner: str, 
                      technologies: List[str] = None, deadline: str = None) -> str:
        """Create new project"""
        project_id = self.generate_id("proj")
        
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            status=ProjectStatus.PLANNING.value,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            owner=owner,
            technologies=technologies or [],
            deadline=deadline
        )
        
        self.projects[project_id] = project
        self.save_data()
        
        logger.info(f"Created project: {name} ({project_id})")
        return project_id
    
    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project details"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now().isoformat()
        self.save_data()
        
        logger.info(f"Updated project {project_id}")
        return True
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return self.projects.get(project_id)
    
    def list_projects(self, status: str = None, owner: str = None) -> List[Project]:
        """List projects with optional filtering"""
        projects = list(self.projects.values())
        
        if status:
            projects = [p for p in projects if p.status == status]
        if owner:
            projects = [p for p in projects if p.owner == owner]
        
        return sorted(projects, key=lambda x: x.updated_at, reverse=True)
    
    def create_task(self, project_id: str, title: str, description: str, 
                   assigned_to: str, priority: str = "medium", due_date: str = None) -> str:
        """Create new task"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        task_id = self.generate_id("task")
        
        task = Task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING.value,
            priority=priority,
            assigned_to=assigned_to,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            due_date=due_date
        )
        
        self.tasks[task_id] = task
        self.save_data()
        
        logger.info(f"Created task: {title} ({task_id})")
        return task_id
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].status = status
        self.tasks[task_id].updated_at = datetime.now().isoformat()
        self.save_data()
        
        # Update project progress
        self.update_project_progress(self.tasks[task_id].project_id)
        
        logger.info(f"Updated task {task_id} status to {status}")
        return True
    
    def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        return [task for task in self.tasks.values() if task.project_id == project_id]
    
    def update_project_progress(self, project_id: str):
        """Update project progress based on task completion"""
        tasks = self.get_project_tasks(project_id)
        
        if not tasks:
            return
        
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED.value])
        progress = (completed_tasks / len(tasks)) * 100
        
        self.update_project(project_id, progress_percentage=progress)
    
    def create_release(self, project_id: str, version: str, name: str, 
                      description: str, changelog: List[str] = None) -> str:
        """Create new release"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        release_id = self.generate_id("rel")
        
        release = Release(
            release_id=release_id,
            project_id=project_id,
            version=version,
            name=name,
            description=description,
            release_date=datetime.now().isoformat(),
            status="draft",
            changelog=changelog or []
        )
        
        self.releases[release_id] = release
        self.save_data()
        
        # Update project version
        self.update_project(project_id, version=version)
        
        logger.info(f"Created release: {name} v{version} ({release_id})")
        return release_id
    
    def get_project_releases(self, project_id: str) -> List[Release]:
        """Get all releases for a project"""
        return [release for release in self.releases.values() if release.project_id == project_id]
    
    def initialize_git_repository(self, project_id: str, repo_path: str) -> bool:
        """Initialize git repository for project"""
        try:
            project = self.get_project(project_id)
            if not project:
                return False
            
            if not GIT_AVAILABLE:
                logger.warning("Git not available, creating basic project structure instead")
                # Create basic project structure without git
                repo_path = Path(repo_path)
                repo_path.mkdir(exist_ok=True)
                
                gitignore_content = """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
node_modules/
.DS_Store
*.log
"""
                
                (repo_path / ".gitignore").write_text(gitignore_content.strip())
                (repo_path / "README.md").write_text(f"# {project.name}\n\n{project.description}")
                
                # Update project with repository info
                self.update_project(project_id, repository_url=str(repo_path))
                
                logger.info(f"Created basic project structure for {project_id}")
                return True
            
            repo_path = Path(repo_path)
            repo_path.mkdir(exist_ok=True)
            
            # Initialize git repo
            repo = git.Repo.init(repo_path)
            
            # Create initial commit
            gitignore_content = """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
node_modules/
.DS_Store
*.log
"""
            
            (repo_path / ".gitignore").write_text(gitignore_content.strip())
            (repo_path / "README.md").write_text(f"# {project.name}\n\n{project.description}")
            
            repo.index.add([".gitignore", "README.md"])
            repo.index.commit("Initial commit")
            
            # Update project with repository info
            self.update_project(project_id, repository_url=str(repo_path))
            
            logger.info(f"Initialized git repository for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize git repository: {e}")
            return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for overview"""
        total_projects = len(self.projects)
        active_projects = len([p for p in self.projects.values() if p.status in ["development", "testing"]])
        total_tasks = len(self.tasks)
        pending_tasks = len([t for t in self.tasks.values() if t.status == "pending"])
        completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
        
        # Recent activity
        recent_projects = sorted(self.projects.values(), key=lambda x: x.updated_at, reverse=True)[:5]
        recent_tasks = sorted(self.tasks.values(), key=lambda x: x.updated_at, reverse=True)[:10]
        
        # Project status breakdown
        status_counts = {}
        for project in self.projects.values():
            status_counts[project.status] = status_counts.get(project.status, 0) + 1
        
        # Priority breakdown for tasks
        priority_counts = {}
        for task in self.tasks.values():
            if task.status != "completed":
                priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1
        
        return {
            "overview": {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
            },
            "recent_activity": {
                "projects": [{"id": p.project_id, "name": p.name, "status": p.status, "updated": p.updated_at} for p in recent_projects],
                "tasks": [{"id": t.task_id, "title": t.title, "status": t.status, "priority": t.priority} for t in recent_tasks]
            },
            "breakdowns": {
                "project_status": status_counts,
                "task_priority": priority_counts
            }
        }
    
    def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a project"""
        project = self.get_project(project_id)
        if not project:
            return {}
        
        tasks = self.get_project_tasks(project_id)
        releases = self.get_project_releases(project_id)
        
        # Task analytics
        task_status_counts = {}
        task_priority_counts = {}
        total_estimated_hours = 0
        total_actual_hours = 0
        
        for task in tasks:
            task_status_counts[task.status] = task_status_counts.get(task.status, 0) + 1
            task_priority_counts[task.priority] = task_priority_counts.get(task.priority, 0) + 1
            
            if task.estimated_hours:
                total_estimated_hours += task.estimated_hours
            if task.actual_hours:
                total_actual_hours += task.actual_hours
        
        # Timeline analysis
        creation_date = datetime.fromisoformat(project.created_at)
        days_active = (datetime.now() - creation_date).days
        
        return {
            "project": {
                "id": project.project_id,
                "name": project.name,
                "status": project.status,
                "progress": project.progress_percentage,
                "days_active": days_active
            },
            "tasks": {
                "total": len(tasks),
                "status_breakdown": task_status_counts,
                "priority_breakdown": task_priority_counts,
                "estimated_hours": total_estimated_hours,
                "actual_hours": total_actual_hours,
                "efficiency": round((total_estimated_hours / total_actual_hours * 100) if total_actual_hours > 0 else 0, 1)
            },
            "releases": {
                "total": len(releases),
                "latest_version": releases[-1].version if releases else "None"
            }
        }
    
    def export_project_data(self, project_id: str, format: str = "json") -> Optional[str]:
        """Export project data"""
        project = self.get_project(project_id)
        if not project:
            return None
        
        tasks = self.get_project_tasks(project_id)
        releases = self.get_project_releases(project_id)
        
        export_data = {
            "project": asdict(project),
            "tasks": [asdict(task) for task in tasks],
            "releases": [asdict(release) for release in releases],
            "exported_at": datetime.now().isoformat()
        }
        
        filename = f"project_export_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        try:
            if format == "json":
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported project {project_id} to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export project data: {e}")
            return None

def main():
    """Demo of development manager functionality"""
    dm = DevelopmentManager()
    
    # Create a sample project
    project_id = dm.create_project(
        name="MITO Engine Enhancement",
        description="Advanced AI development platform improvements",
        owner="Daniel Guzman",
        technologies=["Python", "Flask", "JavaScript", "PostgreSQL"],
        deadline=(datetime.now() + timedelta(days=30)).isoformat()
    )
    
    # Create some tasks
    task1_id = dm.create_task(
        project_id=project_id,
        title="Implement file handler",
        description="Create comprehensive file management system",
        assigned_to="Daniel Guzman",
        priority="high"
    )
    
    task2_id = dm.create_task(
        project_id=project_id,
        title="Add administrator interface",
        description="Create admin panel for system management",
        assigned_to="Daniel Guzman",
        priority="medium"
    )
    
    # Update task status
    dm.update_task_status(task1_id, TaskStatus.COMPLETED.value)
    dm.update_task_status(task2_id, TaskStatus.IN_PROGRESS.value)
    
    # Get dashboard data
    dashboard = dm.get_dashboard_data()
    print("Development Dashboard:")
    print(json.dumps(dashboard, indent=2))
    
    # Get project analytics
    analytics = dm.get_project_analytics(project_id)
    print(f"\nProject Analytics for {project_id}:")
    print(json.dumps(analytics, indent=2))

if __name__ == "__main__":
    main()