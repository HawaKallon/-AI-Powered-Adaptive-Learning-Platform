"""
PDF Parser for Curriculum Documents
Handles smart chunking and metadata extraction from educational PDFs
"""

import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Optional
import re
import json
from pathlib import Path


class CurriculumPDFParser:
    """Parser for educational PDF documents with smart chunking"""
    
    def __init__(self):
        self.section_patterns = [
            r'^Chapter\s+\d+',
            r'^Section\s+\d+',
            r'^Unit\s+\d+',
            r'^Lesson\s+\d+',
            r'^\d+\.\s+[A-Z]',  # Numbered sections
            r'^[A-Z][a-z]+\s+[A-Z]',  # Title case sections
        ]
        
        self.subject_keywords = {
            'mathematics': ['algebra', 'geometry', 'arithmetic', 'calculus', 'statistics', 'trigonometry', 'equation', 'formula', 'solve'],
            'english': ['grammar', 'vocabulary', 'reading', 'writing', 'comprehension', 'literature', 'essay', 'poetry'],
            'science': ['biology', 'chemistry', 'physics', 'experiment', 'hypothesis', 'theory', 'molecule', 'atom', 'cell']
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {e}")
    
    def detect_subject(self, text: str) -> str:
        """Detect subject based on content keywords"""
        text_lower = text.lower()
        subject_scores = {}
        
        for subject, keywords in self.subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            subject_scores[subject] = score
        
        if subject_scores:
            return max(subject_scores, key=subject_scores.get)
        return "unknown"
    
    def detect_grade_level(self, text: str) -> Optional[int]:
        """Detect grade level from content"""
        # Look for grade indicators
        grade_patterns = [
            r'grade\s+(\d+)',
            r'class\s+(\d+)',
            r'form\s+(\d+)',
            r'year\s+(\d+)'
        ]
        
        for pattern in grade_patterns:
            match = re.search(pattern, text.lower())
            if match:
                grade = int(match.group(1))
                if 7 <= grade <= 12:
                    return grade
        
        return None
    
    def identify_sections(self, text: str) -> List[Dict[str, Any]]:
        """Identify major sections in the text"""
        lines = text.split('\n')
        sections = []
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if line matches section patterns
            is_section = any(re.match(pattern, line, re.IGNORECASE) for pattern in self.section_patterns)
            
            if is_section:
                # Save previous section
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line,
                    'content': '',
                    'line_start': i,
                    'line_end': i
                }
            elif current_section:
                current_section['content'] += line + '\n'
                current_section['line_end'] = i
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def smart_chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create smart chunks based on content structure"""
        sections = self.identify_sections(text)
        chunks = []
        
        if not sections:
            # Fallback to simple chunking
            return self._simple_chunk(text, max_chunk_size, overlap)
        
        for section in sections:
            content = section['content'].strip()
            if len(content) <= max_chunk_size:
                # Section fits in one chunk
                chunks.append({
                    'content': content,
                    'title': section['title'],
                    'chunk_type': 'section',
                    'metadata': {
                        'section_title': section['title'],
                        'line_range': (section['line_start'], section['line_end'])
                    }
                })
            else:
                # Split large section into smaller chunks
                section_chunks = self._chunk_section(content, section['title'], max_chunk_size, overlap)
                chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_section(self, content: str, title: str, max_chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Chunk a large section into smaller pieces"""
        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'title': title,
                        'chunk_type': 'paragraph',
                        'metadata': {
                            'section_title': title,
                            'paragraph_count': len(current_chunk.split('\n\n'))
                        }
                    })
                
                # Start new chunk with overlap
                if overlap > 0 and chunks:
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + paragraph + '\n\n'
                else:
                    current_chunk = paragraph + '\n\n'
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'title': title,
                'chunk_type': 'paragraph',
                'metadata': {
                    'section_title': title,
                    'paragraph_count': len(current_chunk.split('\n\n'))
                }
            })
        
        return chunks
    
    def _simple_chunk(self, text: str, max_chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Simple chunking fallback"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chunk_size:
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                if current_chunk:
                    chunks.append({
                        'content': ' '.join(current_chunk),
                        'title': 'Content Chunk',
                        'chunk_type': 'simple',
                        'metadata': {'word_count': len(current_chunk)}
                    })
                
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    overlap_words = current_chunk[-overlap//10:]  # Approximate word overlap
                    current_chunk = overlap_words + [word]
                    current_length = sum(len(w) + 1 for w in current_chunk)
                else:
                    current_chunk = [word]
                    current_length = len(word)
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': ' '.join(current_chunk),
                'title': 'Content Chunk',
                'chunk_type': 'simple',
                'metadata': {'word_count': len(current_chunk)}
            })
        
        return chunks
    
    def extract_metadata(self, text: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from the document"""
        metadata = {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'subject': self.detect_subject(text),
            'grade': self.detect_grade_level(text),
            'word_count': len(text.split()),
            'char_count': len(text),
            'sections_count': len(self.identify_sections(text))
        }
        
        return metadata
    
    def parse_curriculum_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to parse a curriculum PDF"""
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            # Extract metadata
            metadata = self.extract_metadata(text, pdf_path)
            
            # Create smart chunks
            chunks = self.smart_chunk_text(text)
            
            return {
                'metadata': metadata,
                'chunks': chunks,
                'full_text': text
            }
            
        except Exception as e:
            raise Exception(f"Error parsing PDF {pdf_path}: {e}")


# Example usage
if __name__ == "__main__":
    parser = CurriculumPDFParser()
    
    # Test with a sample PDF (replace with actual path)
    # result = parser.parse_curriculum_pdf("sample_curriculum.pdf")
    # print(json.dumps(result['metadata'], indent=2))

