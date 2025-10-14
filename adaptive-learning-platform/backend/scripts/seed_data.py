#!/usr/bin/env python3
"""
Sample Data Generation Script
Creates sample curriculum content and test data for the Adaptive Learning Platform
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Student, Teacher, TopicMastery, Assessment, GeneratedContent
from app.services.curriculum_ingestion import get_curriculum_ingestion_service


def create_sample_students(db):
    """Create sample students"""
    print("Creating sample students...")
    
    students_data = [
        {
            "name": "Fatmata Kamara",
            "email": "fatmata.kamara@example.com",
            "grade": 8,
            "reading_level": "intermediate",
            "learning_pace": "moderate"
        },
        {
            "name": "Mohamed Sesay",
            "email": "mohamed.sesay@example.com",
            "grade": 9,
            "reading_level": "advanced",
            "learning_pace": "fast"
        },
        {
            "name": "Aminata Bangura",
            "email": "aminata.bangura@example.com",
            "grade": 7,
            "reading_level": "basic",
            "learning_pace": "slow"
        },
        {
            "name": "Ibrahim Conteh",
            "email": "ibrahim.conteh@example.com",
            "grade": 10,
            "reading_level": "intermediate",
            "learning_pace": "moderate"
        },
        {
            "name": "Mariama Koroma",
            "email": "mariama.koroma@example.com",
            "grade": 11,
            "reading_level": "advanced",
            "learning_pace": "fast"
        }
    ]
    
    students = []
    for student_data in students_data:
        student = Student(**student_data)
        db.add(student)
        students.append(student)
    
    db.commit()
    print(f"✓ Created {len(students)} sample students")
    return students


def create_sample_teachers(db):
    """Create sample teachers"""
    print("Creating sample teachers...")
    
    teachers_data = [
        {
            "name": "Dr. Ibrahim Conteh",
            "email": "ibrahim.conteh@school.edu.sl",
            "password_hash": "$2b$12$dummy_hash_for_demo",  # In real app, properly hash passwords
            "subjects": ["mathematics", "english", "science"]
        },
        {
            "name": "Ms. Fatmata Sesay",
            "email": "fatmata.sesay@school.edu.sl",
            "password_hash": "$2b$12$dummy_hash_for_demo",
            "subjects": ["mathematics", "science"]
        },
        {
            "name": "Mr. Mohamed Bangura",
            "email": "mohamed.bangura@school.edu.sl",
            "password_hash": "$2b$12$dummy_hash_for_demo",
            "subjects": ["english", "science"]
        }
    ]
    
    teachers = []
    for teacher_data in teachers_data:
        teacher = Teacher(**teacher_data)
        db.add(teacher)
        teachers.append(teacher)
    
    db.commit()
    print(f"✓ Created {len(teachers)} sample teachers")
    return teachers


def create_sample_topic_mastery(db, students):
    """Create sample topic mastery records"""
    print("Creating sample topic mastery records...")
    
    subjects = ["mathematics", "english", "science"]
    topics = {
        "mathematics": ["algebra", "geometry", "arithmetic", "fractions", "decimals"],
        "english": ["grammar", "reading_comprehension", "writing", "vocabulary", "literature"],
        "science": ["biology", "chemistry", "physics", "earth_science", "experiments"]
    }
    
    mastery_records = []
    for student in students:
        for subject in subjects:
            for topic in topics[subject]:
                # Create varied mastery levels
                base_mastery = 50 + (student.grade - 7) * 5  # Higher grades = higher base mastery
                mastery_level = max(0, min(100, base_mastery + (hash(f"{student.id}{topic}") % 40 - 20)))
                
                mastery = TopicMastery(
                    student_id=student.id,
                    subject=subject,
                    topic=topic,
                    mastery_level=mastery_level,
                    total_attempts=max(1, mastery_level // 20),
                    last_practiced=datetime.now() - timedelta(days=hash(f"{student.id}{topic}") % 30)
                )
                db.add(mastery)
                mastery_records.append(mastery)
    
    db.commit()
    print(f"✓ Created {len(mastery_records)} topic mastery records")
    return mastery_records


def create_sample_assessments(db, students):
    """Create sample assessment records"""
    print("Creating sample assessment records...")
    
    subjects = ["mathematics", "english", "science"]
    topics = {
        "mathematics": ["algebra", "geometry", "arithmetic"],
        "english": ["grammar", "reading_comprehension", "writing"],
        "science": ["biology", "chemistry", "physics"]
    }
    
    assessments = []
    for student in students:
        for subject in subjects:
            for topic in topics[subject]:
                # Create 2-5 assessments per topic
                num_assessments = 2 + (hash(f"{student.id}{topic}") % 4)
                
                for attempt in range(1, num_assessments + 1):
                    # Simulate improving scores over attempts
                    base_score = 60 + (student.grade - 7) * 5
                    score = min(100, base_score + (attempt - 1) * 10 + (hash(f"{student.id}{topic}{attempt}") % 20 - 10))
                    
                    assessment = Assessment(
                        student_id=student.id,
                        subject=subject,
                        topic=topic,
                        score=score,
                        time_taken=300 + (hash(f"{student.id}{topic}{attempt}") % 300),  # 5-10 minutes
                        attempt_number=attempt,
                        errors=json.dumps([f"Error in question {i}" for i in range(1, 4)]) if score < 70 else None,
                        completed_at=datetime.now() - timedelta(days=hash(f"{student.id}{topic}{attempt}") % 30)
                    )
                    db.add(assessment)
                    assessments.append(assessment)
    
    db.commit()
    print(f"✓ Created {len(assessments)} assessment records")
    return assessments


def create_sample_generated_content(db):
    """Create sample generated content"""
    print("Creating sample generated content...")
    
    subjects = ["mathematics", "english", "science"]
    topics = {
        "mathematics": ["algebra", "geometry", "arithmetic"],
        "english": ["grammar", "reading_comprehension", "writing"],
        "science": ["biology", "chemistry", "physics"]
    }
    content_types = ["lesson", "exercise", "explanation", "example"]
    difficulty_levels = ["easy", "medium", "hard"]
    
    generated_content = []
    for subject in subjects:
        for topic in topics[subject]:
            for content_type in content_types:
                for difficulty in difficulty_levels:
                    for grade in range(7, 13):
                        content_data = {
                            "title": f"Sample {content_type.title()} for {topic}",
                            "content": f"This is a sample {content_type} for {topic} in {subject} at Grade {grade} level with {difficulty} difficulty.",
                            "examples": [
                                {
                                    "title": "Sierra Leone Example",
                                    "problem": f"A student in Freetown has a problem related to {topic}",
                                    "solution": "Step-by-step solution with local context"
                                }
                            ],
                            "key_points": [f"Key point 1 about {topic}", f"Key point 2 about {topic}"],
                            "estimated_time": 20 + (hash(f"{subject}{topic}{content_type}") % 20)
                        }
                        
                        content = GeneratedContent(
                            topic=topic,
                            subject=subject,
                            grade=grade,
                            difficulty_level=difficulty,
                            content_type=content_type,
                            content=json.dumps(content_data),
                            usage_count=hash(f"{subject}{topic}{content_type}") % 50
                        )
                        db.add(content)
                        generated_content.append(content)
    
    db.commit()
    print(f"✓ Created {len(generated_content)} generated content records")
    return generated_content


def create_sample_curriculum_content():
    """Create sample curriculum content files"""
    print("Creating sample curriculum content...")
    
    # Create data directories
    data_dir = Path("../data")
    for subject in ["mathematics", "english", "science"]:
        subject_dir = data_dir / subject
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample curriculum files
        for grade in range(7, 13):
            filename = subject_dir / f"grade_{grade}_{subject}.txt"
            content = f"""
Grade {grade} {subject.title()} Curriculum

Chapter 1: Introduction to {subject.title()}
This chapter introduces the fundamental concepts of {subject} for Grade {grade} students in Sierra Leone.

Section 1.1: Basic Concepts
Students will learn about basic {subject} concepts with examples from Sierra Leone:
- Local examples from Freetown, Bo, and Kenema
- Traditional practices and modern applications
- Currency examples using Leone

Section 1.2: Problem Solving
Students will practice solving {subject} problems:
- Step-by-step solutions
- Real-world applications
- Group work and collaboration

Chapter 2: Advanced Topics
This chapter covers more advanced {subject} topics suitable for Grade {grade}.

Section 2.1: Complex Problems
Students will tackle more challenging problems:
- Multi-step solutions
- Critical thinking skills
- Application to daily life in Sierra Leone

Section 2.2: Assessment and Evaluation
Students will be assessed on their understanding:
- Formative assessments
- Summative evaluations
- Self-reflection and peer review

Chapter 3: Practical Applications
This chapter focuses on real-world applications of {subject}.

Section 3.1: Local Context
Students will explore how {subject} applies to Sierra Leone:
- Economic applications
- Social implications
- Environmental considerations

Section 3.2: Future Learning
Students will prepare for advanced studies:
- Prerequisites for higher grades
- Career applications
- Lifelong learning skills
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
    
    print("✓ Created sample curriculum content files")
    
    # Ingest the content
    try:
        ingestion_service = get_curriculum_ingestion_service()
        db = SessionLocal()
        
        result = ingestion_service.ingest_directory(str(data_dir), db)
        
        if result['success']:
            print(f"✓ Ingested curriculum content: {result['processed_files']} files processed")
        else:
            print(f"❌ Failed to ingest curriculum content: {result.get('error', 'Unknown error')}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error ingesting curriculum content: {e}")


def main():
    """Main function to create all sample data"""
    print("🚀 Adaptive Learning Platform - Sample Data Generation")
    print("=" * 60)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create sample data
        students = create_sample_students(db)
        teachers = create_sample_teachers(db)
        mastery_records = create_sample_topic_mastery(db, students)
        assessments = create_sample_assessments(db, students)
        generated_content = create_sample_generated_content(db)
        
        # Create curriculum content
        create_sample_curriculum_content()
        
        print("\n✅ Sample data generation completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Students: {len(students)}")
        print(f"   - Teachers: {len(teachers)}")
        print(f"   - Topic Mastery Records: {len(mastery_records)}")
        print(f"   - Assessments: {len(assessments)}")
        print(f"   - Generated Content: {len(generated_content)}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("\n✨ Sample data ready for testing!")


if __name__ == "__main__":
    main()
