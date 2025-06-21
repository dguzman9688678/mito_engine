"""
MITO Engine - Terminal Manager
Complete terminal execution system with command history and output capture
"""

import subprocess
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import signal
import psutil
from pathlib import Path

class TerminalSession:
    """Individual terminal session management"""
    
    def __init__(self, session_id: str, working_dir: str = "."):
        self.session_id = session_id
        self.working_dir = Path(working_dir).absolute()
        self.command_history = []
        self.environment = os.environ.copy()
        self.active_processes = {}
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in this session"""
        try:
            self.last_active = datetime.now()
            
            # Record command in history
            cmd_entry = {
                "command": command,
                "timestamp": self.last_active.isoformat(),
                "working_dir": str(self.working_dir)
            }
            
            # Handle cd command specially
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip()
                if not new_dir:
                    new_dir = str(Path.home())
                
                try:
                    if new_dir.startswith('/'):
                        target_dir = Path(new_dir)
                    else:
                        target_dir = self.working_dir / new_dir
                    
                    target_dir = target_dir.resolve()
                    
                    if target_dir.exists() and target_dir.is_dir():
                        self.working_dir = target_dir
                        cmd_entry["output"] = f"Changed directory to {self.working_dir}"
                        cmd_entry["exit_code"] = 0
                        self.command_history.append(cmd_entry)
                        
                        return {
                            "success": True,
                            "output": cmd_entry["output"],
                            "error": "",
                            "exit_code": 0,
                            "working_dir": str(self.working_dir)
                        }
                    else:
                        error_msg = f"Directory not found: {target_dir}"
                        cmd_entry["output"] = ""
                        cmd_entry["error"] = error_msg
                        cmd_entry["exit_code"] = 1
                        self.command_history.append(cmd_entry)
                        
                        return {
                            "success": False,
                            "output": "",
                            "error": error_msg,
                            "exit_code": 1,
                            "working_dir": str(self.working_dir)
                        }
                except Exception as e:
                    error_msg = f"Error changing directory: {str(e)}"
                    cmd_entry["output"] = ""
                    cmd_entry["error"] = error_msg
                    cmd_entry["exit_code"] = 1
                    self.command_history.append(cmd_entry)
                    
                    return {
                        "success": False,
                        "output": "",
                        "error": error_msg,
                        "exit_code": 1,
                        "working_dir": str(self.working_dir)
                    }
            
            # Execute other commands
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(self.working_dir),
                    env=self.environment
                )
                
                # Store process for potential termination
                self.active_processes[process.pid] = process
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    exit_code = process.returncode
                finally:
                    # Remove from active processes
                    if process.pid in self.active_processes:
                        del self.active_processes[process.pid]
                
                cmd_entry["output"] = stdout
                cmd_entry["error"] = stderr
                cmd_entry["exit_code"] = exit_code
                self.command_history.append(cmd_entry)
                
                return {
                    "success": exit_code == 0,
                    "output": stdout,
                    "error": stderr,
                    "exit_code": exit_code,
                    "working_dir": str(self.working_dir)
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                if process.pid in self.active_processes:
                    del self.active_processes[process.pid]
                
                error_msg = f"Command timed out after {timeout} seconds"
                cmd_entry["output"] = ""
                cmd_entry["error"] = error_msg
                cmd_entry["exit_code"] = -1
                self.command_history.append(cmd_entry)
                
                return {
                    "success": False,
                    "output": "",
                    "error": error_msg,
                    "exit_code": -1,
                    "working_dir": str(self.working_dir)
                }
                
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            return {
                "success": False,
                "output": "",
                "error": error_msg,
                "exit_code": -1,
                "working_dir": str(self.working_dir)
            }
    
    def kill_processes(self):
        """Kill all active processes in this session"""
        for pid, process in list(self.active_processes.items()):
            try:
                process.kill()
                process.wait(timeout=5)
            except:
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
        self.active_processes.clear()
    
    def get_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "working_dir": str(self.working_dir),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "command_count": len(self.command_history),
            "active_processes": len(self.active_processes),
            "environment_vars": len(self.environment)
        }

class TerminalManager:
    """Complete terminal management system"""
    
    def __init__(self):
        self.sessions = {}
        self.default_session_id = "default"
        self.max_history_per_session = 1000
        
        # Create default session
        self.create_session(self.default_session_id)
    
    def create_session(self, session_id: str = None, working_dir: str = ".") -> str:
        """Create new terminal session"""
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        if session_id in self.sessions:
            return session_id
        
        self.sessions[session_id] = TerminalSession(session_id, working_dir)
        return session_id
    
    def execute_command(self, command: str, session_id: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in specified session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        return self.sessions[session_id].execute_command(command, timeout)
    
    def get_session_history(self, session_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get command history for session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            return []
        
        history = self.sessions[session_id].command_history
        return history[-limit:] if limit > 0 else history
    
    def clear_session_history(self, session_id: str = None) -> bool:
        """Clear command history for session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].command_history.clear()
        return True
    
    def kill_session(self, session_id: str) -> bool:
        """Kill session and all its processes"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].kill_processes()
        if session_id != self.default_session_id:
            del self.sessions[session_id]
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        return [session.get_info() for session in self.sessions.values()]
    
    def get_session_info(self, session_id: str = None) -> Dict[str, Any]:
        """Get information about specific session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        return self.sessions[session_id].get_info()
    
    def set_environment_variable(self, key: str, value: str, session_id: str = None) -> bool:
        """Set environment variable for session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        self.sessions[session_id].environment[key] = value
        return True
    
    def get_environment_variables(self, session_id: str = None) -> Dict[str, str]:
        """Get environment variables for session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            return {}
        
        return self.sessions[session_id].environment.copy()
    
    def change_working_directory(self, path: str, session_id: str = None) -> Dict[str, Any]:
        """Change working directory for session"""
        return self.execute_command(f"cd {path}", session_id)
    
    def get_working_directory(self, session_id: str = None) -> str:
        """Get current working directory for session"""
        if session_id is None:
            session_id = self.default_session_id
        
        if session_id not in self.sessions:
            return str(Path.cwd())
        
        return str(self.sessions[session_id].working_dir)
    
    def execute_script(self, script_content: str, script_type: str = "bash", session_id: str = None) -> Dict[str, Any]:
        """Execute script content"""
        if session_id is None:
            session_id = self.default_session_id
        
        # Create temporary script file
        import tempfile
        
        extensions = {
            "bash": ".sh",
            "python": ".py",
            "javascript": ".js",
            "powershell": ".ps1"
        }
        
        ext = extensions.get(script_type, ".sh")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            if script_type == "python":
                command = f"python {script_path}"
            elif script_type == "javascript":
                command = f"node {script_path}"
            elif script_type == "powershell":
                command = f"powershell -File {script_path}"
            else:
                command = f"bash {script_path}"
            
            result = self.execute_command(command, session_id)
            
            # Clean up
            try:
                os.unlink(script_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            try:
                os.unlink(script_path)
            except:
                pass
            
            return {
                "success": False,
                "output": "",
                "error": f"Error executing script: {str(e)}",
                "exit_code": -1
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "active_sessions": len(self.sessions),
                "total_processes": sum(len(s.active_processes) for s in self.sessions.values())
            }
        except Exception as e:
            return {"error": f"Error getting system info: {str(e)}"}

# Global terminal manager instance
terminal_manager = TerminalManager()

def main():
    """Demo of terminal manager functionality"""
    
    # Execute some commands
    result = terminal_manager.execute_command("ls -la")
    print("Command result:", json.dumps(result, indent=2))
    
    # Get history
    history = terminal_manager.get_session_history()
    print("Command history:", json.dumps(history[-1:], indent=2))
    
    # Get system info
    sys_info = terminal_manager.get_system_info()
    print("System info:", json.dumps(sys_info, indent=2))

if __name__ == "__main__":
    main()