from sentence_transformers import SentenceTransformer
import numpy as np
from loguru import logger

class EPASEmbedder:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Loaded embedding model '{model_name}' with dim={self.dim}")

    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
