from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    grade: Optional[int] = Field(None, ge=7, le=12)
    reading_level: Optional[str] = Field(None, pattern="^(basic|intermediate|advanced)$")
    learning_pace: Optional[str] = Field(None, pattern="^(slow|moderate|fast)$")


class StudentCreate(StudentBase):
    password: str = Field(..., min_length=8)


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    grade: Optional[int] = Field(None, ge=7, le=12)
    reading_level: Optional[str] = Field(None, pattern="^(basic|intermediate|advanced)$")
    learning_pace: Optional[str] = Field(None, pattern="^(slow|moderate|fast)$")


class StudentResponse(StudentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TopicMasteryBase(BaseModel):
    subject: str = Field(..., max_length=50)
    topic: str = Field(..., max_length=200)
    mastery_level: float = Field(..., ge=0, le=100)
    total_attempts: int = Field(default=0, ge=0)


class TopicMasteryCreate(TopicMasteryBase):
    student_id: UUID


class TopicMasteryResponse(TopicMasteryBase):
    id: UUID
    student_id: UUID
    last_practiced: datetime
    
    class Config:
        from_attributes = True


class AssessmentBase(BaseModel):
    subject: str = Field(..., max_length=50)
    topic: str = Field(..., max_length=200)
    score: float = Field(..., ge=0, le=100)
    time_taken: Optional[int] = Field(None, ge=0)  # seconds
    attempt_number: int = Field(default=1, ge=1)
    errors: Optional[List[str]] = None


class AssessmentCreate(AssessmentBase):
    student_id: UUID


class AssessmentResponse(AssessmentBase):
    id: UUID
    student_id: UUID
    completed_at: datetime
    
    class Config:
        from_attributes = True


class ChatLogBase(BaseModel):
    subject: Optional[str] = Field(None, max_length=50)
    topic: Optional[str] = Field(None, max_length=200)
    user_message: str = Field(..., min_length=1)
    bot_response: str = Field(..., min_length=1)


class ChatLogCreate(ChatLogBase):
    student_id: UUID
    session_id: Optional[UUID] = None


class ChatLogResponse(ChatLogBase):
    id: UUID
    student_id: UUID
    session_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subjects: List[str] = Field(default_factory=list)


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=8)


class TeacherResponse(TeacherBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ClassAssignmentBase(BaseModel):
    teacher_id: UUID
    student_id: UUID
    subject: Optional[str] = Field(None, max_length=50)


class ClassAssignmentCreate(ClassAssignmentBase):
    pass


class ClassAssignmentResponse(ClassAssignmentBase):
    id: UUID
    
    class Config:
        from_attributes = True
