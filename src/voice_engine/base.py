"""Abstract base class for voice engines — Layer 1 of VoiceClone

Defines the interface that ALL voice engines must implement.
This enables the Engine Adapter pattern: swap Chatterbox → XTTS → future models
without changing any consumer code.

Reference: ~/clawd/projects/voiceclone/docs/arquitectura-completa.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime


class AudioFormat(Enum):
    """Supported output audio formats"""
    WAV = "wav"
    OGG = "ogg"
    MP3 = "mp3"


class EngineStatus(Enum):
    """Engine loading states"""
    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


@dataclass
class VoiceProfile:
    """Profile of a cloned voice
    
    Stored at: ~/.voiceclone/voices/{name}/
    Contents:
        - reference.wav    — Original audio used for cloning
        - embedding.pt     — Speaker embedding (torch tensor)
        - metadata.json    — This dataclass serialized
    """
    name: str
    voice_id: str  # UUID for API references
    path: Path  # Directory containing voice files
    language: str = "es"
    quality_score: Optional[float] = None  # MOS score (1-5) if available
    duration_seconds: Optional[float] = None  # Duration of reference audio
    engine: str = "chatterbox"  # Which engine created this voice
    has_personality: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sample_rate: int = 24000  # Default Chatterbox sample rate

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict"""
        return {
            "name": self.name,
            "voice_id": self.voice_id,
            "path": str(self.path),
            "language": self.language,
            "quality_score": self.quality_score,
            "duration_seconds": self.duration_seconds,
            "engine": self.engine,
            "has_personality": self.has_personality,
            "created_at": self.created_at,
            "sample_rate": self.sample_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """Deserialize from dict"""
        data = data.copy()
        data["path"] = Path(data["path"])
        return cls(**data)


@dataclass
class SynthesisResult:
    """Result of a synthesis operation"""
    audio_data: bytes  # Raw audio bytes
    sample_rate: int
    duration_seconds: float
    format: AudioFormat = AudioFormat.WAV
    voice_name: str = ""
    text: str = ""


class VoiceEngine(ABC):
    """Abstract voice engine interface
    
    All voice engines (Chatterbox, XTTS, future models) must implement this.
    The EngineManager uses this interface to provide automatic fallback.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine display name (e.g., 'Chatterbox TTS')"""
        pass

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Engine identifier (e.g., 'chatterbox')"""
        pass

    @property
    @abstractmethod
    def status(self) -> EngineStatus:
        """Current engine status"""
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Native sample rate of this engine's output"""
        pass

    @abstractmethod
    def load_model(self) -> bool:
        """Load the TTS model into memory
        
        Returns:
            True if model loaded successfully
            
        Raises:
            RuntimeError: If model files not found or incompatible hardware
        """
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unload model from memory to free resources"""
        pass

    @abstractmethod
    def clone_voice(
        self,
        audio_path: Path,
        voice_name: str,
        output_dir: Path,
    ) -> VoiceProfile:
        """Clone a voice from audio input
        
        Args:
            audio_path: Path to reference audio file (wav, mp3, ogg, m4a)
            voice_name: Human-friendly name for the cloned voice
            output_dir: Directory to save voice files
            
        Returns:
            VoiceProfile with cloned voice metadata
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio is too short (<3s) or poor quality
            RuntimeError: If cloning fails
        """
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: VoiceProfile,
        output_format: AudioFormat = AudioFormat.WAV,
        exaggeration: float = 0.5,
        cfg: float = 0.5,
    ) -> SynthesisResult:
        """Synthesize speech from text using a cloned voice
        
        Args:
            text: Text to convert to speech (max ~500 chars recommended)
            voice: VoiceProfile to use for synthesis
            output_format: Desired output format
            exaggeration: Emotional expressiveness (0.0-1.0, Chatterbox-specific)
            cfg: Classifier-free guidance strength (0.0-1.0, Chatterbox-specific)
            
        Returns:
            SynthesisResult with audio data and metadata
            
        Raises:
            ValueError: If text is empty or voice not found
            RuntimeError: If synthesis fails
        """
        pass

    @abstractmethod
    def list_voices(self, voices_dir: Path) -> list[VoiceProfile]:
        """List all cloned voices available in the voices directory
        
        Args:
            voices_dir: Root directory containing voice subdirectories
            
        Returns:
            List of VoiceProfile objects
        """
        pass

    @abstractmethod
    def delete_voice(self, voice: VoiceProfile) -> bool:
        """Delete a cloned voice and all its files
        
        Args:
            voice: VoiceProfile to delete
            
        Returns:
            True if deleted successfully
        """
        pass

    def is_ready(self) -> bool:
        """Check if engine is loaded and ready to use"""
        return self.status == EngineStatus.READY
