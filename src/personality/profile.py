"""Personality Profile management for VoiceClone

A PersonalityProfile captures how a person communicates:
- Tone (formal/casual/warm/direct)
- Catchphrases and common expressions
- Vocabulary patterns
- Topics they care about
- Communication style
- Example phrases and texts

Storage layout:
    ~/.voiceclone/personality/{voice_name}/
    ├── profile.json          ← Main personality data
    ├── vocabulary.json       ← Extracted vocabulary/patterns
    └── examples/             ← Example texts and conversations
        ├── example_001.txt
        └── ...
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PersonalityProfile:
    """Represents a person's communication personality
    
    This is what makes VoiceClone unique: not just the voice,
    but HOW the person expresses themselves.
    """
    voice_name: str  # Links to VoiceProfile
    
    # Core traits
    description: str = ""  # "Soy alegre, cercana, me gusta bromear"
    formality: str = "casual"  # formal | casual | mixed
    humor_style: str = ""  # "Cotidiano, cosas del día a día"
    
    # Language patterns
    catchphrases: list[str] = field(default_factory=list)  # ["¿Sabes?", "Venga"]
    topics: list[str] = field(default_factory=list)  # ["familia", "cocina"]
    vocabulary_level: str = "everyday"  # academic | professional | everyday | colloquial
    emoji_usage: str = "moderate"  # none | minimal | moderate | heavy
    
    # Communication style
    sentence_length: str = "short"  # short | medium | long
    directness: str = "direct"  # direct | indirect | varies
    warmth: str = "warm"  # cold | neutral | warm | very_warm
    energy: str = "high"  # low | medium | high
    
    # Example phrases that represent their style
    sample_phrases: list[str] = field(default_factory=list)
    
    # Source info
    sources: list[str] = field(default_factory=list)  # ["questionnaire", "whatsapp_342"]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "voice_name": self.voice_name,
            "description": self.description,
            "formality": self.formality,
            "humor_style": self.humor_style,
            "catchphrases": self.catchphrases,
            "topics": self.topics,
            "vocabulary_level": self.vocabulary_level,
            "emoji_usage": self.emoji_usage,
            "sentence_length": self.sentence_length,
            "directness": self.directness,
            "warmth": self.warmth,
            "energy": self.energy,
            "sample_phrases": self.sample_phrases,
            "sources": self.sources,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_system_prompt(self) -> str:
        """Generate LLM system prompt from this personality
        
        This is the key integration point: the profile becomes
        instructions for the LLM to rewrite text in this person's style.
        """
        parts = [
            f"Eres {self.voice_name}. Reescribe el texto que te den como si lo dijeras tú.",
            "",
            "## Tu estilo de comunicación:",
        ]

        if self.description:
            parts.append(f"- Personalidad: {self.description}")
        parts.append(f"- Tono: {self.formality}")
        if self.humor_style:
            parts.append(f"- Humor: {self.humor_style}")
        parts.append(f"- Energía: {self.energy}")
        parts.append(f"- Calidez: {self.warmth}")
        parts.append(f"- Frases: {self.sentence_length}")
        parts.append(f"- Directness: {self.directness}")

        if self.catchphrases:
            parts.append("")
            parts.append("## Muletillas y frases típicas:")
            for phrase in self.catchphrases:
                parts.append(f'- "{phrase}"')

        if self.topics:
            parts.append("")
            parts.append(f"## Temas que te importan: {', '.join(self.topics)}")

        if self.sample_phrases:
            parts.append("")
            parts.append("## Ejemplos de cómo hablas:")
            for i, phrase in enumerate(self.sample_phrases[:5], 1):
                parts.append(f'{i}. "{phrase}"')

        parts.extend([
            "",
            "## Reglas:",
            "- Responde SOLO con el texto reescrito, nada más",
            "- Mantén el significado original",
            "- Usa tu estilo natural, no exageres",
            "- Si el texto ya suena como tú, déjalo casi igual",
            "- No añadas información nueva",
            f"- Vocabulario: {self.vocabulary_level}",
        ])

        return "\n".join(parts)


class PersonalityManager:
    """Manages personality profiles on disk
    
    Handles saving, loading, updating profiles.
    Links to voice profiles in ~/.voiceclone/voices/.
    """

    def __init__(self, personality_dir: Optional[Path] = None):
        self.personality_dir = personality_dir or (
            Path.home() / ".voiceclone" / "personality"
        )
        self.personality_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile: PersonalityProfile) -> Path:
        """Save personality profile to disk"""
        profile_dir = self.personality_dir / profile.voice_name
        profile_dir.mkdir(parents=True, exist_ok=True)

        profile.updated_at = datetime.now().isoformat()

        profile_path = profile_dir / "profile.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        # Also save as human-readable markdown
        md_path = profile_dir / "profile.md"
        self._save_markdown(profile, md_path)

        logger.info(f"Saved personality profile for '{profile.voice_name}'")
        return profile_path

    def _save_markdown(self, profile: PersonalityProfile, path: Path) -> None:
        """Save profile as readable markdown"""
        lines = [
            f"# Personalidad de {profile.voice_name}",
            f"*Actualizado: {profile.updated_at}*",
            "",
            f"## Descripción",
            profile.description or "(sin descripción)",
            "",
            f"## Estilo",
            f"- **Tono:** {profile.formality}",
            f"- **Humor:** {profile.humor_style or 'No especificado'}",
            f"- **Energía:** {profile.energy}",
            f"- **Calidez:** {profile.warmth}",
            f"- **Frases:** {profile.sentence_length}",
            "",
        ]

        if profile.catchphrases:
            lines.append("## Muletillas")
            for p in profile.catchphrases:
                lines.append(f'- "{p}"')
            lines.append("")

        if profile.topics:
            lines.append(f"## Temas: {', '.join(profile.topics)}")
            lines.append("")

        if profile.sample_phrases:
            lines.append("## Frases ejemplo")
            for p in profile.sample_phrases:
                lines.append(f'- "{p}"')

        path.write_text("\n".join(lines), encoding="utf-8")

    def load_profile(self, voice_name: str) -> Optional[PersonalityProfile]:
        """Load personality profile from disk"""
        profile_path = self.personality_dir / voice_name / "profile.json"
        if not profile_path.exists():
            return None

        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PersonalityProfile.from_dict(data)

    def has_personality(self, voice_name: str) -> bool:
        """Check if a voice has a personality profile"""
        return (self.personality_dir / voice_name / "profile.json").exists()

    def delete_profile(self, voice_name: str) -> bool:
        """Delete personality profile"""
        import shutil
        profile_dir = self.personality_dir / voice_name
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            logger.info(f"Deleted personality for '{voice_name}'")
            return True
        return False

    def list_profiles(self) -> list[PersonalityProfile]:
        """List all personality profiles"""
        profiles = []
        for profile_dir in sorted(self.personality_dir.iterdir()):
            if not profile_dir.is_dir():
                continue
            profile = self.load_profile(profile_dir.name)
            if profile:
                profiles.append(profile)
        return profiles

    def save_examples(
        self, voice_name: str, texts: list[str], source: str = "manual"
    ) -> int:
        """Save example texts for a voice
        
        Used for vocabulary extraction and style analysis.
        """
        examples_dir = self.personality_dir / voice_name / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for i, text in enumerate(texts):
            if not text.strip():
                continue
            path = examples_dir / f"{source}_{i:04d}.txt"
            path.write_text(text.strip(), encoding="utf-8")
            count += 1

        logger.info(f"Saved {count} examples for '{voice_name}' from {source}")
        return count

    def get_examples(self, voice_name: str) -> list[str]:
        """Get all example texts for a voice"""
        examples_dir = self.personality_dir / voice_name / "examples"
        if not examples_dir.exists():
            return []

        texts = []
        for path in sorted(examples_dir.glob("*.txt")):
            texts.append(path.read_text(encoding="utf-8"))
        return texts
