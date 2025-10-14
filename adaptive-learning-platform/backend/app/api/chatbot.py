"""
Chatbot API endpoints
Handles conversational interactions with the AI tutor
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from uuid import UUID

from ..database import get_db
from ..models import Student, ChatLog
from ..schemas import ChatMessage, ChatResponse, ChatLogResponse
from ..utils.auth import get_current_student, get_current_teacher
from ..services.chatbot_service import get_chatbot_service

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/chat", response_model=Dict[str, Any])
async def send_chat_message(
    message: str,
    session_id: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Send a message to the chatbot and get a response"""
    try:
        # Validate message
        if not message or not message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        chatbot_service = get_chatbot_service()
        
        # Create new session if not provided
        if not session_id:
            session_id = chatbot_service.create_new_session(str(current_student.id))
        
        # Process the message
        response_data = chatbot_service.process_chat_message(
            student_id=str(current_student.id),
            message=message.strip(),
            session_id=session_id,
            db=db
        )
        
        if not response_data['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response_data.get('error', 'Failed to process message')
            )
        
        return {
            "success": True,
            "response": response_data['response'],
            "session_id": session_id,
            "timestamp": response_data['timestamp']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/suggested-questions", response_model=Dict[str, Any])
async def get_suggested_questions(
    subject: str = None,
    topic: str = None,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get suggested questions based on student's current context"""
    try:
        chatbot_service = get_chatbot_service()
        
        # Get student context
        context = chatbot_service._get_student_context(str(current_student.id), db)
        
        # Override context with provided parameters
        if subject:
            context['current_subject'] = subject
        if topic:
            context['current_topic'] = topic
        
        # Get suggested questions
        suggested_questions = chatbot_service.get_suggested_questions(
            student_id=str(current_student.id),
            context=context
        )
        
        return {
            "success": True,
            "suggested_questions": suggested_questions,
            "current_context": {
                "subject": context.get('current_subject', 'mathematics'),
                "topic": context.get('current_topic', 'introduction'),
                "mastery_level": context.get('mastery_level', 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggested questions: {str(e)}"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_chat_history(
    session_id: str = None,
    limit: int = 50,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get chat history for the current student"""
    try:
        # Validate limit
        if not (1 <= limit <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        chatbot_service = get_chatbot_service()
        
        # If no session_id provided, get the most recent session
        if not session_id:
            # Get the most recent chat log to find the latest session
            recent_chat = db.query(ChatLog).filter(
                ChatLog.student_id == current_student.id
            ).order_by(ChatLog.created_at.desc()).first()
            
            if recent_chat:
                session_id = str(recent_chat.session_id)
            else:
                return {
                    "success": True,
                    "chat_history": [],
                    "session_id": None
                }
        
        # Get chat history
        chat_history = chatbot_service.get_chat_history(
            student_id=str(current_student.id),
            session_id=session_id,
            db=db,
            limit=limit
        )
        
        return {
            "success": True,
            "chat_history": chat_history,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.get("/sessions", response_model=Dict[str, Any])
async def get_chat_sessions(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current student"""
    try:
        # Get all unique sessions for the student
        sessions = db.query(ChatLog.session_id).filter(
            ChatLog.student_id == current_student.id
        ).distinct().all()
        
        session_list = []
        for session in sessions:
            if session[0]:  # session_id is not None
                # Get session info
                session_chats = db.query(ChatLog).filter(
                    ChatLog.student_id == current_student.id,
                    ChatLog.session_id == session[0]
                ).order_by(ChatLog.created_at.desc()).all()
                
                if session_chats:
                    session_info = {
                        "session_id": str(session[0]),
                        "message_count": len(session_chats),
                        "last_message": session_chats[0].created_at.isoformat(),
                        "first_message": session_chats[-1].created_at.isoformat(),
                        "subjects": list(set(chat.subject for chat in session_chats if chat.subject)),
                        "topics": list(set(chat.topic for chat in session_chats if chat.topic))
                    }
                    session_list.append(session_info)
        
        # Sort by last message time
        session_list.sort(key=lambda x: x['last_message'], reverse=True)
        
        return {
            "success": True,
            "sessions": session_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat sessions: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_chat_analytics(
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get chatbot usage analytics for the current student"""
    try:
        chatbot_service = get_chatbot_service()
        
        analytics = chatbot_service.get_conversation_analytics(
            student_id=str(current_student.id),
            db=db
        )
        
        if 'error' in analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analytics['error']
            )
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat analytics: {str(e)}"
        )


@router.post("/new-session", response_model=Dict[str, Any])
async def create_new_chat_session(
    current_student: Student = Depends(get_current_student)
):
    """Create a new chat session"""
    try:
        chatbot_service = get_chatbot_service()
        
        session_id = chatbot_service.create_new_session(str(current_student.id))
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "New chat session created"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new session: {str(e)}"
        )


# Teacher endpoints for chatbot management
@router.get("/student/{student_id}/history", response_model=Dict[str, Any])
async def get_student_chat_history(
    student_id: UUID,
    session_id: str = None,
    limit: int = 50,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get chat history for a specific student (teacher only)"""
    try:
        # Validate limit
        if not (1 <= limit <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        chatbot_service = get_chatbot_service()
        
        # If no session_id provided, get the most recent session
        if not session_id:
            recent_chat = db.query(ChatLog).filter(
                ChatLog.student_id == student_id
            ).order_by(ChatLog.created_at.desc()).first()
            
            if recent_chat:
                session_id = str(recent_chat.session_id)
            else:
                return {
                    "success": True,
                    "chat_history": [],
                    "session_id": None
                }
        
        # Get chat history
        chat_history = chatbot_service.get_chat_history(
            student_id=str(student_id),
            session_id=session_id,
            db=db,
            limit=limit
        )
        
        return {
            "success": True,
            "chat_history": chat_history,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student chat history: {str(e)}"
        )


@router.get("/student/{student_id}/analytics", response_model=Dict[str, Any])
async def get_student_chat_analytics(
    student_id: UUID,
    current_teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get chatbot usage analytics for a specific student (teacher only)"""
    try:
        chatbot_service = get_chatbot_service()
        
        analytics = chatbot_service.get_conversation_analytics(
            student_id=str(student_id),
            db=db
        )
        
        if 'error' in analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analytics['error']
            )
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student chat analytics: {str(e)}"
        )


