"""
VoiceClone — Retriever

Combines document ingestion and vector search to provide
context-aware retrieval for the LLM.

Usage:
    retriever = Retriever()
    retriever.add_document("/path/to/whatsapp_export.txt")
    context = retriever.get_context("¿Qué dijo María ayer?")

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from src.rag.ingester import DocumentIngester
from src.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """
    High-level retriever that combines ingestion and search.

    Provides a simple interface for the LLM to get relevant context
    from the user's documents.
    """

    def __init__(
        self,
        store_path: str = "~/.voiceclone/data/vectors",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self.ingester = DocumentIngester(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.store = VectorStore(store_path=store_path)

    def add_document(self, file_path: str | Path) -> int:
        """
        Ingest a document and add to the vector store.

        Args:
            file_path: Path to the document.

        Returns:
            Number of chunks added.
        """
        path = Path(file_path).expanduser().resolve()
        chunks = self.ingester.ingest_file(path)

        if not chunks:
            logger.warning("No chunks extracted from %s", path)
            return 0

        texts = [c.text for c in chunks]
        sources = [c.source for c in chunks]
        metadata = [c.metadata for c in chunks]

        added = self.store.add(texts, sources=sources, metadata_list=metadata)
        logger.info("Added %d chunks from %s", added, path.name)
        return added

    def add_whatsapp_export(self, file_path: str | Path) -> int:
        """
        Ingest a WhatsApp chat export.

        Args:
            file_path: Path to the WhatsApp export .txt file.

        Returns:
            Number of chunks added.
        """
        chunks = self.ingester.ingest_whatsapp_export(file_path)

        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        sources = [c.source for c in chunks]
        metadata = [c.metadata for c in chunks]

        return self.store.add(texts, sources=sources, metadata_list=metadata)

    def add_directory(self, dir_path: str | Path) -> int:
        """Ingest all supported documents in a directory."""
        chunks = self.ingester.ingest_directory(dir_path)

        if not chunks:
            return 0

        texts = [c.text for c in chunks]
        sources = [c.source for c in chunks]
        metadata = [c.metadata for c in chunks]

        return self.store.add(texts, sources=sources, metadata_list=metadata)

    def get_context(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.1,
    ) -> str:
        """
        Retrieve relevant context for a query.

        Returns a formatted string ready to inject into LLM context.

        Args:
            query: The user's question or current context.
            top_k: Number of chunks to retrieve.
            min_score: Minimum similarity threshold.

        Returns:
            Formatted context string.
        """
        results = self.store.search(query, top_k=top_k, min_score=min_score)

        if not results:
            return ""

        context_parts: list[str] = []
        for i, result in enumerate(results, 1):
            source = result.get("source", "desconocido")
            source_name = Path(source).name if source else "desconocido"
            context_parts.append(
                f"[Fragmento {i} — {source_name}]\n{result['text']}"
            )

        return "\n\n".join(context_parts)

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Direct search returning raw results."""
        return self.store.search(query, top_k=top_k, min_score=min_score)

    @property
    def document_count(self) -> int:
        """Number of chunks in the store."""
        return self.store.count

    def clear(self) -> None:
        """Clear all stored documents."""
        self.store.clear()
