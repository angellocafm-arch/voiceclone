"""Abstract base class for voice engines"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VoiceProfile:
    """Profile of a cloned voice"""
    name: str
    path: Path  # Location of voice model
    language: str = "es"  # Spanish default
    quality_score: Optional[float] = None  # MOS score if available
    created_at: Optional[str] = None
    

class VoiceEngine(ABC):
    """Abstract voice engine interface"""
    
    @abstractmethod
    def clone_voice(self, audio_input: Path, voice_name: str) -> VoiceProfile:
        """Clone a voice from audio input
        
        Args:
            audio_input: Path to audio file (wav, m4a, mp3)
            voice_name: Name for the cloned voice
            
        Returns:
            VoiceProfile with cloned voice info
        """
        pass
    
    @abstractmethod
    def synthesize(self, text: str, voice: VoiceProfile) -> bytes:
        """Synthesize audio with cloned voice
        
        Args:
            text: Text to synthesize
            voice: VoiceProfile to use
            
        Returns:
            Audio bytes (wav format)
        """
        pass
    
    @abstractmethod
    def list_voices(self) -> list[VoiceProfile]:
        """List all available cloned voices"""
        pass
    
    @abstractmethod
    def delete_voice(self, voice_name: str) -> bool:
        """Delete a cloned voice"""
        pass
