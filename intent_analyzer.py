"""
MITO Engine - Intent Analyzer
Advanced Python system to understand user intent and provide intelligent responses
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntentAnalysis:
    """Structure for intent analysis results"""
    primary_intent: str
    confidence: float
    action_required: str
    entities: List[str]
    context: Dict[str, Any]
    suggested_response: str
    follow_up_questions: List[str]
    technical_keywords: List[str]
    urgency_level: str

class IntentAnalyzer:
    """Advanced intent analysis system"""
    
    def __init__(self):
        self.intent_patterns = {
            'create': {
                'patterns': [
                    r'\b(create|make|build|generate|add|new)\b',
                    r'\bneed\s+(a|an|some)\b',
                    r'\bwant\s+to\s+(create|make|build)\b'
                ],
                'keywords': ['file', 'function', 'class', 'module', 'system', 'handler', 'manager'],
                'confidence_boost': 0.8
            },
            'fix': {
                'patterns': [
                    r'\b(fix|repair|solve|debug|error|issue|problem|broken)\b',
                    r'\bnot\s+working\b',
                    r'\bdoesn\'?t\s+work\b',
                    r'\bfailing\b'
                ],
                'keywords': ['bug', 'error', 'exception', 'crash', 'fail'],
                'confidence_boost': 0.9
            },
            'improve': {
                'patterns': [
                    r'\b(improve|enhance|optimize|better|upgrade)\b',
                    r'\bmore\s+(efficient|effective)\b',
                    r'\bbetter\s+performance\b'
                ],
                'keywords': ['performance', 'speed', 'efficiency', 'optimization'],
                'confidence_boost': 0.7
            },
            'understand': {
                'patterns': [
                    r'\b(explain|understand|how|what|why|tell\s+me)\b',
                    r'\bwhat\s+(is|does|happens)\b',
                    r'\bhow\s+(do|does|to)\b'
                ],
                'keywords': ['documentation', 'help', 'guide', 'tutorial'],
                'confidence_boost': 0.6
            },
            'integrate': {
                'patterns': [
                    r'\b(integrate|connect|link|add\s+to|combine)\b',
                    r'\bwork\s+with\b',
                    r'\bconnect\s+to\b'
                ],
                'keywords': ['api', 'database', 'service', 'system', 'module'],
                'confidence_boost': 0.8
            },
            'configure': {
                'patterns': [
                    r'\b(configure|setup|set\s+up|install|enable)\b',
                    r'\bsettings?\b',
                    r'\bparameters?\b'
                ],
                'keywords': ['config', 'settings', 'environment', 'variables'],
                'confidence_boost': 0.7
            }
        }
        
        self.entity_patterns = {
            'file_types': r'\b(\w+\.(py|js|html|css|json|xml|sql|txt|md))\b',
            'technologies': r'\b(python|javascript|html|css|sql|flask|django|react|vue|node)\b',
            'actions': r'\b(upload|download|save|load|delete|update|insert|select)\b',
            'components': r'\b(database|api|server|client|frontend|backend|ui|interface)\b'
        }
        
        self.urgency_keywords = {
            'high': ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'broken', 'down'],
            'medium': ['soon', 'need', 'important', 'should', 'please'],
            'low': ['when', 'could', 'might', 'eventually', 'sometime']
        }
        
        self.technical_domains = {
            'web_development': ['html', 'css', 'javascript', 'frontend', 'backend', 'api', 'server'],
            'data_management': ['database', 'sql', 'data', 'storage', 'query', 'table'],
            'file_operations': ['file', 'upload', 'download', 'save', 'load', 'import', 'export'],
            'system_administration': ['server', 'deploy', 'configure', 'setup', 'install', 'admin'],
            'development_tools': ['editor', 'ide', 'debug', 'test', 'build', 'compile']
        }
        
        logger.info("IntentAnalyzer initialized with comprehensive pattern matching")
    
    def analyze_intent(self, user_input: str, context: Dict[str, Any] = None) -> IntentAnalysis:
        """Analyze user input to determine intent"""
        user_input = user_input.lower().strip()
        context = context or {}
        
        # Extract entities
        entities = self.extract_entities(user_input)
        
        # Determine primary intent
        intent_scores = self.calculate_intent_scores(user_input)
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        confidence = intent_scores[primary_intent]
        
        # Determine urgency
        urgency_level = self.determine_urgency(user_input)
        
        # Extract technical keywords
        technical_keywords = self.extract_technical_keywords(user_input)
        
        # Determine technical domain
        technical_domain = self.identify_technical_domain(user_input, technical_keywords)
        
        # Generate action plan
        action_required = self.generate_action_plan(primary_intent, entities, technical_keywords)
        
        # Generate suggested response
        suggested_response = self.generate_response(primary_intent, entities, technical_domain, urgency_level)
        
        # Generate follow-up questions
        follow_up_questions = self.generate_follow_up_questions(primary_intent, entities, technical_domain)
        
        analysis = IntentAnalysis(
            primary_intent=primary_intent,
            confidence=confidence,
            action_required=action_required,
            entities=entities,
            context={
                'technical_domain': technical_domain,
                'user_input_length': len(user_input),
                'has_technical_terms': len(technical_keywords) > 0,
                'timestamp': datetime.now().isoformat(),
                **context
            },
            suggested_response=suggested_response,
            follow_up_questions=follow_up_questions,
            technical_keywords=technical_keywords,
            urgency_level=urgency_level
        )
        
        logger.info(f"Intent analysis complete: {primary_intent} (confidence: {confidence:.2f})")
        return analysis
    
    def calculate_intent_scores(self, text: str) -> Dict[str, float]:
        """Calculate confidence scores for each intent"""
        scores = {}
        
        for intent, config in self.intent_patterns.items():
            score = 0.0
            
            # Pattern matching
            for pattern in config['patterns']:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.3
            
            # Keyword matching
            for keyword in config['keywords']:
                if keyword in text:
                    score += 0.2
            
            # Apply confidence boost
            if score > 0:
                score *= config['confidence_boost']
            
            scores[intent] = min(score, 1.0)
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract entities from text"""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))  # Remove duplicates
    
    def determine_urgency(self, text: str) -> str:
        """Determine urgency level from text"""
        for level, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return level
        return 'medium'  # Default urgency
    
    def extract_technical_keywords(self, text: str) -> List[str]:
        """Extract technical keywords"""
        technical_keywords = []
        
        # Combine all technical terms from domains
        all_tech_terms = []
        for domain_terms in self.technical_domains.values():
            all_tech_terms.extend(domain_terms)
        
        for term in set(all_tech_terms):
            if term in text:
                technical_keywords.append(term)
        
        return technical_keywords
    
    def identify_technical_domain(self, text: str, keywords: List[str]) -> str:
        """Identify the primary technical domain"""
        domain_scores = {}
        
        for domain, terms in self.technical_domains.items():
            score = sum(1 for term in terms if term in text or term in keywords)
            domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return 'general'
    
    def generate_action_plan(self, intent: str, entities: List[str], keywords: List[str]) -> str:
        """Generate specific action plan based on intent"""
        actions = {
            'create': f"Create new {' and '.join(entities[:3]) if entities else 'component'} with {' and '.join(keywords[:2]) if keywords else 'standard functionality'}",
            'fix': f"Debug and resolve issues with {' and '.join(entities[:2]) if entities else 'system components'} focusing on {' and '.join(keywords[:2]) if keywords else 'error resolution'}",
            'improve': f"Optimize and enhance {' and '.join(entities[:2]) if entities else 'existing systems'} for better {' and '.join(keywords[:2]) if keywords else 'performance'}",
            'understand': f"Provide detailed explanation of {' and '.join(entities[:2]) if entities else 'concepts'} including {' and '.join(keywords[:2]) if keywords else 'implementation details'}",
            'integrate': f"Connect and integrate {' and '.join(entities[:2]) if entities else 'systems'} with {' and '.join(keywords[:2]) if keywords else 'existing infrastructure'}",
            'configure': f"Set up and configure {' and '.join(entities[:2]) if entities else 'system components'} with proper {' and '.join(keywords[:2]) if keywords else 'settings'}"
        }
        
        return actions.get(intent, "Analyze requirements and implement appropriate solution")
    
    def generate_response(self, intent: str, entities: List[str], domain: str, urgency: str) -> str:
        """Generate appropriate response based on analysis"""
        urgency_prefix = {
            'high': "I'll immediately address this ",
            'medium': "I'll work on this ",
            'low': "I can help with this "
        }
        
        domain_context = {
            'web_development': "web development task",
            'data_management': "data management requirement",
            'file_operations': "file handling operation",
            'system_administration': "system administration task",
            'development_tools': "development tool enhancement",
            'general': "technical requirement"
        }
        
        intent_actions = {
            'create': "by building the required components",
            'fix': "by diagnosing and resolving the issues",
            'improve': "by optimizing the existing functionality",
            'understand': "by providing comprehensive explanations",
            'integrate': "by establishing proper connections",
            'configure': "by setting up the necessary configurations"
        }
        
        response = f"{urgency_prefix.get(urgency, 'I will handle this ')} {domain_context.get(domain, 'requirement')} {intent_actions.get(intent, 'with appropriate solutions')}."
        
        if entities:
            response += f" This involves working with: {', '.join(entities[:3])}."
        
        return response
    
    def generate_follow_up_questions(self, intent: str, entities: List[str], domain: str) -> List[str]:
        """Generate relevant follow-up questions"""
        questions = {
            'create': [
                "What specific features should be included?",
                "Are there any particular requirements or constraints?",
                "Should this integrate with existing systems?"
            ],
            'fix': [
                "What error messages or symptoms are you seeing?",
                "When did this issue first occur?",
                "What was the last working configuration?"
            ],
            'improve': [
                "What aspects need the most improvement?",
                "Are there specific performance targets?",
                "What current limitations are you experiencing?"
            ],
            'understand': [
                "What level of detail would be most helpful?",
                "Are you looking for implementation examples?",
                "Do you need documentation or tutorials?"
            ],
            'integrate': [
                "What systems need to be connected?",
                "Are there existing APIs or interfaces to work with?",
                "What data needs to be shared between systems?"
            ],
            'configure': [
                "What environment are you setting up for?",
                "Are there specific settings or parameters needed?",
                "Do you have existing configuration files?"
            ]
        }
        
        return questions.get(intent, ["What additional details can you provide?", "Are there specific requirements to consider?"])
    
    def save_analysis(self, analysis: IntentAnalysis, filename: str = None):
        """Save analysis results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intent_analysis_{timestamp}.json"
        
        try:
            analysis_dict = {
                'primary_intent': analysis.primary_intent,
                'confidence': analysis.confidence,
                'action_required': analysis.action_required,
                'entities': analysis.entities,
                'context': analysis.context,
                'suggested_response': analysis.suggested_response,
                'follow_up_questions': analysis.follow_up_questions,
                'technical_keywords': analysis.technical_keywords,
                'urgency_level': analysis.urgency_level
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return None
    
    def load_analysis(self, filename: str) -> Optional[IntentAnalysis]:
        """Load analysis from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return IntentAnalysis(**data)
            
        except Exception as e:
            logger.error(f"Failed to load analysis from {filename}: {e}")
            return None
    
    def get_intent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent intent analysis history"""
        history_files = sorted(Path('.').glob('intent_analysis_*.json'), reverse=True)
        history = []
        
        for file_path in history_files[:limit]:
            analysis = self.load_analysis(str(file_path))
            if analysis:
                history.append({
                    'timestamp': analysis.context.get('timestamp'),
                    'intent': analysis.primary_intent,
                    'confidence': analysis.confidence,
                    'entities': analysis.entities,
                    'urgency': analysis.urgency_level,
                    'file': str(file_path)
                })
        
        return history

def main():
    """Demo of intent analyzer functionality"""
    analyzer = IntentAnalyzer()
    
    # Test cases
    test_inputs = [
        "create file handler",
        "need to fix the broken database connection",
        "how do I improve performance of the web server",
        "explain how the authentication system works",
        "connect the API to the frontend",
        "setup the development environment"
    ]
    
    print("Intent Analysis Demo")
    print("=" * 50)
    
    for user_input in test_inputs:
        print(f"\nInput: '{user_input}'")
        analysis = analyzer.analyze_intent(user_input)
        print(f"Intent: {analysis.primary_intent} (confidence: {analysis.confidence:.2f})")
        print(f"Action: {analysis.action_required}")
        print(f"Response: {analysis.suggested_response}")
        print(f"Entities: {analysis.entities}")
        print(f"Keywords: {analysis.technical_keywords}")
        print(f"Urgency: {analysis.urgency_level}")
        print("-" * 30)

if __name__ == "__main__":
    main()