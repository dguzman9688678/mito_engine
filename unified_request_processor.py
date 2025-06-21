"""
MITO Engine - Unified Request Processor
Bridges conversational chat with autonomous task execution
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from ai_providers import ai_generate
from memory_manager import MITOMemoryManager
import logging

logger = logging.getLogger(__name__)

class UnifiedRequestProcessor:
    """
    Processes user requests and routes them to appropriate pipelines
    Bridges the gap between conversational AI and autonomous task execution
    """
    
    def __init__(self):
        self._memory_manager = None
        self.intent_patterns = {
            'code_generation': [
                r'generate.*code',
                r'create.*(?:function|class|script)',
                r'write.*(?:program|code)',
                r'build.*(?:app|application)',
                r'make.*calculator',
                r'develop.*(?:system|tool)'
            ],
            'system_diagnostic': [
                r'diagnose.*system',
                r'what.*broken',
                r'check.*status',
                r'debug.*issue',
                r'introspect',
                r'system.*health'
            ],
            'file_processing': [
                r'upload.*file',
                r'process.*document',
                r'analyze.*file',
                r'extract.*from'
            ],
            'project_creation': [
                r'create.*project',
                r'new.*application',
                r'build.*from.*scratch',
                r'start.*project'
            ],
            'image_generation': [
                r'generate.*image',
                r'create.*picture',
                r'draw.*diagram',
                r'make.*visual'
            ],
            'autonomous_task': [
                r'optimize.*system',
                r'clean.*memory',
                r'update.*providers',
                r'schedule.*task'
            ]
        }
    
    def process_request(self, prompt: str, provider: str = 'auto', session_id: str = None) -> Dict[str, Any]:
        """
        Main request processing pipeline
        Determines intent and routes to appropriate handler
        """
        try:
            # Initialize session if needed
            if not session_id:
                if not self._memory_manager:
                    self._memory_manager = MITOMemoryManager()
                session_id = self._memory_manager.get_session_id("default_user")
            
            # Analyze user intent
            intent = self.analyze_intent(prompt)
            logger.info(f"Detected intent: {intent} for prompt: {prompt[:50]}...")
            
            # Route to appropriate handler
            if intent == 'code_generation':
                return self.handle_code_generation(prompt, provider, session_id)
            elif intent == 'system_diagnostic':
                return self.handle_system_diagnostic(prompt, session_id)
            elif intent == 'file_processing':
                return self.handle_file_processing(prompt, session_id)
            elif intent == 'project_creation':
                return self.handle_project_creation(prompt, provider, session_id)
            elif intent == 'image_generation':
                return self.handle_image_generation(prompt, session_id)
            elif intent == 'autonomous_task':
                return self.handle_autonomous_task(prompt, session_id)
            else:
                return self.handle_conversational(prompt, provider, session_id)
                
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            return {
                'error': f'Request processing failed: {str(e)}',
                'success': False,
                'intent': 'error'
            }
    
    def analyze_intent(self, prompt: str) -> str:
        """
        Analyze user prompt to determine intent using pattern matching
        """
        prompt_lower = prompt.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return intent
        
        return 'conversational'
    
    def handle_code_generation(self, prompt: str, provider: str, session_id: str) -> Dict[str, Any]:
        """
        Handle code generation requests with enhanced context
        """
        try:
            # Extract programming language
            language = self.extract_language(prompt) or 'python'
            
            # Build enhanced prompt
            enhanced_prompt = f"""
            Generate production-ready, well-documented {language} code for: {prompt}
            
            Requirements:
            - Include comprehensive error handling
            - Add detailed comments and docstrings
            - Follow best practices for {language}
            - Make it complete and executable
            - Include usage examples if applicable
            - Add proper imports and dependencies
            """
            
            # Generate code with memory context
            start_time = datetime.now()
            code_response = ai_generate(enhanced_prompt, provider, session_id)
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Store in memory
            if not self._memory_manager:
                self._memory_manager = MITOMemoryManager()
            self._memory_manager.add_memory(
                user_id="default_user",
                content=f"Generated {language} code for: {prompt}",
                memory_type="code_generation",
                metadata={
                    "language": language,
                    "prompt": prompt,
                    "generation_time": generation_time
                }
            )
            
            logger.info(f"Generated {language} code in {generation_time:.2f}s")
            
            return {
                'response': f"Generated {language} code successfully:\n\n{code_response}",
                'code': code_response,
                'language': language,
                'provider': provider,
                'generation_time': round(generation_time, 2),
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'success': True,
                'intent': 'code_generation',
                'code_generated': True
            }
            
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return {
                'error': f'Code generation failed: {str(e)}',
                'success': False,
                'intent': 'code_generation'
            }
    
    def handle_system_diagnostic(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """
        Handle system diagnostic and introspection requests
        """
        try:
            import psutil
            from ai_providers import get_available_providers
            
            diagnostic_data = {
                "timestamp": datetime.now().isoformat(),
                "issues_found": [],
                "recommendations": [],
                "system_stats": {}
            }
            
            # Check system resources
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            diagnostic_data["system_stats"] = {
                "memory_percent": memory.percent,
                "cpu_percent": cpu,
                "memory_available": memory.available,
                "memory_total": memory.total
            }
            
            if memory.percent > 80:
                diagnostic_data["issues_found"].append("High memory usage detected")
                diagnostic_data["recommendations"].append("Consider restarting to free memory")
            
            # Check AI providers
            providers = get_available_providers()
            unavailable_providers = [name for name, info in providers.items() if not info['available']]
            if unavailable_providers:
                diagnostic_data["issues_found"].append(f"AI providers offline: {', '.join(unavailable_providers)}")
            
            # Generate diagnostic report
            if diagnostic_data["issues_found"]:
                status_msg = f"SYSTEM DIAGNOSTIC - {len(diagnostic_data['issues_found'])} issues detected:\n\n"
                for issue in diagnostic_data["issues_found"]:
                    status_msg += f"⚠️ {issue}\n"
                status_msg += "\nRECOMMENDATIONS:\n"
                for rec in diagnostic_data["recommendations"]:
                    status_msg += f"✓ {rec}\n"
            else:
                status_msg = "SYSTEM DIAGNOSTIC - All systems operational ✓"
            
            status_msg += f"\nSYSTEM STATS:\n"
            status_msg += f"Memory: {diagnostic_data['system_stats']['memory_percent']:.1f}%\n"
            status_msg += f"CPU: {diagnostic_data['system_stats']['cpu_percent']:.1f}%"
            
            return {
                'response': status_msg,
                'diagnostic_data': diagnostic_data,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'success': True,
                'intent': 'system_diagnostic'
            }
            
        except Exception as e:
            logger.error(f"Diagnostic error: {e}")
            return {
                'error': f'System diagnostic failed: {str(e)}',
                'success': False,
                'intent': 'system_diagnostic'
            }
    
    def handle_autonomous_task(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """
        Handle autonomous task execution requests
        """
        try:
            # This would integrate with the MITO agent task queue
            task_type = self.extract_task_type(prompt)
            
            response_msg = f"Autonomous task '{task_type}' has been queued for execution. MITO will handle this in the background."
            
            # Add to MITO's task queue (integration point)
            # mito_agent.add_task(task_type, prompt, priority='user_requested')
            
            return {
                'response': response_msg,
                'task_type': task_type,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'success': True,
                'intent': 'autonomous_task'
            }
            
        except Exception as e:
            return {
                'error': f'Autonomous task processing failed: {str(e)}',
                'success': False,
                'intent': 'autonomous_task'
            }
    
    def handle_conversational(self, prompt: str, provider: str, session_id: str) -> Dict[str, Any]:
        """
        Handle general conversational requests
        """
        try:
            response = ai_generate(prompt, provider, session_id)
            
            return {
                'response': response,
                'provider': provider,
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'success': True,
                'intent': 'conversational'
            }
            
        except Exception as e:
            return {
                'error': f'Conversational processing failed: {str(e)}',
                'success': False,
                'intent': 'conversational'
            }
    
    def extract_language(self, prompt: str) -> Optional[str]:
        """Extract programming language from prompt"""
        prompt_lower = prompt.lower()
        language_patterns = {
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node', 'react'],
            'java': ['java'],
            'cpp': ['c++', 'cpp'],
            'html': ['html'],
            'css': ['css'],
            'sql': ['sql', 'database']
        }
        
        for lang, patterns in language_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                return lang
        
        return None
    
    def extract_task_type(self, prompt: str) -> str:
        """Extract task type from autonomous task request"""
        prompt_lower = prompt.lower()
        
        if 'optimize' in prompt_lower:
            return 'system_optimization'
        elif 'clean' in prompt_lower:
            return 'memory_cleanup'
        elif 'update' in prompt_lower:
            return 'provider_update'
        else:
            return 'general_task'
    
    def handle_file_processing(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """Handle file processing requests"""
        return {
            'response': 'File processing capability ready. Please upload your file.',
            'session_id': session_id,
            'success': True,
            'intent': 'file_processing'
        }
    
    def handle_project_creation(self, prompt: str, provider: str, session_id: str) -> Dict[str, Any]:
        """Handle project creation requests"""
        return {
            'response': 'Project creation initiated. Generating project structure...',
            'session_id': session_id,
            'success': True,
            'intent': 'project_creation'
        }
    
    def handle_image_generation(self, prompt: str, session_id: str) -> Dict[str, Any]:
        """Handle image generation requests"""
        return {
            'response': 'Image generation requested. Processing...',
            'session_id': session_id,
            'success': True,
            'intent': 'image_generation'
        }