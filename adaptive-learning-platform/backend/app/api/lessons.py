"""
Lessons API endpoints
Handles lesson generation, delivery, and content management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel

from ..database import get_db
from ..models import Student, GeneratedContent
from ..schemas import PersonalizedLesson, GeneratedContentResponse
from ..utils.auth import get_current_student, get_current_teacher
from ..services.content_generator import get_content_generator_service
from ..services.adaptive_engine import get_adaptive_engine
from ..services.curriculum_ingestion import get_curriculum_ingestion_service

router = APIRouter(prefix="/lessons", tags=["lessons"])


class LessonRequest(BaseModel):
    subject: str
    topic: str
    specific_focus: Optional[str] = None
    grade: int


@router.post("/request", response_model=Dict[str, Any])
async def request_lesson(
    lesson_request: LessonRequest,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate a personalized lesson based on student request"""
    try:
        content_generator = get_content_generator_service()
        
        # Generate lesson using the content generator
        lesson_data = content_generator.generate_personalized_lesson(
            student_id=str(current_student.id),
            subject=lesson_request.subject,
            topic=lesson_request.topic,
            db=db
        )
        
        if not lesson_data['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=lesson_data.get('error', 'Failed to generate lesson')
            )
        
        # Format the response for the frontend
        lesson = lesson_data['lesson']
        
        # Use the generated content directly, not fallbacks
        return {
            "success": True,
            "lesson": {
                "id": lesson.get('id', 'lesson-1'),
                "title": lesson.get('title', f"{lesson_request.topic} - Grade {lesson_request.grade}"),
                "subject": lesson_request.subject,
                "content": lesson.get('content'),  # Don't use fallback - show actual generated content
                "objectives": lesson.get('objectives', []),
                "examples": lesson.get('examples', []),
                "keyPoints": lesson.get('key_points', []),
                "estimatedTime": lesson.get('estimated_time', 45)
            },
            "student_profile": lesson_data.get('student_profile', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lesson: {str(e)}"
        )


@router.post("/generate", response_model=Dict[str, Any])
async def generate_personalized_lesson(
    subject: str,
    topic: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate a personalized lesson for the current student"""
    try:
        content_generator = get_content_generator_service()
        
        lesson_data = content_generator.generate_personalized_lesson(
            student_id=str(current_student.id),
            subject=subject,
            topic=topic,
            db=db
        )
        
        if not lesson_data['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=lesson_data.get('error', 'Failed to generate lesson')
            )
        
        return {
            "success": True,
            "lesson": lesson_data['lesson'],
            "student_profile": lesson_data['student_profile']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lesson: {str(e)}"
        )


@router.get("/content/{content_id}", response_model=Dict[str, Any])
async def get_lesson_content(
    content_id: UUID,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get a specific lesson content by ID"""
    try:
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson content not found"
            )
        
        # Update usage count
        content.usage_count += 1
        db.commit()
        
        return {
            "success": True,
            "content": GeneratedContentResponse.from_orm(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lesson content: {str(e)}"
        )


@router.get("/recommended", response_model=Dict[str, Any])
async def get_recommended_lessons(
    subject: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get recommended lessons for the current student"""
    try:
        adaptive_engine = get_adaptive_engine()
        learning_path = adaptive_engine.get_learning_path(
            student_id=str(current_student.id),
            subject=subject,
            db=db
        )
        
        # Get recommended practice topics
        recommended_practice = learning_path.recommended_practice
        
        # Generate lesson recommendations
        recommendations = []
        for topic in recommended_practice[:3]:  # Top 3 recommendations
            recommendations.append({
                "topic": topic,
                "reason": "Based on your current progress",
                "priority": "high" if topic in recommended_practice[:1] else "medium"
            })
        
        return {
            "success": True,
            "recommended_lessons": recommendations,
            "current_topic": learning_path.current_topic,
            "overall_progress": learning_path.progress
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommended lessons: {str(e)}"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_lesson_history(
    subject: str = None,
    topic: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get lesson history for the current student"""
    try:
        query = db.query(GeneratedContent).filter(
            GeneratedContent.content_type == 'lesson'
        )
        
        if subject:
            query = query.filter(GeneratedContent.subject == subject)
        if topic:
            query = query.filter(GeneratedContent.topic == topic)
        
        # Filter by student's grade
        query = query.filter(GeneratedContent.grade == current_student.grade)
        
        lessons = query.order_by(GeneratedContent.created_at.desc()).limit(20).all()
        
        return {
            "success": True,
            "lessons": [GeneratedContentResponse.from_orm(lesson) for lesson in lessons]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lesson history: {str(e)}"
        )


@router.post("/feedback", response_model=Dict[str, Any])
async def submit_lesson_feedback(
    content_id: UUID,
    rating: int,
    feedback: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit feedback for a lesson"""
    try:
        # Validate rating
        if not (1 <= rating <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        
        # Get the content
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson content not found"
            )
        
        # In a real implementation, you'd store feedback in a separate table
        # For now, we'll just return success
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "content_id": str(content_id),
            "rating": rating,
            "feedback": feedback
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


# Teacher endpoints for lesson management
@router.get("/content/all", response_model=Dict[str, Any])
async def get_all_lesson_content(
    subject: str = None,
    grade: int = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all lesson content (teacher only)"""
    try:
        query = db.query(GeneratedContent).filter(
            GeneratedContent.content_type == 'lesson'
        )
        
        if subject:
            query = query.filter(GeneratedContent.subject == subject)
        if grade:
            query = query.filter(GeneratedContent.grade == grade)
        
        lessons = query.order_by(GeneratedContent.created_at.desc()).all()
        
        return {
            "success": True,
            "lessons": [GeneratedContentResponse.from_orm(lesson) for lesson in lessons]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lesson content: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_lesson_analytics(
    subject: str = None,
    grade: int = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get lesson usage analytics (teacher only)"""
    try:
        query = db.query(GeneratedContent).filter(
            GeneratedContent.content_type == 'lesson'
        )
        
        if subject:
            query = query.filter(GeneratedContent.subject == subject)
        if grade:
            query = query.filter(GeneratedContent.grade == grade)
        
        lessons = query.all()
        
        # Calculate analytics
        total_lessons = len(lessons)
        total_usage = sum(lesson.usage_count for lesson in lessons)
        avg_usage = total_usage / total_lessons if total_lessons > 0 else 0
        
        # Group by subject
        subject_stats = {}
        for lesson in lessons:
            subject = lesson.subject
            if subject not in subject_stats:
                subject_stats[subject] = {
                    'count': 0,
                    'total_usage': 0,
                    'avg_usage': 0
                }
            subject_stats[subject]['count'] += 1
            subject_stats[subject]['total_usage'] += lesson.usage_count
        
        # Calculate averages
        for subject in subject_stats:
            stats = subject_stats[subject]
            stats['avg_usage'] = stats['total_usage'] / stats['count'] if stats['count'] > 0 else 0
        
        # Most popular lessons
        popular_lessons = sorted(lessons, key=lambda x: x.usage_count, reverse=True)[:5]
        
        return {
            "success": True,
            "analytics": {
                "total_lessons": total_lessons,
                "total_usage": total_usage,
                "average_usage": avg_usage,
                "subject_statistics": subject_stats,
                "most_popular_lessons": [
                    {
                        "id": str(lesson.id),
                        "topic": lesson.topic,
                        "subject": lesson.subject,
                        "grade": lesson.grade,
                        "usage_count": lesson.usage_count
                    }
                    for lesson in popular_lessons
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lesson analytics: {str(e)}"
        )


@router.delete("/content/{content_id}", response_model=Dict[str, Any])
async def delete_lesson_content(
    content_id: UUID,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete lesson content (teacher only)"""
    try:
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson content not found"
            )
        
        db.delete(content)
        db.commit()
        
        return {
            "success": True,
            "message": "Lesson content deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson content: {str(e)}"
        )


# Curriculum Topics and Subtopics endpoints
@router.get("/curriculum/topics", response_model=Dict[str, Any])
async def get_curriculum_topics(
    subject: str,
    grade: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get topics and subtopics from curriculum using RAG"""
    try:
        curriculum_service = get_curriculum_ingestion_service()
        
        result = curriculum_service.get_curriculum_topics_and_subtopics(
            subject=subject,
            grade=grade,
            db=db
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to retrieve curriculum topics')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get curriculum topics: {str(e)}"
        )


@router.get("/curriculum/topic/{topic}", response_model=Dict[str, Any])
async def get_topic_details(
    topic: str,
    subject: str,
    grade: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific topic using RAG"""
    try:
        curriculum_service = get_curriculum_ingestion_service()
        
        result = curriculum_service.get_topic_details(
            subject=subject,
            topic=topic,
            grade=grade,
            db=db
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', f'Topic "{topic}" not found')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topic details: {str(e)}"
        )


@router.get("/curriculum/search", response_model=Dict[str, Any])
async def search_curriculum_content(
    query: str,
    subject: str = None,
    grade: int = None,
    n_results: int = 5,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Search curriculum content using RAG"""
    try:
        curriculum_service = get_curriculum_ingestion_service()
        
        # Use student's grade if not specified
        if grade is None:
            grade = current_student.grade
        
        results = curriculum_service.search_curriculum_content(
            query=query,
            subject=subject,
            grade=grade,
            n_results=n_results
        )
        
        return {
            "success": True,
            "query": query,
            "subject": subject,
            "grade": grade,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search curriculum: {str(e)}"
        )

