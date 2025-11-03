# scripts/test_rag.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.rag.vectorstore import EPASVectorStore
from src.rag.retriever import EPASRetriever
from src.rag.chain import EPASRAGChain

if __name__ == "__main__":
    print("=== EPAS RAG System (HuggingFace) ===\n")

    VECTORSTORE_DIR = "data/vectorstore"

    vectorstore = EPASVectorStore(faiss_dir=VECTORSTORE_DIR)
    vectorstore.load()

    retriever = EPASRetriever(vectorstore)
    rag_chain = EPASRAGChain(retriever)
    rag_chain.init_model()
    rag_chain.build_chain()

    query = "What are the training requirements for crew members?"
    print(f"\n🔍 Query: {query}")
    answer = rag_chain.run(query)
    print("\n🧠 Answer:\n", answer)
