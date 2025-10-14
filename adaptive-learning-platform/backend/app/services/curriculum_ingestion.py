"""
Curriculum Ingestion Service
Handles PDF processing, chunking, and embedding storage for curriculum documents
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..models import CurriculumEmbedding
from ..utils.pdf_parser import CurriculumPDFParser
from ..utils.embeddings import get_embedding_service, SierraLeoneContextualizer
from ..config import settings

logger = logging.getLogger(__name__)


class CurriculumIngestionService:
    """Service for ingesting and processing curriculum documents"""
    
    def __init__(self):
        self.pdf_parser = CurriculumPDFParser()
        self.embedding_service = get_embedding_service()
        self.contextualizer = SierraLeoneContextualizer()
    
    def ingest_pdf_file(self, pdf_path: str, db: Session) -> Dict[str, Any]:
        """Ingest a single PDF file and store embeddings"""
        try:
            logger.info(f"Starting ingestion of PDF: {pdf_path}")
            
            # Parse PDF
            parsed_data = self.pdf_parser.parse_curriculum_pdf(pdf_path)
            metadata = parsed_data['metadata']
            chunks = parsed_data['chunks']
            
            logger.info(f"Parsed {len(chunks)} chunks from PDF")
            
            # Process and store each chunk
            stored_count = 0
            failed_count = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # Add contextual information
                    contextualized_content = self.contextualizer.contextualize_content(
                        chunk['content'], 
                        metadata['subject']
                    )
                    
                    # Create embedding record
                    embedding_record = CurriculumEmbedding(
                        subject=metadata['subject'],
                        grade=metadata.get('grade'),
                        topic=chunk.get('title', 'Unknown Topic'),
                        section_title=chunk.get('title', ''),
                        content=contextualized_content,
                        embedding=None,  # Will be stored in ChromaDB
                        metadata=json.dumps({
                            'chunk_type': chunk.get('chunk_type', 'unknown'),
                            'file_path': pdf_path,
                            'file_name': metadata['file_name'],
                            'section_metadata': chunk.get('metadata', {}),
                            'created_at': datetime.now().isoformat()
                        })
                    )
                    
                    # Store in database
                    db.add(embedding_record)
                    db.flush()  # Get the ID
                    
                    # Prepare document for ChromaDB (ensure no None values)
                    doc_for_chroma = {
                        'id': str(embedding_record.id),
                        'content': contextualized_content,
                        'subject': str(metadata.get('subject', 'unknown')),
                        'grade': int(metadata.get('grade') or 10),  # Default to grade 10
                        'topic': str(chunk.get('title') or 'Unknown Topic'),
                        'section_title': str(chunk.get('title') or ''),
                        'chunk_type': str(chunk.get('chunk_type') or 'unknown'),
                        'file_path': str(pdf_path),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Store embedding in ChromaDB
                    if self.embedding_service.store_embeddings([doc_for_chroma]):
                        stored_count += 1
                        logger.debug(f"Stored chunk {i+1}/{len(chunks)}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to store chunk {i+1}")
                        db.rollback()
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {e}")
                    failed_count += 1
                    continue
            
            # Commit database changes
            db.commit()
            
            result = {
                'success': True,
                'file_path': pdf_path,
                'total_chunks': len(chunks),
                'stored_count': stored_count,
                'failed_count': failed_count,
                'metadata': metadata
            }
            
            logger.info(f"✓ Ingestion completed: {stored_count}/{len(chunks)} chunks stored")
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting PDF {pdf_path}: {e}")
            db.rollback()
            return {
                'success': False,
                'file_path': pdf_path,
                'error': str(e)
            }
    
    def ingest_directory(self, directory_path: str, db: Session) -> Dict[str, Any]:
        """Ingest all PDF files in a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise Exception(f"Directory not found: {directory_path}")
            
            # Find all PDF files
            pdf_files = list(directory.glob("*.pdf"))
            if not pdf_files:
                logger.warning(f"No PDF files found in {directory_path}")
                return {
                    'success': True,
                    'directory': directory_path,
                    'total_files': 0,
                    'processed_files': 0,
                    'results': []
                }
            
            logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
            
            results = []
            total_processed = 0
            total_failed = 0
            
            for pdf_file in pdf_files:
                result = self.ingest_pdf_file(str(pdf_file), db)
                results.append(result)
                
                if result['success']:
                    total_processed += 1
                else:
                    total_failed += 1
            
            return {
                'success': True,
                'directory': directory_path,
                'total_files': len(pdf_files),
                'processed_files': total_processed,
                'failed_files': total_failed,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error ingesting directory {directory_path}: {e}")
            return {
                'success': False,
                'directory': directory_path,
                'error': str(e)
            }
    
    def get_ingestion_stats(self, db: Session) -> Dict[str, Any]:
        """Get statistics about ingested content"""
        try:
            # Database stats
            total_documents = db.query(CurriculumEmbedding).count()
            
            # Group by subject
            subject_stats = db.execute(text("""
                SELECT subject, COUNT(*) as count, 
                       COUNT(DISTINCT grade) as grades,
                       COUNT(DISTINCT topic) as topics
                FROM curriculum_embeddings 
                GROUP BY subject
            """)).fetchall()
            
            # Group by grade
            grade_stats = db.execute(text("""
                SELECT grade, COUNT(*) as count
                FROM curriculum_embeddings 
                WHERE grade IS NOT NULL
                GROUP BY grade
                ORDER BY grade
            """)).fetchall()
            
            # ChromaDB stats
            chroma_stats = self.embedding_service.get_collection_stats()
            
            return {
                'database': {
                    'total_documents': total_documents,
                    'subjects': [{'subject': row[0], 'count': row[1], 'grades': row[2], 'topics': row[3]} for row in subject_stats],
                    'grades': [{'grade': row[0], 'count': row[1]} for row in grade_stats]
                },
                'chromadb': chroma_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion stats: {e}")
            return {'error': str(e)}
    
    def search_curriculum_content(self, query: str, subject: str = None, 
                                grade: int = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search curriculum content using RAG"""
        try:
            results = self.embedding_service.search_similar_documents(
                query=query,
                n_results=n_results,
                subject_filter=subject,
                grade_filter=grade
            )
            
            # Add contextual information to results
            for result in results:
                if 'metadata' in result:
                    result['metadata']['sierra_leone_context'] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching curriculum content: {e}")
            return []
    
    def delete_curriculum_content(self, file_path: str, db: Session) -> bool:
        """Delete all content from a specific file"""
        try:
            # Find documents from this file
            documents = db.query(CurriculumEmbedding).filter(
                CurriculumEmbedding.metadata.contains(file_path)
            ).all()
            
            if not documents:
                logger.warning(f"No documents found for file: {file_path}")
                return True
            
            # Get document IDs for ChromaDB deletion
            doc_ids = [str(doc.id) for doc in documents]
            
            # Delete from ChromaDB
            self.embedding_service.delete_documents(doc_ids)
            
            # Delete from database
            for doc in documents:
                db.delete(doc)
            
            db.commit()
            
            logger.info(f"✓ Deleted {len(documents)} documents for file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting curriculum content: {e}")
            db.rollback()
            return False
    
    def reindex_content(self, db: Session) -> Dict[str, Any]:
        """Reindex all content in ChromaDB"""
        try:
            logger.info("Starting content reindexing...")
            
            # Get all documents from database
            documents = db.query(CurriculumEmbedding).all()
            
            if not documents:
                return {'success': True, 'message': 'No documents to reindex'}
            
            # Prepare documents for ChromaDB
            docs_for_chroma = []
            for doc in documents:
                metadata = json.loads(doc.metadata) if doc.metadata else {}
                
                doc_for_chroma = {
                    'id': str(doc.id),
                    'content': doc.content,
                    'subject': doc.subject,
                    'grade': doc.grade or 0,
                    'topic': doc.topic,
                    'section_title': doc.section_title or '',
                    'chunk_type': metadata.get('chunk_type', 'unknown'),
                    'file_path': metadata.get('file_path', ''),
                    'created_at': metadata.get('created_at', datetime.now().isoformat())
                }
                docs_for_chroma.append(doc_for_chroma)
            
            # Store in ChromaDB
            success = self.embedding_service.store_embeddings(docs_for_chroma)
            
            if success:
                logger.info(f"✓ Reindexed {len(documents)} documents")
                return {
                    'success': True,
                    'reindexed_count': len(documents)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to store embeddings in ChromaDB'
                }
                
        except Exception as e:
            logger.error(f"Error reindexing content: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_curriculum_topics_and_subtopics(self, subject: str, grade: int, db: Session) -> Dict[str, Any]:
        """Get structured topics and subtopics from curriculum using RAG"""
        try:
            logger.info(f"Retrieving topics and subtopics for {subject}, Grade {grade}")
            
            # Query curriculum embeddings from database
            curriculum_items = db.query(CurriculumEmbedding).filter(
                CurriculumEmbedding.subject == subject,
                CurriculumEmbedding.grade == grade
            ).all()
            
            if not curriculum_items:
                logger.warning(f"No curriculum content found for {subject}, Grade {grade}")
                return {
                    'success': True,
                    'subject': subject,
                    'grade': grade,
                    'topics': []
                }
            
            # Group by topics and collect subtopics
            topics_dict = {}
            for item in curriculum_items:
                topic = item.topic
                section_title = item.section_title or ""
                
                if topic not in topics_dict:
                    topics_dict[topic] = {
                        'topic': topic,
                        'subtopics': [],
                        'description': ''
                    }
                
                # Add subtopic if it's not empty and not already added
                if section_title and section_title != topic:
                    if section_title not in topics_dict[topic]['subtopics']:
                        topics_dict[topic]['subtopics'].append(section_title)
                
                # Use RAG to get a brief description of the topic
                if not topics_dict[topic]['description'] and len(item.content) > 100:
                    # Extract first meaningful paragraph as description
                    paragraphs = item.content.split('\n\n')
                    for para in paragraphs:
                        if len(para.strip()) > 50 and topic.lower() in para.lower():
                            topics_dict[topic]['description'] = para.strip()[:300] + "..."
                            break
                    
                    # If still no description, use first paragraph
                    if not topics_dict[topic]['description'] and paragraphs:
                        topics_dict[topic]['description'] = paragraphs[0].strip()[:300] + "..."
            
            # Convert to list and sort
            topics_list = list(topics_dict.values())
            topics_list.sort(key=lambda x: x['topic'])
            
            logger.info(f"Found {len(topics_list)} topics for {subject}, Grade {grade}")
            
            return {
                'success': True,
                'subject': subject,
                'grade': grade,
                'total_topics': len(topics_list),
                'topics': topics_list
            }
            
        except Exception as e:
            logger.error(f"Error getting curriculum topics and subtopics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_topic_details(self, subject: str, topic: str, grade: int, db: Session) -> Dict[str, Any]:
        """Get detailed information about a specific topic using RAG"""
        try:
            logger.info(f"Retrieving details for topic: {topic} in {subject}, Grade {grade}")
            
            # Query curriculum content for this specific topic
            curriculum_items = db.query(CurriculumEmbedding).filter(
                CurriculumEmbedding.subject == subject,
                CurriculumEmbedding.grade == grade,
                CurriculumEmbedding.topic == topic
            ).all()
            
            if not curriculum_items:
                # Try a broader search using RAG semantic search
                search_results = self.search_curriculum_content(
                    query=topic,
                    subject=subject,
                    grade=grade,
                    n_results=10
                )
                
                if not search_results:
                    logger.warning(f"No content found for topic: {topic}")
                    return {
                        'success': False,
                        'error': f'No content found for topic: {topic}'
                    }
                
                # Extract information from search results
                subtopics = []
                content_sections = []
                for result in search_results:
                    metadata = result.get('metadata', {})
                    section_title = metadata.get('section_title', '')
                    if section_title and section_title not in subtopics:
                        subtopics.append(section_title)
                    content_sections.append(result.get('content', ''))
                
                combined_content = '\n\n---\n\n'.join(content_sections[:5])
                
            else:
                # Extract subtopics and content from database results
                subtopics = []
                content_sections = []
                
                for item in curriculum_items:
                    if item.section_title and item.section_title not in subtopics:
                        subtopics.append(item.section_title)
                    content_sections.append(item.content)
                
                combined_content = '\n\n---\n\n'.join(content_sections)
            
            # Extract learning objectives from content
            objectives = self._extract_learning_objectives(combined_content, topic)
            
            # Extract key concepts
            key_concepts = self._extract_key_concepts_from_content(combined_content, topic)
            
            return {
                'success': True,
                'topic': topic,
                'subject': subject,
                'grade': grade,
                'subtopics': subtopics,
                'objectives': objectives,
                'key_concepts': key_concepts,
                'content_preview': combined_content[:1000] + "..." if len(combined_content) > 1000 else combined_content
            }
            
        except Exception as e:
            logger.error(f"Error getting topic details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_learning_objectives(self, content: str, topic: str) -> List[str]:
        """Extract learning objectives from curriculum content"""
        objectives = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Look for objective patterns
            if any(keyword in line_lower for keyword in ['objective', 'learn to', 'understand', 'able to', 'by the end']):
                # Check if it's a list item
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    obj = line.strip().lstrip('-•').strip()
                    if len(obj) > 15 and len(obj) < 300:
                        objectives.append(obj)
                # Or if the line contains objective keywords, get the next few lines
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('-') or next_line.startswith('•'):
                        # Add the next list items
                        for j in range(i + 1, min(i + 6, len(lines))):
                            if lines[j].strip().startswith('-') or lines[j].strip().startswith('•'):
                                obj = lines[j].strip().lstrip('-•').strip()
                                if len(obj) > 15 and len(obj) < 300:
                                    objectives.append(obj)
                            else:
                                break
        
        return objectives[:10] if objectives else [f"Understand and apply {topic} concepts"]
    
    def _extract_key_concepts_from_content(self, content: str, topic: str) -> List[str]:
        """Extract key concepts from curriculum content"""
        concepts = []
        lines = content.split('\n')
        
        for line in lines:
            line_strip = line.strip()
            # Look for bulleted lists or key points
            if line_strip.startswith('-') or line_strip.startswith('•'):
                concept = line_strip.lstrip('-•').strip()
                if len(concept) > 20 and len(concept) < 200:
                    concepts.append(concept)
        
        # If we don't have enough concepts, look for important sentences
        if len(concepts) < 5:
            sentences = content.split('.')
            for sentence in sentences:
                sentence_strip = sentence.strip()
                if topic.lower() in sentence_strip.lower() and len(sentence_strip) > 30 and len(sentence_strip) < 200:
                    concepts.append(sentence_strip)
        
        return concepts[:15]  # Return top 15 key concepts


# Global service instance
curriculum_ingestion_service = None

def get_curriculum_ingestion_service() -> CurriculumIngestionService:
    """Get or create the global curriculum ingestion service"""
    global curriculum_ingestion_service
    if curriculum_ingestion_service is None:
        curriculum_ingestion_service = CurriculumIngestionService()
    return curriculum_ingestion_service
