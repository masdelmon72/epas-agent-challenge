#!/usr/bin/env python3
"""
Run EPAS Agent
Main script to run the UiPath SDK agent
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
from src.agent.epas_agent import EPASAgent


def initialize_agent():
    """Initialize the complete EPAS agent system"""
    print("\n" + "="*80)
    print("Initializing EPAS Agent System")
    print("="*80)
    
    # Load vector store
    print("\n1. Loading vector store...")
    vectorstore = EPASVectorStore.load(str(settings.vectorstore_dir))
    stats = vectorstore.get_statistics()
    print(f"   ✓ Loaded {stats['total_chunks']:,} chunks")
    
    # Load embedder
    print("\n2. Loading embedding model...")
    embedder = EPASEmbedder(model_name=settings.embedding_model)
    print(f"   ✓ Model loaded: {settings.embedding_model}")
    
    # Create retriever
    print("\n3. Creating retriever...")
    retriever = EPASContextualRetriever(
        vectorstore=vectorstore,
        embedder=embedder,
        k=settings.top_k_results,
        score_threshold=settings.similarity_threshold
    )
    print(f"   ✓ Retriever configured (k={settings.top_k_results})")
    
    # Create RAG chain
    print("\n4. Creating RAG chain...")
    rag_chain = EPASRAGChain(
        retriever=retriever,
        llm_model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens
    )
    print(f"   ✓ RAG chain initialized ({settings.llm_model})")
    
    # Create agent
    print("\n5. Creating EPAS agent...")
    agent = EPASAgent(
        rag_chain=rag_chain,
        retriever=retriever,
        agent_name="EPASAssistant"
    )
    print("   ✓ Agent ready")
    
    print("\n" + "="*80)
    print("✅ EPAS Agent System Initialized Successfully!")
    print("="*80)
    
    return agent


def run_interactive_mode(agent: EPASAgent):
    """Run agent in interactive mode"""
    print("\n" + "="*80)
    print("EPAS Agent - Interactive Mode")
    print("="*80)
    print("\n📋 Commands:")
    print("  - <your question>        : Ask a question")
    print("  - vol:I <question>       : Filter by Volume I")
    print("  - vol:II <question>      : Filter by Volume II")
    print("  - vol:III <question>     : Filter by Volume III")
    print("  - save <filename>        : Save last response to HTML file")
    print("  - help                   : Show example questions")
    print("  - quit                   : Exit")
    print("="*80 + "\n")
    
    last_response = None
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print_example_questions()
                continue
            
            if user_input.lower().startswith('save '):
                if last_response:
                    filename = user_input[5:].strip() or "response.html"
                    if not filename.endswith('.html'):
                        filename += '.html'
                    save_html_response(last_response, filename, agent.rag_chain)
                    print(f"✓ Saved to {filename}")
                else:
                    print("❌ No response to save")
                continue
            
            # Parse volume filter
            volume_filter = None
            if user_input.lower().startswith('vol:'):
                parts = user_input.split(' ', 1)
                volume_filter = parts[0].split(':')[1].upper()
                user_input = parts[1] if len(parts) > 1 else ""
                if volume_filter not in ['I', 'II', 'III']:
                    print(f"❌ Invalid volume: {volume_filter}")
                    continue
                print(f"🔍 Filtering by Volume {volume_filter}")
            
            if not user_input:
                print("Please provide a question")
                continue
            
            # Process query
            print("\n⏳ Processing...")
            
            response = agent.process_query(user_input, volume_filter=volume_filter)
            
            # Display response
            print("\n" + "="*80)
            print("🤖 EPAS Assistant:")
            print("="*80)
            print(response['answer'])
            
            # Display metadata
            print("\n" + "-"*80)
            print(f"📊 Confidence: {response['confidence']:.1%}")
            print(f"📚 Sources: {len(response.get('sources', []))}")
            
            if response.get('sources'):
                print("\n📖 Top Sources:")
                for i, source in enumerate(response['sources'][:3], 1):
                    print(f"  {i}. Vol {source['volume']}, {source['section_id']}, " +
                          f"p.{source['page']} (Score: {source['relevance_score']:.3f})")
            
            print("-"*80)
            
            # Save for later
            last_response = response
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Type 'quit' to exit properly.")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Error in interactive mode:")


def print_example_questions():
    """Print example questions"""
    examples = {
        "General Questions": [
            "What are the main strategic priorities in EPAS?",
            "Explain the structure of EPAS volumes",
            "What is the purpose of the Safety Risk Portfolio?"
        ],
        "Regulatory Questions (Volume I)": [
            "What are the maintenance requirements for commercial operators?",
            "Explain the requirements for safety management systems",
            "What are the crew training requirements?"
        ],
        "Safety Actions (Volume II)": [
            "What actions are planned for runway safety?",
            "What are the implementation timelines for safety actions?",
            "Which stakeholders are responsible for implementing safety actions?"
        ],
        "Risk Assessment (Volume III)": [
            "What are the main safety risks in commercial aviation?",
            "How are safety risks prioritized?",
            "What mitigation strategies are recommended for runway excursions?"
        ]
    }
    
    print("\n" + "="*80)
    print("Example Questions")
    print("="*80)
    
    for category, questions in examples.items():
        print(f"\n{category}:")
        for q in questions:
            print(f"  • {q}")
    
    print("="*80)


def save_html_response(response: dict, filename: str, rag_chain: EPASRAGChain):
    """Save response to HTML file"""
    html = rag_chain.format_html_response(response)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EPAS Assistant Response</title>
</head>
<body>
{html}
</body>
</html>""")


def run_batch_test(agent: EPASAgent):
    """Run a batch test with predefined questions"""
    print("\n" + "="*80)
    print("Running Batch Test")
    print("="*80)
    
    test_questions = [
        "What are the strategic priorities in EPAS?",
        "Explain safety management system requirements",
        "What are the main safety risks for runway operations?",
        "vol:II What safety actions are planned for 2024?"
    ]
    
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[{i}/{len(test_questions)}] Processing: {question}")
        
        # Parse volume filter
        volume_filter = None
        if question.startswith('vol:'):
            parts = question.split(' ', 1)
            volume_filter = parts[0].split(':')[1]
            question = parts[1]
        
        response = agent.process_query(question, volume_filter=volume_filter)
        
        results.append({
            'question': question,
            'volume_filter': volume_filter,
            'confidence': response['confidence'],
            'num_sources': len(response.get('sources', []))
        })
        
        print(f"   Confidence: {response['confidence']:.1%}, Sources: {len(response.get('sources', []))}")
    
    # Summary
    print("\n" + "="*80)
    print("Batch Test Summary")
    print("="*80)
    
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_sources = sum(r['num_sources'] for r in results) / len(results)
    
    print(f"Questions tested: {len(results)}")
    print(f"Average confidence: {avg_confidence:.1%}")
    print(f"Average sources: {avg_sources:.1f}")
    
    print("\nDetailed Results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['question'][:60]}...")
        if result['volume_filter']:
            print(f"   Volume: {result['volume_filter']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Sources: {result['num_sources']}")


def main():
    """Main function"""
    logger.add("run_agent.log", rotation="10 MB", level="INFO")
    
    print("\n" + "="*80)
    print("EPAS Agent - UiPath SDK Challenge")
    print("="*80)
    
    try:
        # Initialize agent
        agent = initialize_agent()
        
        # Select mode
        print("\nSelect mode:")
        print("1. Interactive Mode (default)")
        print("2. Batch Test Mode")
        
        choice = input("\nEnter choice (1-2) [default: 1]: ").strip() or "1"
        
        if choice == "1":
            run_interactive_mode(agent)
        elif choice == "2":
            run_batch_test(agent)
        else:
            print("Invalid choice")
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Tip: Run 'python scripts/setup_knowledge_base.py' first!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Agent failed:")


if __name__ == "__main__":
    main()
