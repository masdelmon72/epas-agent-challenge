"""
Intelligent Text Chunker for EPAS Documents
Creates semantic chunks suitable for RAG
"""

import re
import tiktoken
from typing import List, Dict
from loguru import logger


class EPASChunker:
    """Intelligent chunker for EPAS documents"""
    
    def __init__(self, 
                 chunk_size: int = 500,
                 chunk_overlap: int = 50,
                 encoding_name: str = "cl100k_base"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        logger.info(f"Chunker initialized: size={chunk_size}, overlap={chunk_overlap}")
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text or ""))  # protezione testo None
    
    def chunk_section(self, section: Dict) -> List[Dict]:
        """Chunk a single section in a robust way"""
        text = section.get('text', '') or ""
        metadata = {k: v for k, v in section.items() if k != 'text'}
        
        # Sezione vuota -> restituisci chunk vuoto con chunk_id
        if not text.strip():
            chunk_dict = {
                'text': '',
                'metadata': {**metadata, 'chunk_index': 0, 'total_chunks': 1},
                'token_count': 0,
                'chunk_id': self._generate_chunk_id(metadata, 0)
            }
            return [chunk_dict]
        
        # Split in paragrafi
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            if para_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                sentences = self._split_into_sentences(para)
                sub_chunk = []
                sub_tokens = 0
                for sent in sentences:
                    sent_tokens = self.count_tokens(sent)
                    if sub_tokens + sent_tokens > self.chunk_size:
                        if sub_chunk:
                            chunks.append(' '.join(sub_chunk))
                        sub_chunk = [sent]
                        sub_tokens = sent_tokens
                    else:
                        sub_chunk.append(sent)
                        sub_tokens += sent_tokens
                if sub_chunk:
                    chunks.append(' '.join(sub_chunk))
            elif current_tokens + para_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_tokens = self.count_tokens(current_chunk[0]) if current_chunk else 0
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        # Crea dizionari chunk con chunk_id garantito
        chunk_dicts = []
        for idx, chunk_text in enumerate(chunks):
            chunk_dict = {
                'text': chunk_text,
                'metadata': {**metadata, 'chunk_index': idx, 'total_chunks': len(chunks)},
                'token_count': self.count_tokens(chunk_text),
                'chunk_id': self._generate_chunk_id(metadata, idx)
            }
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _generate_chunk_id(self, metadata: Dict, chunk_index: int) -> str:
        volume = metadata.get('volume', 'unknown')
        section_id = metadata.get('section_id', 'unknown')
        page = metadata.get('start_page', 0)
        clean_section_id = re.sub(r'[^\w.-]', '_', section_id)
        return f"vol{volume}_sec{clean_section_id}_p{page}_c{chunk_index}"
    
    def chunk_all_sections(self, sections: List[Dict]) -> List[Dict]:
        """Chunk all sections robustly"""
        all_chunks = []
        for section in sections:
            try:
                all_chunks.extend(self.chunk_section(section))
            except Exception as e:
                logger.error(f"Failed to chunk section {section.get('section_id', 'unknown')}: {e}")
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {}
        token_counts = [c['token_count'] for c in chunks]
        return {
            'total_chunks': len(chunks),
            'total_tokens': sum(token_counts),
            'avg_tokens': sum(token_counts)/len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'volumes': len(set(c['metadata']['volume'] for c in chunks))
        }


def chunk_all_volumes(all_volumes: Dict[str, List[Dict]], 
                      chunk_size: int = 500,
                      chunk_overlap: int = 50) -> Dict[str, List[Dict]]:
    """Chunk all volumes in a robust way"""
    chunker = EPASChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunked_volumes = {}
    for volume, sections in all_volumes.items():
        if not sections:
            logger.warning(f"Volume {volume} is empty")
            chunked_volumes[volume] = []
            continue
        try:
            chunks = chunker.chunk_all_sections(sections)
            chunked_volumes[volume] = chunks
        except Exception as e:
            logger.error(f"Failed to chunk volume {volume}: {e}")
            chunked_volumes[volume] = []
    return chunked_volumes


# Solo test locale, non viene eseguito se importato
if __name__ == "__main__":
    logger.add("chunker_test.log", rotation="10 MB")
    print("EPASChunker module ready. Run tests from separate script.")
