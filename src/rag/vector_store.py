"""
VoiceClone — Vector Store

Local vector storage using numpy for similarity search.
Falls back to simple keyword matching when sentence-transformers
is not available.

Designed to run 100% local with no external dependencies.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────

DEFAULT_STORE_PATH = "~/.voiceclone/data/vectors"
EMBEDDING_DIM = 384  # Default for all-MiniLM-L6-v2


@dataclass
class VectorEntry:
    """A stored vector with metadata."""
    id: str
    text: str
    vector: list[float]
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """
    Local vector store for document retrieval.

    Storage: numpy arrays saved to disk.
    Embeddings: sentence-transformers (local) or Ollama embeddings.
    Fallback: TF-IDF-like keyword matching when no embedding model.
    """

    def __init__(
        self,
        store_path: str | Path = DEFAULT_STORE_PATH,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.store_path = Path(store_path).expanduser()
        self.store_path.mkdir(parents=True, exist_ok=True)

        self._vectors_file = self.store_path / "vectors.npy"
        self._metadata_file = self.store_path / "metadata.json"
        self._embedding_model_name = embedding_model
        self._embedding_model = None

        # In-memory storage
        self._vectors: Optional[np.ndarray] = None  # (N, dim)
        self._entries: list[dict[str, Any]] = []

        self._load()

    # ─── Embedding ────────────────────────────────────────

    def _get_embedding_model(self) -> Any:
        """Lazy-load the embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self._embedding_model_name)
                logger.info("Loaded embedding model: %s", self._embedding_model_name)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Using keyword fallback. Install: pip install sentence-transformers"
                )
                self._embedding_model = "fallback"
        return self._embedding_model

    def embed_text(self, text: str | list[str]) -> np.ndarray:
        """
        Generate embeddings for text.

        Args:
            text: Single string or list of strings.

        Returns:
            numpy array of shape (N, dim).
        """
        model = self._get_embedding_model()

        if model == "fallback":
            return self._fallback_embed(text)

        if isinstance(text, str):
            text = [text]

        embeddings = model.encode(text, normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)

    def _fallback_embed(self, text: str | list[str]) -> np.ndarray:
        """Simple word-frequency embedding when no model is available."""
        if isinstance(text, str):
            text = [text]

        # Build a simple bag-of-words vector
        vectors = []
        for t in text:
            words = t.lower().split()
            # Simple hash-based embedding
            vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
            for word in words:
                idx = hash(word) % EMBEDDING_DIM
                vec[idx] += 1.0
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            vectors.append(vec)

        return np.array(vectors, dtype=np.float32)

    # ─── Storage ──────────────────────────────────────────

    def _load(self) -> None:
        """Load vectors and metadata from disk."""
        if self._vectors_file.exists() and self._metadata_file.exists():
            try:
                self._vectors = np.load(str(self._vectors_file))
                self._entries = json.loads(self._metadata_file.read_text())
                logger.info("Loaded %d vectors from disk", len(self._entries))
            except Exception as e:
                logger.error("Failed to load vector store: %s", e)
                self._vectors = None
                self._entries = []

    def _save(self) -> None:
        """Save vectors and metadata to disk."""
        if self._vectors is not None:
            np.save(str(self._vectors_file), self._vectors)
            self._metadata_file.write_text(
                json.dumps(self._entries, ensure_ascii=False)
            )

    # ─── CRUD ─────────────────────────────────────────────

    def add(
        self,
        texts: list[str],
        sources: Optional[list[str]] = None,
        metadata_list: Optional[list[dict[str, Any]]] = None,
    ) -> int:
        """
        Add texts to the vector store.

        Args:
            texts: List of text strings.
            sources: Optional list of source identifiers.
            metadata_list: Optional list of metadata dicts.

        Returns:
            Number of entries added.
        """
        if not texts:
            return 0

        # Generate embeddings
        embeddings = self.embed_text(texts)

        # Create entries
        start_id = len(self._entries)
        for i, text in enumerate(texts):
            entry = {
                "id": f"vec_{start_id + i}",
                "text": text,
                "source": sources[i] if sources else "",
                "metadata": metadata_list[i] if metadata_list else {},
            }
            self._entries.append(entry)

        # Update vectors array
        if self._vectors is None:
            self._vectors = embeddings
        else:
            self._vectors = np.vstack([self._vectors, embeddings])

        self._save()
        logger.info("Added %d entries to vector store", len(texts))
        return len(texts)

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search for similar texts.

        Args:
            query: Search query text.
            top_k: Number of results.
            min_score: Minimum similarity score (0-1).

        Returns:
            List of results with text, score, source, metadata.
        """
        if self._vectors is None or len(self._entries) == 0:
            return []

        # Embed query
        query_vec = self.embed_text(query)
        if query_vec.ndim == 2:
            query_vec = query_vec[0]

        # Cosine similarity
        similarities = np.dot(self._vectors, query_vec)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < min_score:
                continue

            entry = self._entries[idx]
            results.append({
                "text": entry["text"],
                "score": round(score, 4),
                "source": entry.get("source", ""),
                "metadata": entry.get("metadata", {}),
            })

        return results

    @property
    def count(self) -> int:
        """Number of entries in the store."""
        return len(self._entries)

    def clear(self) -> None:
        """Clear all entries."""
        self._vectors = None
        self._entries = []
        self._save()
