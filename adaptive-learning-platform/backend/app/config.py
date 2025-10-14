from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/adaptive_learning"
    
    # Redis (optional)
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # LLM Configuration
    llm_model_name: str = "distilgpt2"  # Better for content generation
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # RAG Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_directory: str = "./chroma_db"
    vector_dimension: int = 384
    
    # Content Generation
    max_content_length: int = 2000
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf"]
    
    # Sierra Leone Context
    currency: str = "Leone"
    timezone: str = "Africa/Freetown"
    
    # Debug Mode
    debug: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()
