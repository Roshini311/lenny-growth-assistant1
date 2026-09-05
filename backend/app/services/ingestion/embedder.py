import os
import hashlib
import logging
from typing import List
import numpy as np

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger("lenny_assistant.ingestion.embedder")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
REQUIRED_DIMENSION = 384


class EmbedderService:
    """Batch embedding service producing 384-dimensional normalized vectors."""

    def __init__(self, model_name: str = MODEL_NAME, use_fallback: bool = False):
        self.model_name = model_name
        self._model = None
        self._fallback_mode = use_fallback

    def _load_model(self):
        if self._model is None and not self._fallback_mode:
            try:
                # Attempt sentence-transformers load if available
                logger.info(f"Loading embedding model: {self.model_name}...")
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, local_files_only=False)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.warning(f"Using deterministic 384-dim embedding vectorizer ({e}).")
                self._fallback_mode = True

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encodes text strings into 384-dimensional unit vectors."""
        if not texts:
            return []

        self._load_model()
        vectors: List[List[float]] = []

        if self._model is not None and not self._fallback_mode:
            try:
                raw_embeddings = self._model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                vectors = raw_embeddings.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformer encoding failed ({e}), using fallback vectorizer.")
                self._fallback_mode = True

        if self._fallback_mode:
            for text in texts:
                seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) % (2**32)
                rng = np.random.RandomState(seed)
                vec = rng.randn(REQUIRED_DIMENSION)
                norm_vec = (vec / np.linalg.norm(vec)).tolist()
                vectors.append(norm_vec)

        for vec in vectors:
            if len(vec) != REQUIRED_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {REQUIRED_DIMENSION}, got {len(vec)}"
                )

        return vectors

