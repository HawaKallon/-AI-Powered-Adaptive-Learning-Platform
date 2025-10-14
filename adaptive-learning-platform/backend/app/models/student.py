from sqlalchemy import Column, String, Integer, DateTime, Float, CheckConstraint, Text, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid


class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    grade = Column(Integer, CheckConstraint('grade BETWEEN 7 AND 12'))
    reading_level = Column(String(20), CheckConstraint("reading_level IN ('basic', 'intermediate', 'advanced')"))
    learning_pace = Column(String(20), CheckConstraint("learning_pace IN ('slow', 'moderate', 'fast')"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topic_mastery = relationship("TopicMastery", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="student", cascade="all, delete-orphan")
    chat_logs = relationship("ChatLog", back_populates="student", cascade="all, delete-orphan")
    class_assignments = relationship("ClassAssignment", back_populates="student", cascade="all, delete-orphan")


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    subject = Column(String(50), nullable=False)
    topic = Column(String(200), nullable=False)
    mastery_level = Column(Float, CheckConstraint('mastery_level BETWEEN 0 AND 100'))
    last_practiced = Column(DateTime(timezone=True), server_default=func.now())
    total_attempts = Column(Integer, default=0)
    
    # Relationships
    student = relationship("Student", back_populates="topic_mastery")
    
    __table_args__ = (
        CheckConstraint('mastery_level BETWEEN 0 AND 100'),
        {'extend_existing': True}
    )


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String(200), nullable=False)
    subject = Column(String(50), nullable=False)
    grade = Column(Integer)
    difficulty_level = Column(String(20))
    content_type = Column(String(50), CheckConstraint("content_type IN ('lesson', 'exercise', 'explanation', 'example')"))
    content = Column(Text, nullable=False)  # JSON content stored as text
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    subject = Column(String(50), nullable=False)
    topic = Column(String(200), nullable=False)
    score = Column(Float, CheckConstraint('score BETWEEN 0 AND 100'))
    time_taken = Column(Integer)  # seconds
    attempt_number = Column(Integer, default=1)
    errors = Column(Text)  # JSON array of specific mistakes
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="assessments")


class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    session_id = Column(UUID(as_uuid=True))
    subject = Column(String(50))
    topic = Column(String(200))
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    student = relationship("Student", back_populates="chat_logs")


class CurriculumEmbedding(Base):
    __tablename__ = "curriculum_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject = Column(String(50), nullable=False)
    grade = Column(Integer)
    topic = Column(String(200), nullable=False)
    section_title = Column(String(300))
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # Vector stored as text (will be converted to vector type)
    content_metadata = Column(Text)  # JSON metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    subjects = Column(ARRAY(String))  # Array of subjects they teach
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    class_assignments = relationship("ClassAssignment", back_populates="teacher")


class ClassAssignment(Base):
    __tablename__ = "class_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey('teachers.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    subject = Column(String(50))
    
    # Relationships
    teacher = relationship("Teacher", back_populates="class_assignments")
    student = relationship("Student", back_populates="class_assignments")
    
    __table_args__ = (
        CheckConstraint('teacher_id IS NOT NULL AND student_id IS NOT NULL'),
        {'extend_existing': True}
    )
