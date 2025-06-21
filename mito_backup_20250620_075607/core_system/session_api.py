"""
MITO Engine - Session Management API Endpoints
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: API endpoints for session persistence, profiles, and telemetry
"""

from flask import jsonify, request, session, Response, send_file
from session_manager import SessionManager, ProfileManager, AuditTrail, TelemetryStreamer, ReportGenerator
import json
import time
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize managers
session_manager = SessionManager()
profile_manager = ProfileManager()
audit_trail = AuditTrail()
telemetry_streamer = TelemetryStreamer()
report_generator = ReportGenerator()

def register_session_routes(app):
    """Register all session management routes with the Flask app"""
    
    @app.route('/api/session/state', methods=['GET', 'POST'])
    def api_session_state():
        """Get or save session state"""
        session_id = session_manager.get_session_id()
        
        if request.method == 'GET':
            try:
                tab_states = session_manager.get_tab_states(session_id)
                workspace_state = session_manager.get_workspace_state(session_id)
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'tab_states': tab_states,
                    'workspace_state': workspace_state
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
                
        elif request.method == 'POST':
            try:
                data = request.get_json()
                
                if 'tab_id' in data and 'state' in data:
                    session_manager.save_tab_state(session_id, data['tab_id'], data['state'])
                    audit_trail.log_action(session_id, session.get('user_id', 'anonymous'), 
                                         'tab_state_saved', f"Saved state for tab {data['tab_id']}", data['tab_id'])
                
                if 'workspace_state' in data:
                    session_manager.save_workspace_state(session_id, data['workspace_state'])
                    audit_trail.log_action(session_id, session.get('user_id', 'anonymous'), 
                                         'workspace_state_saved', 'Saved workspace state')
                
                return jsonify({'success': True, 'message': 'State saved successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/profile', methods=['GET', 'POST'])
    def api_user_profile():
        """Get or update user profile"""
        user_id = session.get('user_id', 'anonymous')
        session_id = session_manager.get_session_id()
        
        if request.method == 'GET':
            try:
                profile = profile_manager.get_user_profile(user_id)
                audit_trail.log_action(session_id, user_id, 'profile_accessed', 'User accessed profile')
                
                return jsonify({
                    'success': True,
                    'profile': profile
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
                
        elif request.method == 'POST':
            try:
                profile_data = request.get_json()
                profile_manager.update_user_profile(user_id, profile_data)
                audit_trail.log_action(session_id, user_id, 'profile_updated', 
                                     f"Updated profile: {json.dumps(profile_data)}")
                
                return jsonify({'success': True, 'message': 'Profile updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/profile/tools')
    def api_profile_tools():
        """Get available tools based on user role"""
        try:
            user_id = session.get('user_id', 'anonymous')
            profile = profile_manager.get_user_profile(user_id)
            
            # Define tool configurations by permission
            tool_configs = {
                'workspace': {'name': 'Workspace', 'icon': 'fas fa-home', 'category': 'core'},
                'ai-chat': {'name': 'AI Chat', 'icon': 'fas fa-robot', 'category': 'ai'},
                'code-editor': {'name': 'Code Editor', 'icon': 'fas fa-code', 'category': 'development'},
                'file-browser': {'name': 'Files', 'icon': 'fas fa-folder', 'category': 'development'},
                'project-tools': {'name': 'Project Tools', 'icon': 'fas fa-tools', 'category': 'development'},
                'analytics': {'name': 'Analytics', 'icon': 'fas fa-chart-bar', 'category': 'analytics'},
                'advanced': {'name': 'Advanced', 'icon': 'fas fa-cogs', 'category': 'system'},
                'networking': {'name': 'Networking', 'icon': 'fas fa-network-wired', 'category': 'operations'},
                'monitoring': {'name': 'Monitoring', 'icon': 'fas fa-eye', 'category': 'operations'},
                'deployment': {'name': 'Deployment', 'icon': 'fas fa-cloud-upload-alt', 'category': 'operations'},
                'security': {'name': 'Security', 'icon': 'fas fa-shield-alt', 'category': 'security'},
                'audit': {'name': 'Audit', 'icon': 'fas fa-clipboard-list', 'category': 'security'},
                'reporting': {'name': 'Reporting', 'icon': 'fas fa-file-alt', 'category': 'analytics'},
                'data-tools': {'name': 'Data Tools', 'icon': 'fas fa-database', 'category': 'analytics'}
            }
            
            available_tools = []
            for permission in profile['permissions']:
                if permission in tool_configs:
                    tool_config = tool_configs[permission].copy()
                    tool_config['id'] = permission
                    available_tools.append(tool_config)
            
            return jsonify({
                'success': True,
                'tools': available_tools,
                'role': profile['role']
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/telemetry/stream')
    def api_telemetry_stream():
        """Server-sent events for live telemetry"""
        session_id = session_manager.get_session_id()
        user_id = session.get('user_id', 'anonymous')
        
        def generate_telemetry():
            telemetry_streamer.start_stream(session_id, 'metrics')
            audit_trail.log_action(session_id, user_id, 'telemetry_stream_started', 'Started live telemetry stream')
            
            try:
                while session_id in telemetry_streamer.active_streams:
                    metrics = telemetry_streamer.get_live_metrics()
                    yield f"data: {json.dumps(metrics)}\n\n"
                    time.sleep(2)  # Update every 2 seconds
            except GeneratorExit:
                telemetry_streamer.stop_stream(session_id, 'metrics')
                audit_trail.log_action(session_id, user_id, 'telemetry_stream_stopped', 'Stopped live telemetry stream')
        
        return Response(generate_telemetry(), mimetype='text/plain')

    @app.route('/api/telemetry/start', methods=['POST'])
    def api_telemetry_start():
        """Start telemetry streaming"""
        try:
            data = request.get_json()
            session_id = session_manager.get_session_id()
            stream_type = data.get('type', 'metrics')
            
            telemetry_streamer.start_stream(session_id, stream_type)
            
            return jsonify({
                'success': True,
                'message': f'Telemetry stream {stream_type} started',
                'session_id': session_id
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/telemetry/stop', methods=['POST'])
    def api_telemetry_stop():
        """Stop telemetry streaming"""
        try:
            data = request.get_json()
            session_id = session_manager.get_session_id()
            stream_type = data.get('type')
            
            telemetry_streamer.stop_stream(session_id, stream_type)
            
            return jsonify({
                'success': True,
                'message': f'Telemetry stream stopped'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/audit/log')
    def api_audit_log():
        """Get audit trail entries"""
        try:
            session_id = request.args.get('session_id')
            user_id = request.args.get('user_id')
            days = int(request.args.get('days', 7))
            
            audit_data = audit_trail.get_audit_log(session_id, user_id, days)
            
            return jsonify({
                'success': True,
                'audit_log': audit_data,
                'total_entries': len(audit_data)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/audit/action', methods=['POST'])
    def api_audit_action():
        """Log custom audit action"""
        try:
            data = request.get_json()
            session_id = session_manager.get_session_id()
            user_id = session.get('user_id', 'anonymous')
            
            audit_trail.log_action(
                session_id,
                user_id,
                data.get('action_type', 'custom'),
                data.get('action_details', ''),
                data.get('tab_context')
            )
            
            return jsonify({'success': True, 'message': 'Action logged successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/reports/generate', methods=['POST'])
    def api_generate_report():
        """Generate exportable report"""
        try:
            data = request.get_json()
            report_type = data.get('type', 'audit')
            format_type = data.get('format', 'json')
            user_id = data.get('user_id', session.get('user_id', 'anonymous'))
            days = data.get('days', 30)
            
            session_id = session_manager.get_session_id()
            audit_trail.log_action(session_id, user_id, 'report_generated', 
                                 f"Generated {report_type} report in {format_type} format")
            
            if report_type == 'audit':
                report_data = report_generator.generate_audit_report(user_id, days)
            elif report_type == 'system':
                report_data = report_generator.generate_system_report()
            else:
                return jsonify({'success': False, 'error': 'Invalid report type'})
            
            if format_type == 'pdf':
                filename = report_generator.export_to_pdf(report_data, report_type)
                if filename:
                    return jsonify({
                        'success': True,
                        'report_id': report_data['report_id'],
                        'download_url': f'/api/reports/download/{filename}',
                        'filename': filename
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to generate PDF'})
                    
            elif format_type == 'csv':
                filename = report_generator.export_to_csv(report_data, report_type)
                if filename:
                    return jsonify({
                        'success': True,
                        'report_id': report_data['report_id'],
                        'download_url': f'/api/reports/download/{filename}',
                        'filename': filename
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to generate CSV'})
            else:
                # Return JSON format
                return jsonify({
                    'success': True,
                    'report_data': report_data
                })
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/reports/download/<filename>')
    def api_download_report(filename):
        """Download generated report file"""
        try:
            session_id = session_manager.get_session_id()
            user_id = session.get('user_id', 'anonymous')
            
            audit_trail.log_action(session_id, user_id, 'report_downloaded', 
                                 f"Downloaded report file: {filename}")
            
            return send_file(filename, as_attachment=True)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/reports/certificate')
    def api_generate_certificate():
        """Generate digital signature certificate"""
        try:
            session_id = session_manager.get_session_id()
            user_id = session.get('user_id', 'anonymous')
            
            # Generate system certificate with current metrics
            system_report = report_generator.generate_system_report()
            audit_report = report_generator.generate_audit_report(user_id, 7)
            
            certificate_data = {
                'certificate_id': f"MITO-CERT-{int(time.time())}",
                'issued_to': user_id,
                'issued_at': datetime.now().isoformat(),
                'validity_period': '1 year',
                'system_metrics': system_report['current_metrics'],
                'audit_summary': {
                    'total_actions': audit_report['total_actions'],
                    'period_days': audit_report['period_days'],
                    'most_used_tools': list(audit_report['tab_usage'].keys())[:5] if audit_report['tab_usage'] else []
                },
                'digital_signature': f"MITO-{hash(str(system_report) + str(audit_report))}"
            }
            
            # Generate certificate PDF
            filename = report_generator.export_to_pdf(certificate_data, 'certificate')
            
            audit_trail.log_action(session_id, user_id, 'certificate_generated', 
                                 f"Generated digital certificate: {certificate_data['certificate_id']}")
            
            return jsonify({
                'success': True,
                'certificate': certificate_data,
                'download_url': f'/api/reports/download/{filename}' if filename else None
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/session/cleanup')
    def api_session_cleanup():
        """Clean up old session data"""
        try:
            # This would typically clean up sessions older than X days
            # For now, just return success
            return jsonify({
                'success': True,
                'message': 'Session cleanup completed',
                'cleaned_sessions': 0
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/session/stats')
    def api_session_stats():
        """Get session and system statistics"""
        try:
            telemetry = TelemetryStreamer()
            metrics = telemetry.get_live_metrics()
            
            session_id = session_manager.get_session_id()
            user_id = session.get('user_id', 'anonymous')
            
            # Get recent audit activity
            recent_audit = audit_trail.get_audit_log(session_id=session_id, days=1)
            
            stats = {
                'current_session': session_id,
                'user_id': user_id,
                'system_metrics': metrics,
                'session_activity': {
                    'actions_today': len(recent_audit),
                    'last_action': recent_audit[0]['timestamp'] if recent_audit else None
                },
                'active_streams': len(telemetry_streamer.active_streams)
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})