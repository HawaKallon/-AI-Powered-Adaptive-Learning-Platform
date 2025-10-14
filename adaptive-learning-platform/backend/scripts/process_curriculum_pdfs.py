#!/usr/bin/env python3
"""
Curriculum PDF Processing Script
Processes Sierra Leone curriculum PDFs and adds them to ChromaDB for AI-powered lesson generation.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
import fitz  # PyMuPDF
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import get_db
from app.utils.embeddings import get_embedding_service
from app.models import CurriculumEmbedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurriculumProcessor:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.db = next(get_db())
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fitz)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n"  # Add line break between pages
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def determine_grade_from_filename(self, filename: str) -> int:
        """Extract grade level from filename"""
        filename_lower = filename.lower()
        
        if "grade_10" in filename_lower or "grade10" in filename_lower:
            return 10
        elif "grade_11" in filename_lower or "grade11" in filename_lower:
            return 11
        elif "grade_12" in filename_lower or "grade12" in filename_lower:
            return 12
        else:
            # Default to grade 10 if not specified
            return 10
    
    def extract_topic_from_filename(self, filename: str) -> str:
        """Extract topic from filename"""
        # Remove file extension
        name = Path(filename).stem
        
        # Remove grade information
        name = name.replace("grade_10", "").replace("grade_11", "").replace("grade_12", "")
        name = name.replace("grade10", "").replace("grade11", "").replace("grade12", "")
        
        # Clean up and format
        name = name.replace("_", " ").replace("-", " ").strip()
        
        # Capitalize first letter of each word
        return " ".join(word.capitalize() for word in name.split())
    
    def process_pdf(self, pdf_path: str, subject: str) -> Dict[str, Any]:
        """Process a single PDF file"""
        filename = Path(pdf_path).name
        logger.info(f"Processing {filename} for subject {subject}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {filename}")
            return None
        
        # Determine grade and topic
        grade = self.determine_grade_from_filename(filename)
        topic = self.extract_topic_from_filename(filename)
        
        # Create embedding
        try:
            embedding = self.embedding_service.generate_embedding(text)
        except Exception as e:
            logger.error(f"Error creating embedding for {filename}: {str(e)}")
            return None
        
        # Store in database
        try:
            curriculum_embedding = CurriculumEmbedding(
                subject=subject,
                grade=grade,
                topic=topic,
                content=text,
                embedding=str(embedding.tolist()),  # Convert numpy array to string
                content_metadata=f'{{"filename": "{filename}", "source": "pdf"}}'
            )
            
            self.db.add(curriculum_embedding)
            self.db.commit()
            
            logger.info(f"Successfully processed {filename}")
            
            return {
                "filename": filename,
                "subject": subject,
                "grade": grade,
                "topic": topic,
                "content_length": len(text),
                "embedding_dimension": len(embedding)
            }
            
        except Exception as e:
            logger.error(f"Error storing {filename} in database: {str(e)}")
            self.db.rollback()
            return None
    
    def process_subject_folder(self, subject_folder: str, subject: str) -> List[Dict[str, Any]]:
        """Process all PDFs in a subject folder"""
        results = []
        
        if not os.path.exists(subject_folder):
            logger.warning(f"Subject folder {subject_folder} does not exist")
            return results
        
        pdf_files = [f for f in os.listdir(subject_folder) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {subject_folder}")
            return results
        
        logger.info(f"Found {len(pdf_files)} PDF files in {subject_folder}")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(subject_folder, pdf_file)
            result = self.process_pdf(pdf_path, subject)
            if result:
                results.append(result)
        
        return results
    
    def process_all_curriculum(self, curriculum_base_path: str) -> Dict[str, Any]:
        """Process all curriculum PDFs"""
        logger.info(f"Starting curriculum processing from {curriculum_base_path}")
        
        grade_folder = os.path.join(curriculum_base_path, "grade_10_12")
        
        if not os.path.exists(grade_folder):
            logger.error(f"Grade folder {grade_folder} does not exist")
            return {"success": False, "error": "Grade folder not found"}
        
        subjects = ["mathematics", "english", "science"]
        all_results = {}
        total_processed = 0
        
        for subject in subjects:
            subject_folder = os.path.join(grade_folder, subject)
            results = self.process_subject_folder(subject_folder, subject)
            all_results[subject] = results
            total_processed += len(results)
        
        logger.info(f"Curriculum processing complete. Processed {total_processed} PDFs total.")
        
        return {
            "success": True,
            "total_processed": total_processed,
            "results": all_results
        }

def main():
    """Main function to run the curriculum processing"""
    # Get the curriculum PDFs path
    script_dir = Path(__file__).parent
    curriculum_path = script_dir.parent.parent / "curriculum_pdfs"
    
    if not curriculum_path.exists():
        logger.error(f"Curriculum path {curriculum_path} does not exist")
        sys.exit(1)
    
    # Initialize processor
    processor = CurriculumProcessor()
    
    try:
        # Process all curriculum PDFs
        result = processor.process_all_curriculum(str(curriculum_path))
        
        if result["success"]:
            logger.info("✅ Curriculum processing completed successfully!")
            logger.info(f"📊 Total PDFs processed: {result['total_processed']}")
            
            for subject, results in result["results"].items():
                logger.info(f"📚 {subject.capitalize()}: {len(results)} PDFs processed")
        else:
            logger.error(f"❌ Curriculum processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error during processing: {str(e)}")
        sys.exit(1)
    
    finally:
        processor.db.close()

if __name__ == "__main__":
    main()
