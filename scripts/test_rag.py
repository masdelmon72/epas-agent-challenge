#!/usr/bin/env python3
"""
Test RAG System
Interactive testing of the EPAS RAG system
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.config.settings import settings
from src.rag.vectorstore import EPASVectorStore
from src.data_processing.embedder import EPASEmbedder
from src.rag.retriever import EPASContextualRetriever
from src.rag.chain import EPASRAGChain


def load_rag_system():
    """Load the RAG system components"""
    logger.info("Loading RAG system...")
    
    # Load vector store
    logger.info(f"Loading vector store from {settings.vectorstore_dir}")
    vectorstore = EPASVectorStore.load(str(settings.vectorstore_dir))
    
    # Load embedder
    logger.info(f"Loading embedding model: {settings.embedding_model}")
    embedder = EPASEmbedder(model_name=settings.embedding_model)
    
    # Create retriever
    retriever = EPASContextualRetriever(
        vectorstore=vectorstore,
        embedder=embedder,
        k=settings.top_k_results,
        score_threshold=settings.similarity_threshold
    )
    
    # Create RAG chain
    rag_chain = EPASRAGChain(
        retriever=retriever,
        llm_model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens
    )
    
    logger.info("✓ RAG system loaded successfully\n")
    
    return rag_chain, retriever, vectorstore


def test_retrieval_only(retriever):
    """Test retrieval without LLM generation"""
    print("\n" + "="*80)
    print("TEST 1: Retrieval Only (without LLM)")
    print("="*80)
    
    test_queries = [
        "What are the strategic priorities in EPAS?",
        "Tell me about safety management systems",
        "What are the main safety risks?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        
        response = retriever.retrieve(query, include_context=False)
        
        print(f"Results found: {response['total_results']}")
        
        if response['results']:
            for i, result in enumerate(response['results'][:3], 1):
                metadata = result['metadata']
                print(f"\n{i}. Volume {metadata.get('volume')}, " + 
                      f"Score: {result['score']:.3f}")
                if 'section_id' in metadata:
                    print(f"   Section: {metadata['section_id']}")
                print(f"   Text: {result['text'][:150]}...")
        
        print()


def test_full_rag(rag_chain):
    """Test full RAG with LLM generation"""
    print("\n" + "="*80)
    print("TEST 2: Full RAG (with LLM Generation)")
    print("="*80)
    
    test_queries = [
        "What are the main strategic priorities in the European Plan for Aviation Safety?",
        "Explain the safety management system requirements for operators",
        "What safety actions are recommended for runway safety?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("=" * 80)
        
        result = rag_chain.query(query)
        
        print(f"\nAnswer:")
        print(result['answer'])
        
        print(f"\nSources: {len(result['sources'])}")
        print(f"Confidence: {result['confidence']:.1%}")
        
        if result['sources']:
            print("\nTop Sources:")
            for i, source in enumerate(result['sources'][:2], 1):
                print(f"{i}. Vol {source['volume']}, {source['section_id']}, " +
                      f"Page {source['page']} (Score: {source['relevance_score']:.3f})")
        
        print("\n" + "-"*80)


def interactive_mode(rag_chain):
    """Interactive testing mode"""
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("Ask questions about EPAS. Type 'quit' to exit.")
    print("Commands:")
    print("  - vol:<I|II|III> <question> - Filter by volume")
    print("  - html <question> - Get HTML formatted response")
    print("  - quit - Exit")
    print("="*80 + "\n")
    
    while True:
        try:
            user_input = input("\n💬 Your question: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Parse commands
            volume_filter = None
            html_format = False
            
            if user_input.lower().startswith('vol:'):
                parts = user_input.split(' ', 1)
                volume_filter = parts[0].split(':')[1].upper()
                user_input = parts[1] if len(parts) > 1 else ""
                print(f"🔍 Filtering by Volume {volume_filter}")
            
            if user_input.lower().startswith('html'):
                html_format = True
                user_input = user_input[4:].strip()
            
            if not user_input:
                print("Please provide a question")
                continue
            
            # Process query
            print("\n⏳ Processing...")
            
            result = rag_chain.query(user_input, volume_filter=volume_filter)
            
            if html_format:
                html = rag_chain.format_html_response(result)
                # Save to file
                output_file = Path("last_response.html")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"\n✓ HTML response saved to: {output_file}")
                print("\nAnswer (text):")
                print(result['answer'])
            else:
                print("\n📝 Answer:")
                print(result['answer'])
            
            print(f"\n📊 Confidence: {result['confidence']:.1%}")
            print(f"📚 Sources: {len(result['sources'])}")
            
            if result['sources']:
                print("\nTop 3 Sources:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"  {i}. Vol {source['volume']}, {source['section_id']}, " +
                          f"p.{source['page']} (Score: {source['relevance_score']:.3f})")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit properly.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Error in interactive mode:")


def print_statistics(vectorstore):
    """Print vector store statistics"""
    print("\n" + "="*80)
    print("VECTOR STORE STATISTICS")
    print("="*80)
    
    stats = vectorstore.get_statistics()
    
    print(f"Total chunks: {stats['total_chunks']:,}")
    print(f"Embedding dimension: {stats['embedding_dim']}")
    print(f"Index size: {stats['index_size']:,} vectors")
    print("\nChunks per volume:")
    for volume, count in stats['volumes'].items():
        print(f"  - Volume {volume}: {count:,} chunks")
    print("="*80)


def main():
    """Main test function"""
    logger.add("test_rag.log", rotation="10 MB", level="INFO")
    
    print("\n" + "="*80)
    print("EPAS RAG SYSTEM - Testing Suite")
    print("="*80)
    
    try:
        # Load system
        rag_chain, retriever, vectorstore = load_rag_system()
        
        # Print statistics
        print_statistics(vectorstore)
        
        # Run tests
        print("\nSelect test mode:")
        print("1. Retrieval Only Test")
        print("2. Full RAG Test")
        print("3. Interactive Mode")
        print("4. All Tests + Interactive")
        
        choice = input("\nEnter choice (1-4) [default: 3]: ").strip() or "3"
        
        if choice == "1":
            test_retrieval_only(retriever)
        elif choice == "2":
            test_full_rag(rag_chain)
        elif choice == "3":
            interactive_mode(rag_chain)
        elif choice == "4":
            test_retrieval_only(retriever)
            test_full_rag(rag_chain)
            interactive_mode(rag_chain)
        else:
            print("Invalid choice")
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Tip: Run 'python scripts/setup_knowledge_base.py' first!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Test failed:")


if __name__ == "__main__":
    main()
