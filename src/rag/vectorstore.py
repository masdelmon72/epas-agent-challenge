"""
FAISS Vector Store for EPAS Documents
Manages vector storage and similarity search
"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger


class EPASVectorStore:
    """FAISS-based vector store for EPAS documents"""
    
    def __init__(self, embedding_dim: int = 384):
        """
        Initialize vector store
        
        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks = []
        self.chunk_id_to_idx = {}
        
        logger.info(f"Initialized vector store with dimension: {embedding_dim}")
    
    def create_index(self, chunks: List[Dict]):
        """
        Create FAISS index from chunks
        
        Args:
            chunks: List of chunks with embeddings
        """
        logger.info(f"Creating FAISS index for {len(chunks)} chunks...")
        
        # Extract embeddings
        embeddings = np.array([chunk['embedding'] for chunk in chunks]).astype('float32')
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create index (IndexFlatIP for inner product = cosine similarity)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Add vectors to index
        self.index.add(embeddings)
        
        # Store chunks
        self.chunks = chunks
        
        # Create chunk_id to index mapping
        self.chunk_id_to_idx = {
            chunk['chunk_id']: idx 
            for idx, chunk in enumerate(chunks)
        }
        
        logger.info(f"Index created with {self.index.ntotal} vectors")
    
    def search(self, 
               query_embedding: np.ndarray, 
               k: int = 10,
               filter_metadata: Optional[Dict] = None) -> List[Tuple[Dict, float]]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {'volume': 'I'})
            
        Returns:
            List of (chunk, score) tuples
        """
        if self.index is None:
            raise ValueError("Index not created. Call create_index() first.")
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        if filter_metadata is None:
            # Search all
            scores, indices = self.index.search(query_embedding, k)
        else:
            # Filter and search
            filtered_indices = self._filter_chunks(filter_metadata)
            
            if not filtered_indices:
                logger.warning(f"No chunks match filter: {filter_metadata}")
                return []
            
            # Search only filtered indices
            k_search = min(k * 3, len(filtered_indices))  # Search more to account for filtering
            scores, indices = self.index.search(query_embedding, k_search)
            
            # Keep only filtered results
            mask = np.isin(indices[0], filtered_indices)
            scores = scores[0][mask]
            indices = indices[0][mask]
            
            # Limit to k results
            if len(indices) > k:
                scores = scores[:k]
                indices = indices[:k]
            else:
                scores = scores
                indices = indices
        
        # Prepare results
        results = []
        for idx, score in zip(indices[0] if filter_metadata is None else indices, 
                             scores[0] if filter_metadata is None else scores):
            if idx < len(self.chunks):  # Validate index
                chunk = self.chunks[idx]
                results.append((chunk, float(score)))
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def _filter_chunks(self, filter_metadata: Dict) -> List[int]:
        """
        Get indices of chunks matching metadata filter
        
        Args:
            filter_metadata: Metadata to filter by
            
        Returns:
            List of matching chunk indices
        """
        matching_indices = []
        
        for idx, chunk in enumerate(self.chunks):
            chunk_metadata = chunk.get('metadata', {})
            
            # Check if all filter criteria match
            match = True
            for key, value in filter_metadata.items():
                if chunk_metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                matching_indices.append(idx)
        
        return matching_indices
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """Get chunk by its ID"""
        idx = self.chunk_id_to_idx.get(chunk_id)
        if idx is not None:
            return self.chunks[idx]
        return None
    
    def save(self, directory: str):
        """
        Save vector store to disk
        
        Args:
            directory: Directory to save files
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving vector store to {directory}")
        
        # Save FAISS index
        index_path = dir_path / "faiss_index.bin"
        faiss.write_index(self.index, str(index_path))
        logger.info(f"  - Saved index: {index_path}")
        
        # Save chunks (without embeddings to save space)
        chunks_no_embedding = []
        for chunk in self.chunks:
            chunk_copy = chunk.copy()
            if 'embedding' in chunk_copy:
                del chunk_copy['embedding']
            chunks_no_embedding.append(chunk_copy)
        
        chunks_path = dir_path / "chunks.pkl"
        with open(chunks_path, 'wb') as f:
            pickle.dump(chunks_no_embedding, f)
        logger.info(f"  - Saved chunks: {chunks_path}")
        
        # Save metadata
        metadata = {
            'embedding_dim': self.embedding_dim,
            'num_chunks': len(self.chunks),
            'chunk_id_to_idx': self.chunk_id_to_idx
        }
        metadata_path = dir_path / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        logger.info(f"  - Saved metadata: {metadata_path}")
        
        logger.info("Vector store saved successfully")
    
    @classmethod
    def load(cls, directory: str) -> 'EPASVectorStore':
        """
        Load vector store from disk
        
        Args:
            directory: Directory containing saved files
            
        Returns:
            Loaded EPASVectorStore instance
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        logger.info(f"Loading vector store from {directory}")
        
        # Load metadata
        metadata_path = dir_path / "metadata.pkl"
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Create instance
        store = cls(embedding_dim=metadata['embedding_dim'])
        
        # Load FAISS index
        index_path = dir_path / "faiss_index.bin"
        store.index = faiss.read_index(str(index_path))
        logger.info(f"  - Loaded index: {store.index.ntotal} vectors")
        
        # Load chunks
        chunks_path = dir_path / "chunks.pkl"
        with open(chunks_path, 'rb') as f:
            store.chunks = pickle.load(f)
        logger.info(f"  - Loaded {len(store.chunks)} chunks")
        
        # Restore mapping
        store.chunk_id_to_idx = metadata['chunk_id_to_idx']
        
        logger.info("Vector store loaded successfully")
        return store
    
    def get_statistics(self) -> Dict:
        """Get statistics about the vector store"""
        if not self.chunks:
            return {}
        
        volumes = {}
        for chunk in self.chunks:
            vol = chunk.get('metadata', {}).get('volume', 'unknown')
            volumes[vol] = volumes.get(vol, 0) + 1
        
        return {
            'total_chunks': len(self.chunks),
            'embedding_dim': self.embedding_dim,
            'index_size': self.index.ntotal if self.index else 0,
            'volumes': volumes
        }


def create_vectorstore_from_embeddings(
    embedded_volumes: Dict[str, List[Dict]],
    embedding_dim: int = 384
) -> EPASVectorStore:
    """
    Create vector store from embedded volumes
    
    Args:
        embedded_volumes: Dictionary mapping volume to embedded chunks
        embedding_dim: Embedding dimension
        
    Returns:
        Created EPASVectorStore
    """
    logger.info("\n" + "="*60)
    logger.info("Creating Vector Store")
    logger.info("="*60)
    
    # Combine all chunks
    all_chunks = []
    for volume, chunks in embedded_volumes.items():
        logger.info(f"Adding {len(chunks)} chunks from Volume {volume}")
        all_chunks.extend(chunks)
    
    logger.info(f"Total chunks: {len(all_chunks)}")
    
    # Create vector store
    store = EPASVectorStore(embedding_dim=embedding_dim)
    store.create_index(all_chunks)
    
    # Print statistics
    stats = store.get_statistics()
    logger.info("\nVector Store Statistics:")
    logger.info(f"  - Total chunks: {stats['total_chunks']}")
    logger.info(f"  - Embedding dimension: {stats['embedding_dim']}")
    logger.info(f"  - Volumes:")
    for vol, count in stats['volumes'].items():
        logger.info(f"    • Volume {vol}: {count} chunks")
    
    logger.info("="*60)
    
    return store


if __name__ == "__main__":
    # Test vector store
    logger.add("vectorstore.log", rotation="10 MB")
    
    # Create sample data
    np.random.seed(42)
    sample_chunks = []
    
    for i in range(100):
        chunk = {
            'text': f"Sample chunk {i}",
            'chunk_id': f"chunk_{i}",
            'metadata': {
                'volume': ['I', 'II', 'III'][i % 3],
                'page': i + 1
            },
            'embedding': np.random.randn(384).astype('float32'),
            'token_count': 50 + i
        }
        sample_chunks.append(chunk)
    
    # Create vector store
    store = EPASVectorStore(embedding_dim=384)
    store.create_index(sample_chunks)
    
    # Test search
    query_embedding = np.random.randn(384).astype('float32')
    results = store.search(query_embedding, k=5)
    
    print(f"\nSearch results:")
    for chunk, score in results:
        print(f"  - Chunk: {chunk['chunk_id']}, Score: {score:.3f}, Volume: {chunk['metadata']['volume']}")
    
    # Test filtered search
    print(f"\nFiltered search (Volume I only):")
    results = store.search(query_embedding, k=5, filter_metadata={'volume': 'I'})
    for chunk, score in results:
        print(f"  - Chunk: {chunk['chunk_id']}, Score: {score:.3f}, Volume: {chunk['metadata']['volume']}")
    
    # Test save/load
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        store.save(tmpdir)
        loaded_store = EPASVectorStore.load(tmpdir)
        print(f"\nLoaded store statistics: {loaded_store.get_statistics()}")
