"""Personality profile management.

A personality profile captures HOW a person speaks:
- Tone (formal, casual, humorous)
- Common phrases and expressions  
- Vocabulary preferences
- Communication style

This enables the LLM to rewrite text "as the person would say it"
before the TTS engine synthesizes it with their cloned voice.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PersonalityProfile:
    """A person's communication personality."""
    
    voice_id: str
    name: str
    
    # Core personality traits (from questionnaire)
    tone: str = "casual"  # formal, casual, humorous, direct
    formality: str = "informal"  # formal, informal, mixed
    humor_style: str = "none"  # none, dry, playful, sarcastic
    
    # Custom descriptions
    self_description: str = ""
    favorite_phrases: list[str] = field(default_factory=list)
    
    # Example texts (for few-shot prompting)
    examples: list[str] = field(default_factory=list)
    
    # Cached phrases for AAC instant playback
    cached_phrases: dict[str, str] = field(default_factory=dict)
    # key: phrase text, value: path to cached audio file
    
    # Metadata
    created_at: str = ""
    updated_at: str = ""


def save_profile(profile: PersonalityProfile, base_dir: Path) -> Path:
    """Save personality profile to disk."""
    profile_dir = base_dir / "personality" / profile.voice_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    data = {
        "voice_id": profile.voice_id,
        "name": profile.name,
        "tone": profile.tone,
        "formality": profile.formality,
        "humor_style": profile.humor_style,
        "self_description": profile.self_description,
        "favorite_phrases": profile.favorite_phrases,
        "examples": profile.examples,
        "cached_phrases": profile.cached_phrases,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
    
    profile_path = profile_dir / "profile.json"
    profile_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    
    # Also save as human-readable markdown
    md_path = profile_dir / "profile.md"
    md_content = f"""# Perfil de Personalidad: {profile.name}

## Tono: {profile.tone}
## Formalidad: {profile.formality}
## Humor: {profile.humor_style}

## Autodescripción
{profile.self_description}

## Frases favoritas
{chr(10).join(f'- "{p}"' for p in profile.favorite_phrases)}

## Ejemplos de cómo habla
{chr(10).join(f'> {e}' for e in profile.examples)}
"""
    md_path.write_text(md_content)
    
    logger.info("Saved personality profile for voice %s", profile.voice_id)
    return profile_dir


def load_profile(voice_id: str, base_dir: Path) -> Optional[PersonalityProfile]:
    """Load personality profile from disk."""
    profile_path = base_dir / "personality" / voice_id / "profile.json"
    
    if not profile_path.exists():
        return None
    
    data = json.loads(profile_path.read_text())
    
    return PersonalityProfile(
        voice_id=data["voice_id"],
        name=data["name"],
        tone=data.get("tone", "casual"),
        formality=data.get("formality", "informal"),
        humor_style=data.get("humor_style", "none"),
        self_description=data.get("self_description", ""),
        favorite_phrases=data.get("favorite_phrases", []),
        examples=data.get("examples", []),
        cached_phrases=data.get("cached_phrases", {}),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )
