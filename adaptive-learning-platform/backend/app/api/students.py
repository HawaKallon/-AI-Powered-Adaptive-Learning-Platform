"""
Student API endpoints
Handles student management, profiles, and learning progress
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from uuid import UUID

from ..database import get_db
from ..models import Student, TopicMastery, Assessment
from ..schemas import StudentUpdate, StudentResponse, TopicMasteryResponse, AssessmentResponse
from ..utils.auth import get_current_student, get_current_teacher
from ..services.adaptive_engine import get_adaptive_engine
from ..services.assessment_service import get_assessment_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=Dict[str, Any])
async def get_my_profile(current_student: Student = Depends(get_current_student)):
    """Get current student's profile"""
    try:
        return {
            "success": True,
            "student": StudentResponse.from_orm(current_student)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.put("/me", response_model=Dict[str, Any])
async def update_my_profile(
    student_update: StudentUpdate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Update current student's profile"""
    try:
        # Update student fields
        update_data = student_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_student, field, value)
        
        db.commit()
        db.refresh(current_student)
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "student": StudentResponse.from_orm(current_student)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/me/mastery", response_model=Dict[str, Any])
async def get_my_mastery(
    subject: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's topic mastery levels"""
    try:
        query = db.query(TopicMastery).filter(TopicMastery.student_id == current_student.id)
        
        if subject:
            query = query.filter(TopicMastery.subject == subject)
        
        masteries = query.all()
        
        return {
            "success": True,
            "mastery_levels": [TopicMasteryResponse.from_orm(m) for m in masteries]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mastery levels: {str(e)}"
        )


@router.get("/me/assessments", response_model=Dict[str, Any])
async def get_my_assessments(
    subject: str = None,
    topic: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's assessment history"""
    try:
        query = db.query(Assessment).filter(Assessment.student_id == current_student.id)
        
        if subject:
            query = query.filter(Assessment.subject == subject)
        if topic:
            query = query.filter(Assessment.topic == topic)
        
        assessments = query.order_by(Assessment.completed_at.desc()).all()
        
        return {
            "success": True,
            "assessments": [AssessmentResponse.from_orm(a) for a in assessments]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assessments: {str(e)}"
        )


@router.get("/me/learning-path", response_model=Dict[str, Any])
async def get_my_learning_path(
    subject: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's personalized learning path"""
    try:
        adaptive_engine = get_adaptive_engine()
        learning_path = adaptive_engine.get_learning_path(
            student_id=str(current_student.id),
            subject=subject,
            db=db
        )
        
        return {
            "success": True,
            "learning_path": learning_path
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning path: {str(e)}"
        )


@router.get("/me/performance", response_model=Dict[str, Any])
async def get_my_performance(
    subject: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get current student's performance analytics"""
    try:
        adaptive_engine = get_adaptive_engine()
        analytics = adaptive_engine.get_performance_analytics(
            student_id=str(current_student.id),
            subject=subject,
            db=db
        )
        
        return {
            "success": True,
            "performance_analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance analytics: {str(e)}"
        )


@router.get("/me/interventions", response_model=Dict[str, Any])
async def get_my_interventions(
    subject: str,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get recommended interventions for current student"""
    try:
        adaptive_engine = get_adaptive_engine()
        interventions = adaptive_engine.recommend_interventions(
            student_id=str(current_student.id),
            subject=subject,
            db=db
        )
        
        return {
            "success": True,
            "interventions": interventions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interventions: {str(e)}"
        )


# Teacher endpoints for managing students
@router.get("/", response_model=Dict[str, Any])
async def get_all_students(
    grade: int = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students (teacher only)"""
    try:
        query = db.query(Student)
        
        if grade:
            query = query.filter(Student.grade == grade)
        
        students = query.all()
        
        return {
            "success": True,
            "students": [StudentResponse.from_orm(s) for s in students]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get students: {str(e)}"
        )


@router.get("/{student_id}", response_model=Dict[str, Any])
async def get_student(
    student_id: UUID,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific student's details (teacher only)"""
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        return {
            "success": True,
            "student": StudentResponse.from_orm(student)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student: {str(e)}"
        )


@router.get("/{student_id}/mastery", response_model=Dict[str, Any])
async def get_student_mastery(
    student_id: UUID,
    subject: str = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a student's mastery levels (teacher only)"""
    try:
        query = db.query(TopicMastery).filter(TopicMastery.student_id == student_id)
        
        if subject:
            query = query.filter(TopicMastery.subject == subject)
        
        masteries = query.all()
        
        return {
            "success": True,
            "mastery_levels": [TopicMasteryResponse.from_orm(m) for m in masteries]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student mastery: {str(e)}"
        )


@router.get("/{student_id}/assessments", response_model=Dict[str, Any])
async def get_student_assessments(
    student_id: UUID,
    subject: str = None,
    topic: str = None,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a student's assessment history (teacher only)"""
    try:
        query = db.query(Assessment).filter(Assessment.student_id == student_id)
        
        if subject:
            query = query.filter(Assessment.subject == subject)
        if topic:
            query = query.filter(Assessment.topic == topic)
        
        assessments = query.order_by(Assessment.completed_at.desc()).all()
        
        return {
            "success": True,
            "assessments": [AssessmentResponse.from_orm(a) for a in assessments]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student assessments: {str(e)}"
        )


@router.get("/{student_id}/performance", response_model=Dict[str, Any])
async def get_student_performance(
    student_id: UUID,
    subject: str,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a student's performance analytics (teacher only)"""
    try:
        adaptive_engine = get_adaptive_engine()
        analytics = adaptive_engine.get_performance_analytics(
            student_id=str(student_id),
            subject=subject,
            db=db
        )
        
        return {
            "success": True,
            "performance_analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student performance: {str(e)}"
        )

