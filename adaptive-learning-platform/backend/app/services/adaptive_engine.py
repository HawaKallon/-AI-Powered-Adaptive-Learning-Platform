"""
Adaptive Learning Engine
Handles mastery tracking, difficulty adjustment, and personalized learning paths
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models import Student, TopicMastery, Assessment, GeneratedContent
from ..schemas import LearningPath, PersonalizedLesson
from ..services.content_generator import get_content_generator_service

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """Engine for adaptive learning logic and mastery tracking"""
    
    def __init__(self):
        self.content_generator = get_content_generator_service()
        
        # Adaptive learning parameters
        self.mastery_thresholds = {
            'remediation': 40,  # Below this, provide easier content
            'practice': 60,     # Between remediation and advancement
            'advancement': 85   # Above this, can advance to next topic
        }
        
        self.attempt_limits = {
            'max_attempts_before_remediation': 3,
            'max_attempts_per_session': 5
        }
    
    def update_mastery_level(self, student_id: str, subject: str, topic: str,
                           assessment_score: float, time_taken: int,
                           attempt_number: int, db: Session) -> Dict[str, Any]:
        """Update student's mastery level based on assessment results"""
        try:
            # Get or create topic mastery record
            mastery = db.query(TopicMastery).filter(
                and_(
                    TopicMastery.student_id == student_id,
                    TopicMastery.subject == subject,
                    TopicMastery.topic == topic
                )
            ).first()
            
            if not mastery:
                mastery = TopicMastery(
                    student_id=student_id,
                    subject=subject,
                    topic=topic,
                    mastery_level=0.0,
                    total_attempts=0
                )
                db.add(mastery)
            
            # Calculate new mastery level using weighted average
            old_mastery = mastery.mastery_level
            new_mastery = self._calculate_mastery_level(
                old_mastery, assessment_score, attempt_number, time_taken
            )
            
            # Update mastery record
            mastery.mastery_level = new_mastery
            mastery.total_attempts += 1
            mastery.last_practiced = datetime.now()
            
            db.commit()
            
            # Determine next action
            next_action = self._determine_next_action(
                new_mastery, attempt_number, assessment_score
            )
            
            logger.info(f"Updated mastery for {student_id}: {topic} = {new_mastery:.1f}%")
            
            return {
                'success': True,
                'old_mastery': old_mastery,
                'new_mastery': new_mastery,
                'next_action': next_action,
                'mastery_change': new_mastery - old_mastery
            }
            
        except Exception as e:
            logger.error(f"Error updating mastery level: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_mastery_level(self, old_mastery: float, score: float,
                               attempt_number: int, time_taken: int) -> float:
        """Calculate new mastery level using adaptive algorithm"""
        
        # Base weight for the new score
        base_weight = 0.3
        
        # Adjust weight based on attempt number (later attempts have less impact)
        attempt_weight = max(0.1, base_weight / attempt_number)
        
        # Adjust weight based on time taken (faster completion = higher confidence)
        time_weight = 1.0
        if time_taken > 0:
            # Assume optimal time is 2 minutes per question
            optimal_time = 120  # seconds
            if time_taken < optimal_time:
                time_weight = 1.2  # Bonus for fast completion
            elif time_taken > optimal_time * 2:
                time_weight = 0.8  # Penalty for slow completion
        
        # Calculate weighted score
        weighted_score = score * attempt_weight * time_weight
        
        # Update mastery using exponential moving average
        alpha = 0.3  # Learning rate
        new_mastery = (1 - alpha) * old_mastery + alpha * weighted_score
        
        # Ensure mastery stays within bounds
        return max(0.0, min(100.0, new_mastery))
    
    def _determine_next_action(self, mastery_level: float, attempt_number: int,
                             score: float) -> Dict[str, Any]:
        """Determine the next learning action based on performance"""
        
        if mastery_level < self.mastery_thresholds['remediation'] or attempt_number >= self.attempt_limits['max_attempts_before_remediation']:
            return {
                'action': 'remediation',
                'difficulty': 'easier',
                'reason': 'Low mastery level or too many attempts',
                'suggested_content': 'Review basic concepts and provide scaffolded practice'
            }
        elif mastery_level < self.mastery_thresholds['practice']:
            return {
                'action': 'practice',
                'difficulty': 'same',
                'reason': 'Need more practice at current level',
                'suggested_content': 'Continue practice with similar difficulty'
            }
        elif mastery_level >= self.mastery_thresholds['advancement'] and attempt_number == 1:
            return {
                'action': 'advance',
                'difficulty': 'harder',
                'reason': 'High mastery with first attempt',
                'suggested_content': 'Move to next topic or increase difficulty'
            }
        else:
            return {
                'action': 'continue',
                'difficulty': 'same',
                'reason': 'Steady progress, continue current path',
                'suggested_content': 'Continue with current difficulty level'
            }
    
    def get_learning_path(self, student_id: str, subject: str, db: Session) -> LearningPath:
        """Generate a personalized learning path for a student"""
        try:
            # Get student profile
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise Exception(f"Student not found: {student_id}")
            
            # Get all topic masteries for the subject
            masteries = db.query(TopicMastery).filter(
                and_(
                    TopicMastery.student_id == student_id,
                    TopicMastery.subject == subject
                )
            ).all()
            
            # Determine current topic and progress
            current_topic = self._determine_current_topic(masteries)
            overall_progress = self._calculate_overall_progress(masteries)
            
            # Get next lessons
            next_lessons = self._get_next_lessons(masteries, subject, student.grade)
            
            # Get recommended practice
            recommended_practice = self._get_recommended_practice(masteries)
            
            # Estimate completion time
            estimated_completion = self._estimate_completion_time(masteries, student.learning_pace)
            
            return LearningPath(
                student_id=student_id,
                subject=subject,
                current_topic=current_topic,
                progress=overall_progress,
                next_lessons=next_lessons,
                recommended_practice=recommended_practice,
                estimated_completion=estimated_completion
            )
            
        except Exception as e:
            logger.error(f"Error generating learning path: {e}")
            raise
    
    def _determine_current_topic(self, masteries: List[TopicMastery]) -> str:
        """Determine the current topic the student should focus on"""
        if not masteries:
            return "Introduction"
        
        # Find the topic with the lowest mastery that's not at 0
        incomplete_topics = [m for m in masteries if m.mastery_level < 85 and m.mastery_level > 0]
        
        if incomplete_topics:
            # Return the topic with lowest mastery
            return min(incomplete_topics, key=lambda x: x.mastery_level).topic
        
        # If all topics are mastered, find the one with 0 mastery (not started)
        unstarted_topics = [m for m in masteries if m.mastery_level == 0]
        if unstarted_topics:
            return unstarted_topics[0].topic
        
        # If everything is mastered, return the last practiced topic
        return max(masteries, key=lambda x: x.last_practiced).topic
    
    def _calculate_overall_progress(self, masteries: List[TopicMastery]) -> float:
        """Calculate overall progress across all topics"""
        if not masteries:
            return 0.0
        
        total_mastery = sum(m.mastery_level for m in masteries)
        return total_mastery / len(masteries)
    
    def _get_next_lessons(self, masteries: List[TopicMastery], subject: str, grade: int) -> List[str]:
        """Get the next lessons the student should take"""
        # This is a simplified version - in practice, you'd have a curriculum structure
        topics = [m.topic for m in masteries if m.mastery_level < 85]
        return topics[:3]  # Return next 3 topics
    
    def _get_recommended_practice(self, masteries: List[TopicMastery]) -> List[str]:
        """Get topics that need more practice"""
        practice_topics = []
        
        for mastery in masteries:
            if 40 <= mastery.mastery_level < 85:
                practice_topics.append(mastery.topic)
        
        return practice_topics
    
    def _estimate_completion_time(self, masteries: List[TopicMastery], learning_pace: str) -> Optional[datetime]:
        """Estimate when the student will complete the subject"""
        if not masteries:
            return None
        
        # Calculate remaining work
        remaining_topics = [m for m in masteries if m.mastery_level < 85]
        if not remaining_topics:
            return datetime.now()
        
        # Estimate time based on learning pace
        pace_multipliers = {
            'slow': 1.5,
            'moderate': 1.0,
            'fast': 0.7
        }
        
        base_time_per_topic = 2  # hours
        multiplier = pace_multipliers.get(learning_pace, 1.0)
        
        total_hours = len(remaining_topics) * base_time_per_topic * multiplier
        
        return datetime.now() + timedelta(hours=total_hours)
    
    def get_struggling_students(self, subject: str, db: Session, 
                              threshold: float = 40.0) -> List[Dict[str, Any]]:
        """Get students who are struggling in a subject"""
        try:
            # Find students with low mastery levels
            struggling_masteries = db.query(TopicMastery).filter(
                and_(
                    TopicMastery.subject == subject,
                    TopicMastery.mastery_level < threshold,
                    TopicMastery.total_attempts >= 2
                )
            ).all()
            
            # Group by student and get additional info
            struggling_students = []
            for mastery in struggling_masteries:
                student = db.query(Student).filter(Student.id == mastery.student_id).first()
                if student:
                    struggling_students.append({
                        'student_id': str(student.id),
                        'student_name': student.name,
                        'grade': student.grade,
                        'topic': mastery.topic,
                        'mastery_level': mastery.mastery_level,
                        'total_attempts': mastery.total_attempts,
                        'last_practiced': mastery.last_practiced,
                        'learning_pace': student.learning_pace,
                        'reading_level': student.reading_level
                    })
            
            return struggling_students
            
        except Exception as e:
            logger.error(f"Error getting struggling students: {e}")
            return []
    
    def get_performance_analytics(self, student_id: str, subject: str, 
                                db: Session) -> Dict[str, Any]:
        """Get detailed performance analytics for a student"""
        try:
            # Get all assessments for the student in this subject
            assessments = db.query(Assessment).filter(
                and_(
                    Assessment.student_id == student_id,
                    Assessment.subject == subject
                )
            ).order_by(Assessment.completed_at.desc()).all()
            
            if not assessments:
                return {'error': 'No assessments found'}
            
            # Calculate analytics
            recent_scores = [a.score for a in assessments[:10]]  # Last 10 assessments
            average_score = sum(recent_scores) / len(recent_scores)
            
            # Time analysis
            time_taken = [a.time_taken for a in assessments if a.time_taken]
            average_time = sum(time_taken) / len(time_taken) if time_taken else 0
            
            # Topic performance
            topic_performance = {}
            for assessment in assessments:
                topic = assessment.topic
                if topic not in topic_performance:
                    topic_performance[topic] = []
                topic_performance[topic].append(assessment.score)
            
            # Calculate topic averages
            topic_averages = {
                topic: sum(scores) / len(scores) 
                for topic, scores in topic_performance.items()
            }
            
            # Learning velocity (improvement over time)
            if len(recent_scores) >= 5:
                recent_avg = sum(recent_scores[:5]) / 5
                older_avg = sum(recent_scores[5:]) / len(recent_scores[5:])
                learning_velocity = recent_avg - older_avg
            else:
                learning_velocity = 0
            
            return {
                'total_assessments': len(assessments),
                'average_score': average_score,
                'average_time_per_assessment': average_time,
                'recent_scores': recent_scores,
                'topic_performance': topic_averages,
                'learning_velocity': learning_velocity,
                'last_assessment': assessments[0].completed_at.isoformat() if assessments else None
            }
            
        except Exception as e:
            logger.error(f"Error getting performance analytics: {e}")
            return {'error': str(e)}
    
    def recommend_interventions(self, student_id: str, subject: str, 
                              db: Session) -> List[Dict[str, Any]]:
        """Recommend interventions for struggling students"""
        try:
            analytics = self.get_performance_analytics(student_id, subject, db)
            
            if 'error' in analytics:
                return []
            
            interventions = []
            
            # Low average score intervention
            if analytics['average_score'] < 50:
                interventions.append({
                    'type': 'remediation',
                    'priority': 'high',
                    'description': 'Student needs foundational support',
                    'actions': [
                        'Provide easier content with more scaffolding',
                        'Focus on basic concepts before advancing',
                        'Increase practice time with immediate feedback'
                    ]
                })
            
            # Slow learning velocity intervention
            if analytics['learning_velocity'] < -10:
                interventions.append({
                    'type': 'pace_adjustment',
                    'priority': 'medium',
                    'description': 'Student is falling behind expected pace',
                    'actions': [
                        'Reduce content complexity',
                        'Provide more practice opportunities',
                        'Consider one-on-one support'
                    ]
                })
            
            # High time per assessment intervention
            if analytics['average_time_per_assessment'] > 600:  # 10 minutes
                interventions.append({
                    'type': 'time_management',
                    'priority': 'medium',
                    'description': 'Student takes too long on assessments',
                    'actions': [
                        'Provide time management strategies',
                        'Break down complex problems',
                        'Offer timed practice sessions'
                    ]
                })
            
            return interventions
            
        except Exception as e:
            logger.error(f"Error recommending interventions: {e}")
            return []


# Global service instance
adaptive_engine = None

def get_adaptive_engine() -> AdaptiveLearningEngine:
    """Get or create the global adaptive learning engine"""
    global adaptive_engine
    if adaptive_engine is None:
        adaptive_engine = AdaptiveLearningEngine()
    return adaptive_engine
