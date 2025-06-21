"""
MITO Engine - Networking API Endpoints
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: Networking API endpoints for MITO Engine
"""

from flask import jsonify, request
from networking_manager import NetworkingManager
import subprocess
import os
from datetime import datetime

# Initialize networking manager
networking_manager = NetworkingManager()

def register_networking_routes(app):
    """Register all networking-related routes with the Flask app"""
    
    @app.route('/api/network/interfaces')
    def api_network_interfaces():
        """Get network interfaces"""
        try:
            interfaces = networking_manager.get_network_interfaces()
            return jsonify({'success': True, 'interfaces': interfaces})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/connections')
    def api_network_connections():
        """Get active network connections"""
        try:
            connections = networking_manager.get_active_connections()
            return jsonify({'success': True, 'connections': connections})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/ping', methods=['POST'])
    def api_network_ping():
        """Ping a host"""
        try:
            data = request.get_json()
            host = data.get('host')
            if not host:
                return jsonify({'success': False, 'error': 'Host required'})
            result = networking_manager.ping_host(host, data.get('count', 4))
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/dns', methods=['POST'])
    def api_network_dns():
        """Resolve DNS for hostname"""
        try:
            data = request.get_json()
            hostname = data.get('hostname')
            if not hostname:
                return jsonify({'success': False, 'error': 'Hostname required'})
            result = networking_manager.resolve_dns(hostname)
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/port-scan', methods=['POST'])
    def api_network_port_scan():
        """Scan ports on a host"""
        try:
            data = request.get_json()
            host = data.get('host')
            if not host:
                return jsonify({'success': False, 'error': 'Host required'})
            start_port = data.get('start_port', 80)
            end_port = data.get('end_port', 80)
            
            if start_port == end_port:
                result = networking_manager.scan_port(host, start_port)
                return jsonify({'success': True, 'result': [result] if result['open'] else []})
            else:
                result = networking_manager.scan_port_range(host, start_port, end_port)
                return jsonify({'success': True, 'result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/listening-ports')
    def api_network_listening_ports():
        """Get listening ports"""
        try:
            ports = networking_manager.get_listening_ports()
            return jsonify({'success': True, 'ports': ports})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/network/bandwidth')
    def api_network_bandwidth():
        """Get bandwidth usage"""
        try:
            bandwidth = networking_manager.get_bandwidth_usage()
            return jsonify({'success': True, 'bandwidth': bandwidth})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/execute-command', methods=['POST'])
    def api_execute_command():
        """Execute terminal command"""
        try:
            data = request.get_json()
            command = data.get('command')
            if not command:
                return jsonify({'success': False, 'error': 'Command required'})
            
            dangerous_commands = ['rm -rf', 'sudo rm', 'format', 'fdisk', 'mkfs']
            if any(danger in command.lower() for danger in dangerous_commands):
                return jsonify({'success': False, 'error': 'Command not allowed'})
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return jsonify({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            })
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Command timeout'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/secrets', methods=['GET'])
    def api_secrets():
        """Get secrets status"""
        try:
            secrets = []
            env_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
            for var in env_vars:
                if os.environ.get(var):
                    secrets.append({'name': var, 'exists': True})
            return jsonify({'success': True, 'secrets': secrets})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/storage')
    def api_storage():
        """Get object storage information"""
        try:
            storage_objects = []
            storage_dirs = ['mito_uploads', 'generated_code', 'static', 'templates']
            
            for directory in storage_dirs:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            filepath = os.path.join(root, file)
                            stat = os.stat(filepath)
                            storage_objects.append({
                                'name': os.path.relpath(filepath),
                                'size': stat.st_size,
                                'type': os.path.splitext(file)[1] or 'file',
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
            
            return jsonify({'success': True, 'objects': storage_objects})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/workflows')
    def api_workflows():
        """Get workflow information"""
        try:
            workflows = [
                {
                    'id': 'start-application',
                    'name': 'Start Application',
                    'description': 'Main MITO Engine application server',
                    'status': 'running'
                }
            ]
            return jsonify({'success': True, 'workflows': workflows})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/problems')
    def api_problems():
        """Get system problems and issues"""
        try:
            problems = []
            if not os.environ.get('ANTHROPIC_API_KEY'):
                problems.append({
                    'severity': 'warning',
                    'message': 'Claude API key not configured',
                    'file': '.env',
                    'line': 1
                })
            return jsonify({'success': True, 'problems': problems})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/workbench-tabs')
    def workbench_tabs():
        """MITO Engine tabbed workbench interface"""
        from flask import render_template
        return render_template('giant_workbench_tabs.html')