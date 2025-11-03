"""
EPAS Vector Store
Wrapper per FAISS con compatibilità ai file salvati:
- chunks.pkl
- metadata.pkl
- faiss_index.bin
"""

import os
import pickle
from pathlib import Path
from loguru import logger
from langchain_community.vectorstores import FAISS


class EPASVectorStore:
    """Wrapper per FAISS vector store compatibile con EPAS"""

    def __init__(self, faiss_index: FAISS, chunks: list, metadata: list):
        self.faiss_index = faiss_index
        self.chunks = chunks
        self.metadata = metadata

    @classmethod
    def load(cls, folder_path: str):
        """
        Carica il vector store dai file salvati
        Args:
            folder_path: percorso della cartella contenente i file
        """
        folder = Path(folder_path)
        chunks_file = folder / "chunks.pkl"
        metadata_file = folder / "metadata.pkl"
        faiss_file = folder / "faiss_index.bin"

        if not chunks_file.exists() or not metadata_file.exists() or not faiss_file.exists():
            raise FileNotFoundError(
                f"One or more required files are missing in {folder_path}.\n"
                "Required: chunks.pkl, metadata.pkl, faiss_index.bin"
            )

        # Carica chunk e metadata
        with open(chunks_file, "rb") as f:
            chunks = pickle.load(f)
        with open(metadata_file, "rb") as f:
            metadata = pickle.load(f)

        # Carica FAISS
        faiss_index = FAISS.load_local(
            folder_path=str(folder),
            embeddings=None,  # Gli embeddings non sono necessari per query read-only
            allow_dangerous_deserialization=True
        )

        logger.info(f"FAISS vector store caricato da {folder_path}")
        return cls(faiss_index, chunks, metadata)

    def similarity_search(self, query_vector, k: int = 5):
        """
        Ricerca di similarità usando il vettore della query
        """
        try:
            results = self.faiss_index.similarity_search_by_vector(query_vector, k=k)
            return [doc for doc, score in results]
        except Exception as e:
            logger.error(f"Errore in similarity_search: {e}")
            return []

    def get_statistics(self):
        """Ritorna statistiche sul vector store"""
        total_chunks = len(self.chunks)
        return {
            "total_chunks": total_chunks,
            "index_size": self.faiss_index.index.ntotal if self.faiss_index.index else 0,
            "volumes": self._count_chunks_per_volume()
        }

    def _count_chunks_per_volume(self):
        volumes = {}
        for doc in self.chunks:
            vol = doc.get("metadata", {}).get("volume", "Unknown")
            volumes[vol] = volumes.get(vol, 0) + 1
        return volumes
