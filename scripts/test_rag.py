# scripts/test_rag.py

from src.rag.chain import EPASRAGChain

if __name__ == "__main__":
    rag = EPASRAGChain("data/vectorstore")

    question = "What are the training requirements for crew members?"
    result = rag.query(question)

    print("\n=== EPAS RAG Result ===")
    print(f"Answer: {result['answer']}\n")
    print(f"Chunks retrieved: {result['chunks']}")
    print(f"Sources: {result['sources']}")
