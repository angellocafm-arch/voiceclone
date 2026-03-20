"""
VoiceClone — Phrase Predictor

Predicts likely phrases based on:
1. Recent phrase history (frequency-weighted)
2. Time of day context
3. Current conversation context
4. User's common patterns

Designed for eye-tracking interface: shows top 5 predicted phrases
that the user can select with a single gaze dwell.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Default Phrases ─────────────────────────────────────

DEFAULT_PHRASES = [
    # Basics
    "Sí", "No", "Gracias", "Por favor", "De acuerdo",
    # Needs
    "Tengo sed", "Tengo hambre", "Necesito ir al baño",
    "Me duele", "Tengo frío", "Tengo calor",
    "Necesito ayuda", "Estoy cansado",
    # Communication
    "¿Puedes repetir?", "No entiendo", "Un momento",
    "Quiero decir algo", "Lee mis mensajes",
    # Social
    "Hola", "Adiós", "Te quiero", "Buenas noches",
    "¿Cómo estás?", "Estoy bien",
    # Medical
    "Llama al médico", "Necesito mi medicación",
    "Me encuentro mal",
]

# Time-based phrase categories
TIME_PHRASES = {
    "morning": ["Buenos días", "¿Qué hay de desayunar?", "¿Qué hora es?"],
    "afternoon": ["Buenas tardes", "¿Hay algo de comer?", "Necesito descansar"],
    "evening": ["Buenas noches", "Estoy cansado", "Apaga la luz"],
    "night": ["No puedo dormir", "Necesito agua", "Llama a alguien"],
}


@dataclass
class PhraseEntry:
    """A phrase with usage statistics."""
    text: str
    count: int = 0
    last_used: float = 0.0
    contexts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "count": self.count,
            "last_used": self.last_used,
        }


@dataclass
class Prediction:
    """A predicted phrase with confidence score."""
    text: str
    confidence: float  # 0.0 - 1.0
    source: str  # "history" | "context" | "time" | "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 3),
            "source": self.source,
        }


class PhrasePredictor:
    """
    Predicts likely phrases for the user.

    Combines multiple signals:
    - Frequency: most-used phrases rank higher
    - Recency: recently used phrases get a boost
    - Time of day: morning/afternoon/evening phrases
    - Context: if user just said "Hola", "¿Cómo estás?" is likely next
    """

    def __init__(
        self,
        history_path: str | Path = "~/.voiceclone/data/phrase_history.json",
        max_history: int = 500,
    ) -> None:
        self.history_path = Path(history_path).expanduser()
        self.max_history = max_history
        self.phrases: dict[str, PhraseEntry] = {}
        self._load_history()

        # Add defaults if history is empty
        if not self.phrases:
            for phrase in DEFAULT_PHRASES:
                self.phrases[phrase] = PhraseEntry(text=phrase)

    # ─── History Management ───────────────────────────────

    def _load_history(self) -> None:
        """Load phrase history from disk."""
        if self.history_path.exists():
            try:
                data = json.loads(self.history_path.read_text())
                for entry in data.get("phrases", []):
                    text = entry.get("text", "")
                    if text:
                        self.phrases[text] = PhraseEntry(
                            text=text,
                            count=entry.get("count", 0),
                            last_used=entry.get("last_used", 0),
                            contexts=entry.get("contexts", []),
                        )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load phrase history: %s", e)

    def _save_history(self) -> None:
        """Save phrase history to disk."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        # Keep top N by usage count
        sorted_phrases = sorted(
            self.phrases.values(),
            key=lambda p: p.count,
            reverse=True,
        )[:self.max_history]

        data = {
            "phrases": [
                {
                    "text": p.text,
                    "count": p.count,
                    "last_used": p.last_used,
                    "contexts": p.contexts[-10:],  # Keep last 10 contexts
                }
                for p in sorted_phrases
            ],
            "updated_at": time.time(),
        }

        self.history_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def record_phrase(self, text: str, context: str = "") -> None:
        """
        Record that a phrase was used.

        Args:
            text: The phrase that was spoken/selected.
            context: Optional context (previous phrase, conversation topic).
        """
        if not text.strip():
            return

        text = text.strip()

        if text not in self.phrases:
            self.phrases[text] = PhraseEntry(text=text)

        entry = self.phrases[text]
        entry.count += 1
        entry.last_used = time.time()
        if context:
            entry.contexts.append(context)

        self._save_history()

    # ─── Prediction ───────────────────────────────────────

    def predict(
        self,
        context: str = "",
        limit: int = 5,
    ) -> list[Prediction]:
        """
        Predict the most likely next phrases.

        Args:
            context: Current context (last phrase said, conversation topic).
            limit: Number of predictions to return.

        Returns:
            List of Prediction objects, sorted by confidence.
        """
        candidates: list[Prediction] = []

        # 1. History-based predictions (frequency + recency)
        now = time.time()
        for entry in self.phrases.values():
            if entry.count == 0:
                continue

            # Frequency score (logarithmic)
            freq_score = min(entry.count / 10.0, 1.0)

            # Recency score (exponential decay, 1h half-life)
            time_diff = now - entry.last_used
            recency_score = 2 ** (-time_diff / 3600)

            # Combined score
            score = freq_score * 0.6 + recency_score * 0.4

            candidates.append(Prediction(
                text=entry.text,
                confidence=min(score, 0.99),
                source="history",
            ))

        # 2. Context-based predictions
        if context:
            context_lower = context.lower()
            for entry in self.phrases.values():
                # Check if this phrase often follows the context
                context_match = sum(
                    1 for c in entry.contexts
                    if context_lower in c.lower()
                )
                if context_match > 0:
                    ctx_score = min(context_match / 5.0, 0.9)
                    # Boost existing candidate or add new
                    existing = next(
                        (c for c in candidates if c.text == entry.text), None
                    )
                    if existing:
                        existing.confidence = min(
                            existing.confidence + ctx_score * 0.3, 0.99
                        )
                    else:
                        candidates.append(Prediction(
                            text=entry.text,
                            confidence=ctx_score,
                            source="context",
                        ))

        # 3. Time-based predictions
        hour = time.localtime().tm_hour
        if 5 <= hour < 12:
            time_key = "morning"
        elif 12 <= hour < 18:
            time_key = "afternoon"
        elif 18 <= hour < 22:
            time_key = "evening"
        else:
            time_key = "night"

        for phrase in TIME_PHRASES.get(time_key, []):
            existing = next((c for c in candidates if c.text == phrase), None)
            if existing:
                existing.confidence = min(existing.confidence + 0.1, 0.99)
            else:
                candidates.append(Prediction(
                    text=phrase,
                    confidence=0.3,
                    source="time",
                ))

        # 4. Defaults (fill remaining slots)
        for phrase in DEFAULT_PHRASES:
            if len(candidates) >= limit * 2:
                break
            existing = next((c for c in candidates if c.text == phrase), None)
            if not existing:
                candidates.append(Prediction(
                    text=phrase,
                    confidence=0.1,
                    source="default",
                ))

        # Sort by confidence and deduplicate
        seen: set[str] = set()
        unique: list[Prediction] = []
        for pred in sorted(candidates, key=lambda p: p.confidence, reverse=True):
            if pred.text not in seen:
                seen.add(pred.text)
                unique.append(pred)

        return unique[:limit]

    def get_frequent_phrases(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get the most frequently used phrases."""
        sorted_phrases = sorted(
            self.phrases.values(),
            key=lambda p: p.count,
            reverse=True,
        )
        return [p.to_dict() for p in sorted_phrases[:limit] if p.count > 0]

    def add_custom_phrase(self, text: str) -> None:
        """Add a custom phrase to the library."""
        if text.strip() and text not in self.phrases:
            self.phrases[text] = PhraseEntry(text=text.strip())
            self._save_history()

    def remove_phrase(self, text: str) -> bool:
        """Remove a phrase from the library."""
        if text in self.phrases:
            del self.phrases[text]
            self._save_history()
            return True
        return False
