"""Voice cloning engine — Layer 1 of VoiceClone

Handles voice cloning and speech synthesis using multiple TTS backends.
Primary: Chatterbox TTS (MIT, SOTA quality)
Fallback: XTTS v2 (Coqui TTS, battle-tested)

Usage:
    from voice_engine.manager import EngineManager
    
    manager = EngineManager()
    manager.initialize()
    
    profile = manager.clone_voice(Path("audio.wav"), "maria")
    result = manager.synthesize("Hola mundo", profile)
"""

from .base import AudioFormat, EngineStatus, SynthesisResult, VoiceEngine, VoiceProfile
from .chatterbox_engine import ChatterboxEngine
from .xtts_engine import XTTSEngine
from .manager import EngineManager

__all__ = [
    "AudioFormat",
    "EngineStatus",
    "SynthesisResult",
    "VoiceEngine",
    "VoiceProfile",
    "ChatterboxEngine",
    "XTTSEngine",
    "EngineManager",
]
