"""
Embedding Generator for EPAS Documents
Creates vector embeddings for semantic search
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
from tqdm import tqdm


class EPASEmbedder:
    """Generate embeddings for EPAS document chunks"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedder
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding vector
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        logger.info(f"Generated embeddings shape: {embeddings.shape}")
        return embeddings
    
    def embed_chunks(self, chunks: List[Dict], batch_size: int = 32) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dictionaries
            batch_size: Batch size for processing
            
        Returns:
            Chunks with added 'embedding' field
        """
        logger.info(f"Embedding {len(chunks)} chunks...")
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts, batch_size=batch_size)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        logger.info(f"Successfully embedded {len(chunks)} chunks")
        return chunks
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a user query
        
        Args:
            query: User query string
            
        Returns:
            Embedding vector
        """
        return self.embed_text(query)
    
    def get_embedding_stats(self, embeddings: np.ndarray) -> Dict:
        """Get statistics about embeddings"""
        return {
            'count': len(embeddings),
            'dimension': embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
            'mean_norm': float(np.mean(np.linalg.norm(embeddings, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(embeddings, axis=1)))
        }


def embed_all_volumes(chunked_volumes: Dict[str, List[Dict]], 
                      model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                      batch_size: int = 32) -> Dict[str, List[Dict]]:
    """
    Embed all chunks from all volumes
    
    Args:
        chunked_volumes: Dictionary mapping volume to chunks
        model_name: Embedding model name
        batch_size: Batch size for embedding
        
    Returns:
        Dictionary with embedded chunks
    """
    embedder = EPASEmbedder(model_name=model_name)
    
    embedded_volumes = {}
    total_embedded = 0
    
    for volume, chunks in chunked_volumes.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Embedding Volume {volume}")
        logger.info(f"{'='*60}")
        
        embedded_chunks = embedder.embed_chunks(chunks, batch_size=batch_size)
        embedded_volumes[volume] = embedded_chunks
        total_embedded += len(embedded_chunks)
        
        # Statistics
        embeddings = np.array([c['embedding'] for c in embedded_chunks])
        stats = embedder.get_embedding_stats(embeddings)
        logger.info(f"Volume {volume} embedding stats:")
        logger.info(f"  - Count: {stats['count']}")
        logger.info(f"  - Dimension: {stats['dimension']}")
        logger.info(f"  - Mean norm: {stats['mean_norm']:.3f}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Total chunks embedded: {total_embedded}")
    logger.info(f"{'='*60}")
    
    return embedded_volumes


def save_embeddings(embedded_volumes: Dict[str, List[Dict]], output_dir: str):
    """
    Save embeddings to disk (for later loading)
    
    Args:
        embedded_volumes: Dictionary with embedded chunks
        output_dir: Directory to save embeddings
    """
    import json
    import pickle
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for volume, chunks in embedded_volumes.items():
        logger.info(f"Saving Volume {volume} embeddings...")
        
        # Save as pickle (includes numpy arrays)
        pickle_path = output_path / f"volume_{volume}_embedded.pkl"
        with open(pickle_path, 'wb') as f:
            pickle.dump(chunks, f)
        
        # Also save metadata as JSON (for inspection)
        metadata_chunks = []
        for chunk in chunks:
            metadata_chunk = {
                'chunk_id': chunk['chunk_id'],
                'text_preview': chunk['text'][:200],
                'metadata': chunk['metadata'],
                'token_count': chunk['token_count']
            }
            metadata_chunks.append(metadata_chunk)
        
        json_path = output_path / f"volume_{volume}_metadata.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  - Saved: {pickle_path}")
        logger.info(f"  - Metadata: {json_path}")


def load_embeddings(volume: str, embeddings_dir: str) -> List[Dict]:
    """
    Load embeddings from disk
    
    Args:
        volume: Volume identifier (I, II, III)
        embeddings_dir: Directory containing saved embeddings
        
    Returns:
        List of chunks with embeddings
    """
    import pickle
    from pathlib import Path
    
    pickle_path = Path(embeddings_dir) / f"volume_{volume}_embedded.pkl"
    
    if not pickle_path.exists():
        raise FileNotFoundError(f"Embeddings not found: {pickle_path}")
    
    logger.info(f"Loading embeddings from: {pickle_path}")
    
    with open(pickle_path, 'rb') as f:
        chunks = pickle.load(f)
    
    logger.info(f"Loaded {len(chunks)} chunks for Volume {volume}")
    return chunks


if __name__ == "__main__":
    # Test embedder
    logger.add("embedder.log", rotation="10 MB")
    
    # Test with sample chunks
    sample_chunks = [
        {
            'text': "The operator shall ensure compliance with aviation safety regulations.",
            'chunk_id': 'test_chunk_1',
            'metadata': {'volume': 'I', 'page': 1},
            'token_count': 12
        },
        {
            'text': "Safety risk assessment must be conducted before operations.",
            'chunk_id': 'test_chunk_2',
            'metadata': {'volume': 'III', 'page': 50},
            'token_count': 10
        }
    ]
    
    embedder = EPASEmbedder()
    embedded_chunks = embedder.embed_chunks(sample_chunks, batch_size=2)
    
    print(f"\nEmbedded {len(embedded_chunks)} chunks")
    print(f"Embedding dimension: {embedder.embedding_dim}")
    print(f"\nFirst chunk embedding shape: {embedded_chunks[0]['embedding'].shape}")
    print(f"First 10 values: {embedded_chunks[0]['embedding'][:10]}")
