# src/rag/embeddings.py
from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Inizializza il modello HuggingFace per generare embeddings.
    """
    return HuggingFaceEmbeddings(model_name=model_name)
