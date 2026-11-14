"""Semantic vector embedding generation with offline fallback."""
from __future__ import annotations

import hashlib
import math
import re
from typing import List


class EmbeddingGenerator:
    """Produces normalized vector embeddings for code and security findings."""

    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self._st_model = None
        self._use_sentence_transformers = False

        # Attempt to load local sentence_transformers if available
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._use_sentence_transformers = True
            self.dimension = 384
        except Exception:
            self._use_sentence_transformers = False

    def embed_text(self, text: str) -> List[float]:
        """Convert string to normalized dense vector."""
        if self._use_sentence_transformers and self._st_model is not None:
            try:
                vec = self._st_model.encode(text).tolist()
                return vec
            except Exception:
                pass

        # Deterministic feature-hashing embedding fallback
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> List[float]:
        """Deterministic subword / character n-gram projection with L2 normalization."""
        vec = [0.0] * self.dimension
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec

        for word in words:
            # 3-gram features
            for i in range(max(1, len(word) - 2)):
                gram = word[i:i+3]
                h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dimension
                sign = 1.0 if ((h >> 8) & 1) else -1.0
                vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-9:
            vec = [v / norm for v in vec]
        return vec

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two unit vectors."""
        if len(vec_a) != len(vec_b):
            return 0.0
        return sum(a * b for a, b in zip(vec_a, vec_b))
