"""
Chatbot Service
Provides context-aware conversational assistance for students
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import uuid4

from ..models import Student, ChatLog, TopicMastery, Assessment
from ..schemas import ChatMessage, ChatResponse
from ..services.content_generator import get_content_generator_service
from ..services.adaptive_engine import get_adaptive_engine
from ..services.curriculum_ingestion import get_curriculum_ingestion_service

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for providing intelligent chatbot responses to students"""
    
    def __init__(self):
        self.content_generator = get_content_generator_service()
        self.adaptive_engine = get_adaptive_engine()
        self.curriculum_service = get_curriculum_ingestion_service()
        
        # Chatbot personality and context
        self.personality = {
            'name': 'EduBot',
            'tone': 'encouraging and supportive',
            'style': 'conversational and age-appropriate',
            'context': 'Sierra Leone educational system'
        }
    
    def process_chat_message(self, student_id: str, message: str, 
                           session_id: str, db: Session) -> Dict[str, Any]:
        """Process a chat message and generate a response"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return {
                    'success': False,
                    'error': 'Student not found'
                }
            
            # Get current learning context
            context = self._get_student_context(student_id, db)
            
            # Generate response using content generator
            response_data = self.content_generator.generate_chatbot_response(
                student_id=student_id,
                user_message=message,
                context=context,
                db=db
            )
            
            if not response_data['success']:
                return response_data
            
            # Extract response
            response = response_data['response']
            
            # Log the conversation
            self._log_conversation(
                student_id=student_id,
                session_id=session_id,
                user_message=message,
                bot_response=response.get('response', ''),
                context=context,
                db=db
            )
            
            # Enhance response with additional context
            enhanced_response = self._enhance_response(response, context, student)
            
            return {
                'success': True,
                'response': enhanced_response,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_student_context(self, student_id: str, db: Session) -> Dict[str, Any]:
        """Get current learning context for the student"""
        try:
            # Get recent topic mastery
            recent_mastery = db.query(TopicMastery).filter(
                TopicMastery.student_id == student_id
            ).order_by(TopicMastery.last_practiced.desc()).first()
            
            # Get recent assessments
            recent_assessments = db.query(Assessment).filter(
                Assessment.student_id == student_id
            ).order_by(Assessment.completed_at.desc()).limit(5).all()
            
            # Get recent mistakes
            recent_mistakes = []
            for assessment in recent_assessments:
                if assessment.errors:
                    try:
                        errors = json.loads(assessment.errors)
                        recent_mistakes.extend(errors)
                    except:
                        pass
            
            # Get chat history for context
            recent_chats = db.query(ChatLog).filter(
                ChatLog.student_id == student_id
            ).order_by(ChatLog.created_at.desc()).limit(3).all()
            
            context = {
                'current_subject': recent_mastery.subject if recent_mastery else 'mathematics',
                'current_topic': recent_mastery.topic if recent_mastery else 'introduction',
                'mastery_level': recent_mastery.mastery_level if recent_mastery else 0,
                'recent_mistakes': recent_mistakes[:5],  # Last 5 mistakes
                'recent_scores': [a.score for a in recent_assessments],
                'chat_history': [
                    {
                        'user_message': chat.user_message,
                        'bot_response': chat.bot_response,
                        'timestamp': chat.created_at.isoformat()
                    }
                    for chat in recent_chats
                ]
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting student context: {e}")
            return {
                'current_subject': 'mathematics',
                'current_topic': 'introduction',
                'mastery_level': 0,
                'recent_mistakes': [],
                'recent_scores': [],
                'chat_history': []
            }
    
    def _enhance_response(self, response: Dict[str, Any], context: Dict[str, Any], 
                         student: Student) -> Dict[str, Any]:
        """Enhance the chatbot response with additional context and personality"""
        try:
            enhanced = response.copy()
            
            # Add personalized greeting if it's the first message in session
            if not context.get('chat_history'):
                enhanced['response'] = f"Hello {student.name}! I'm {self.personality['name']}, your AI learning assistant. " + enhanced['response']
            
            # Add encouragement based on recent performance
            recent_scores = context.get('recent_scores', [])
            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                if avg_score >= 80:
                    encouragement = "Great job on your recent assessments! "
                elif avg_score >= 60:
                    encouragement = "You're making good progress! "
                else:
                    encouragement = "Don't worry, I'm here to help you improve! "
                
                enhanced['response'] = encouragement + enhanced['response']
            
            # Add topic-specific suggestions
            current_topic = context.get('current_topic', '')
            if current_topic and current_topic != 'introduction':
                enhanced['suggested_actions'].append(f"Review the {current_topic} lesson")
                enhanced['suggested_actions'].append(f"Practice more {current_topic} exercises")
            
            # Add Sierra Leone context
            enhanced['response'] = self._add_sierra_leone_context(enhanced['response'], context)
            
            # Add learning tips
            enhanced['learning_tip'] = self._get_learning_tip(context, student)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            return response
    
    def _add_sierra_leone_context(self, response: str, context: Dict[str, Any]) -> str:
        """Add Sierra Leone-specific context to the response"""
        # This is a simple implementation - in practice, you'd have more sophisticated context injection
        sierra_leone_examples = [
            "like the markets in Freetown",
            "similar to the rice farms in Bo",
            "just like the schools in Kenema",
            "like the traditional foods we enjoy"
        ]
        
        # Add context if the response mentions examples
        if any(keyword in response.lower() for keyword in ['example', 'like', 'similar']):
            import random
            example = random.choice(sierra_leone_examples)
            response = response.replace('.', f' {example}.', 1)
        
        return response
    
    def _get_learning_tip(self, context: Dict[str, Any], student: Student) -> str:
        """Get a personalized learning tip for the student"""
        tips = {
            'slow': "Take your time and don't rush. It's better to understand fully than to hurry.",
            'moderate': "Keep up the good pace! Try to maintain consistency in your study schedule.",
            'fast': "Great speed! Make sure you're also taking time to review and reinforce what you've learned."
        }
        
        # Get tip based on learning pace
        base_tip = tips.get(student.learning_pace, tips['moderate'])
        
        # Add subject-specific tip
        subject = context.get('current_subject', 'mathematics')
        if subject == 'mathematics':
            base_tip += " For math, practice with real examples from daily life in Sierra Leone."
        elif subject == 'english':
            base_tip += " For English, try reading local newspapers or stories to improve your skills."
        elif subject == 'science':
            base_tip += " For science, observe the natural world around you - it's full of examples!"
        
        return base_tip
    
    def _log_conversation(self, student_id: str, session_id: str, user_message: str,
                         bot_response: str, context: Dict[str, Any], db: Session):
        """Log the conversation for learning and analytics"""
        try:
            chat_log = ChatLog(
                student_id=student_id,
                session_id=session_id,
                subject=context.get('current_subject'),
                topic=context.get('current_topic'),
                user_message=user_message,
                bot_response=bot_response
            )
            
            db.add(chat_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
            db.rollback()
    
    def get_chat_history(self, student_id: str, session_id: str, 
                        db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a student session"""
        try:
            chats = db.query(ChatLog).filter(
                ChatLog.student_id == student_id,
                ChatLog.session_id == session_id
            ).order_by(ChatLog.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': str(chat.id),
                    'user_message': chat.user_message,
                    'bot_response': chat.bot_response,
                    'timestamp': chat.created_at.isoformat(),
                    'subject': chat.subject,
                    'topic': chat.topic
                }
                for chat in reversed(chats)  # Return in chronological order
            ]
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def get_conversation_analytics(self, student_id: str, db: Session) -> Dict[str, Any]:
        """Get analytics about student's chatbot usage"""
        try:
            # Get all chat logs for the student
            chats = db.query(ChatLog).filter(
                ChatLog.student_id == student_id
            ).all()
            
            if not chats:
                return {'error': 'No chat history found'}
            
            # Calculate analytics
            total_messages = len(chats)
            
            # Group by subject
            subject_counts = {}
            for chat in chats:
                subject = chat.subject or 'general'
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
            
            # Group by topic
            topic_counts = {}
            for chat in chats:
                topic = chat.topic or 'general'
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            # Calculate average message length
            user_message_lengths = [len(chat.user_message) for chat in chats]
            avg_message_length = sum(user_message_lengths) / len(user_message_lengths)
            
            # Get most active sessions
            session_counts = {}
            for chat in chats:
                session_id = chat.session_id
                if session_id:
                    session_counts[session_id] = session_counts.get(session_id, 0) + 1
            
            most_active_session = max(session_counts.items(), key=lambda x: x[1]) if session_counts else None
            
            return {
                'total_messages': total_messages,
                'subject_distribution': subject_counts,
                'topic_distribution': topic_counts,
                'average_message_length': avg_message_length,
                'most_active_session': most_active_session,
                'first_chat': chats[0].created_at.isoformat(),
                'last_chat': chats[-1].created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics: {e}")
            return {'error': str(e)}
    
    def create_new_session(self, student_id: str) -> str:
        """Create a new chat session"""
        return str(uuid4())
    
    def get_suggested_questions(self, student_id: str, context: Dict[str, Any]) -> List[str]:
        """Get suggested questions based on student's current context"""
        try:
            subject = context.get('current_subject', 'mathematics')
            topic = context.get('current_topic', 'introduction')
            mastery_level = context.get('mastery_level', 0)
            
            # Base questions for any topic
            base_questions = [
                f"Can you explain {topic} in simple terms?",
                f"What are some examples of {topic}?",
                f"How is {topic} used in real life?",
                f"What should I focus on when studying {topic}?"
            ]
            
            # Subject-specific questions
            if subject == 'mathematics':
                base_questions.extend([
                    f"How do I solve {topic} problems step by step?",
                    f"What formulas do I need to know for {topic}?",
                    f"Can you give me a Sierra Leone example of {topic}?"
                ])
            elif subject == 'english':
                base_questions.extend([
                    f"How do I improve my {topic} skills?",
                    f"What are common mistakes in {topic}?",
                    f"Can you help me practice {topic}?"
                ])
            elif subject == 'science':
                base_questions.extend([
                    f"What experiments can I do to understand {topic}?",
                    f"How does {topic} relate to Sierra Leone's environment?",
                    f"What are the key concepts in {topic}?"
                ])
            
            # Adjust questions based on mastery level
            if mastery_level < 40:
                base_questions.extend([
                    f"I'm struggling with {topic}. Can you help me understand the basics?",
                    f"What are the most important things to know about {topic}?",
                    f"Can you break down {topic} into smaller parts?"
                ])
            elif mastery_level > 80:
                base_questions.extend([
                    f"What are some advanced applications of {topic}?",
                    f"How can I challenge myself with {topic}?",
                    f"What comes after {topic} in the curriculum?"
                ])
            
            return base_questions[:8]  # Return top 8 questions
            
        except Exception as e:
            logger.error(f"Error getting suggested questions: {e}")
            return [
                "Can you help me understand this topic?",
                "What should I study next?",
                "How can I improve my performance?"
            ]


# Global service instance
chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Get or create the global chatbot service"""
    global chatbot_service
    if chatbot_service is None:
        chatbot_service = ChatbotService()
    return chatbot_service
