"""
RAG Retriever for EPAS Documents
Integrates FAISS vector store with LangChain
"""
from typing import List, Dict, Optional
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from loguru import logger
import numpy as np


class EPASRetriever(BaseRetriever):
    """Custom LangChain retriever for EPAS documents"""
    
    vectorstore: object  # EPASVectorStore
    embedder: object  # EPASEmbedder
    k: int = 10
    score_threshold: float = 0.7
    filter_metadata: Optional[Dict] = None
    
    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query string
            run_manager: Callback manager
            
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"Retrieving documents for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search vector store
        results = self.vectorstore.search(
            query_embedding=query_embedding,
            k=self.k,
            filter_metadata=self.filter_metadata
        )
        
        # Filter by score threshold
        filtered_results = [
            (chunk, score) for chunk, score in results 
            if score >= self.score_threshold
        ]
        
        logger.info(f"Found {len(filtered_results)} documents above threshold {self.score_threshold}")
        
        # Convert to LangChain Documents
        documents = []
        for chunk, score in filtered_results:
            # Prepare metadata
            metadata = chunk.get('metadata', {}).copy()
            metadata['score'] = score
            metadata['chunk_id'] = chunk['chunk_id']
            
            # Create Document
            doc = Document(
                page_content=chunk['text'],
                metadata=metadata
            )
            documents.append(doc)
        
        return documents
    
    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Async version of retrieval (delegates to sync for now)"""
        return self._get_relevant_documents(query, run_manager=run_manager)


class EPASContextualRetriever:
    """Enhanced retriever with reranking and context building"""
    
    def __init__(self, 
                 vectorstore,
                 embedder,
                 k: int = 10,
                 score_threshold: float = 0.7):
        """
        Initialize contextual retriever
        
        Args:
            vectorstore: EPASVectorStore instance
            embedder: EPASEmbedder instance
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score
        """
        self.vectorstore = vectorstore
        self.embedder = embedder
        self.k = k
        self.score_threshold = score_threshold
    
    def retrieve(self, 
                 query: str, 
                 volume_filter: Optional[str] = None,
                 include_context: bool = True) -> Dict:
        """
        Retrieve documents with enhanced context
        
        Args:
            query: User query
            volume_filter: Optional volume filter (I, II, III)
            include_context: Whether to include surrounding context
            
        Returns:
            Dictionary with results and metadata
        """
        logger.info(f"Contextual retrieval for: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Prepare filter
        filter_metadata = {'volume': volume_filter} if volume_filter else None
        
        # Search
        results = self.vectorstore.search(
            query_embedding=query_embedding,
            k=self.k * 2,  # Get more for reranking
            filter_metadata=filter_metadata
        )
        
        # Filter by threshold
        filtered_results = [
            (chunk, score) for chunk, score in results 
            if score >= self.score_threshold
        ][:self.k]  # Limit to k after filtering
        
        # Build contextual results
        contextual_results = []
        for chunk, score in filtered_results:
            result = {
                'chunk': chunk,
                'score': score,
                'metadata': chunk.get('metadata', {}),
                'text': chunk['text']
            }
            
            # Add surrounding context if requested
            if include_context:
                context = self._get_surrounding_context(chunk)
                if context:
                    result['context'] = context
            
            # Add cross-references
            result['cross_references'] = self._find_cross_references(chunk)
            
            contextual_results.append(result)
        
        # Prepare response
        response = {
            'query': query,
            'results': contextual_results,
            'total_results': len(contextual_results),
            'volume_filter': volume_filter,
            'retrieval_metadata': {
                'k': self.k,
                'score_threshold': self.score_threshold,
                'highest_score': filtered_results[0][1] if filtered_results else 0,
                'lowest_score': filtered_results[-1][1] if filtered_results else 0
            }
        }
        
        logger.info(f"Retrieved {len(contextual_results)} contextual results")
        
        return response
    
    def _get_surrounding_context(self, chunk: Dict) -> Optional[Dict]:
        """
        Get surrounding chunks for context
        
        Args:
            chunk: Current chunk
            
        Returns:
            Dictionary with previous and next chunks
        """
        metadata = chunk.get('metadata', {})
        chunk_index = metadata.get('chunk_index', 0)
        total_chunks = metadata.get('total_chunks', 1)
        
        context = {}
        
        # Get previous chunk if exists
        if chunk_index > 0:
            # Find previous chunk with same section
            prev_chunk_id = chunk['chunk_id'].rsplit('_c', 1)[0] + f"_c{chunk_index - 1}"
            prev_chunk = self.vectorstore.get_chunk_by_id(prev_chunk_id)
            if prev_chunk:
                context['previous'] = prev_chunk['text']
        
        # Get next chunk if exists
        if chunk_index < total_chunks - 1:
            next_chunk_id = chunk['chunk_id'].rsplit('_c', 1)[0] + f"_c{chunk_index + 1}"
            next_chunk = self.vectorstore.get_chunk_by_id(next_chunk_id)
            if next_chunk:
                context['next'] = next_chunk['text']
        
        return context if context else None
    
    def _find_cross_references(self, chunk: Dict) -> List[str]:
        """
        Find cross-references to other volumes
        
        Args:
            chunk: Current chunk
            
        Returns:
            List of related sections in other volumes
        """
        # Simple implementation: look for section references in text
        import re
        
        text = chunk['text']
        metadata = chunk.get('metadata', {})
        current_volume = metadata.get('volume')
        
        cross_refs = []
        
        # Pattern for section references
        patterns = [
            r'(Volume [I]+)',
            r'(Vol\. [I]+)',
            r'(see (?:also )?(?:Volume |Vol\. )?([I]+))',
            r'([A-Z]{2,4}\.[\w.]+)',  # Section IDs
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                ref = match if isinstance(match, str) else match[0]
                if ref and ref not in cross_refs:
                    cross_refs.append(ref)
        
        # Filter out current volume references
        cross_refs = [ref for ref in cross_refs if current_volume not in ref]
        
        return cross_refs[:5]  # Limit to 5 references
    
    def format_results_for_llm(self, retrieval_response: Dict) -> str:
        """
        Format retrieval results for LLM context
        
        Args:
            retrieval_response: Response from retrieve()
            
        Returns:
            Formatted string for LLM
        """
        results = retrieval_response['results']
        
        if not results:
            return "No relevant documents found in the EPAS knowledge base."
        
        formatted = "# Retrieved EPAS Documents\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            
            formatted += f"## Document {i}\n"
            formatted += f"**Source**: Volume {metadata.get('volume', 'N/A')}"
            
            if 'section_id' in metadata:
                formatted += f", Section {metadata['section_id']}"
            if 'start_page' in metadata:
                formatted += f", Page {metadata['start_page']}"
            
            formatted += f"\n**Relevance Score**: {result['score']:.3f}\n\n"
            
            if 'section_title' in metadata and metadata['section_title']:
                formatted += f"**Section**: {metadata['section_title']}\n\n"
            
            formatted += f"**Content**:\n{result['text']}\n\n"
            
            if result.get('cross_references'):
                formatted += f"**Cross-references**: {', '.join(result['cross_references'])}\n\n"
            
            formatted += "---\n\n"
        
        return formatted


if __name__ == "__main__":
    # Test retriever
    from src.rag.vectorstore import EPASVectorStore
    from src.data_processing.embedder import EPASEmbedder
    import numpy as np
    
    logger.add("retriever.log", rotation="10 MB")
    
    # Create mock vectorstore and embedder
    embedder = EPASEmbedder()
    
    # Create sample chunks
    sample_chunks = []
    for i in range(50):
        chunk = {
            'text': f"Sample aviation safety regulation {i} about operational procedures.",
            'chunk_id': f"vol{['I','II','III'][i%3]}_sec{i}_p{i}_c0",
            'metadata': {
                'volume': ['I', 'II', 'III'][i % 3],
                'section_id': f'CAT.GEN.{i}',
                'start_page': i + 1
            },
            'embedding': embedder.embed_text(f"Aviation safety regulation {i}"),
            'token_count': 20
        }
        sample_chunks.append(chunk)
    
    vectorstore = EPASVectorStore(embedding_dim=384)
    vectorstore.create_index(sample_chunks)
    
    # Test contextual retriever
    retriever = EPASContextualRetriever(
        vectorstore=vectorstore,
        embedder=embedder,
        k=5,
        score_threshold=0.5
    )
    
    query = "What are the operational safety procedures?"
    response = retriever.retrieve(query, include_context=True)
    
    print(f"\nQuery: {query}")
    print(f"Results: {response['total_results']}")
    print(f"\nFormatted for LLM:")
    print(retriever.format_results_for_llm(response)[:500] + "...")
