#!/usr/bin/env python3
"""
Simple Curriculum Data Update Script
Updates curriculum embeddings from text files
"""

import os
import sys
import json
from pathlib import Path
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import get_db
from app.models import CurriculumEmbedding

def update_curriculum_data():
    """Update curriculum data from text files"""
    db = next(get_db())
    
    # Clear existing curriculum data
    db.query(CurriculumEmbedding).delete()
    db.commit()
    
    # Define curriculum files
    curriculum_files = {
        'mathematics': '/Users/hawakallon/Desktop/learning_Platform/adaptive-learning-platform/data/mathematics/grade_10_mathematics.txt',
        'english': '/Users/hawakallon/Desktop/learning_Platform/adaptive-learning-platform/data/english/grade_10_english.txt',
        'science': '/Users/hawakallon/Desktop/learning_Platform/adaptive-learning-platform/data/science/grade_10_science.txt'
    }
    
    for subject, file_path in curriculum_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create curriculum embedding record
            embedding_record = CurriculumEmbedding(
                subject=subject,
                grade=10,
                topic=f"Grade 10 {subject.title()} Curriculum",
                section_title="Complete Curriculum",
                content=content,
                embedding=None,  # Will be stored in ChromaDB
                metadata=json.dumps({
                    'chunk_type': 'curriculum',
                    'file_path': file_path,
                    'file_name': f"grade_10_{subject}.txt",
                    'created_at': '2024-01-01T00:00:00'
                })
            )
            
            db.add(embedding_record)
            print(f"Added {subject} curriculum data")
    
    db.commit()
    print("Curriculum data updated successfully!")

if __name__ == "__main__":
    update_curriculum_data()
