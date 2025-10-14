#!/usr/bin/env python3
"""
Simple Text File Ingestion Script
Directly ingests curriculum from text files instead of PDFs
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import CurriculumEmbedding
from app.utils.embeddings import get_embedding_service
from datetime import datetime
import json


def ingest_text_file(file_path: str, subject: str, grade: int):
    """Ingest a single text file"""
    print(f"\n📖 Processing: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    db = SessionLocal()
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            print(f"⚠️  File is empty, skipping...")
            return False
        
        # Split into chunks (by paragraphs or sections)
        chunks = split_into_chunks(content, subject, grade)
        print(f"  - Split into {len(chunks)} chunks")
        
        embedding_service = get_embedding_service()
        stored_count = 0
        
        for i, chunk_data in enumerate(chunks):
            try:
                # Create embedding record in database
                embedding_record = CurriculumEmbedding(
                    subject=subject,
                    grade=grade,
                    topic=chunk_data['topic'],
                    section_title=chunk_data['title'],
                    content=chunk_data['content'],
                    embedding=None,
                    metadata=json.dumps({
                        'chunk_type': 'text_section',
                        'file_path': file_path,
                        'file_name': os.path.basename(file_path),
                        'created_at': datetime.now().isoformat()
                    })
                )
                
                db.add(embedding_record)
                db.flush()
                
                # Prepare for ChromaDB
                doc_for_chroma = {
                    'id': str(embedding_record.id),
                    'content': chunk_data['content'],
                    'subject': subject,
                    'grade': grade,
                    'topic': chunk_data['topic'],
                    'section_title': chunk_data['title'],
                    'chunk_type': 'text_section',
                    'file_path': file_path,
                    'created_at': datetime.now().isoformat()
                }
                
                # Store in ChromaDB
                if embedding_service.store_embeddings([doc_for_chroma]):
                    stored_count += 1
                else:
                    print(f"  ⚠️  Failed to store chunk {i+1}")
                    
            except Exception as e:
                print(f"  ❌ Error processing chunk {i+1}: {e}")
                continue
        
        db.commit()
        print(f"  ✓ Stored {stored_count}/{len(chunks)} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def split_into_chunks(content: str, subject: str, grade: int):
    """Split content into meaningful chunks"""
    chunks = []
    
    # Split by double newlines (paragraphs)
    sections = content.split('\n\n')
    
    current_chunk = ""
    current_title = f"Grade {grade} {subject.title()} Curriculum"
    chunk_number = 1
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # Detect if this is a title/heading (short, possibly capitalized)
        if len(section) < 100 and (section.isupper() or section.startswith('#') or 
                                   any(keyword in section.lower() for keyword in ['chapter', 'unit', 'lesson', 'topic'])):
            # Save previous chunk if it exists
            if current_chunk:
                chunks.append({
                    'topic': current_title,
                    'title': current_title,
                    'content': current_chunk.strip()
                })
                chunk_number += 1
            
            # Start new chunk with this title
            current_title = section.replace('#', '').strip()
            current_chunk = section + "\n\n"
        else:
            # Add to current chunk
            current_chunk += section + "\n\n"
            
            # If chunk is getting large, split it
            if len(current_chunk) > 1500:
                chunks.append({
                    'topic': current_title,
                    'title': current_title,
                    'content': current_chunk.strip()
                })
                current_chunk = ""
                chunk_number += 1
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append({
            'topic': current_title,
            'title': current_title,
            'content': current_chunk.strip()
        })
    
    # If no chunks were created, create one with all content
    if not chunks:
        chunks.append({
            'topic': f"Grade {grade} {subject.title()}",
            'title': f"Grade {grade} {subject.title()} Curriculum",
            'content': content
        })
    
    return chunks


def main():
    """Main function"""
    print("🚀 Adaptive Learning Platform - Text File Ingestion")
    print("=" * 60)
    
    # Data directory
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Subject mappings
    subjects = {
        'mathematics': list(range(7, 13)),  # Grades 7-12
        'english': list(range(7, 13)),
        'science': list(range(7, 13))
    }
    
    total_processed = 0
    total_failed = 0
    
    for subject, grades in subjects.items():
        print(f"\n📚 Processing {subject.upper()}")
        subject_dir = data_dir / subject
        
        if not subject_dir.exists():
            print(f"  ⚠️  Directory not found: {subject_dir}")
            continue
        
        for grade in grades:
            file_path = subject_dir / f"grade_{grade}_{subject}.txt"
            
            if not file_path.exists():
                print(f"  ⚠️  File not found: {file_path}")
                continue
            
            if ingest_text_file(str(file_path), subject, grade):
                total_processed += 1
            else:
                total_failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Ingestion complete!")
    print(f"  - Successfully processed: {total_processed} files")
    print(f"  - Failed: {total_failed} files")
    
    # Show stats
    print("\n📊 Getting ingestion statistics...")
    db = SessionLocal()
    try:
        from app.services.curriculum_ingestion import get_curriculum_ingestion_service
        ingestion_service = get_curriculum_ingestion_service()
        stats = ingestion_service.get_ingestion_stats(db)
        
        if 'database' in stats:
            print(f"  - Total documents: {stats['database']['total_documents']}")
            print(f"  - ChromaDB documents: {stats['chromadb'].get('total_documents', 0)}")
    except Exception as e:
        print(f"  ⚠️  Error getting stats: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

