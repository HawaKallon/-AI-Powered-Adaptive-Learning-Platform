from .student import (
    StudentBase, StudentCreate, StudentUpdate, StudentResponse,
    TopicMasteryBase, TopicMasteryCreate, TopicMasteryResponse,
    AssessmentBase, AssessmentCreate, AssessmentResponse,
    ChatLogBase, ChatLogCreate, ChatLogResponse,
    TeacherBase, TeacherCreate, TeacherResponse,
    ClassAssignmentBase, ClassAssignmentCreate, ClassAssignmentResponse
)
from .lesson import (
    LessonContent, ExerciseQuestion, Exercise,
    GeneratedContentBase, GeneratedContentCreate, GeneratedContentResponse,
    PersonalizedLesson, LearningPath, ChatMessage, ChatResponse,
    DiagnosticAssessment, DiagnosticResult
)

__all__ = [
    # Student schemas
    "StudentBase", "StudentCreate", "StudentUpdate", "StudentResponse",
    "TopicMasteryBase", "TopicMasteryCreate", "TopicMasteryResponse",
    "AssessmentBase", "AssessmentCreate", "AssessmentResponse",
    "ChatLogBase", "ChatLogCreate", "ChatLogResponse",
    "TeacherBase", "TeacherCreate", "TeacherResponse",
    "ClassAssignmentBase", "ClassAssignmentCreate", "ClassAssignmentResponse",
    # Lesson schemas
    "LessonContent", "ExerciseQuestion", "Exercise",
    "GeneratedContentBase", "GeneratedContentCreate", "GeneratedContentResponse",
    "PersonalizedLesson", "LearningPath", "ChatMessage", "ChatResponse",
    "DiagnosticAssessment", "DiagnosticResult"
]
