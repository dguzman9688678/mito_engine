#!/usr/bin/env python3
"""
Advanced NLP Engine for MITO
Integrates GPT-4 and BERT for enhanced communication and understanding
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import openai
import requests
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import sqlite3
from collections import defaultdict
import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class AdvancedNLPEngine:
    """Advanced Natural Language Processing Engine"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.conversation_history = []
        self.user_context = {}
        self.init_nlp_models()
        self.init_conversation_db()
        
    def init_nlp_models(self):
        """Initialize NLP models and pipelines"""
        try:
            # BERT-based models for various tasks
            self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                             model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            self.question_answerer = pipeline("question-answering", 
                                             model="deepset/roberta-base-squad2")
            self.text_classifier = pipeline("text-classification", 
                                           model="microsoft/DialoGPT-medium")
            
            # Load spaCy model for advanced NLP
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found. Installing...")
                os.system("python -m spacy download en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize NLTK components
            nltk.download('vader_lexicon', quiet=True)
            self.vader_analyzer = SentimentIntensityAnalyzer()
            
            logger.info("NLP models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP models: {e}")
            self.sentiment_analyzer = None
            self.question_answerer = None
            
    def init_conversation_db(self):
        """Initialize conversation history database"""
        conn = sqlite3.connect("nlp_conversations.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_input TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                sentiment_score REAL,
                intent TEXT,
                entities TEXT,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                preferences TEXT,
                conversation_style TEXT,
                technical_level TEXT,
                interests TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
    def analyze_text_advanced(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive text analysis"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'text_length': len(text),
            'word_count': len(text.split())
        }
        
        # Sentiment analysis with multiple models
        if self.sentiment_analyzer:
            try:
                sentiment_result = self.sentiment_analyzer(text)[0]
                analysis['sentiment'] = {
                    'label': sentiment_result['label'],
                    'score': sentiment_result['score']
                }
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
                
        # VADER sentiment analysis
        try:
            vader_scores = self.vader_analyzer.polarity_scores(text)
            analysis['vader_sentiment'] = vader_scores
        except Exception as e:
            logger.error(f"VADER analysis failed: {e}")
            
        # spaCy analysis
        if self.nlp:
            try:
                doc = self.nlp(text)
                
                # Named Entity Recognition
                entities = []
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'description': spacy.explain(ent.label_)
                    })
                analysis['entities'] = entities
                
                # Part-of-speech analysis
                pos_tags = []
                for token in doc:
                    if not token.is_stop and not token.is_punct:
                        pos_tags.append({
                            'text': token.text,
                            'lemma': token.lemma_,
                            'pos': token.pos_,
                            'tag': token.tag_
                        })
                analysis['pos_tags'] = pos_tags[:10]  # Limit to first 10
                
                # Dependency parsing
                dependencies = []
                for token in doc:
                    if token.dep_ != 'ROOT':
                        dependencies.append({
                            'text': token.text,
                            'dependency': token.dep_,
                            'head': token.head.text
                        })
                analysis['dependencies'] = dependencies[:10]
                
            except Exception as e:
                logger.error(f"spaCy analysis failed: {e}")
                
        return analysis
        
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        intent_patterns = {
            'code_generation': [
                r'(create|generate|build|make).*?(function|class|script|app)',
                r'(write|code).*?(python|javascript|java|c\+\+)',
                r'(implement|develop).*?(algorithm|feature)'
            ],
            'question_answering': [
                r'(what|how|why|when|where|which).*?\?',
                r'(explain|describe|tell me about)',
                r'(help|assist).*?(with|me)'
            ],
            'project_management': [
                r'(create|setup|initialize).*?(project|repository)',
                r'(manage|organize|track).*?(tasks|issues)',
                r'(deploy|release|publish)'
            ],
            'debugging': [
                r'(fix|debug|solve|resolve).*?(error|bug|issue)',
                r'(not working|failing|broken)',
                r'(troubleshoot|diagnose)'
            ],
            'learning': [
                r'(learn|understand|study).*?(about|how)',
                r'(tutorial|guide|documentation)',
                r'(best practices|examples)'
            ]
        }
        
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            intent_scores[intent] = score
            
        # Get the intent with highest score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return {
                    'intent': best_intent[0],
                    'confidence': min(best_intent[1] / 5.0, 1.0),  # Normalize to 0-1
                    'all_scores': intent_scores
                }
                
        return {
            'intent': 'general_conversation',
            'confidence': 0.5,
            'all_scores': intent_scores
        }
        
    def generate_contextual_response(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Generate contextual response using GPT-4"""
        try:
            # Analyze the input
            analysis = self.analyze_text_advanced(user_input)
            intent_info = self.detect_intent(user_input)
            
            # Build context for GPT-4
            system_prompt = self._build_system_prompt(analysis, intent_info, context)
            
            # Prepare conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history
            for msg in self.conversation_history[-5:]:  # Last 5 messages
                messages.append({"role": "user", "content": msg.get('user_input', '')})
                messages.append({"role": "assistant", "content": msg.get('bot_response', '')})
                
            messages.append({"role": "user", "content": user_input})
            
            # Generate response with GPT-4
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest GPT-4 model
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9
            )
            
            bot_response = response.choices[0].message.content
            
            # Store conversation
            self._store_conversation(user_input, bot_response, analysis, intent_info)
            
            return bot_response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return self._generate_fallback_response(user_input, intent_info)
            
    def _build_system_prompt(self, analysis: Dict[str, Any], intent_info: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build dynamic system prompt based on analysis"""
        base_prompt = """You are MITO Engine, an advanced AI development assistant with deep expertise in:
- Software development and architecture
- AI/ML implementation and optimization
- DevOps and cloud infrastructure
- Project management and collaboration
- Security and compliance best practices

You provide comprehensive, practical solutions with working code examples."""
        
        # Add intent-specific instructions
        intent = intent_info.get('intent', 'general_conversation')
        
        if intent == 'code_generation':
            base_prompt += "\n\nFocus on generating high-quality, production-ready code with proper error handling, documentation, and best practices."
        elif intent == 'question_answering':
            base_prompt += "\n\nProvide detailed explanations with examples. Break down complex concepts into digestible parts."
        elif intent == 'debugging':
            base_prompt += "\n\nAnalyze the problem systematically, identify root causes, and provide step-by-step solutions."
        elif intent == 'project_management':
            base_prompt += "\n\nFocus on practical project organization, workflow optimization, and team collaboration strategies."
            
        # Add sentiment-aware instructions
        sentiment = analysis.get('sentiment', {})
        if sentiment.get('label') == 'NEGATIVE':
            base_prompt += "\n\nThe user seems frustrated or concerned. Be extra helpful and provide reassuring, clear guidance."
        elif sentiment.get('label') == 'POSITIVE':
            base_prompt += "\n\nThe user appears enthusiastic. Match their energy and provide comprehensive solutions."
            
        # Add context if available
        if context:
            base_prompt += f"\n\nAdditional context: {json.dumps(context, indent=2)}"
            
        return base_prompt
        
    def _generate_fallback_response(self, user_input: str, intent_info: Dict[str, Any]) -> str:
        """Generate fallback response when GPT-4 is unavailable"""
        intent = intent_info.get('intent', 'general_conversation')
        
        fallback_responses = {
            'code_generation': "I can help you generate code. Please specify the programming language and requirements for your project.",
            'question_answering': "I'd be happy to answer your question. Could you provide more specific details about what you'd like to know?",
            'debugging': "I can assist with debugging. Please share the error message, code snippet, and expected behavior.",
            'project_management': "I can help with project management. What specific aspect would you like assistance with?",
            'learning': "I can provide learning resources and explanations. What topic would you like to explore?",
            'general_conversation': "I'm here to help with your development and AI projects. How can I assist you today?"
        }
        
        return fallback_responses.get(intent, fallback_responses['general_conversation'])
        
    def _store_conversation(self, user_input: str, bot_response: str, analysis: Dict[str, Any], intent_info: Dict[str, Any]):
        """Store conversation in database"""
        try:
            conn = sqlite3.connect("nlp_conversations.db")
            cursor = conn.cursor()
            
            sentiment_score = analysis.get('sentiment', {}).get('score', 0.0)
            intent = intent_info.get('intent', 'unknown')
            entities = json.dumps(analysis.get('entities', []))
            confidence = intent_info.get('confidence', 0.0)
            
            cursor.execute("""
                INSERT INTO conversations 
                (session_id, user_input, bot_response, sentiment_score, intent, entities, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('default_session', user_input, bot_response, sentiment_score, intent, entities, confidence))
            
            conn.commit()
            conn.close()
            
            # Add to conversation history
            self.conversation_history.append({
                'user_input': user_input,
                'bot_response': bot_response,
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'intent': intent_info
            })
            
            # Keep only last 20 conversations in memory
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
                
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            
    def personalize_response(self, user_id: str, base_response: str) -> str:
        """Personalize response based on user profile"""
        try:
            # Get user profile
            conn = sqlite3.connect("nlp_conversations.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT preferences, technical_level FROM user_profiles WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                preferences = json.loads(result[0]) if result[0] else {}
                technical_level = result[1] or 'intermediate'
                
                # Adjust response based on technical level
                if technical_level == 'beginner':
                    # Add more explanations and context
                    base_response += "\n\nLet me know if you need any clarification or would like me to explain any technical terms."
                elif technical_level == 'expert':
                    # Be more concise and technical
                    base_response = base_response.replace("Let me explain", "").replace("For beginners", "")
                    
                # Apply preferences
                if preferences.get('code_style') == 'verbose':
                    base_response += "\n\nI've included detailed comments and explanations in the code."
                elif preferences.get('code_style') == 'minimal':
                    # Remove excessive explanations
                    lines = base_response.split('\n')
                    base_response = '\n'.join(line for line in lines if not line.strip().startswith('#') or 'TODO' in line)
                    
            conn.close()
            return base_response
            
        except Exception as e:
            logger.error(f"Failed to personalize response: {e}")
            return base_response
            
    def update_user_profile(self, user_id: str, preferences: Dict[str, Any], technical_level: str = None):
        """Update user profile for personalization"""
        try:
            conn = sqlite3.connect("nlp_conversations.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles 
                (user_id, preferences, technical_level, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, json.dumps(preferences), technical_level))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            
    def get_conversation_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get insights from conversation history"""
        try:
            conn = sqlite3.connect("nlp_conversations.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT intent, COUNT(*) as count, AVG(sentiment_score) as avg_sentiment
                FROM conversations 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY intent
                ORDER BY count DESC
            """.format(days))
            
            intent_stats = []
            for row in cursor.fetchall():
                intent_stats.append({
                    'intent': row[0],
                    'count': row[1],
                    'avg_sentiment': row[2]
                })
                
            cursor.execute("""
                SELECT COUNT(*) as total_conversations,
                       AVG(sentiment_score) as overall_sentiment,
                       AVG(confidence) as avg_confidence
                FROM conversations 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days))
            
            overall_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'period_days': days,
                'total_conversations': overall_stats[0],
                'overall_sentiment': overall_stats[1],
                'avg_confidence': overall_stats[2],
                'intent_breakdown': intent_stats,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation insights: {e}")
            return {}

class ConversationManager:
    """Manages conversation flow and context"""
    
    def __init__(self, nlp_engine: AdvancedNLPEngine):
        self.nlp_engine = nlp_engine
        self.active_sessions = {}
        
    def start_conversation(self, session_id: str, user_id: str = None) -> Dict[str, Any]:
        """Start a new conversation session"""
        session_info = {
            'session_id': session_id,
            'user_id': user_id,
            'started_at': datetime.now().isoformat(),
            'context': {},
            'message_count': 0
        }
        
        self.active_sessions[session_id] = session_info
        
        return {
            'session_id': session_id,
            'welcome_message': "Hello! I'm MITO Engine's advanced AI assistant. I can help you with development, AI implementation, project management, and much more. How can I assist you today?",
            'capabilities': [
                'Advanced code generation and architecture design',
                'AI/ML model implementation and optimization',
                'Project management and workflow automation',
                'Security and compliance guidance',
                'Cloud infrastructure and DevOps',
                'Real-time problem solving and debugging'
            ]
        }
        
    def process_message(self, session_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a conversation message"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found. Please start a new conversation.'}
            
        session = self.active_sessions[session_id]
        session['message_count'] += 1
        
        # Update context
        if context:
            session['context'].update(context)
            
        # Generate response
        response = self.nlp_engine.generate_contextual_response(message, session['context'])
        
        # Personalize if user_id available
        if session.get('user_id'):
            response = self.nlp_engine.personalize_response(session['user_id'], response)
            
        return {
            'response': response,
            'session_id': session_id,
            'message_count': session['message_count'],
            'timestamp': datetime.now().isoformat()
        }
        
    def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """End a conversation session"""
        if session_id in self.active_sessions:
            session = self.active_sessions.pop(session_id)
            return {
                'session_ended': True,
                'duration_minutes': (datetime.now() - datetime.fromisoformat(session['started_at'])).seconds // 60,
                'total_messages': session['message_count']
            }
        return {'error': 'Session not found'}

# Global instances
nlp_engine = AdvancedNLPEngine()
conversation_manager = ConversationManager(nlp_engine)

def main():
    """Demo of advanced NLP capabilities"""
    print("Advanced NLP Engine for MITO - Demo")
    print("=" * 50)
    
    # Start conversation
    session = conversation_manager.start_conversation("demo_session", "demo_user")
    print(f"Welcome: {session['welcome_message']}")
    
    # Test various types of inputs
    test_inputs = [
        "Can you help me create a Python web scraper?",
        "I'm getting an error in my React application. The component won't render.",
        "What are the best practices for implementing microservices architecture?",
        "How do I set up CI/CD pipeline for a machine learning project?",
        "I need to optimize my database queries for better performance."
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n--- Test {i} ---")
        print(f"User: {test_input}")
        
        # Analyze the input
        analysis = nlp_engine.analyze_text_advanced(test_input)
        intent = nlp_engine.detect_intent(test_input)
        
        print(f"Intent: {intent['intent']} (confidence: {intent['confidence']:.2f})")
        print(f"Sentiment: {analysis.get('sentiment', {}).get('label', 'N/A')}")
        
        # Generate response
        result = conversation_manager.process_message("demo_session", test_input)
        print(f"MITO: {result['response'][:200]}...")
        
    # Get conversation insights
    insights = nlp_engine.get_conversation_insights(1)
    print(f"\n--- Conversation Insights ---")
    print(f"Total conversations: {insights.get('total_conversations', 0)}")
    print(f"Overall sentiment: {insights.get('overall_sentiment', 0):.2f}")
    print(f"Intent breakdown: {insights.get('intent_breakdown', [])}")

if __name__ == "__main__":
    main()