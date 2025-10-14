from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class LessonContent(BaseModel):
    title: str
    content: str
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    estimated_time: int = Field(..., ge=1)  # minutes


class ExerciseQuestion(BaseModel):
    question: str
    type: str = Field(..., pattern="^(mcq|short_answer|problem_solving)$")
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: str
    explanation: str
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    points: int = Field(default=1, ge=1)


class Exercise(BaseModel):
    title: str
    questions: List[ExerciseQuestion]
    total_points: int
    estimated_time: int = Field(..., ge=1)  # minutes


class GeneratedContentBase(BaseModel):
    topic: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=50)
    grade: Optional[int] = Field(None, ge=7, le=12)
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    content_type: str = Field(..., pattern="^(lesson|exercise|explanation|example)$")
    content: Dict[str, Any]


class GeneratedContentCreate(GeneratedContentBase):
    pass


class GeneratedContentResponse(GeneratedContentBase):
    id: UUID
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PersonalizedLesson(BaseModel):
    student_id: UUID
    subject: str
    topic: str
    lesson_content: LessonContent
    exercises: List[Exercise]
    prerequisites: List[str] = Field(default_factory=list)
    next_topics: List[str] = Field(default_factory=list)
    mastery_required: float = Field(default=85.0, ge=0, le=100)


class LearningPath(BaseModel):
    student_id: UUID
    subject: str
    current_topic: str
    progress: float = Field(..., ge=0, le=100)
    next_lessons: List[str] = Field(default_factory=list)
    recommended_practice: List[str] = Field(default_factory=list)
    estimated_completion: Optional[datetime] = None


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    suggested_actions: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0, le=1)


class DiagnosticAssessment(BaseModel):
    student_id: UUID
    subject: str
    questions: List[ExerciseQuestion]
    time_limit: int = Field(..., ge=1)  # minutes


class DiagnosticResult(BaseModel):
    student_id: UUID
    subject: str
    overall_score: float = Field(..., ge=0, le=100)
    topic_scores: Dict[str, float] = Field(default_factory=dict)
    reading_level: str = Field(..., pattern="^(basic|intermediate|advanced)$")
    learning_pace: str = Field(..., pattern="^(slow|moderate|fast)$")
    recommendations: List[str] = Field(default_factory=list)
    completed_at: datetime
