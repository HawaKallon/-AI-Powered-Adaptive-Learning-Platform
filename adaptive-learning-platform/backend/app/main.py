"""
Main FastAPI application
Entry point for the Adaptive Learning Platform API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from .config import settings
from .api import auth, students, lessons, assessments, chatbot
from .database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Adaptive Learning Platform",
    description="Personalized education platform for Sierra Leonean students",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Adaptive Learning Platform API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "success": True,
        "message": "Welcome to the AI-Powered Adaptive Learning Platform",
        "description": "Personalized education for Sierra Leonean students",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Adaptive Learning Platform API...")
    
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")
        
        # Initialize services
        from .services.content_generator import get_content_generator_service
        from .services.adaptive_engine import get_adaptive_engine
        from .services.chatbot_service import get_chatbot_service
        from .services.assessment_service import get_assessment_service
        from .services.curriculum_ingestion import get_curriculum_ingestion_service
        
        # Initialize all services
        get_content_generator_service()
        get_adaptive_engine()
        get_chatbot_service()
        get_assessment_service()
        get_curriculum_ingestion_service()
        
        logger.info("✓ All services initialized")
        logger.info("🚀 Adaptive Learning Platform API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Adaptive Learning Platform API...")
    logger.info("✓ Shutdown complete")


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
