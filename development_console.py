"""
MITO Engine - Development Console with Extensions & Tools
Comprehensive developer environment with console, extensions, problem diagnostics, and debugging tools
"""

import json
import os
import sys
import subprocess
import time
import threading
import logging
import traceback
import psutil
import inspect
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import ast
import re

@dataclass
class ConsoleMessage:
    """Console message structure"""
    timestamp: str
    level: str
    source: str
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class Problem:
    """Problem diagnostic structure"""
    id: str
    severity: str  # error, warning, info
    source: str
    line: Optional[int]
    column: Optional[int]
    message: str
    solution: Optional[str]
    timestamp: str

@dataclass
class Extension:
    """Development extension structure"""
    id: str
    name: str
    version: str
    description: str
    enabled: bool
    commands: List[str]
    settings: Dict[str, Any]

class SystemMonitor:
    """Real-time system monitoring"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_usage': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0},
            'process_count': 0,
            'uptime': 0
        }
        
    def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
        
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.monitoring:
            try:
                self.metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
                self.metrics['memory_percent'] = psutil.virtual_memory().percent
                self.metrics['disk_usage'] = psutil.disk_usage('/').percent
                self.metrics['network_io'] = psutil.net_io_counters()._asdict()
                self.metrics['process_count'] = len(psutil.pids())
                self.metrics['uptime'] = time.time() - psutil.boot_time()
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
            time.sleep(1)
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return self.metrics.copy()

class ProblemDiagnostics:
    """Problem detection and analysis"""
    
    def __init__(self):
        self.problems: List[Problem] = []
        
    def scan_file(self, filepath: str) -> List[Problem]:
        """Scan file for problems"""
        problems = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Python syntax check
            if filepath.endswith('.py'):
                problems.extend(self._check_python_syntax(filepath, content))
                problems.extend(self._check_python_style(filepath, content))
                
            # JSON validation
            elif filepath.endswith('.json'):
                problems.extend(self._check_json_syntax(filepath, content))
                
            # General checks
            problems.extend(self._check_common_issues(filepath, content))
            
        except Exception as e:
            problems.append(Problem(
                id=f"file_read_{int(time.time())}",
                severity="error",
                source=filepath,
                line=None,
                column=None,
                message=f"Could not read file: {str(e)}",
                solution="Check file permissions and encoding",
                timestamp=datetime.now().isoformat()
            ))
            
        return problems
        
    def _check_python_syntax(self, filepath: str, content: str) -> List[Problem]:
        """Check Python syntax"""
        problems = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            problems.append(Problem(
                id=f"syntax_{int(time.time())}",
                severity="error",
                source=filepath,
                line=e.lineno,
                column=e.offset,
                message=f"Syntax Error: {e.msg}",
                solution="Fix syntax error according to Python grammar",
                timestamp=datetime.now().isoformat()
            ))
        except Exception as e:
            problems.append(Problem(
                id=f"parse_{int(time.time())}",
                severity="error",
                source=filepath,
                line=None,
                column=None,
                message=f"Parse Error: {str(e)}",
                solution="Check file encoding and structure",
                timestamp=datetime.now().isoformat()
            ))
            
        return problems
        
    def _check_python_style(self, filepath: str, content: str) -> List[Problem]:
        """Check Python style issues"""
        problems = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Long lines
            if len(line) > 120:
                problems.append(Problem(
                    id=f"long_line_{i}_{int(time.time())}",
                    severity="warning",
                    source=filepath,
                    line=i,
                    column=120,
                    message="Line too long (>120 characters)",
                    solution="Break line into multiple lines or refactor",
                    timestamp=datetime.now().isoformat()
                ))
                
            # Trailing whitespace
            if line.rstrip() != line:
                problems.append(Problem(
                    id=f"trailing_ws_{i}_{int(time.time())}",
                    severity="info",
                    source=filepath,
                    line=i,
                    column=len(line.rstrip()),
                    message="Trailing whitespace",
                    solution="Remove trailing whitespace",
                    timestamp=datetime.now().isoformat()
                ))
                
        return problems
        
    def _check_json_syntax(self, filepath: str, content: str) -> List[Problem]:
        """Check JSON syntax"""
        problems = []
        
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            problems.append(Problem(
                id=f"json_{int(time.time())}",
                severity="error",
                source=filepath,
                line=e.lineno,
                column=e.colno,
                message=f"JSON Error: {e.msg}",
                solution="Fix JSON syntax - check for missing commas, quotes, or brackets",
                timestamp=datetime.now().isoformat()
            ))
            
        return problems
        
    def _check_common_issues(self, filepath: str, content: str) -> List[Problem]:
        """Check common issues"""
        problems = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # TODO comments
            if 'TODO' in line or 'FIXME' in line:
                problems.append(Problem(
                    id=f"todo_{i}_{int(time.time())}",
                    severity="info",
                    source=filepath,
                    line=i,
                    column=line.find('TODO') if 'TODO' in line else line.find('FIXME'),
                    message="TODO/FIXME comment found",
                    solution="Address the TODO/FIXME item",
                    timestamp=datetime.now().isoformat()
                ))
                
        return problems
        
    def scan_project(self, project_path: str = '.') -> List[Problem]:
        """Scan entire project for problems"""
        all_problems = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                filepath = os.path.join(root, file)
                file_problems = self.scan_file(filepath)
                all_problems.extend(file_problems)
                
        self.problems = all_problems
        return all_problems

class ExtensionManager:
    """Manage development extensions"""
    
    def __init__(self):
        self.extensions: Dict[str, Extension] = {}
        self._load_builtin_extensions()
        
    def _load_builtin_extensions(self):
        """Load built-in extensions"""
        
        # Code formatter extension
        self.extensions['formatter'] = Extension(
            id='formatter',
            name='Code Formatter',
            version='1.0.0',
            description='Automatic code formatting for Python, JSON, and other languages',
            enabled=True,
            commands=['format', 'format-file', 'format-project'],
            settings={
                'line_length': 120,
                'indent_size': 4,
                'format_on_save': True
            }
        )
        
        # Linter extension
        self.extensions['linter'] = Extension(
            id='linter',
            name='Code Linter',
            version='1.0.0',
            description='Real-time code analysis and error detection',
            enabled=True,
            commands=['lint', 'lint-file', 'lint-project'],
            settings={
                'show_warnings': True,
                'show_style_issues': True,
                'auto_fix': False
            }
        )
        
        # Git integration
        self.extensions['git'] = Extension(
            id='git',
            name='Git Integration',
            version='1.0.0',
            description='Git version control integration',
            enabled=True,
            commands=['git-status', 'git-commit', 'git-push', 'git-pull'],
            settings={
                'auto_stage': False,
                'commit_template': True,
                'show_diff': True
            }
        )
        
        # Terminal extension
        self.extensions['terminal'] = Extension(
            id='terminal',
            name='Integrated Terminal',
            version='1.0.0',
            description='Built-in terminal with command execution',
            enabled=True,
            commands=['terminal', 'run', 'exec'],
            settings={
                'shell': '/bin/bash',
                'working_directory': '.',
                'history_size': 1000
            }
        )
        
        # Database tools
        self.extensions['database'] = Extension(
            id='database',
            name='Database Tools',
            version='1.0.0',
            description='Database connection and query tools',
            enabled=True,
            commands=['db-connect', 'db-query', 'db-schema'],
            settings={
                'auto_complete': True,
                'query_timeout': 30,
                'max_results': 1000
            }
        )
        
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get extension by ID"""
        return self.extensions.get(extension_id)
        
    def enable_extension(self, extension_id: str) -> bool:
        """Enable extension"""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = True
            return True
        return False
        
    def disable_extension(self, extension_id: str) -> bool:
        """Disable extension"""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = False
            return True
        return False
        
    def get_enabled_extensions(self) -> List[Extension]:
        """Get all enabled extensions"""
        return [ext for ext in self.extensions.values() if ext.enabled]

class CommandProcessor:
    """Process console commands"""
    
    def __init__(self, extension_manager: ExtensionManager, problem_diagnostics: ProblemDiagnostics):
        self.extension_manager = extension_manager
        self.problem_diagnostics = problem_diagnostics
        self.command_history: List[str] = []
        
    def execute_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute console command"""
        args = args or []
        self.command_history.append(f"{command} {' '.join(args)}")
        
        try:
            if command == 'help':
                return self._help_command()
            elif command == 'extensions':
                return self._extensions_command(args)
            elif command == 'problems':
                return self._problems_command(args)
            elif command == 'format':
                return self._format_command(args)
            elif command == 'lint':
                return self._lint_command(args)
            elif command == 'run':
                return self._run_command(args)
            elif command == 'git':
                return self._git_command(args)
            elif command == 'system':
                return self._system_command(args)
            elif command == 'clear':
                return {'success': True, 'action': 'clear', 'message': 'Console cleared'}
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Command failed: {str(e)}'}
            
    def _help_command(self) -> Dict[str, Any]:
        """Show help information"""
        commands = {
            'help': 'Show this help message',
            'extensions': 'Manage extensions (list, enable <id>, disable <id>)',
            'problems': 'Show problems (scan, list, fix)',
            'format': 'Format code (file <path>, project)',
            'lint': 'Lint code (file <path>, project)',
            'run': 'Run command (python <file>, npm <command>)',
            'git': 'Git operations (status, commit, push, pull)',
            'system': 'System information (status, processes, logs)',
            'clear': 'Clear console'
        }
        
        return {
            'success': True,
            'commands': commands,
            'message': f'Available commands: {", ".join(commands.keys())}'
        }
        
    def _extensions_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle extensions command"""
        if not args or args[0] == 'list':
            extensions = []
            for ext in self.extension_manager.extensions.values():
                extensions.append({
                    'id': ext.id,
                    'name': ext.name,
                    'version': ext.version,
                    'enabled': ext.enabled,
                    'description': ext.description
                })
            return {'success': True, 'extensions': extensions}
            
        elif args[0] == 'enable' and len(args) > 1:
            success = self.extension_manager.enable_extension(args[1])
            return {'success': success, 'message': f'Extension {args[1]} {"enabled" if success else "not found"}'}
            
        elif args[0] == 'disable' and len(args) > 1:
            success = self.extension_manager.disable_extension(args[1])
            return {'success': success, 'message': f'Extension {args[1]} {"disabled" if success else "not found"}'}
            
        return {'success': False, 'error': 'Invalid extensions command'}
        
    def _problems_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle problems command"""
        if not args or args[0] == 'scan':
            problems = self.problem_diagnostics.scan_project()
            return {
                'success': True,
                'problems': [
                    {
                        'id': p.id,
                        'severity': p.severity,
                        'source': p.source,
                        'line': p.line,
                        'column': p.column,
                        'message': p.message,
                        'solution': p.solution
                    } for p in problems
                ],
                'count': len(problems)
            }
            
        elif args[0] == 'list':
            return {
                'success': True,
                'problems': [
                    {
                        'id': p.id,
                        'severity': p.severity,
                        'source': p.source,
                        'line': p.line,
                        'message': p.message
                    } for p in self.problem_diagnostics.problems
                ],
                'count': len(self.problem_diagnostics.problems)
            }
            
        return {'success': False, 'error': 'Invalid problems command'}
        
    def _format_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle format command"""
        if args and args[0] == 'file' and len(args) > 1:
            filepath = args[1]
            try:
                # Simple Python formatting
                if filepath.endswith('.py'):
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Basic formatting - could be enhanced
                    formatted = content.replace('\t', '    ')  # Convert tabs to spaces
                    
                    with open(filepath, 'w') as f:
                        f.write(formatted)
                        
                    return {'success': True, 'message': f'Formatted {filepath}'}
                else:
                    return {'success': False, 'error': 'Only Python files supported'}
                    
            except Exception as e:
                return {'success': False, 'error': f'Format failed: {str(e)}'}
                
        return {'success': False, 'error': 'Invalid format command'}
        
    def _lint_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle lint command"""
        if args and args[0] == 'file' and len(args) > 1:
            filepath = args[1]
            problems = self.problem_diagnostics.scan_file(filepath)
            return {
                'success': True,
                'problems': [
                    {
                        'severity': p.severity,
                        'line': p.line,
                        'message': p.message,
                        'solution': p.solution
                    } for p in problems
                ],
                'count': len(problems)
            }
            
        return {'success': False, 'error': 'Invalid lint command'}
        
    def _run_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle run command"""
        if not args:
            return {'success': False, 'error': 'No command specified'}
            
        try:
            cmd = ' '.join(args)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Command timed out'}
        except Exception as e:
            return {'success': False, 'error': f'Execution failed: {str(e)}'}
            
    def _git_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle git command"""
        if not args:
            args = ['status']
            
        try:
            cmd = f"git {' '.join(args)}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout or result.stderr,
                'returncode': result.returncode
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Git command failed: {str(e)}'}
            
    def _system_command(self, args: List[str]) -> Dict[str, Any]:
        """Handle system command"""
        if not args or args[0] == 'status':
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                return {
                    'success': True,
                    'system': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_available': memory.available,
                        'disk_percent': disk.percent,
                        'disk_free': disk.free,
                        'process_count': len(psutil.pids()),
                        'python_version': sys.version
                    }
                }
                
            except Exception as e:
                return {'success': False, 'error': f'System check failed: {str(e)}'}
                
        return {'success': False, 'error': 'Invalid system command'}

class DevelopmentConsole:
    """Main development console"""
    
    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.problem_diagnostics = ProblemDiagnostics()
        self.extension_manager = ExtensionManager()
        self.command_processor = CommandProcessor(self.extension_manager, self.problem_diagnostics)
        self.console_log: List[ConsoleMessage] = []
        
        # Start system monitoring
        self.system_monitor.start_monitoring()
        
        # Initial problem scan
        self.log_message('info', 'system', 'Development console initialized')
        
    def log_message(self, level: str, source: str, message: str, details: Dict[str, Any] = None):
        """Log message to console"""
        console_message = ConsoleMessage(
            timestamp=datetime.now().isoformat(),
            level=level,
            source=source,
            message=message,
            details=details
        )
        self.console_log.append(console_message)
        
        # Keep only last 1000 messages
        if len(self.console_log) > 1000:
            self.console_log = self.console_log[-1000:]
            
    def execute_command(self, command_line: str) -> Dict[str, Any]:
        """Execute command line"""
        parts = command_line.strip().split()
        if not parts:
            return {'success': False, 'error': 'Empty command'}
            
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        self.log_message('info', 'user', f'Executing: {command_line}')
        
        result = self.command_processor.execute_command(command, args)
        
        if result.get('success'):
            self.log_message('info', 'system', f'Command completed: {command}')
        else:
            self.log_message('error', 'system', f'Command failed: {result.get("error", "Unknown error")}')
            
        return result
        
    def get_console_state(self) -> Dict[str, Any]:
        """Get current console state"""
        return {
            'log': [
                {
                    'timestamp': msg.timestamp,
                    'level': msg.level,
                    'source': msg.source,
                    'message': msg.message,
                    'details': msg.details
                } for msg in self.console_log[-100:]  # Last 100 messages
            ],
            'system_metrics': self.system_monitor.get_metrics(),
            'extensions': [
                {
                    'id': ext.id,
                    'name': ext.name,
                    'enabled': ext.enabled
                } for ext in self.extension_manager.extensions.values()
            ],
            'problems_count': len(self.problem_diagnostics.problems),
            'command_history': self.command_processor.command_history[-20:]  # Last 20 commands
        }

def main():
    """Demo of development console"""
    console = DevelopmentConsole()
    
    print("MITO Development Console initialized")
    print("Type 'help' for available commands")
    
    while True:
        try:
            command = input("MITO> ").strip()
            if command.lower() in ['exit', 'quit']:
                break
                
            result = console.execute_command(command)
            
            if result.get('success'):
                if 'message' in result:
                    print(result['message'])
                if 'output' in result:
                    print(result['output'])
                if 'commands' in result:
                    for cmd, desc in result['commands'].items():
                        print(f"  {cmd}: {desc}")
                if 'extensions' in result:
                    for ext in result['extensions']:
                        status = "✓" if ext['enabled'] else "✗"
                        print(f"  {status} {ext['id']}: {ext['name']}")
                if 'problems' in result:
                    for problem in result['problems'][:10]:  # Show first 10
                        print(f"  {problem['severity']}: {problem['message']} ({problem.get('source', 'unknown')}:{problem.get('line', '?')})")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Console error: {e}")
            
    print("Console session ended")

if __name__ == "__main__":
    main()