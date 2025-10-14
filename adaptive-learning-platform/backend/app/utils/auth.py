"""
Authentication utilities: password hashing, JWT tokens, etc.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.student import Student, Teacher

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hash a plain text password
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    password = password[:72]
    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    """
    Alias for hash_password for compatibility
    """
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash
    """
    # Truncate password to 72 bytes for bcrypt compatibility
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing user data (typically user_id and role)
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current authenticated user (student or teacher)
    
    Usage in endpoints:
        @app.get("/protected")
        async def protected_route(current_user = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    user_type: str = payload.get("type")  # "student" or "teacher"
    
    if user_id is None or user_type is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Fetch user from database
    if user_type == "student":
        user = db.query(Student).filter(Student.id == user_id).first()
    elif user_type == "teacher":
        user = db.query(Teacher).filter(Teacher.id == user_id).first()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type")
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user


async def get_current_student(current_user = Depends(get_current_user)) -> Student:
    """
    Dependency to ensure current user is a student
    """
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this resource"
        )
    return current_user


async def get_current_teacher(current_user = Depends(get_current_user)) -> Teacher:
    """
    Dependency to ensure current user is a teacher
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this resource"
        )
    return current_user


def create_student_token(student: Student) -> str:
    """
    Create a JWT token for a student
    """
    token_data = {
        "sub": str(student.id),
        "type": "student",
        "name": student.name,
        "grade": student.grade
    }
    return create_access_token(token_data)


def create_teacher_token(teacher: Teacher) -> str:
    """
    Create a JWT token for a teacher
    """
    token_data = {
        "sub": str(teacher.id),
        "type": "teacher",
        "name": teacher.name,
        "subjects": teacher.subjects
    }
    return create_access_token(token_data)


def authenticate_teacher(email: str, password: str, db: Session) -> Optional[Teacher]:
    """
    Authenticate a teacher with email and password
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if not teacher:
        return None
    if not verify_password(password, teacher.password_hash):
        return None
    return teacher


def authenticate_student(email: str, password: str, db: Session) -> Optional[Student]:
    """
    Authenticate a student with email and password
    """
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        return None
    if not verify_password(password, student.password_hash):
        return None
    return student