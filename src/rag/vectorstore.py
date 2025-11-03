# src/rag/vectorstore.py
from langchain_community.vectorstores import FAISS
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import os


class EPASVectorStore:
    def __init__(self, vectorstore_path="data/vectorstore"):
        self.vectorstore_path = vectorstore_path

        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        print(f"📂 Caricamento vector store FAISS da {vectorstore_path}")
        self.db = FAISS.load_local(
            vectorstore_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        print("✅ Vector store caricato con successo.")

