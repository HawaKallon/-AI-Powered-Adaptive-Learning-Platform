"""
Authentication API endpoints
Handles login, registration, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models import Student, Teacher
from ..schemas import StudentCreate, TeacherCreate, StudentResponse, TeacherResponse
from ..utils.auth import (
    get_password_hash, create_student_token, create_teacher_token,
    authenticate_teacher, authenticate_student, get_current_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register/student", response_model=Dict[str, Any])
async def register_student(student_data: StudentCreate, db: Session = Depends(get_db)):
    """Register a new student"""
    try:
        # Check if student already exists
        existing_student = db.query(Student).filter(Student.email == student_data.email).first()
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student with this email already exists"
            )
        
        # Create new student
        student = Student(
            name=student_data.name,
            email=student_data.email,
            password_hash=get_password_hash(student_data.password),
            grade=student_data.grade,
            reading_level=student_data.reading_level,
            learning_pace=student_data.learning_pace
        )
        
        db.add(student)
        db.commit()
        db.refresh(student)
        
        # Create token
        token = create_student_token(student)
        
        return {
            "success": True,
            "message": "Student registered successfully",
            "student": StudentResponse.from_orm(student),
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/register/teacher", response_model=Dict[str, Any])
async def register_teacher(teacher_data: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher"""
    try:
        # Check if teacher already exists
        existing_teacher = db.query(Teacher).filter(Teacher.email == teacher_data.email).first()
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher with this email already exists"
            )
        
        # Create new teacher
        teacher = Teacher(
            name=teacher_data.name,
            email=teacher_data.email,
            password_hash=get_password_hash(teacher_data.password),
            subjects=teacher_data.subjects
        )
        
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        # Create token
        token = create_teacher_token(teacher)
        
        return {
            "success": True,
            "message": "Teacher registered successfully",
            "teacher": TeacherResponse.from_orm(teacher),
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login/teacher", response_model=Dict[str, Any])
async def login_teacher(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login for teachers"""
    try:
        # Authenticate teacher
        teacher = authenticate_teacher(form_data.username, form_data.password, db)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token
        token = create_teacher_token(teacher)
        
        return {
            "success": True,
            "message": "Login successful",
            "teacher": TeacherResponse.from_orm(teacher),
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/login/student", response_model=Dict[str, Any])
async def login_student(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login for students using email and password"""
    try:
        # Authenticate student
        student = authenticate_student(form_data.username, form_data.password, db)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token
        token = create_student_token(student)
        
        return {
            "success": True,
            "message": "Login successful",
            "student": StudentResponse.from_orm(student),
            "access_token": token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    try:
        if isinstance(current_user, Student):
            return {
                "success": True,
                "user_type": "student",
                "user": StudentResponse.from_orm(current_user)
            }
        elif isinstance(current_user, Teacher):
            return {
                "success": True,
                "user_type": "teacher",
                "user": TeacherResponse.from_orm(current_user)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user type"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )


@router.post("/logout", response_model=Dict[str, Any])
async def logout():
    """Logout (client-side token removal)"""
    return {
        "success": True,
        "message": "Logout successful. Please remove the token from client storage."
    }

