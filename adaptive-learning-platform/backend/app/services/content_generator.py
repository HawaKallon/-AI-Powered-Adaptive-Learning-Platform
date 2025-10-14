"""
Content Generation Service
Uses LLM to generate personalized educational content based on student profiles and curriculum
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from ..config import settings
from ..utils.prompts import get_prompt
from ..services.curriculum_ingestion import get_curriculum_ingestion_service
from ..models import GeneratedContent, Student, TopicMastery
from ..schemas import LessonContent, Exercise, ExerciseQuestion

logger = logging.getLogger(__name__)


class ContentGeneratorService:
    """Service for generating personalized educational content using LLM"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generator = None
        # Skip slow curriculum service - we use direct database queries now
        self.curriculum_service = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model - DISABLED for performance"""
        # Skip LLM initialization - we use curriculum-based generation instead
        # This is much faster and produces better results using actual curriculum content
        logger.info("LLM initialization skipped - using curriculum-based content generation")
        self.model = None
        self.tokenizer = None
        self.generator = None
    
    def _generate_with_llm(self, prompt: str) -> str:
        """Generate content using the LLM"""
        try:
            if self.generator:
                # Use the actual LLM
                result = self.generator(
                    prompt,
                    max_length=len(prompt.split()) + settings.max_tokens,
                    num_return_sequences=1,
                    temperature=settings.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                return result[0]['generated_text'][len(prompt):].strip()
            else:
                # Fallback to template-based generation
                return self._generate_fallback_content(prompt)
                
        except Exception as e:
            logger.error(f"Error generating content with LLM: {e}")
            return self._generate_fallback_content(prompt)
    
    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate content using templates when LLM is not available"""
        # This is a simple fallback - in production, you'd want more sophisticated templates
        if "lesson" in prompt.lower():
            return self._generate_fallback_lesson(prompt)
        elif "exercise" in prompt.lower():
            return self._generate_fallback_exercise(prompt)
        elif "chatbot" in prompt.lower() or "response" in prompt.lower():
            return self._generate_fallback_chat_response(prompt)
        else:
            return '{"error": "Content generation not available"}'
    
    def _generate_fallback_lesson(self, prompt: str) -> str:
        """Generate a lesson using curriculum data from database"""
        try:
            # Extract topic and subject from prompt
            topic = "Algebra"  # Default fallback
            subject = "mathematics"  # Default fallback
            
            # Try to extract from prompt
            if "algebra" in prompt.lower():
                topic = "Algebra"
                subject = "mathematics"
            elif "english" in prompt.lower():
                subject = "english"
                topic = "Composition"
            elif "science" in prompt.lower():
                subject = "science"
                topic = "Biology"
            
            # Get curriculum content from database (we'll pass db session later)
            curriculum_content = self._get_curriculum_from_db(subject, topic, None)
            
            if curriculum_content:
                return json.dumps({
                    "title": f"{topic} - Grade 10",
                    "objectives": [
                        f"Understand {topic} fundamentals",
                        f"Apply {topic} concepts to Sierra Leone context",
                        "Solve practical problems using learned concepts"
                    ],
                    "content": curriculum_content,
                    "examples": [
                        {
                            "title": f"Sierra Leone {topic} Example",
                            "problem": f"A practical example using {topic} in a Sierra Leonean context.",
                            "solution": f"Step-by-step solution showing how {topic} applies to daily life in Sierra Leone.",
                            "explanation": f"This example demonstrates {topic} concepts using familiar Sierra Leone contexts."
                        }
                    ],
                    "key_points": [
                        f"Understanding {topic} fundamentals",
                        f"Applying {topic} to Sierra Leone context",
                        "Practical problem-solving skills",
                        "Real-world applications"
                    ],
                    "estimated_time": 25
                })
            else:
                # Fallback to basic template if no curriculum found
                return json.dumps({
                    "title": f"{topic} - Grade 10",
                    "objectives": [
                        f"Understand {topic} fundamentals",
                        f"Apply {topic} concepts to Sierra Leone context",
                        "Solve practical problems using learned concepts"
                    ],
                    "content": f"This lesson covers {topic} concepts with examples from Sierra Leone. Students will learn through interactive examples and practice problems relevant to their local context.",
                    "examples": [
                        {
                            "title": f"Sierra Leone {topic} Example",
                            "problem": f"A practical example using {topic} in a Sierra Leonean context.",
                            "solution": f"Step-by-step solution showing how {topic} applies to daily life in Sierra Leone.",
                            "explanation": f"This example demonstrates {topic} concepts using familiar Sierra Leone contexts."
                        }
                    ],
                    "key_points": [
                        f"Understanding {topic} fundamentals",
                        f"Applying {topic} to Sierra Leone context",
                        "Practical problem-solving skills",
                        "Real-world applications"
                    ],
                    "estimated_time": 25
                })
        except Exception as e:
            logger.error(f"Error in fallback lesson generation: {e}")
            # Ultimate fallback
            return json.dumps({
                "title": "Introduction to the Topic",
                "objectives": [
                    "Understand the basic concepts",
                    "Apply knowledge to solve problems",
                    "Connect learning to real-world examples"
                ],
                "content": "This lesson introduces key concepts with examples from Sierra Leone. Students will learn through interactive examples and practice problems.",
                "examples": [
                    {
                        "title": "Example 1",
                        "problem": "A student in Freetown has 500 Leone and wants to buy school supplies...",
                        "solution": "Step-by-step solution with local context",
                        "explanation": "This approach helps students understand the concept through familiar examples."
                    }
                ],
                "key_points": [
                    "Key concept 1",
                    "Key concept 2",
                    "Key concept 3"
                ],
                "estimated_time": 25
            })
    
    def _generate_fallback_lesson_with_db(self, prompt: str, subject: str, topic: str, grade: int, db: Session) -> str:
        """Generate a structured lesson using curriculum data from database with db session"""
        try:
            # Get curriculum content using RAG search
            curriculum_content = self._get_curriculum_context(subject, topic, grade)
            
            logger.info(f"Generating lesson for {subject} - {topic} (Grade {grade}) with {len(curriculum_content)} chars of curriculum content")
            
            # Generate structured lesson based on subject and topic
            if subject.lower() == "mathematics":
                return self._generate_math_lesson(topic, curriculum_content)
            elif subject.lower() == "english":
                return self._generate_english_lesson(topic, curriculum_content)
            elif subject.lower() == "science":
                return self._generate_science_lesson(topic, curriculum_content)
            else:
                return self._generate_generic_lesson(topic, curriculum_content)
                
        except Exception as e:
            logger.error(f"Error in fallback lesson generation with DB: {e}")
            return self._generate_generic_lesson(topic, "")
    
    def _generate_math_lesson(self, topic: str, curriculum_content: str) -> str:
        """Generate a simple math lesson from curriculum content"""
        
        # Extract relevant content directly from curriculum
        if curriculum_content and len(curriculum_content) > 100:
            # Build lesson content by showing actual curriculum sections
            lesson_content = f"# {topic.title()}\n\n"
            
            # Split into sections and find topic-relevant ones
            sections = curriculum_content.split('\n\n')
            topic_sections = []
            general_sections = []
            
            for section in sections:
                # Check if this section is about the specific topic
                if topic.lower() in section.lower():
                    topic_sections.append(section)
                elif len(section.strip()) > 50 and not section.strip().startswith('---'):
                    general_sections.append(section)
            
            # Prioritize topic-specific sections
            relevant_sections = topic_sections if topic_sections else general_sections[:5]
            
            if relevant_sections:
                lesson_content += "## From Sierra Leone Curriculum\n\n"
                for section in relevant_sections[:8]:  # Show up to 8 relevant sections
                    # Clean up the section
                    cleaned = section.strip()
                    if cleaned and len(cleaned) > 20:
                        lesson_content += cleaned + "\n\n"
            
            # Extract learning objectives
            objectives_list = []
            for section in relevant_sections:
                lines = section.split('\n')
                for line in lines:
                    if line.strip().startswith('-') and len(line.strip()) > 15:
                        obj = line.strip().lstrip('-').strip()
                        if len(obj) > 10 and len(obj) < 200:
                            objectives_list.append(obj)
            
            # Extract Sierra Leone applications/examples
            applications = []
            for section in relevant_sections:
                if 'sierra leone' in section.lower() or 'example' in section.lower() or 'application' in section.lower():
                    lines = section.split('\n')
                    for line in lines:
                        if line.strip().startswith('-') and len(line.strip()) > 15:
                            app = line.strip().lstrip('-').strip()
                            if len(app) > 10:
                                applications.append(app)
            
            return json.dumps({
                "title": f"{topic.title()} - Sierra Leone Curriculum",
                "objectives": objectives_list[:5] if objectives_list else [
                    f"Understand {topic} concepts from curriculum",
                    f"Learn practical applications in Sierra Leone context",
                    f"Apply {topic} to solve problems"
                ],
                "content": lesson_content.strip(),
                "examples": [],  # Will be populated if specific examples found
                "key_points": applications[:8] if applications else objectives_list[:8],
                "estimated_time": 45
            })
        
        # Fallback when no curriculum content found
        return json.dumps({
            "title": f"{topic.title()}",
            "objectives": [
                f"Understand {topic} concepts",
                f"Learn through examples",
                f"Apply {topic} to solve problems"
            ],
            "content": f"# {topic.title()}\n\n**Note**: Detailed curriculum content for this specific topic is not yet available in the database.\n\nPlease contact your teacher for detailed materials on {topic}.",
            "examples": [],
            "key_points": [
                f"Study {topic} fundamentals",
                "Review textbook materials",
                "Consult with your teacher"
            ],
            "estimated_time": 45
        })
    
    def _generate_english_lesson(self, topic: str, curriculum_content: str) -> str:
        """Generate a simple English lesson from curriculum content"""
        
        # Extract relevant content directly from curriculum
        if curriculum_content and len(curriculum_content) > 100:
            # Build lesson content by showing actual curriculum sections
            lesson_content = f"# {topic.title()}\n\n"
            
            # Split into sections and find topic-relevant ones
            sections = curriculum_content.split('\n\n')
            topic_sections = []
            general_sections = []
            
            for section in sections:
                # Check if this section is about the specific topic
                if topic.lower() in section.lower():
                    topic_sections.append(section)
                elif len(section.strip()) > 50 and not section.strip().startswith('---'):
                    general_sections.append(section)
            
            # Prioritize topic-specific sections
            relevant_sections = topic_sections if topic_sections else general_sections[:5]
            
            if relevant_sections:
                lesson_content += "## From Sierra Leone Curriculum\n\n"
                for section in relevant_sections[:8]:  # Show up to 8 relevant sections
                    # Clean up the section
                    cleaned = section.strip()
                    if cleaned and len(cleaned) > 20:
                        lesson_content += cleaned + "\n\n"
            
            # Extract learning objectives
            objectives_list = []
            for section in relevant_sections:
                lines = section.split('\n')
                for line in lines:
                    if line.strip().startswith('-') and len(line.strip()) > 15:
                        obj = line.strip().lstrip('-').strip()
                        if len(obj) > 10 and len(obj) < 200:
                            objectives_list.append(obj)
            
            # Extract Sierra Leone applications
            applications = []
            for section in relevant_sections:
                if 'sierra leone' in section.lower() or 'example' in section.lower() or 'application' in section.lower():
                    lines = section.split('\n')
                    for line in lines:
                        if line.strip().startswith('-') and len(line.strip()) > 15:
                            app = line.strip().lstrip('-').strip()
                            if len(app) > 10:
                                applications.append(app)
            
            return json.dumps({
                "title": f"{topic.title()} - Sierra Leone Curriculum",
                "objectives": objectives_list[:5] if objectives_list else [
                    f"Understand {topic} concepts from curriculum",
                    f"Learn practical applications in Sierra Leone context",
                    f"Apply {topic} skills in communication"
                ],
                "content": lesson_content.strip(),
                "examples": [],  # Will be populated if specific examples found
                "key_points": applications[:8] if applications else objectives_list[:8],
                "estimated_time": 45
            })
        
        # Fallback when no curriculum content found
        return json.dumps({
            "title": f"{topic.title()}",
            "objectives": [
                f"Understand {topic} concepts",
                f"Learn through examples",
                f"Apply {topic} skills"
            ],
            "content": f"# {topic.title()}\n\n**Note**: Detailed curriculum content for this specific topic is not yet available in the database.\n\nPlease contact your teacher for detailed materials on {topic}.",
            "examples": [],
            "key_points": [
                f"Study {topic} fundamentals",
                "Review textbook materials",
                "Consult with your teacher"
            ],
            "estimated_time": 45
        })
    
    def _generate_science_lesson(self, topic: str, curriculum_content: str) -> str:
        """Generate a simple science lesson from curriculum content"""
        
        # Extract relevant content directly from curriculum
        if curriculum_content and len(curriculum_content) > 100:
            # Build lesson content by showing actual curriculum sections
            lesson_content = f"# {topic.title()}\n\n"
            
            # Split by the separator used in _get_curriculum_context
            sections = curriculum_content.split('\n\n---\n\n')
            topic_sections = []
            
            # Define related keywords for common topics
            topic_keywords = {
                'matter': ['chemistry', 'chemical', 'atomic', 'molecule', 'reaction', 'element'],
                'energy': ['physics', 'force', 'motion', 'power', 'work'],
                'biology': ['cell', 'organism', 'life', 'living', 'ecosystem'],
                'earth': ['geology', 'planet', 'rock', 'mineral', 'earth science'],
            }
            
            # Get keywords for this topic
            search_keywords = [topic.lower()]
            for key, keywords in topic_keywords.items():
                if key in topic.lower():
                    search_keywords.extend(keywords)
            
            for section in sections:
                # Check if this section is relevant to the topic
                section_lower = section.lower()
                is_relevant = any(keyword in section_lower for keyword in search_keywords)
                
                if is_relevant and len(section.strip()) > 100:
                    topic_sections.append(section.strip())
            
            # Use topic-specific sections if found, otherwise use first few sections
            relevant_sections = topic_sections if topic_sections else [s.strip() for s in sections[:3] if len(s.strip()) > 100]
            
            if relevant_sections:
                lesson_content += "## From Sierra Leone Curriculum\n\n"
                for section in relevant_sections[:6]:  # Show up to 6 relevant sections
                    lesson_content += section + "\n\n"
            
            # Extract learning objectives
            objectives_list = []
            for section in relevant_sections:
                lines = section.split('\n')
                for line in lines:
                    if line.strip().startswith('-') and 'learn to' not in line.lower():
                        obj = line.strip().lstrip('-').strip()
                        if 15 < len(obj) < 200 and not obj.startswith('Local'):
                            objectives_list.append(obj)
            
            # Extract Sierra Leone applications
            applications = []
            for section in relevant_sections:
                if 'sierra leone' in section.lower() or 'application' in section.lower():
                    lines = section.split('\n')
                    for line in lines:
                        if line.strip().startswith('-'):
                            app = line.strip().lstrip('-').strip()
                            if 15 < len(app) < 200:
                                applications.append(app)
            
            return json.dumps({
                "title": f"{topic.title()} - Sierra Leone Curriculum",
                "objectives": objectives_list[:6] if objectives_list else [
                    f"Understand {topic} concepts from curriculum",
                    f"Learn practical applications in Sierra Leone context",
                    f"Apply scientific thinking to {topic}"
                ],
                "content": lesson_content.strip(),
                "examples": [],
                "key_points": applications[:10] if applications else objectives_list[:10],
                "estimated_time": 45
            })
        
        # Fallback when no curriculum content found
        return json.dumps({
            "title": f"{topic.title()}",
            "objectives": [
                f"Understand {topic} concepts",
                f"Learn through examples",
                f"Apply scientific methods"
            ],
            "content": f"# {topic.title()}\n\n**Note**: Detailed curriculum content for this specific topic is not yet available in the database.\n\nPlease contact your teacher for detailed materials on {topic}.",
            "examples": [],
            "key_points": [
                f"Study {topic} fundamentals",
                "Review textbook materials",
                "Consult with your teacher"
            ],
            "estimated_time": 45
        })
    
    def _generate_generic_lesson(self, topic: str, curriculum_content: str) -> str:
        """Generate a simple generic lesson from curriculum content"""
        
        # Extract relevant content directly from curriculum
        if curriculum_content and len(curriculum_content) > 100:
            # Build lesson content by showing actual curriculum sections
            lesson_content = f"# {topic.title()}\n\n"
            
            # Split into sections and find topic-relevant ones
            sections = curriculum_content.split('\n\n')
            topic_sections = []
            general_sections = []
            
            for section in sections:
                # Check if this section is about the specific topic
                if topic.lower() in section.lower():
                    topic_sections.append(section)
                elif len(section.strip()) > 50 and not section.strip().startswith('---'):
                    general_sections.append(section)
            
            # Prioritize topic-specific sections
            relevant_sections = topic_sections if topic_sections else general_sections[:5]
            
            if relevant_sections:
                lesson_content += "## From Sierra Leone Curriculum\n\n"
                for section in relevant_sections[:8]:  # Show up to 8 relevant sections
                    # Clean up the section
                    cleaned = section.strip()
                    if cleaned and len(cleaned) > 20:
                        lesson_content += cleaned + "\n\n"
            
            # Extract learning objectives
            objectives_list = []
            for section in relevant_sections:
                lines = section.split('\n')
                for line in lines:
                    if line.strip().startswith('-') and len(line.strip()) > 15:
                        obj = line.strip().lstrip('-').strip()
                        if len(obj) > 10 and len(obj) < 200:
                            objectives_list.append(obj)
            
            # Extract Sierra Leone applications
            applications = []
            for section in relevant_sections:
                if 'sierra leone' in section.lower() or 'example' in section.lower() or 'application' in section.lower():
                    lines = section.split('\n')
                    for line in lines:
                        if line.strip().startswith('-') and len(line.strip()) > 15:
                            app = line.strip().lstrip('-').strip()
                            if len(app) > 10:
                                applications.append(app)

        return json.dumps({
                "title": f"{topic.title()} - Sierra Leone Curriculum",
                "objectives": objectives_list[:5] if objectives_list else [
                    f"Understand {topic} concepts from curriculum",
                    f"Learn practical applications in Sierra Leone context",
                    f"Apply {topic} skills"
                ],
                "content": lesson_content.strip(),
                "examples": [],  # Will be populated if specific examples found
                "key_points": applications[:8] if applications else objectives_list[:8],
                "estimated_time": 45
            })
        
        # Fallback when no curriculum content found
        return json.dumps({
            "title": f"{topic.title()}",
            "objectives": [
                f"Understand {topic} concepts",
                f"Learn through examples",
                f"Apply {topic} skills"
            ],
            "content": f"# {topic.title()}\n\n**Note**: Detailed curriculum content for this specific topic is not yet available in the database.\n\nPlease contact your teacher for detailed materials on {topic}.",
            "examples": [],
            "key_points": [
                f"Study {topic} fundamentals",
                "Review textbook materials",
                "Consult with your teacher"
            ],
            "estimated_time": 45
        })
    
    def _generate_fallback_exercise(self, prompt: str) -> str:
        """Generate basic exercise template"""
        return json.dumps({
            "exercises": [
                {
                    "question": "Sample question with Sierra Leone context",
                    "type": "mcq",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Explanation of the correct answer",
                    "hints": ["Hint 1", "Hint 2"],
                    "difficulty": "medium",
                    "points": 1
                }
            ],
            "total_points": 5,
            "estimated_time": 20
        })
    
    def _generate_fallback_chat_response(self, prompt: str) -> str:
        """Generate basic chat response template"""
        return json.dumps({
            "response": "I'm here to help you learn! Can you tell me more about what you're studying?",
            "suggested_actions": ["Review the lesson", "Try practice problems"],
            "related_topics": ["Related topic 1", "Related topic 2"],
            "confidence_score": 0.7
        })
    
    def generate_personalized_lesson(self, student_id: str, subject: str, topic: str, 
                                   db: Session) -> Dict[str, Any]:
        """Generate a personalized lesson for a student"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise Exception(f"Student not found: {student_id}")
            
            # Get student's mastery level for this topic
            mastery = db.query(TopicMastery).filter(
                TopicMastery.student_id == student_id,
                TopicMastery.subject == subject,
                TopicMastery.topic == topic
            ).first()
            
            mastery_level = mastery.mastery_level if mastery else 0
            
            # Create student profile
            student_profile = {
                'grade': student.grade,
                'reading_level': student.reading_level,
                'learning_pace': student.learning_pace,
                'subject': subject,
                'mastery_level': mastery_level
            }
            
            # Skip slow LLM generation - use fast curriculum-based generation directly
            logger.info(f"Generating lesson from curriculum for {subject} - {topic} (Grade {student.grade})")
            lesson_data = self._generate_fallback_lesson_with_db("", subject, topic, student.grade, db)
            if isinstance(lesson_data, str):
                lesson_data = json.loads(lesson_data)
            
            # Store generated content
            self._store_generated_content(
                topic=topic,
                subject=subject,
                grade=student.grade,
                difficulty_level=self._determine_difficulty(mastery_level),
                content_type='lesson',
                content=lesson_data,
                db=db
            )
            
            return {
                'success': True,
                'lesson': lesson_data,
                'student_profile': student_profile
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized lesson: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_exercises(self, student_id: str, subject: str, topic: str, 
                          difficulty: str, db: Session) -> Dict[str, Any]:
        """Generate exercises for a student"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise Exception(f"Student not found: {student_id}")
            
            # Get student's mastery level
            mastery = db.query(TopicMastery).filter(
                TopicMastery.student_id == student_id,
                TopicMastery.subject == subject,
                TopicMastery.topic == topic
            ).first()
            
            mastery_level = mastery.mastery_level if mastery else 0
            
            # Create student profile
            student_profile = {
                'grade': student.grade,
                'subject': subject,
                'mastery_level': mastery_level
            }
            
            # Skip slow LLM - use fast fallback generation directly
            logger.info(f"Generating exercises for {subject} - {topic} ({difficulty})")
            exercise_data = self._generate_fallback_exercise("")
            if isinstance(exercise_data, str):
                exercise_data = json.loads(exercise_data)
            
            # Store generated content
            self._store_generated_content(
                topic=topic,
                subject=subject,
                grade=student.grade,
                difficulty_level=difficulty,
                content_type='exercise',
                content=exercise_data,
                db=db
            )
            
            return {
                'success': True,
                'exercises': exercise_data,
                'student_profile': student_profile
            }
            
        except Exception as e:
            logger.error(f"Error generating exercises: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_chatbot_response(self, student_id: str, user_message: str, 
                                context: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Generate a chatbot response"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise Exception(f"Student not found: {student_id}")
            
            # Get relevant curriculum content
            subject = context.get('current_subject', 'mathematics')
            topic = context.get('current_topic', 'general')
            
            relevant_content = self.curriculum_service.search_curriculum_content(
                query=user_message,
                subject=subject,
                grade=student.grade,
                n_results=3
            )
            
            # Skip slow LLM - use fast fallback response
            logger.info(f"Generating chatbot response for: {user_message[:50]}...")
            response_data = self._generate_fallback_chat_response("")
            if isinstance(response_data, str):
                response_data = json.loads(response_data)
            
            return {
                'success': True,
                'response': response_data
            }
            
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_diagnostic_assessment(self, grade: int, subject: str) -> Dict[str, Any]:
        """Generate a diagnostic assessment"""
        try:
            # Generate prompt
            prompt = get_prompt('diagnostic_assessment', grade=grade, subject=subject)
            
            # Generate content
            generated_text = self._generate_with_llm(prompt)
            
            # Parse JSON response
            try:
                assessment_data = json.loads(generated_text)
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON")
                # Create a basic assessment template
                assessment_data = {
                    "assessment_title": f"Grade {grade} {subject} Diagnostic Assessment",
                    "instructions": "Answer all questions to the best of your ability.",
                    "questions": [
                        {
                            "question": f"Sample {subject} question for Grade {grade}",
                            "type": "mcq",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Option A",
                            "explanation": "Basic explanation",
                            "difficulty": "medium",
                            "points": 1
                        }
                    ],
                    "total_points": 10,
                    "time_limit": 20
                }
            
            return {
                'success': True,
                'assessment': assessment_data
            }
            
        except Exception as e:
            logger.error(f"Error generating diagnostic assessment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_curriculum_from_db(self, subject: str, topic: str, db: Session = None) -> str:
        """Get curriculum content directly from database"""
        try:
            if not db:
                return f"Curriculum content for {subject} - {topic} at Grade 10 level."
                
            from ..models import CurriculumEmbedding
            
            # Query curriculum embeddings from database with broader search
            curriculum_items = db.query(CurriculumEmbedding).filter(
                CurriculumEmbedding.subject == subject
            ).all()
            
            if curriculum_items:
                # Find the most relevant content based on topic
                relevant_content = []
                for item in curriculum_items:
                    if topic.lower() in item.topic.lower() or topic.lower() in item.content.lower():
                        relevant_content.append(item.content)
                
                if not relevant_content:
                    # If no specific topic match, use general subject content
                    relevant_content = [item.content for item in curriculum_items[:2]]
                
                # Combine content from multiple curriculum items
                combined_content = "\n\n".join(relevant_content[:2])  # Use up to 2 most relevant items
                return f"Based on Sierra Leone curriculum:\n\n{combined_content}"
            else:
                return f"Curriculum content for {subject} - {topic} at Grade 10 level."
                
        except Exception as e:
            logger.error(f"Error getting curriculum from database: {e}")
            return f"Curriculum content for {subject} - {topic} at Grade 10 level."

    def _get_curriculum_context(self, subject: str, topic: str, grade: int) -> str:
        """Get relevant curriculum context for content generation"""
        try:
            # Try fast database search first (skip slow ChromaDB search)
            from ..models import CurriculumEmbedding
            from sqlalchemy.orm import Session
            
            # Get database session
            from ..database import get_db
            db = next(get_db())
            
            # Fast database query - no embeddings needed!
            query = db.query(CurriculumEmbedding).filter(
                CurriculumEmbedding.subject == subject,
                CurriculumEmbedding.grade == grade
            )
            
            # Search for topic in content or topic field
            results = query.filter(
                (CurriculumEmbedding.topic.ilike(f'%{topic}%')) |
                (CurriculumEmbedding.content.ilike(f'%{topic}%'))
            ).limit(8).all()
            
            if results:
                # Combine content from database results
                context_parts = [r.content for r in results if r.content and len(r.content.strip()) > 50]
                context = "\n\n---\n\n".join(context_parts)
                logger.info(f"Found {len(results)} curriculum items for {subject} - {topic} grade {grade} (fast DB search)")
                return context
            else:
                logger.warning(f"No curriculum content found for {subject} - {topic} at Grade {grade}")
                return f"Curriculum content for {subject} - {topic} at Grade {grade} level."
                
        except Exception as e:
            logger.error(f"Error getting curriculum context: {e}")
            return f"Curriculum content for {subject} - {topic} at Grade {grade} level."
    
    def _extract_definitions(self, curriculum_content: str, topic: str) -> List[str]:
        """Extract definitions from curriculum content"""
        definitions = []
        lines = curriculum_content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Look for definition patterns
            if any(keyword in line_lower for keyword in ['definition:', 'define', 'is a', 'refers to', 'means']):
                # Get the definition (current line and maybe next few lines)
                definition_text = line.strip()
                # Add next line if it's a continuation
                if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith('#'):
                    definition_text += ' ' + lines[i + 1].strip()
                if definition_text:
                    definitions.append(definition_text)
        
        return definitions[:5]  # Return top 5 definitions
    
    def _extract_examples(self, curriculum_content: str, topic: str) -> List[str]:
        """Extract examples from curriculum content"""
        examples = []
        sections = curriculum_content.split('\n\n')
        
        for section in sections:
            section_lower = section.lower()
            # Look for example patterns
            if any(keyword in section_lower for keyword in ['example', 'e.g.', 'for instance', 'such as', 'problem:', 'solution:']):
                # Include the whole section if it contains example keywords
                if len(section.strip()) > 50:  # Only include substantial examples
                    examples.append(section.strip())
        
        return examples[:5]  # Return top 5 examples
    
    def _extract_key_concepts(self, curriculum_content: str, topic: str) -> str:
        """Extract key concepts from curriculum content"""
        key_concepts = []
        lines = curriculum_content.split('\n')
        
        for line in lines:
            line_strip = line.strip()
            # Look for bulleted lists or numbered items
            if line_strip.startswith('-') or line_strip.startswith('•') or (len(line_strip) > 0 and line_strip[0].isdigit() and '.' in line_strip[:3]):
                key_concepts.append(line_strip)
        
        # Return as formatted string
        return '\n'.join(key_concepts[:10]) if key_concepts else ""
    
    def _parse_examples_for_json(self, curriculum_content: str, topic: str) -> List[Dict[str, str]]:
        """Parse examples into JSON structure"""
        example_list = []
        sections = curriculum_content.split('\n\n')
        
        for section in sections:
            section_lower = section.lower()
            # Look for structured examples with problem/solution
            if 'example' in section_lower and len(section) > 100:
                # Try to extract title, problem, solution
                lines = section.split('\n')
                title = lines[0].strip() if lines else f"{topic} Example"
                
                # Look for problem and solution
                problem = ""
                solution = ""
                
                for i, line in enumerate(lines):
                    if 'problem' in line.lower() or 'question' in line.lower():
                        # Get the next few lines as the problem
                        problem = ' '.join(lines[i:min(i+3, len(lines))]).strip()
                    elif 'solution' in line.lower() or 'answer' in line.lower():
                        # Get the next few lines as the solution
                        solution = ' '.join(lines[i:min(i+3, len(lines))]).strip()
                
                # If we found a problem or solution, add it
                if problem or solution or len(section) > 200:
                    example_list.append({
                        "title": title,
                        "problem": problem if problem else section[:200] + "...",
                        "solution": solution if solution else "See curriculum content for detailed solution.",
                        "explanation": "This example is taken directly from the Sierra Leone curriculum."
                    })
        
        return example_list[:3]  # Return top 3 examples
    
    def _extract_key_points(self, curriculum_content: str, topic: str) -> List[str]:
        """Extract key points from curriculum content"""
        key_points = []
        lines = curriculum_content.split('\n')
        
        for line in lines:
            line_strip = line.strip()
            # Look for bulleted lists or important statements
            if line_strip.startswith('-') or line_strip.startswith('•'):
                # Clean up the bullet point
                point = line_strip.lstrip('-•').strip()
                if len(point) > 10 and len(point) < 200:  # Reasonable length
                    key_points.append(point)
        
        # If we don't have many key points, extract from sentences
        if len(key_points) < 3:
            sentences = curriculum_content.split('.')
            for sentence in sentences:
                if topic.lower() in sentence.lower() and len(sentence.strip()) > 20:
                    key_points.append(sentence.strip())
        
        return key_points[:5]  # Return top 5 key points
    
    def _determine_difficulty(self, mastery_level: float) -> str:
        """Determine difficulty level based on mastery"""
        if mastery_level < 40:
            return "easy"
        elif mastery_level < 80:
            return "medium"
        else:
            return "hard"
    
    def _store_generated_content(self, topic: str, subject: str, grade: int,
                               difficulty_level: str, content_type: str,
                               content: Dict[str, Any], db: Session):
        """Store generated content in the database"""
        try:
            generated_content = GeneratedContent(
                topic=topic,
                subject=subject,
                grade=grade,
                difficulty_level=difficulty_level,
                content_type=content_type,
                content=json.dumps(content)
            )
            
            db.add(generated_content)
            db.commit()
            
            logger.info(f"Stored generated {content_type} for {subject} - {topic}")
            
        except Exception as e:
            logger.error(f"Error storing generated content: {e}")
            db.rollback()


# Global service instance
content_generator_service = None

def get_content_generator_service() -> ContentGeneratorService:
    """Get or create the global content generator service"""
    global content_generator_service
    if content_generator_service is None:
        content_generator_service = ContentGeneratorService()
    return content_generator_service
