"""Embedding service — generates and manages vector embeddings for Memory content.

Backend: scikit-learn TF-IDF + TruncatedSVD for local, no-GPU embeddings.
Dimension: 384 (configurable via settings.embedding_dimension).
Storage: JSON column on Memory.embedding.
Versioned: embedding_model, embedding_dimension, embedding_version, embedded_at.
"""
from __future__ import annotations

import logging
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Singleton vectorizer/SVD ──────────────────────────────────────────────
# A single trained instance is shared — safe because the corpus grows
# monotonically and the model is only *fit*, never *refit* on existing data.

class _EmbeddingModel:
    """Lazy-initialized TF-IDF + SVD embedding pipeline."""

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._svd: TruncatedSVD | None = None
        self._fitted = False
        self._dimension: int = settings.embedding_dimension

    def fit(self, texts: list[str]) -> None:
        """Fit the vectorizer and SVD on a corpus of texts."""
        if not texts:
            return
        self._vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
        )
        tfidf_matrix = self._vectorizer.fit_transform(texts)
        actual_dim = min(self._dimension, tfidf_matrix.shape[0] - 1, tfidf_matrix.shape[1] - 1)
        actual_dim = max(actual_dim, 1)
        self._svd = TruncatedSVD(n_components=actual_dim, random_state=42)
        self._svd.fit(tfidf_matrix)
        self._fitted = True
        self._dimension = actual_dim
        logger.info("[embeddings] model fitted: %d dims on %d texts", actual_dim, len(texts))

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts. Returns array of shape (n, dim)."""
        if not self._fitted or self._vectorizer is None or self._svd is None:
            # Fallback: simple character n-gram hashing
            return np.array([self._hash_embed(t) for t in texts], dtype=np.float32)

        tfidf = self._vectorizer.transform(texts)
        dense = self._svd.transform(tfidf)
        dense = normalize(dense, norm="l2")
        return dense.astype(np.float32)

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text and return as list of floats."""
        arr = self.embed([text])
        return arr[0].tolist()

    @staticmethod
    def _hash_embed(text: str, dim: int = 384) -> list[float]:
        """Deterministic fallback embedding using character n-gram hashing."""
        vec = np.zeros(dim, dtype=np.float32)
        for n in (2, 3, 4):
            for i in range(len(text) - n + 1):
                gram = text[i:i + n]
                h = int(hashlib.sha256(gram.encode()).hexdigest(), 16)
                idx = h % dim
                vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Module-level singleton
_model = _EmbeddingModel()


def get_model() -> _EmbeddingModel:
    return _model


# ── Public API ───────────────────────────────────────────────────────────

def generate_embedding(text: str) -> tuple[list[float], str, int]:
    """Generate an embedding for a text string.

    Returns:
        (embedding_list, model_name, dimension)
    """
    start = time.monotonic()
    model_name = settings.embedding_model
    dim = settings.embedding_dimension

    try:
        embedding = _model.embed_one(text)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.debug("[embeddings] generated %d-dim embedding in %dms", dim, elapsed_ms)
        return embedding, model_name, dim
    except Exception:
        logger.exception("[embeddings] embedding generation failed, using fallback")
        return _EmbeddingModel._hash_embed(text, dim), model_name, dim


def fit_corpus(texts: list[str]) -> None:
    """Fit the embedding model on a corpus (called during backfill)."""
    _model.fit(texts)


def embedding_version() -> str:
    """Return a version string for the current embedding configuration."""
    return f"{settings.embedding_provider}:{settings.embedding_model}:{settings.embedding_dimension}"


def content_hash(text: str) -> str:
    """SHA-256 hash of text content, for idempotency checks."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
