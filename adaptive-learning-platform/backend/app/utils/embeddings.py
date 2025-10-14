"""
Embedding utilities for RAG system
Handles text embedding generation and similarity search
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
import json
import pickle
from pathlib import Path
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", persist_directory: str = "./chroma_db"):
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.model = None
        self.chroma_client = None
        self.collection = None
        
        # Initialize components
        self._initialize_model()
        self._initialize_chroma()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✓ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            logger.info("Initializing ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Create or get collection
            collection_name = "curriculum_embeddings"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                logger.info(f"✓ Loaded existing collection: {collection_name}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Curriculum content embeddings"}
                )
                logger.info(f"✓ Created new collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            logger.warning("ChromaDB initialization failed, will use fallback mode")
            self.chroma_client = None
            self.collection = None
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if not self.model:
            raise Exception("Embedding model not initialized")
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            raise Exception("Embedding model not initialized")
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=32)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def store_embeddings(self, documents: List[Dict[str, Any]], batch_size: int = 10) -> bool:
        """Store document embeddings in ChromaDB with batch processing"""
        if not self.collection:
            logger.warning("ChromaDB not available, skipping embedding storage")
            return True
        
        try:
            total_stored = 0
            total_docs = len(documents)
            
            # Process in batches to avoid overwhelming ChromaDB
            for batch_start in range(0, total_docs, batch_size):
                batch_end = min(batch_start + batch_size, total_docs)
                batch_docs = documents[batch_start:batch_end]
                
                # Prepare data for ChromaDB
                ids = []
                texts = []
                metadatas = []
                embeddings = []
                
                for i, doc in enumerate(batch_docs):
                    try:
                        doc_id = f"doc_{batch_start + i}_{doc.get('id', 'unknown')}"
                        ids.append(doc_id)
                        texts.append(doc['content'])
                        
                        # Prepare metadata - ensure no None values (ChromaDB doesn't accept None)
                        metadata = {
                            'subject': str(doc.get('subject') or 'unknown'),
                            'grade': int(doc.get('grade') or 0),
                            'topic': str(doc.get('topic') or 'unknown'),
                            'section_title': str(doc.get('section_title') or ''),
                            'chunk_type': str(doc.get('chunk_type') or 'unknown'),
                            'file_path': str(doc.get('file_path') or ''),
                            'created_at': str(doc.get('created_at') or '')
                        }
                        metadatas.append(metadata)
                        
                        # Generate embedding
                        embedding = self.generate_embedding(doc['content'])
                        embeddings.append(embedding.tolist())
                    except Exception as e:
                        logger.error(f"Error preparing document {batch_start + i}: {e}")
                        continue
                
                if not ids:  # Skip empty batches
                    continue
                
                # Store batch in ChromaDB
                try:
                    self.collection.add(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )
                    total_stored += len(ids)
                    logger.info(f"✓ Stored batch {batch_start+1}-{batch_end}/{total_docs}")
                except Exception as e:
                    logger.error(f"Error storing batch {batch_start+1}-{batch_end}: {e}")
                    continue
            
            logger.info(f"✓ Stored {total_stored}/{total_docs} document embeddings")
            return total_stored > 0
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return False
    
    def search_similar_documents(self, query: str, n_results: int = 5, 
                                subject_filter: str = None, grade_filter: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity"""
        if not self.collection:
            logger.warning("ChromaDB not available, returning empty results")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Prepare where clause for filtering
            where_clause = None
            if subject_filter and grade_filter:
                where_clause = {"$and": [{"subject": subject_filter}, {"grade": grade_filter}]}
            elif subject_filter:
                where_clause = {"subject": subject_filter}
            elif grade_filter:
                where_clause = {"grade": grade_filter}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'id': results['ids'][0][i]
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        if not self.collection:
            return {}
        
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.collection.name,
                'model_name': self.model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the collection"""
        if not self.collection:
            raise Exception("ChromaDB collection not initialized")
        
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"✓ Deleted {len(document_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    def update_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Update a document in the collection"""
        if not self.collection:
            raise Exception("ChromaDB collection not initialized")
        
        try:
            # Generate new embedding
            embedding = self.generate_embedding(content)
            
            # Update in ChromaDB
            self.collection.update(
                ids=[document_id],
                documents=[content],
                metadatas=[metadata],
                embeddings=[embedding.tolist()]
            )
            
            logger.info(f"✓ Updated document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False


class SierraLeoneContextualizer:
    """Adds Sierra Leone-specific context to educational content"""
    
    def __init__(self):
        self.local_context = {
            'currency': 'Leone',
            'currency_symbol': 'SLL',
            'cities': ['Freetown', 'Bo', 'Kenema', 'Makeni', 'Koidu', 'Port Loko'],
            'regions': ['Western Area', 'Northern Province', 'Southern Province', 'Eastern Province'],
            'landmarks': ['Mount Bintumani', 'Tiwai Island', 'Outamba-Kilimi National Park'],
            'common_names': ['Fatmata', 'Mohamed', 'Aminata', 'Ibrahim', 'Mariama', 'Saidu'],
            'local_foods': ['jollof rice', 'groundnut soup', 'cassava leaves', 'palm wine'],
            'schools': ['Fourah Bay College', 'Njala University', 'University of Sierra Leone']
        }
    
    def contextualize_content(self, content: str, subject: str) -> str:
        """Add Sierra Leone context to educational content"""
        contextualized = content
        
        # Add local examples based on subject
        if subject.lower() == 'mathematics':
            contextualized = self._add_math_examples(contextualized)
        elif subject.lower() == 'english':
            contextualized = self._add_english_examples(contextualized)
        elif subject.lower() == 'science':
            contextualized = self._add_science_examples(contextualized)
        
        return contextualized
    
    def _add_math_examples(self, content: str) -> str:
        """Add Sierra Leone-specific math examples"""
        examples = [
            f"If a student in {self.local_context['cities'][0]} has 500 {self.local_context['currency']} and spends 200 {self.local_context['currency']}, how much is left?",
            f"A farmer in {self.local_context['regions'][1]} harvested 150 kg of rice. If each bag holds 25 kg, how many bags can he fill?",
            f"The distance from {self.local_context['cities'][0]} to {self.local_context['cities'][1]} is 180 km. If a bus travels at 60 km/h, how long will the journey take?"
        ]
        
        # Add examples if content mentions generic math problems
        if any(keyword in content.lower() for keyword in ['example', 'problem', 'solve', 'calculate']):
            content += f"\n\nLocal Examples:\n" + "\n".join(examples[:2])
        
        return content
    
    def _add_english_examples(self, content: str) -> str:
        """Add Sierra Leone-specific English examples"""
        examples = [
            f"Write a letter to your friend {self.local_context['common_names'][0]} about your visit to {self.local_context['landmarks'][0]}.",
            f"Describe the traditional {self.local_context['local_foods'][0]} served during celebrations in {self.local_context['cities'][0]}.",
            f"Create a story about a student from {self.local_context['regions'][2]} who dreams of studying at {self.local_context['schools'][0]}."
        ]
        
        if any(keyword in content.lower() for keyword in ['write', 'describe', 'story', 'essay']):
            content += f"\n\nLocal Writing Prompts:\n" + "\n".join(examples[:2])
        
        return content
    
    def _add_science_examples(self, content: str) -> str:
        """Add Sierra Leone-specific science examples"""
        examples = [
            f"Study the ecosystem of {self.local_context['landmarks'][1]} and identify the different species of plants and animals.",
            f"Investigate the water quality in the rivers of {self.local_context['regions'][1]} and its impact on local communities.",
            f"Research the traditional farming methods used in {self.local_context['regions'][2]} and their environmental impact."
        ]
        
        if any(keyword in content.lower() for keyword in ['experiment', 'investigate', 'study', 'research']):
            content += f"\n\nLocal Science Projects:\n" + "\n".join(examples[:2])
        
        return content


# Initialize global embedding service
embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance"""
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service
