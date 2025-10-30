"""
PDF Loader for EPAS Documents
Extracts text from PDF while preserving structure and metadata
"""
import re
from pathlib import Path
from typing import List, Dict, Optional
from pypdf import PdfReader
from loguru import logger
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""
    text: str
    metadata: Dict
    chunk_id: str


class EPASPDFLoader:
    """Loads and processes EPAS PDF documents"""
    
    def __init__(self, volume: str, volume_info: Dict):
        """
        Initialize PDF loader for specific volume
        
        Args:
            volume: Volume identifier (I, II, III)
            volume_info: Dictionary with volume metadata
        """
        self.volume = volume
        self.volume_info = volume_info
        self.volume_title = volume_info["title"]
        self.document_type = volume_info["type"]
    
    def load_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Load PDF and extract text with metadata
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dictionaries with text and metadata per page
        """
        logger.info(f"Loading PDF: {pdf_path}")
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            reader = PdfReader(str(pdf_path))
            pages = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                
                if text.strip():  # Skip empty pages
                    pages.append({
                        "text": text,
                        "page_number": page_num,
                        "volume": self.volume,
                        "volume_title": self.volume_title,
                        "document_type": self.document_type
                    })
            
            logger.info(f"Extracted {len(pages)} pages from Volume {self.volume}")
            return pages
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
            raise
    
    def extract_sections(self, pages: List[Dict]) -> List[Dict]:
        """
        Extract sections from pages based on EASA document structure
        
        Args:
            pages: List of page dictionaries
            
        Returns:
            List of section dictionaries with enhanced metadata
        """
        sections = []
        current_section = None
        current_text = []
        
        # Patterns for EASA section headers
        section_patterns = [
            r'^([A-Z]{2,4}[\d.]+)\s+(.+?)$',  # e.g., "CAT.GEN.MPA.210 Title"
            r'^(AMC\d*|GM\d*)\s+([A-Z]{2,4}[\d.]+)',  # e.g., "AMC1 CAT.GEN.MPA.210"
            r'^SUBPART\s+([A-Z])\s*[-–]\s*(.+?)$',  # e.g., "SUBPART A - GENERAL"
            r'^CHAPTER\s+(\d+)\s*[-–]\s*(.+?)$',  # e.g., "CHAPTER 1 - SCOPE"
            r'^(\d+\.[\d.]+)\s+(.+?)$',  # e.g., "1.2.3 Title"
        ]
        
        for page in pages:
            text = page["text"]
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line is a section header
                is_section_header = False
                section_id = None
                section_title = None
                
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        is_section_header = True
                        section_id = match.group(1)
                        section_title = match.group(2) if len(match.groups()) > 1 else ""
                        break
                
                if is_section_header:
                    # Save previous section
                    if current_section and current_text:
                        sections.append({
                            **current_section,
                            "text": '\n'.join(current_text),
                            "char_count": len('\n'.join(current_text))
                        })
                    
                    # Start new section
                    current_section = {
                        "section_id": section_id,
                        "section_title": section_title,
                        "start_page": page["page_number"],
                        "volume": page["volume"],
                        "volume_title": page["volume_title"],
                        "document_type": page["document_type"]
                    }
                    current_text = [line]
                else:
                    # Add line to current section
                    if current_section:
                        current_text.append(line)
        
        # Add last section
        if current_section and current_text:
            sections.append({
                **current_section,
                "text": '\n'.join(current_text),
                "char_count": len('\n'.join(current_text))
            })
        
        logger.info(f"Extracted {len(sections)} sections from Volume {self.volume}")
        return sections
    
    def detect_priority_level(self, text: str) -> Optional[str]:
        """
        Detect priority level from text (for Volume II and III)
        
        Args:
            text: Text to analyze
            
        Returns:
            Priority level: 'strategic', 'operational', or None
        """
        text_lower = text.lower()
        
        strategic_keywords = [
            'strategic priority',
            'strategic objective',
            'key safety issue',
            'critical safety'
        ]
        
        operational_keywords = [
            'operational objective',
            'safety action',
            'implementation',
            'mitigation'
        ]
        
        for keyword in strategic_keywords:
            if keyword in text_lower:
                return 'strategic'
        
        for keyword in operational_keywords:
            if keyword in text_lower:
                return 'operational'
        
        return None
    
    def enrich_metadata(self, sections: List[Dict]) -> List[Dict]:
        """
        Enrich sections with additional metadata
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Sections with enriched metadata
        """
        for section in sections:
            # Detect priority level
            section['priority_level'] = self.detect_priority_level(section['text'])
            
            # Extract keywords (simple frequency-based)
            section['keywords'] = self._extract_keywords(section['text'])
            
            # Add searchable text (cleaned)
            section['searchable_text'] = self._clean_text(section['text'])
        
        return sections
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text"""
        # Simple keyword extraction (frequency-based)
        # In production, use more sophisticated NLP
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        
        # Filter common words
        stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 
                     'will', 'shall', 'would', 'should', 'could', 'their',
                     'which', 'where', 'when', 'what', 'such', 'these'}
        
        words = [w for w in words if w not in stop_words]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(words)
        
        return [word for word, _ in word_freq.most_common(top_n)]
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better searching"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:()\-]', '', text)
        return text.strip()


def load_all_volumes(settings) -> Dict[str, List[Dict]]:
    """
    Load all EPAS volumes
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary mapping volume to list of sections
    """
    all_volumes = {}
    
    for volume, volume_info in settings.volumes.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Volume {volume}")
        logger.info(f"{'='*60}")
        
        pdf_path = settings.get_pdf_path(volume)
        
        loader = EPASPDFLoader(volume, volume_info)
        
        # Load PDF
        pages = loader.load_pdf(pdf_path)
        
        # Extract sections
        sections = loader.extract_sections(pages)
        
        # Enrich metadata
        sections = loader.enrich_metadata(sections)
        
        all_volumes[volume] = sections
        
        logger.info(f"Volume {volume} processed: {len(sections)} sections")
    
    return all_volumes


if __name__ == "__main__":
    # Test the loader
    from src.config.settings import settings
    
    logger.add("pdf_loader.log", rotation="10 MB")
    
    # Test loading one volume
    volume = "I"
    volume_info = settings.volumes[volume]
    pdf_path = settings.get_pdf_path(volume)
    
    loader = EPASPDFLoader(volume, volume_info)
    pages = loader.load_pdf(pdf_path)
    sections = loader.extract_sections(pages)
    sections = loader.enrich_metadata(sections)
    
    print(f"\nLoaded {len(sections)} sections")
    print(f"\nFirst section:")
    print(f"ID: {sections[0].get('section_id', 'N/A')}")
    print(f"Title: {sections[0].get('section_title', 'N/A')}")
    print(f"Page: {sections[0].get('start_page', 'N/A')}")
    print(f"Text preview: {sections[0]['text'][:200]}...")
