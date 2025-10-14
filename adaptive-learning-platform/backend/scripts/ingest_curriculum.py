#!/usr/bin/env python3
"""
Curriculum Ingestion Script
Processes PDF curriculum documents and stores them in the database
"""

import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.curriculum_ingestion import get_curriculum_ingestion_service


def ingest_single_file(pdf_path: str):
    """Ingest a single PDF file"""
    print(f"Processing PDF: {pdf_path}")
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get curriculum ingestion service
        ingestion_service = get_curriculum_ingestion_service()
        
        # Ingest the file
        result = ingestion_service.ingest_pdf_file(pdf_path, db)
        
        if result['success']:
            print(f"✓ Successfully processed: {result['file_path']}")
            print(f"  - Total chunks: {result['total_chunks']}")
            print(f"  - Stored: {result['stored_count']}")
            print(f"  - Failed: {result['failed_count']}")
            print(f"  - Subject: {result['metadata']['subject']}")
            print(f"  - Grade: {result['metadata'].get('grade', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to process: {result['file_path']}")
            print(f"  - Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return False
    finally:
        db.close()


def ingest_directory(directory_path: str):
    """Ingest all PDF files in a directory"""
    print(f"Processing directory: {directory_path}")
    
    # Check if directory exists
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return False
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get curriculum ingestion service
        ingestion_service = get_curriculum_ingestion_service()
        
        # Ingest the directory
        result = ingestion_service.ingest_directory(directory_path, db)
        
        if result['success']:
            print(f"✓ Successfully processed directory: {result['directory']}")
            print(f"  - Total files: {result['total_files']}")
            print(f"  - Processed: {result['processed_files']}")
            print(f"  - Failed: {result['failed_files']}")
            
            # Show individual file results
            for file_result in result['results']:
                if file_result['success']:
                    print(f"    ✓ {file_result['file_path']}: {file_result['stored_count']}/{file_result['total_chunks']} chunks")
                else:
                    print(f"    ❌ {file_result['file_path']}: {file_result.get('error', 'Unknown error')}")
            
            return True
        else:
            print(f"❌ Failed to process directory: {result['directory']}")
            print(f"  - Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing directory {directory_path}: {e}")
        return False
    finally:
        db.close()


def get_ingestion_stats():
    """Get statistics about ingested content"""
    print("Getting ingestion statistics...")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get curriculum ingestion service
        ingestion_service = get_curriculum_ingestion_service()
        
        # Get stats
        stats = ingestion_service.get_ingestion_stats(db)
        
        if 'error' in stats:
            print(f"❌ Error getting stats: {stats['error']}")
            return False
        
        print("✓ Ingestion Statistics:")
        print(f"  - Total documents: {stats['database']['total_documents']}")
        
        print("  - By Subject:")
        for subject_stat in stats['database']['subjects']:
            print(f"    - {subject_stat['subject']}: {subject_stat['count']} documents, {subject_stat['grades']} grades, {subject_stat['topics']} topics")
        
        print("  - By Grade:")
        for grade_stat in stats['database']['grades']:
            print(f"    - Grade {grade_stat['grade']}: {grade_stat['count']} documents")
        
        if stats['chromadb']:
            print(f"  - ChromaDB: {stats['chromadb'].get('total_documents', 0)} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return False
    finally:
        db.close()


def reindex_content():
    """Reindex all content in ChromaDB"""
    print("Reindexing content in ChromaDB...")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get curriculum ingestion service
        ingestion_service = get_curriculum_ingestion_service()
        
        # Reindex content
        result = ingestion_service.reindex_content(db)
        
        if result['success']:
            print(f"✓ Successfully reindexed {result['reindexed_count']} documents")
            return True
        else:
            print(f"❌ Failed to reindex content: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error reindexing content: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Curriculum Ingestion Script")
    parser.add_argument("command", choices=["ingest", "stats", "reindex"], help="Command to execute")
    parser.add_argument("--file", "-f", help="Path to PDF file to ingest")
    parser.add_argument("--directory", "-d", help="Path to directory containing PDF files")
    
    args = parser.parse_args()
    
    print("🚀 Adaptive Learning Platform - Curriculum Ingestion")
    print("=" * 60)
    
    if args.command == "ingest":
        if args.file:
            success = ingest_single_file(args.file)
        elif args.directory:
            success = ingest_directory(args.directory)
        else:
            print("❌ Please specify either --file or --directory")
            sys.exit(1)
        
        if success:
            print("\n✅ Ingestion completed successfully!")
        else:
            print("\n❌ Ingestion failed!")
            sys.exit(1)
    
    elif args.command == "stats":
        success = get_ingestion_stats()
        if not success:
            sys.exit(1)
    
    elif args.command == "reindex":
        success = reindex_content()
        if not success:
            sys.exit(1)
    
    print("\n✨ Operation complete!")


if __name__ == "__main__":
    main()


