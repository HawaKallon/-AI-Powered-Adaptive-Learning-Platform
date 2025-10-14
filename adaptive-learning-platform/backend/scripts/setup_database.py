#!/usr/bin/env python3
"""
Database setup script for the Adaptive Learning Platform
Creates all tables and sets up pgvector extension
"""

import asyncio
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base, engine
from app.models import *  # Import all models


async def setup_database():
    """Set up the database with all required tables and extensions"""
    
    print("Setting up database...")
    
    try:
        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        
        # Set up pgvector extension
        print("Setting up pgvector extension...")
        with engine.connect() as conn:
            # Enable pgvector extension (optional)
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("✓ pgvector extension enabled")
            except Exception as e:
                print(f"Note: pgvector extension not available: {e}")
                print("✓ Continuing without pgvector extension")
            
            # Create vector index for curriculum embeddings (optional)
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_curriculum_embedding 
                    ON curriculum_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100);
                """))
                conn.commit()
                print("✓ Vector index created")
            except Exception as e:
                print(f"Note: Vector index creation skipped (pgvector not available): {e}")
        
        print("\n🎉 Database setup completed successfully!")
        print(f"Database URL: {settings.database_url}")
        
    except SQLAlchemyError as e:
        print(f"❌ Database setup failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


async def create_sample_data():
    """Create sample data for testing"""
    
    print("\nCreating sample data...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models import Student, Teacher, TopicMastery
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Create sample students
        sample_students = [
            Student(
                name="Fatmata Kamara",
                email="fatmata.kamara@example.com",
                grade=8,
                reading_level="intermediate",
                learning_pace="moderate"
            ),
            Student(
                name="Mohamed Sesay",
                email="mohamed.sesay@example.com", 
                grade=9,
                reading_level="advanced",
                learning_pace="fast"
            ),
            Student(
                name="Aminata Bangura",
                email="aminata.bangura@example.com",
                grade=7,
                reading_level="basic",
                learning_pace="slow"
            )
        ]
        
        for student in sample_students:
            db.add(student)
        
        # Create sample teacher
        sample_teacher = Teacher(
            name="Dr. Ibrahim Conteh",
            email="ibrahim.conteh@school.edu.sl",
            password_hash="$2b$12$dummy_hash_for_demo",  # In real app, properly hash passwords
            subjects=["mathematics", "english", "science"]
        )
        db.add(sample_teacher)
        
        db.commit()
        print("✓ Sample data created successfully")
        
        # Create sample topic mastery records
        students = db.query(Student).all()
        subjects = ["mathematics", "english", "science"]
        topics = {
            "mathematics": ["algebra", "geometry", "arithmetic"],
            "english": ["grammar", "reading_comprehension", "writing"],
            "science": ["biology", "chemistry", "physics"]
        }
        
        for student in students:
            for subject in subjects:
                for topic in topics[subject]:
                    mastery = TopicMastery(
                        student_id=student.id,
                        subject=subject,
                        topic=topic,
                        mastery_level=0.0,  # Will be updated through assessments
                        total_attempts=0
                    )
                    db.add(mastery)
        
        db.commit()
        print("✓ Sample topic mastery records created")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Adaptive Learning Platform - Database Setup")
    print("=" * 50)
    
    # Run database setup
    success = asyncio.run(setup_database())
    
    if success:
        # Ask if user wants to create sample data
        create_samples = input("\nCreate sample data? (y/n): ").lower().strip()
        if create_samples == 'y':
            asyncio.run(create_sample_data())
    
    print("\n✨ Setup complete!")
