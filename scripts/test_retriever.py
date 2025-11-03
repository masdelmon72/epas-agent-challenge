# scripts/test_retriever.py

from src.rag.retriever import EPASContextualRetriever

if __name__ == "__main__":
    retriever = EPASContextualRetriever("data/vectorstore")

    query = "What are the training requirements for crew members?"
    print("⏳ Query:", query)

    results = retriever.retrieve(query)
    print("\n--- Top Results ---")
    for r in results:
        print(f"#{r['rank']}: {r['content'][:250]}...")
