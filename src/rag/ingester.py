"""
VoiceClone — Document Ingester

Parses and extracts text from various document formats:
- WhatsApp chat exports (.txt)
- Plain text files (.txt)
- PDF documents (.pdf)
- Email exports (.eml)

The extracted text is chunked for vector storage and retrieval.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────

DEFAULT_CHUNK_SIZE = 500  # characters per chunk
DEFAULT_CHUNK_OVERLAP = 50
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".eml", ".md", ".csv"}


@dataclass
class TextChunk:
    """A chunk of text from a document."""
    text: str
    source: str             # Original file path
    chunk_index: int        # Index within the document
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }


class DocumentIngester:
    """
    Ingests documents and produces text chunks for vector storage.

    Supports multiple formats commonly found on a user's computer
    or shared by family members (WhatsApp exports, PDFs, etc.).
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest_file(self, file_path: str | Path) -> list[TextChunk]:
        """
        Ingest a single file and return text chunks.

        Args:
            file_path: Path to the file.

        Returns:
            List of TextChunk objects.
        """
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            logger.error("File not found: %s", path)
            return []

        ext = path.suffix.lower()

        if ext == ".txt":
            return self._ingest_text(path)
        elif ext == ".pdf":
            return self._ingest_pdf(path)
        elif ext == ".eml":
            return self._ingest_email(path)
        elif ext == ".md":
            return self._ingest_text(path)
        elif ext == ".csv":
            return self._ingest_text(path)
        else:
            logger.warning("Unsupported file type: %s", ext)
            return []

    def ingest_directory(self, dir_path: str | Path) -> list[TextChunk]:
        """Ingest all supported files in a directory."""
        path = Path(dir_path).expanduser().resolve()
        chunks: list[TextChunk] = []

        for file in path.rglob("*"):
            if file.suffix.lower() in SUPPORTED_EXTENSIONS:
                chunks.extend(self.ingest_file(file))

        logger.info("Ingested %d chunks from %s", len(chunks), path)
        return chunks

    def ingest_whatsapp_export(self, file_path: str | Path) -> list[TextChunk]:
        """
        Ingest a WhatsApp chat export file.

        WhatsApp exports have format:
        [DD/MM/YYYY, HH:MM:SS] Name: Message text

        Extracts messages and groups them into chunks.
        """
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            return []

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to read WhatsApp export: %s", e)
            return []

        # Parse WhatsApp messages
        pattern = r"\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:]+):\s*(.*)"
        messages: list[str] = []
        current_speaker = ""

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                date, time_str, speaker, message = match.groups()
                current_speaker = speaker.strip()
                messages.append(f"{current_speaker}: {message.strip()}")
            elif line.strip() and current_speaker:
                # Continuation of previous message
                messages.append(f"{current_speaker}: {line.strip()}")

        # Chunk the messages
        full_text = "\n".join(messages)
        return self._chunk_text(full_text, str(path), {"type": "whatsapp"})

    # ─── Format-Specific Ingesters ────────────────────────

    def _ingest_text(self, path: Path) -> list[TextChunk]:
        """Ingest a plain text file."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            return self._chunk_text(text, str(path), {"type": "text"})
        except Exception as e:
            logger.error("Failed to read text file %s: %s", path, e)
            return []

    def _ingest_pdf(self, path: Path) -> list[TextChunk]:
        """Ingest a PDF file. Requires pypdf or pdfplumber."""
        try:
            # Try pypdf first
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                    text += "\n"
            except ImportError:
                # Fallback: pdfplumber
                try:
                    import pdfplumber
                    with pdfplumber.open(str(path)) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                            text += "\n"
                except ImportError:
                    logger.warning(
                        "No PDF library available. Install: pip install pypdf"
                    )
                    return []

            return self._chunk_text(text, str(path), {"type": "pdf"})

        except Exception as e:
            logger.error("Failed to read PDF %s: %s", path, e)
            return []

    def _ingest_email(self, path: Path) -> list[TextChunk]:
        """Ingest an email (.eml) file."""
        try:
            import email
            from email import policy

            with open(path, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)

            subject = msg.get("Subject", "")
            sender = msg.get("From", "")
            date = msg.get("Date", "")

            # Get body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_content() or ""
            else:
                body = msg.get_content() or ""

            header = f"De: {sender}\nAsunto: {subject}\nFecha: {date}\n\n"
            full_text = header + body

            return self._chunk_text(
                full_text, str(path),
                {"type": "email", "subject": subject, "from": sender},
            )

        except Exception as e:
            logger.error("Failed to read email %s: %s", path, e)
            return []

    # ─── Chunking ─────────────────────────────────────────

    def _chunk_text(
        self,
        text: str,
        source: str,
        metadata: dict[str, Any],
    ) -> list[TextChunk]:
        """
        Split text into overlapping chunks.

        Uses paragraph boundaries when possible, falls back to
        character-based splitting.
        """
        if not text.strip():
            return []

        # Normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        chunks: list[TextChunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                # Try to break at paragraph boundary
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2
                else:
                    # Try sentence boundary
                    sent_break = max(
                        text.rfind(". ", start, end),
                        text.rfind("? ", start, end),
                        text.rfind("! ", start, end),
                    )
                    if sent_break > start + self.chunk_size // 3:
                        end = sent_break + 2

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text,
                    source=source,
                    chunk_index=index,
                    metadata=metadata,
                ))
                index += 1

            start = end - self.chunk_overlap

        logger.info("Chunked %s: %d chunks", source, len(chunks))
        return chunks
