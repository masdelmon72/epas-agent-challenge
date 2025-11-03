# src/rag/retriever.py

"""
EPAS RAG Retriever
Gestisce il caricamento del vector store FAISS e il recupero contestuale
dei documenti più rilevanti per una query.
"""

import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


class EPASContextualRetriever:
    """
    Classe per gestire il recupero di documenti dal vector store FAISS.
    """

    def __init__(self, vectorstore_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print("🔹 Inizializzo EPASContextualRetriever...")

        # 1️⃣ Carica modello di embedding HuggingFace
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        # 2️⃣ Carica il vectorstore FAISS locale
        if not os.path.exists(vectorstore_path):
            raise FileNotFoundError(f"Vectorstore non trovato: {vectorstore_path}")

        self.vectorstore = FAISS.load_local(
            vectorstore_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        # 3️⃣ Crea retriever LangChain
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        print(f"✅ Vectorstore caricato correttamente da {vectorstore_path}")

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Recupera i documenti più rilevanti per una query.
        Restituisce una lista di dizionari con testo e metadata.
        """
        docs = self.retriever.invoke(query)
        print(f"🔍 Recuperati {len(docs)} documenti per la query: '{query}'")

        results = []
        for i, d in enumerate(docs):
            results.append({
                "rank": i + 1,
                "content": d.page_content,
                "metadata": d.metadata
            })
        return results
