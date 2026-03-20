"""Voice profile storage — manages cloned voices on disk.

Storage layout:
    ~/.voiceclone/
    ├── voices/
    │   └── {voice_id}/
    │       ├── reference.wav    ← original audio
    │       ├── embedding.pt     ← speaker embedding
    │       └── metadata.json    ← voice info
    ├── personality/
    │   └── {voice_id}/
    │       ├── profile.md
    │       ├── vocabulary.md
    │       └── cached_phrases/
    ├── models/
    │   └── chatterbox/
    └── config.json
"""

import json
import logging
from pathlib import Path
from typing import Optional

from voiceclone.engine.base import VoiceProfile

logger = logging.getLogger(__name__)

DEFAULT_BASE_DIR = Path.home() / ".voiceclone"


class VoiceStore:
    """Manages voice profiles on disk."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or DEFAULT_BASE_DIR
        self.voices_dir = self.base_dir / "voices"
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    def save(self, profile: VoiceProfile) -> Path:
        """Save a voice profile to disk.
        
        Returns path to the voice directory.
        """
        voice_dir = self.voices_dir / profile.voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            "voice_id": profile.voice_id,
            "name": profile.name,
            "engine": profile.engine,
            "reference_audio": str(profile.reference_audio_path),
            "embedding": str(profile.embedding_path) if profile.embedding_path else None,
            "created_at": profile.created_at,
            "duration_seconds": profile.duration_seconds,
            "quality_score": profile.quality_score,
            "metadata": profile.metadata,
        }
        
        metadata_path = voice_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        logger.info("Saved voice '%s' (id=%s) to %s", profile.name, profile.voice_id, voice_dir)
        return voice_dir

    def load(self, voice_id: str) -> VoiceProfile:
        """Load a voice profile from disk."""
        voice_dir = self.voices_dir / voice_id
        metadata_path = voice_dir / "metadata.json"
        
        if not metadata_path.exists():
            raise FileNotFoundError(f"Voice not found: {voice_id}")
        
        data = json.loads(metadata_path.read_text())
        
        return VoiceProfile(
            voice_id=data["voice_id"],
            name=data["name"],
            engine=data["engine"],
            reference_audio_path=Path(data["reference_audio"]),
            embedding_path=Path(data["embedding"]) if data.get("embedding") else None,
            created_at=data.get("created_at", ""),
            duration_seconds=data.get("duration_seconds", 0.0),
            quality_score=data.get("quality_score", 0.0),
            metadata=data.get("metadata", {}),
        )

    def list_voices(self) -> list[VoiceProfile]:
        """List all saved voices."""
        voices = []
        for voice_dir in sorted(self.voices_dir.iterdir()):
            if voice_dir.is_dir():
                try:
                    profile = self.load(voice_dir.name)
                    voices.append(profile)
                except Exception as e:
                    logger.warning("Failed to load voice %s: %s", voice_dir.name, e)
        return voices

    def delete(self, voice_id: str) -> bool:
        """Delete a voice profile."""
        voice_dir = self.voices_dir / voice_id
        if not voice_dir.exists():
            return False
        
        import shutil
        shutil.rmtree(voice_dir)
        
        # Also delete personality if exists
        personality_dir = self.base_dir / "personality" / voice_id
        if personality_dir.exists():
            shutil.rmtree(personality_dir)
        
        logger.info("Deleted voice: %s", voice_id)
        return True

    def exists(self, voice_id: str) -> bool:
        """Check if a voice exists."""
        return (self.voices_dir / voice_id / "metadata.json").exists()

    def get_voice_dir(self, voice_id: str) -> Path:
        """Get the directory path for a voice."""
        return self.voices_dir / voice_id
