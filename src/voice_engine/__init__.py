"""Voice cloning engine - Layer 1 of VoiceClone

Handles voice recording, cloning, and synthesis using Chatterbox TTS.
"""

from .base import VoiceEngine
from .chatterbox_engine import ChatterboxEngine

__all__ = ["VoiceEngine", "ChatterboxEngine"]
