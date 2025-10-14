"""
Assessments API endpoints
Handles exercise generation, assessment taking, and grading
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from uuid import UUID

from ..database import get_db
from ..models import Student, Assessment
from ..schemas import AssessmentCreate, AssessmentResponse, Exercise
from ..utils.auth import get_current_student, get_current_teacher
from ..services.assessment_service import get_assessment_service
from ..services.adaptive_engine import get_adaptive_engine

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/generate-exercise", response_model=Dict[str, Any])
async def generate_exercise_set(
    subject: str,
    topic: str,
    difficulty: str,
    question_count: int = 5,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate a set of exercises for the current student"""
    try:
        # Validate difficulty
        if difficulty not in ['easy', 'medium', 'hard']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Difficulty must be 'easy', 'medium', or 'hard'"
            )
        
        # Validate question count
        if not (1 <= question_count <= 20):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question count must be between 1 and 20"
            )
        
        assessment_service = get_assessment_service()
        
        exercise_data = assessment_service.generate_exercise_set(
            student_id=str(current_student.id),
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
            db=db
        )
        
        if not exercise_data['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=exercise_data.get('error', 'Failed to generate exercises')
            )
        
        return {
            "success": True,
            "exercise_set": exercise_data['exercise_set']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exercises: {str(e)}"
        )


@router.post("/submit", response_model=Dict[str, Any])
async def submit_assessment(
    subject: str,
    topic: str,
    answers: List[Dict[str, Any]],
    time_taken: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit an assessment for grading"""
    try:
        # Validate time taken
        if time_taken < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time taken must be non-negative"
            )
        
        # Validate answers
        if not answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answers cannot be empty"
            )
        
        assessment_service = get_assessment_service()
        
        grading_result = assessment_service.grade_assessment(
            student_id=str(current_student.id),
            subject=subject,
            topic=topic,
            answers=answers,
            time_taken=time_taken,
            db=db
        )
        
        if not grading_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=grading_result.get('error', 'Failed to grade assessment')
            )
        
        return {
            "success": True,
            "assessment_result": grading_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit assessment: {str(e)}"
        )


@router.get("/my-assessments", response_model=Dict[str, Any])
async def get_my_assessments(
    subject: str = None,
    topic: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's assessment history"""
    try:
        assessment_service = get_assessment_service()
        
        assessments = assessment_service.get_assessment_history(
            student_id=str(current_student.id),
            subject=subject or '',
            topic=topic or '',
            db=db
        )
        
        return {
            "success": True,
            "assessments": assessments
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessments: {str(e)}"
        )


@router.get("/my-performance", response_model=Dict[str, Any])
async def get_my_performance(
    subject: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's performance summary"""
    try:
        assessment_service = get_assessment_service()
        
        performance = assessment_service.get_performance_summary(
            student_id=str(current_student.id),
            subject=subject,
            db=db
        )
        
        if 'error' in performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=performance['error']
            )
        
        return {
            "success": True,
            "performance_summary": performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )


@router.post("/diagnostic", response_model=Dict[str, Any])
async def create_diagnostic_assessment(
    grade: int,
    subject: str,
    current_student: Student = Depends(get_current_student)
):
    """Create a diagnostic assessment for initial evaluation"""
    try:
        # Validate grade
        if not (7 <= grade <= 12):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Grade must be between 7 and 12"
            )
        
        # Validate subject
        if subject not in ['mathematics', 'english', 'science']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject must be 'mathematics', 'english', or 'science'"
            )
        
        assessment_service = get_assessment_service()
        
        diagnostic_data = assessment_service.create_diagnostic_assessment(
            grade=grade,
            subject=subject
        )
        
        if not diagnostic_data['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=diagnostic_data.get('error', 'Failed to create diagnostic assessment')
            )
        
        return {
            "success": True,
            "diagnostic_assessment": diagnostic_data['diagnostic_assessment']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagnostic assessment: {str(e)}"
        )


@router.post("/diagnostic/submit", response_model=Dict[str, Any])
async def submit_diagnostic_assessment(
    subject: str,
    answers: List[Dict[str, Any]],
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit diagnostic assessment results"""
    try:
        # Validate answers
        if not answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answers cannot be empty"
            )
        
        assessment_service = get_assessment_service()
        
        analysis_result = assessment_service.analyze_diagnostic_results(
            student_id=str(current_student.id),
            subject=subject,
            answers=answers,
            db=db
        )
        
        if not analysis_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis_result.get('error', 'Failed to analyze diagnostic results')
            )
        
        return {
            "success": True,
            "diagnostic_results": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit diagnostic assessment: {str(e)}"
        )


# Teacher endpoints for assessment management
@router.get("/student/{student_id}", response_model=Dict[str, Any])
async def get_student_assessments(
    student_id: UUID,
    subject: str = None,
    topic: str = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a student's assessment history (teacher only)"""
    try:
        assessment_service = get_assessment_service()
        
        assessments = assessment_service.get_assessment_history(
            student_id=str(student_id),
            subject=subject or '',
            topic=topic or '',
            db=db
        )
        
        return {
            "success": True,
            "assessments": assessments
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student assessments: {str(e)}"
        )


@router.get("/student/{student_id}/performance", response_model=Dict[str, Any])
async def get_student_performance(
    student_id: UUID,
    subject: str,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a student's performance summary (teacher only)"""
    try:
        assessment_service = get_assessment_service()
        
        performance = assessment_service.get_performance_summary(
            student_id=str(student_id),
            subject=subject,
            db=db
        )
        
        if 'error' in performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=performance['error']
            )
        
        return {
            "success": True,
            "performance_summary": performance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student performance: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_assessment_analytics(
    subject: str = None,
    grade: int = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get assessment analytics (teacher only)"""
    try:
        query = db.query(Assessment)
        
        if subject:
            query = query.filter(Assessment.subject == subject)
        
        # Filter by grade through student relationship
        if grade:
            from ..models import Student
            query = query.join(Student).filter(Student.grade == grade)
        
        assessments = query.all()
        
        if not assessments:
            return {
                "success": True,
                "analytics": {
                    "total_assessments": 0,
                    "average_score": 0,
                    "subject_distribution": {},
                    "grade_distribution": {},
                    "topic_performance": {}
                }
            }
        
        # Calculate analytics
        total_assessments = len(assessments)
        average_score = sum(a.score for a in assessments) / total_assessments
        
        # Subject distribution
        subject_distribution = {}
        for assessment in assessments:
            subject = assessment.subject
            subject_distribution[subject] = subject_distribution.get(subject, 0) + 1
        
        # Grade distribution
        grade_distribution = {}
        for assessment in assessments:
            # Get student grade
            student = db.query(Student).filter(Student.id == assessment.student_id).first()
            if student:
                grade = student.grade
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
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
        
        return {
            "success": True,
            "analytics": {
                "total_assessments": total_assessments,
                "average_score": average_score,
                "subject_distribution": subject_distribution,
                "grade_distribution": grade_distribution,
                "topic_performance": topic_averages
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessment analytics: {str(e)}"
        )


