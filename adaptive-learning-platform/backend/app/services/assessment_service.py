"""
Assessment Service
Handles exercise generation, grading, and assessment management
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ..models import Student, Assessment, TopicMastery, GeneratedContent
from ..schemas import Exercise, ExerciseQuestion, AssessmentCreate, AssessmentResponse
from ..services.content_generator import get_content_generator_service
from ..services.adaptive_engine import get_adaptive_engine

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service for managing assessments and exercises"""
    
    def __init__(self):
        self.content_generator = get_content_generator_service()
        self.adaptive_engine = get_adaptive_engine()
        
        # Assessment parameters
        self.grading_weights = {
            'mcq': 1.0,
            'short_answer': 1.5,
            'problem_solving': 2.0
        }
        
        self.time_limits = {
            'mcq': 60,  # seconds per question
            'short_answer': 120,
            'problem_solving': 300
        }
    
    def generate_exercise_set(self, student_id: str, subject: str, topic: str,
                            difficulty: str, question_count: int, db: Session) -> Dict[str, Any]:
        """Generate a set of exercises for a student"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return {'success': False, 'error': 'Student not found'}
            
            # Generate exercises using content generator
            exercise_data = self.content_generator.generate_exercises(
                student_id=student_id,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                db=db
            )
            
            if not exercise_data['success']:
                return exercise_data
            
            # Extract and format exercises
            exercises = exercise_data['exercises']['exercises']
            
            # Limit to requested number of questions
            if len(exercises) > question_count:
                exercises = exercises[:question_count]
            
            # Calculate total points and estimated time
            total_points = sum(ex.get('points', 1) for ex in exercises)
            estimated_time = sum(
                self.time_limits.get(ex.get('type', 'short_answer'), 120) 
                for ex in exercises
            )
            
            # Create exercise set
            exercise_set = {
                'student_id': student_id,
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'exercises': exercises,
                'total_points': total_points,
                'estimated_time': estimated_time,
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'exercise_set': exercise_set
            }
            
        except Exception as e:
            logger.error(f"Error generating exercise set: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def grade_assessment(self, student_id: str, subject: str, topic: str,
                        answers: List[Dict[str, Any]], time_taken: int,
                        db: Session) -> Dict[str, Any]:
        """Grade an assessment and update student progress"""
        try:
            # Get the original exercise set (in a real app, you'd store this)
            # For now, we'll generate it again to get the correct answers
            exercise_data = self.content_generator.generate_exercises(
                student_id=student_id,
                subject=subject,
                topic=topic,
                difficulty='medium',  # Default difficulty
                db=db
            )
            
            if not exercise_data['success']:
                return exercise_data
            
            original_exercises = exercise_data['exercises']['exercises']
            
            # Grade each answer
            graded_answers = []
            total_score = 0
            total_possible = 0
            errors = []
            
            for i, answer in enumerate(answers):
                if i >= len(original_exercises):
                    break
                
                original_exercise = original_exercises[i]
                student_answer = answer.get('answer', '').strip().lower()
                correct_answer = original_exercise.get('correct_answer', '').strip().lower()
                
                # Grade based on question type
                question_type = original_exercise.get('type', 'short_answer')
                is_correct = self._grade_answer(student_answer, correct_answer, question_type)
                
                # Calculate points
                points = original_exercise.get('points', 1)
                if is_correct:
                    earned_points = points
                else:
                    earned_points = 0
                    errors.append(f"Question {i+1}: {original_exercise.get('question', '')}")
                
                graded_answers.append({
                    'question_index': i,
                    'student_answer': answer.get('answer', ''),
                    'correct_answer': original_exercise.get('correct_answer', ''),
                    'is_correct': is_correct,
                    'points_earned': earned_points,
                    'points_possible': points,
                    'explanation': original_exercise.get('explanation', '')
                })
                
                total_score += earned_points
                total_possible += points
            
            # Calculate percentage score
            percentage_score = (total_score / total_possible * 100) if total_possible > 0 else 0
            
            # Determine attempt number
            attempt_number = self._get_attempt_number(student_id, subject, topic, db) + 1
            
            # Create assessment record
            assessment = Assessment(
                student_id=student_id,
                subject=subject,
                topic=topic,
                score=percentage_score,
                time_taken=time_taken,
                attempt_number=attempt_number,
                errors=json.dumps(errors)
            )
            
            db.add(assessment)
            db.flush()
            
            # Update mastery level
            mastery_update = self.adaptive_engine.update_mastery_level(
                student_id=student_id,
                subject=subject,
                topic=topic,
                assessment_score=percentage_score,
                time_taken=time_taken,
                attempt_number=attempt_number,
                db=db
            )
            
            db.commit()
            
            return {
                'success': True,
                'assessment_id': str(assessment.id),
                'score': percentage_score,
                'total_points': total_score,
                'possible_points': total_possible,
                'attempt_number': attempt_number,
                'graded_answers': graded_answers,
                'errors': errors,
                'mastery_update': mastery_update,
                'time_taken': time_taken
            }
            
        except Exception as e:
            logger.error(f"Error grading assessment: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _grade_answer(self, student_answer: str, correct_answer: str, question_type: str) -> bool:
        """Grade a single answer based on question type"""
        try:
            if question_type == 'mcq':
                # Multiple choice - exact match
                return student_answer == correct_answer
            elif question_type == 'short_answer':
                # Short answer - check if correct answer is contained in student answer
                return correct_answer in student_answer or student_answer in correct_answer
            elif question_type == 'problem_solving':
                # Problem solving - more flexible grading
                # Remove common words and check for key numbers/concepts
                student_clean = self._clean_answer(student_answer)
                correct_clean = self._clean_answer(correct_answer)
                return correct_clean in student_clean or student_clean in correct_clean
            else:
                # Default to exact match
                return student_answer == correct_answer
                
        except Exception as e:
            logger.error(f"Error grading answer: {e}")
            return False
    
    def _clean_answer(self, answer: str) -> str:
        """Clean answer for comparison"""
        # Remove common words and normalize
        common_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being']
        words = answer.lower().split()
        cleaned = [word for word in words if word not in common_words]
        return ' '.join(cleaned)
    
    def _get_attempt_number(self, student_id: str, subject: str, topic: str, db: Session) -> int:
        """Get the current attempt number for a topic"""
        try:
            last_assessment = db.query(Assessment).filter(
                and_(
                    Assessment.student_id == student_id,
                    Assessment.subject == subject,
                    Assessment.topic == topic
                )
            ).order_by(Assessment.completed_at.desc()).first()
            
            return last_assessment.attempt_number if last_assessment else 0
            
        except Exception as e:
            logger.error(f"Error getting attempt number: {e}")
            return 0
    
    def get_assessment_history(self, student_id: str, subject: str, 
                             topic: str, db: Session) -> List[Dict[str, Any]]:
        """Get assessment history for a student"""
        try:
            assessments = db.query(Assessment).filter(
                and_(
                    Assessment.student_id == student_id,
                    Assessment.subject == subject,
                    Assessment.topic == topic
                )
            ).order_by(Assessment.completed_at.desc()).all()
            
            return [
                {
                    'id': str(assessment.id),
                    'score': assessment.score,
                    'time_taken': assessment.time_taken,
                    'attempt_number': assessment.attempt_number,
                    'errors': json.loads(assessment.errors) if assessment.errors else [],
                    'completed_at': assessment.completed_at.isoformat()
                }
                for assessment in assessments
            ]
            
        except Exception as e:
            logger.error(f"Error getting assessment history: {e}")
            return []
    
    def create_diagnostic_assessment(self, grade: int, subject: str) -> Dict[str, Any]:
        """Create a diagnostic assessment for initial student evaluation"""
        try:
            # Generate diagnostic assessment
            assessment_data = self.content_generator.generate_diagnostic_assessment(
                grade=grade,
                subject=subject
            )
            
            if not assessment_data['success']:
                return assessment_data
            
            return {
                'success': True,
                'diagnostic_assessment': assessment_data['assessment']
            }
            
        except Exception as e:
            logger.error(f"Error creating diagnostic assessment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_diagnostic_results(self, student_id: str, subject: str,
                                 answers: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
        """Analyze diagnostic assessment results and set initial student profile"""
        try:
            # Grade the diagnostic
            grading_result = self.grade_assessment(
                student_id=student_id,
                subject=subject,
                topic='diagnostic',
                answers=answers,
                time_taken=0,  # Diagnostic time not tracked
                db=db
            )
            
            if not grading_result['success']:
                return grading_result
            
            # Analyze results to determine student profile
            overall_score = grading_result['score']
            
            # Determine reading level based on performance
            if overall_score >= 80:
                reading_level = 'advanced'
            elif overall_score >= 60:
                reading_level = 'intermediate'
            else:
                reading_level = 'basic'
            
            # Determine learning pace based on time and accuracy
            # This is simplified - in practice, you'd analyze time per question
            if overall_score >= 85:
                learning_pace = 'fast'
            elif overall_score >= 60:
                learning_pace = 'moderate'
            else:
                learning_pace = 'slow'
            
            # Update student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                student.reading_level = reading_level
                student.learning_pace = learning_pace
                db.commit()
            
            # Create initial topic mastery records
            self._create_initial_mastery_records(student_id, subject, overall_score, db)
            
            return {
                'success': True,
                'overall_score': overall_score,
                'reading_level': reading_level,
                'learning_pace': learning_pace,
                'recommendations': self._get_initial_recommendations(overall_score, reading_level, learning_pace)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing diagnostic results: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_initial_mastery_records(self, student_id: str, subject: str,
                                      initial_score: float, db: Session):
        """Create initial topic mastery records based on diagnostic results"""
        try:
            # Define initial topics for each subject
            topics = {
                'mathematics': ['arithmetic', 'algebra', 'geometry'],
                'english': ['grammar', 'reading_comprehension', 'writing'],
                'science': ['biology', 'chemistry', 'physics']
            }
            
            subject_topics = topics.get(subject, ['introduction'])
            
            for topic in subject_topics:
                # Set initial mastery based on diagnostic score
                initial_mastery = max(0, initial_score - 20)  # Slightly lower than diagnostic
                
                mastery = TopicMastery(
                    student_id=student_id,
                    subject=subject,
                    topic=topic,
                    mastery_level=initial_mastery,
                    total_attempts=0
                )
                
                db.add(mastery)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating initial mastery records: {e}")
            db.rollback()
    
    def _get_initial_recommendations(self, overall_score: float, reading_level: str,
                                   learning_pace: str) -> List[str]:
        """Get initial learning recommendations based on diagnostic results"""
        recommendations = []
        
        if overall_score < 50:
            recommendations.extend([
                "Focus on foundational concepts",
                "Take extra time to understand each topic",
                "Ask for help when needed"
            ])
        elif overall_score < 70:
            recommendations.extend([
                "Review basic concepts before advancing",
                "Practice regularly to build confidence",
                "Use the chatbot for additional support"
            ])
        else:
            recommendations.extend([
                "You're ready for more challenging content",
                "Try to complete exercises quickly and accurately",
                "Explore advanced topics when ready"
            ])
        
        # Add pace-specific recommendations
        if learning_pace == 'slow':
            recommendations.append("Don't rush - take time to understand each concept fully")
        elif learning_pace == 'fast':
            recommendations.append("Make sure to review and reinforce what you've learned")
        
        return recommendations
    
    def get_performance_summary(self, student_id: str, subject: str, db: Session) -> Dict[str, Any]:
        """Get a comprehensive performance summary for a student"""
        try:
            # Get all assessments for the subject
            assessments = db.query(Assessment).filter(
                and_(
                    Assessment.student_id == student_id,
                    Assessment.subject == subject
                )
            ).all()
            
            if not assessments:
                return {'error': 'No assessments found'}
            
            # Calculate summary statistics
            total_assessments = len(assessments)
            average_score = sum(a.score for a in assessments) / total_assessments
            best_score = max(a.score for a in assessments)
            worst_score = min(a.score for a in assessments)
            
            # Topic performance
            topic_scores = {}
            for assessment in assessments:
                topic = assessment.topic
                if topic not in topic_scores:
                    topic_scores[topic] = []
                topic_scores[topic].append(assessment.score)
            
            topic_averages = {
                topic: sum(scores) / len(scores)
                for topic, scores in topic_scores.items()
            }
            
            # Time analysis
            time_taken = [a.time_taken for a in assessments if a.time_taken]
            average_time = sum(time_taken) / len(time_taken) if time_taken else 0
            
            # Improvement trend
            recent_scores = [a.score for a in assessments[-5:]]  # Last 5 assessments
            if len(recent_scores) >= 2:
                improvement = recent_scores[-1] - recent_scores[0]
            else:
                improvement = 0
            
            return {
                'total_assessments': total_assessments,
                'average_score': average_score,
                'best_score': best_score,
                'worst_score': worst_score,
                'topic_performance': topic_averages,
                'average_time_per_assessment': average_time,
                'improvement_trend': improvement,
                'last_assessment': assessments[-1].completed_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}


# Global service instance
assessment_service = None

def get_assessment_service() -> AssessmentService:
    """Get or create the global assessment service"""
    global assessment_service
    if assessment_service is None:
        assessment_service = AssessmentService()
    return assessment_service
