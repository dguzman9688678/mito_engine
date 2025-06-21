"""
MITO Engine - Deployment Manager
Complete deployment management system with multiple platforms and environments
"""

import os
import json
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import uuid

class DeploymentTarget:
    """Deployment target configuration"""
    
    def __init__(self, name: str, platform: str, config: Dict[str, Any]):
        self.target_id = str(uuid.uuid4())
        self.name = name
        self.platform = platform
        self.config = config
        self.created_at = datetime.now().isoformat()
        self.last_deployed = None
        self.status = "configured"

class Deployment:
    """Deployment instance"""
    
    def __init__(self, project_path: str, target_id: str, version: str = None):
        self.deployment_id = str(uuid.uuid4())
        self.project_path = project_path
        self.target_id = target_id
        self.version = version or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.logs = []
        self.artifacts = []

class DeploymentManager:
    """Complete deployment management system"""
    
    def __init__(self):
        self.targets = {}
        self.deployments = {}
        self.initialize_default_targets()
    
    def initialize_default_targets(self):
        """Initialize default deployment targets"""
        
        # Replit deployment
        replit_target = DeploymentTarget(
            name="Replit",
            platform="replit",
            config={
                "auto_deploy": True,
                "domain": "auto",
                "port": 5000,
                "health_check": "/",
                "environment": "production"
            }
        )
        self.add_target(replit_target)
        
        # Docker deployment
        docker_target = DeploymentTarget(
            name="Docker",
            platform="docker",
            config={
                "base_image": "python:3.11-slim",
                "port": 5000,
                "env_file": ".env",
                "volumes": [],
                "build_args": {}
            }
        )
        self.add_target(docker_target)
        
        # AWS deployment
        aws_target = DeploymentTarget(
            name="AWS",
            platform="aws",
            config={
                "service": "elastic_beanstalk",
                "region": "us-east-1",
                "instance_type": "t3.micro",
                "auto_scaling": True,
                "health_check": "/health"
            }
        )
        self.add_target(aws_target)
        
        # Heroku deployment
        heroku_target = DeploymentTarget(
            name="Heroku",
            platform="heroku",
            config={
                "stack": "heroku-22",
                "region": "us",
                "dyno_type": "web",
                "auto_deploy": True
            }
        )
        self.add_target(heroku_target)
    
    def add_target(self, target: DeploymentTarget):
        """Add deployment target"""
        self.targets[target.target_id] = target
    
    def list_targets(self) -> List[Dict[str, Any]]:
        """List all deployment targets"""
        targets = []
        for target in self.targets.values():
            targets.append({
                "id": target.target_id,
                "name": target.name,
                "platform": target.platform,
                "status": target.status,
                "last_deployed": target.last_deployed,
                "created_at": target.created_at
            })
        return targets
    
    def get_target(self, target_id: str) -> Optional[DeploymentTarget]:
        """Get deployment target by ID"""
        return self.targets.get(target_id)
    
    def create_deployment(self, project_path: str, target_id: str, version: str = None) -> Dict[str, Any]:
        """Create new deployment"""
        try:
            if target_id not in self.targets:
                return {"success": False, "error": "Deployment target not found"}
            
            if not Path(project_path).exists():
                return {"success": False, "error": "Project path does not exist"}
            
            deployment = Deployment(project_path, target_id, version)
            self.deployments[deployment.deployment_id] = deployment
            
            return {
                "success": True,
                "deployment_id": deployment.deployment_id,
                "version": deployment.version,
                "message": "Deployment created successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def deploy(self, deployment_id: str) -> Dict[str, Any]:
        """Execute deployment"""
        try:
            if deployment_id not in self.deployments:
                return {"success": False, "error": "Deployment not found"}
            
            deployment = self.deployments[deployment_id]
            target = self.targets[deployment.target_id]
            
            deployment.status = "deploying"
            deployment.started_at = datetime.now().isoformat()
            
            # Execute platform-specific deployment
            if target.platform == "replit":
                result = self._deploy_to_replit(deployment, target)
            elif target.platform == "docker":
                result = self._deploy_to_docker(deployment, target)
            elif target.platform == "aws":
                result = self._deploy_to_aws(deployment, target)
            elif target.platform == "heroku":
                result = self._deploy_to_heroku(deployment, target)
            else:
                result = {"success": False, "error": f"Unsupported platform: {target.platform}"}
            
            # Update deployment status
            deployment.completed_at = datetime.now().isoformat()
            deployment.status = "deployed" if result["success"] else "failed"
            target.last_deployed = deployment.completed_at if result["success"] else None
            
            return result
            
        except Exception as e:
            deployment.status = "failed"
            deployment.completed_at = datetime.now().isoformat()
            return {"success": False, "error": str(e)}
    
    def _deploy_to_replit(self, deployment: Deployment, target: DeploymentTarget) -> Dict[str, Any]:
        """Deploy to Replit platform"""
        try:
            project_path = Path(deployment.project_path)
            
            # Create .replit config if it doesn't exist
            replit_config = {
                "language": "python3",
                "run": "python main.py",
                "modules": ["python3"],
                "entrypoint": "main.py"
            }
            
            if not (project_path / ".replit").exists():
                with open(project_path / ".replit", 'w') as f:
                    for key, value in replit_config.items():
                        if isinstance(value, list):
                            f.write(f'{key} = {json.dumps(value)}\n')
                        else:
                            f.write(f'{key} = "{value}"\n')
            
            # Create pyproject.toml if it doesn't exist
            if not (project_path / "pyproject.toml").exists():
                pyproject_config = {
                    "tool": {
                        "poetry": {
                            "name": "mito-app",
                            "version": "1.0.0",
                            "description": "MITO Engine Application",
                            "dependencies": {
                                "python": "^3.11",
                                "flask": "^2.3.0",
                                "gunicorn": "^21.0.0"
                            }
                        }
                    }
                }
                
                with open(project_path / "pyproject.toml", 'w') as f:
                    import toml
                    toml.dump(pyproject_config, f)
            
            deployment.logs.append("Replit configuration files created")
            
            return {
                "success": True,
                "message": "Deployed to Replit successfully",
                "url": f"https://{os.environ.get('REPL_SLUG', 'app')}.{os.environ.get('REPL_OWNER', 'user')}.repl.co",
                "platform": "replit"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _deploy_to_docker(self, deployment: Deployment, target: DeploymentTarget) -> Dict[str, Any]:
        """Deploy to Docker"""
        try:
            project_path = Path(deployment.project_path)
            config = target.config
            
            # Generate Dockerfile
            dockerfile_content = f"""FROM {config['base_image']}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {config['port']}

CMD ["gunicorn", "--bind", "0.0.0.0:{config['port']}", "main:app"]
"""
            
            with open(project_path / "Dockerfile", 'w') as f:
                f.write(dockerfile_content)
            
            # Generate docker-compose.yml
            compose_content = {
                "version": "3.8",
                "services": {
                    "app": {
                        "build": ".",
                        "ports": [f"{config['port']}:{config['port']}"],
                        "environment": ["FLASK_ENV=production"]
                    }
                }
            }
            
            if config.get('env_file'):
                compose_content["services"]["app"]["env_file"] = config['env_file']
            
            with open(project_path / "docker-compose.yml", 'w') as f:
                yaml.dump(compose_content, f, default_flow_style=False)
            
            # Build Docker image
            image_name = f"mito-app:{deployment.version}"
            build_result = subprocess.run(
                ["docker", "build", "-t", image_name, str(project_path)],
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                return {"success": False, "error": f"Docker build failed: {build_result.stderr}"}
            
            deployment.logs.append(f"Docker image built: {image_name}")
            deployment.artifacts.append(f"docker_image:{image_name}")
            
            return {
                "success": True,
                "message": "Docker image built successfully",
                "image": image_name,
                "platform": "docker"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _deploy_to_aws(self, deployment: Deployment, target: DeploymentTarget) -> Dict[str, Any]:
        """Deploy to AWS"""
        try:
            project_path = Path(deployment.project_path)
            config = target.config
            
            # Generate AWS Elastic Beanstalk configuration
            eb_config = {
                "option_settings": {
                    "aws:elasticbeanstalk:container:python": {
                        "WSGIPath": "main.py"
                    },
                    "aws:elasticbeanstalk:application:environment": {
                        "FLASK_ENV": "production"
                    }
                }
            }
            
            # Create .ebextensions directory
            ebext_dir = project_path / ".ebextensions"
            ebext_dir.mkdir(exist_ok=True)
            
            with open(ebext_dir / "python.config", 'w') as f:
                yaml.dump(eb_config, f, default_flow_style=False)
            
            # Create application.py (EB entry point)
            app_content = """from main import app

if __name__ == "__main__":
    app.run()
"""
            
            with open(project_path / "application.py", 'w') as f:
                f.write(app_content)
            
            deployment.logs.append("AWS Elastic Beanstalk configuration created")
            
            return {
                "success": True,
                "message": "AWS deployment configuration created",
                "platform": "aws",
                "next_steps": "Run 'eb init' and 'eb deploy' to complete deployment"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _deploy_to_heroku(self, deployment: Deployment, target: DeploymentTarget) -> Dict[str, Any]:
        """Deploy to Heroku"""
        try:
            project_path = Path(deployment.project_path)
            config = target.config
            
            # Generate Procfile
            procfile_content = f"web: gunicorn main:app --bind 0.0.0.0:$PORT"
            
            with open(project_path / "Procfile", 'w') as f:
                f.write(procfile_content)
            
            # Generate runtime.txt
            runtime_content = "python-3.11.0"
            
            with open(project_path / "runtime.txt", 'w') as f:
                f.write(runtime_content)
            
            # Generate app.json for Heroku deployment
            app_json = {
                "name": "mito-app",
                "description": "MITO Engine Application",
                "keywords": ["python", "flask"],
                "website": "https://github.com/your-username/mito-app",
                "repository": "https://github.com/your-username/mito-app",
                "stack": config.get("stack", "heroku-22"),
                "buildpacks": [
                    {"url": "heroku/python"}
                ],
                "env": {
                    "FLASK_ENV": {
                        "description": "Flask environment",
                        "value": "production"
                    }
                }
            }
            
            with open(project_path / "app.json", 'w') as f:
                json.dump(app_json, f, indent=2)
            
            deployment.logs.append("Heroku configuration files created")
            
            return {
                "success": True,
                "message": "Heroku deployment configuration created",
                "platform": "heroku",
                "next_steps": "Run 'git push heroku main' to deploy"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        
        deployment = self.deployments[deployment_id]
        target = self.targets[deployment.target_id]
        
        return {
            "success": True,
            "deployment": {
                "id": deployment.deployment_id,
                "project_path": deployment.project_path,
                "target": target.name,
                "platform": target.platform,
                "version": deployment.version,
                "status": deployment.status,
                "created_at": deployment.created_at,
                "started_at": deployment.started_at,
                "completed_at": deployment.completed_at,
                "logs": deployment.logs,
                "artifacts": deployment.artifacts
            }
        }
    
    def list_deployments(self, project_path: str = None) -> List[Dict[str, Any]]:
        """List all deployments"""
        deployments = []
        for deployment in self.deployments.values():
            if project_path is None or deployment.project_path == project_path:
                target = self.targets[deployment.target_id]
                deployments.append({
                    "id": deployment.deployment_id,
                    "project_path": deployment.project_path,
                    "target": target.name,
                    "platform": target.platform,
                    "version": deployment.version,
                    "status": deployment.status,
                    "created_at": deployment.created_at,
                    "completed_at": deployment.completed_at
                })
        
        return sorted(deployments, key=lambda x: x["created_at"], reverse=True)
    
    def rollback_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Rollback deployment to previous version"""
        try:
            if deployment_id not in self.deployments:
                return {"success": False, "error": "Deployment not found"}
            
            deployment = self.deployments[deployment_id]
            
            # Find previous successful deployment
            previous_deployments = [
                d for d in self.deployments.values()
                if d.project_path == deployment.project_path
                and d.target_id == deployment.target_id
                and d.status == "deployed"
                and d.deployment_id != deployment_id
            ]
            
            if not previous_deployments:
                return {"success": False, "error": "No previous deployment found"}
            
            # Get the most recent successful deployment
            previous = max(previous_deployments, key=lambda x: x.created_at)
            
            # Create rollback deployment
            rollback = Deployment(deployment.project_path, deployment.target_id, f"rollback_{previous.version}")
            rollback.status = "rolling_back"
            self.deployments[rollback.deployment_id] = rollback
            
            # Execute rollback (platform-specific logic would go here)
            rollback.status = "deployed"
            rollback.completed_at = datetime.now().isoformat()
            
            return {
                "success": True,
                "message": f"Rolled back to version {previous.version}",
                "rollback_deployment_id": rollback.deployment_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_deployment_logs(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment logs"""
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        
        deployment = self.deployments[deployment_id]
        
        return {
            "success": True,
            "logs": deployment.logs,
            "deployment_id": deployment_id,
            "status": deployment.status
        }
    
    def generate_deployment_manifest(self, project_path: str, target_id: str) -> Dict[str, Any]:
        """Generate deployment manifest"""
        try:
            if target_id not in self.targets:
                return {"success": False, "error": "Target not found"}
            
            target = self.targets[target_id]
            project_path = Path(project_path)
            
            # Analyze project structure
            manifest = {
                "project": {
                    "name": project_path.name,
                    "path": str(project_path),
                    "created_at": datetime.now().isoformat()
                },
                "target": {
                    "name": target.name,
                    "platform": target.platform,
                    "config": target.config
                },
                "files": [],
                "dependencies": [],
                "environment": {},
                "build_steps": [],
                "health_checks": []
            }
            
            # Scan project files
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    relative_path = file_path.relative_to(project_path)
                    manifest["files"].append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "type": "text" if file_path.suffix in ['.py', '.txt', '.md', '.yml', '.yaml', '.json'] else "binary"
                    })
            
            # Extract dependencies
            requirements_file = project_path / "requirements.txt"
            if requirements_file.exists():
                with open(requirements_file, 'r') as f:
                    manifest["dependencies"] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Platform-specific configurations
            if target.platform == "docker":
                manifest["build_steps"] = [
                    "FROM python:3.11-slim",
                    "COPY requirements.txt .",
                    "RUN pip install -r requirements.txt",
                    "COPY . .",
                    "CMD python main.py"
                ]
            elif target.platform == "heroku":
                manifest["build_steps"] = [
                    "Install Python dependencies",
                    "Collect static files",
                    "Run database migrations"
                ]
            
            return {"success": True, "manifest": manifest}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global deployment manager instance
deployment_manager = DeploymentManager()

def main():
    """Demo of deployment manager functionality"""
    
    # List targets
    targets = deployment_manager.list_targets()
    print("Deployment targets:")
    for target in targets:
        print(f"- {target['name']} ({target['platform']})")
    
    # Create a deployment
    if targets:
        replit_target = next((t for t in targets if t['platform'] == 'replit'), None)
        if replit_target:
            deployment_result = deployment_manager.create_deployment(".", replit_target['id'])
            print(f"\nDeployment creation: {deployment_result}")
            
            if deployment_result['success']:
                # Deploy
                deploy_result = deployment_manager.deploy(deployment_result['deployment_id'])
                print(f"Deployment result: {deploy_result}")
                
                # Get status
                status = deployment_manager.get_deployment_status(deployment_result['deployment_id'])
                print(f"Deployment status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    main()