"""Engine Manager — Adapter pattern with automatic fallback

The EngineManager is the primary interface consumers use.
It tries the primary engine (Chatterbox) first, and falls back
to secondary engines (XTTS v2) if the primary fails.

Usage:
    manager = EngineManager()
    manager.initialize()  # Loads best available engine
    
    # Clone
    profile = manager.clone_voice(audio_path, "maria")
    
    # Speak
    result = manager.synthesize("Hola mundo", profile)
    
    # The consumer never knows which engine is running.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from .base import (
    AudioFormat,
    EngineStatus,
    SynthesisResult,
    VoiceEngine,
    VoiceProfile,
)
from .chatterbox_engine import ChatterboxEngine
from .xtts_engine import XTTSEngine

logger = logging.getLogger(__name__)

# Default storage location
DEFAULT_VOICECLONE_DIR = Path.home() / ".voiceclone"


class EngineManager:
    """Manages voice engines with automatic fallback
    
    Priority:
    1. Chatterbox TTS (MIT, best quality, emotion control)
    2. XTTS v2 (fallback, good quality, works on CPU)
    
    The manager presents a unified interface regardless of which
    engine is active. Voices are stored in ~/.voiceclone/voices/
    and are engine-agnostic (reference.wav + metadata).
    """

    def __init__(
        self,
        voiceclone_dir: Optional[Path] = None,
        device: Optional[str] = None,
        preferred_engine: Optional[str] = None,
    ):
        """
        Args:
            voiceclone_dir: Root directory for all VoiceClone data
            device: Force compute device (cuda/mps/cpu/None=auto)
            preferred_engine: Force specific engine ("chatterbox" or "xtts-v2")
        """
        self.voiceclone_dir = voiceclone_dir or DEFAULT_VOICECLONE_DIR
        self.voices_dir = self.voiceclone_dir / "voices"
        self.models_dir = self.voiceclone_dir / "models"
        self.config_path = self.voiceclone_dir / "config.json"

        self._device = device
        self._preferred_engine = preferred_engine

        # Engine instances
        self._engines: list[VoiceEngine] = []
        self._active_engine: Optional[VoiceEngine] = None

        # Ensure directories exist
        self.voiceclone_dir.mkdir(parents=True, exist_ok=True)
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    # ─── Initialization ──────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize the best available engine
        
        Tries engines in priority order. First one that loads successfully
        becomes the active engine.
        
        Returns:
            True if at least one engine loaded successfully
        """
        logger.info("Initializing VoiceClone engine manager...")

        # Build engine list based on preference
        if self._preferred_engine == "xtts-v2":
            self._engines = [
                XTTSEngine(device=self._device),
                ChatterboxEngine(device=self._device),
            ]
        else:
            self._engines = [
                ChatterboxEngine(device=self._device),
                XTTSEngine(device=self._device),
            ]

        # Try each engine
        for engine in self._engines:
            logger.info(f"Trying engine: {engine.name}...")
            try:
                if engine.load_model():
                    self._active_engine = engine
                    logger.info(f"✅ Active engine: {engine.name} on {engine.device}")
                    self._save_config()
                    return True
                else:
                    logger.warning(f"❌ {engine.name} failed to load")
            except Exception as e:
                logger.warning(f"❌ {engine.name} error: {e}")

        logger.error("No voice engine could be loaded!")
        return False

    def _save_config(self) -> None:
        """Save current configuration"""
        config = {
            "active_engine": self._active_engine.engine_id if self._active_engine else None,
            "device": self._active_engine.device if self._active_engine else None,
            "voiceclone_dir": str(self.voiceclone_dir),
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)

    # ─── Engine Access ────────────────────────────────────────────

    @property
    def active_engine(self) -> Optional[VoiceEngine]:
        """Currently active engine"""
        return self._active_engine

    @property
    def engine_name(self) -> str:
        """Name of active engine"""
        if self._active_engine:
            return self._active_engine.name
        return "None"

    @property
    def is_ready(self) -> bool:
        """Check if an engine is loaded and ready"""
        return self._active_engine is not None and self._active_engine.is_ready()

    def _ensure_ready(self) -> VoiceEngine:
        """Ensure an engine is ready, raise if not"""
        if not self.is_ready or self._active_engine is None:
            raise RuntimeError(
                "No voice engine loaded. Call initialize() first, "
                "or install chatterbox-tts: pip install chatterbox-tts"
            )
        return self._active_engine

    # ─── Voice Cloning ────────────────────────────────────────────

    def clone_voice(
        self,
        audio_path: Path,
        voice_name: str,
    ) -> VoiceProfile:
        """Clone a voice from audio
        
        Args:
            audio_path: Path to reference audio (3-120s recommended)
            voice_name: Name for the cloned voice
            
        Returns:
            VoiceProfile with voice metadata
        """
        engine = self._ensure_ready()
        return engine.clone_voice(audio_path, voice_name, self.voices_dir)

    # ─── Speech Synthesis ─────────────────────────────────────────

    def synthesize(
        self,
        text: str,
        voice: VoiceProfile,
        output_format: AudioFormat = AudioFormat.WAV,
        exaggeration: float = 0.5,
        cfg: float = 0.5,
    ) -> SynthesisResult:
        """Synthesize speech with automatic engine fallback
        
        If the active engine fails, tries the fallback engine.
        """
        engine = self._ensure_ready()

        try:
            return engine.synthesize(text, voice, output_format, exaggeration, cfg)
        except RuntimeError as primary_error:
            # Try fallback
            fallback = self._get_fallback()
            if fallback is None:
                raise primary_error

            logger.warning(
                f"Primary engine ({engine.name}) failed, "
                f"trying fallback ({fallback.name})..."
            )
            try:
                if not fallback.is_ready():
                    fallback.load_model()
                return fallback.synthesize(text, voice, output_format, exaggeration, cfg)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise primary_error  # Re-raise original error

    def synthesize_to_file(
        self,
        text: str,
        voice: VoiceProfile,
        output_path: Path,
        exaggeration: float = 0.5,
        cfg: float = 0.5,
    ) -> Path:
        """Synthesize and save to file"""
        engine = self._ensure_ready()

        # Use engine-specific file output if available
        if hasattr(engine, "synthesize_to_file"):
            return engine.synthesize_to_file(
                text, voice, output_path, exaggeration, cfg
            )

        # Fallback: synthesize to bytes, then save
        result = self.synthesize(text, voice, AudioFormat.WAV, exaggeration, cfg)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(result.audio_data)
        return output_path

    def _get_fallback(self) -> Optional[VoiceEngine]:
        """Get fallback engine (the one that's not active)"""
        for engine in self._engines:
            if engine != self._active_engine:
                return engine
        return None

    # ─── Voice Management ─────────────────────────────────────────

    def list_voices(self) -> list[VoiceProfile]:
        """List all available cloned voices"""
        engine = self._ensure_ready()
        return engine.list_voices(self.voices_dir)

    def get_voice(self, voice_name: str) -> Optional[VoiceProfile]:
        """Get a specific voice by name"""
        for voice in self.list_voices():
            if voice.name == voice_name or voice.voice_id == voice_name:
                return voice
        return None

    def delete_voice(self, voice_name: str) -> bool:
        """Delete a voice by name"""
        voice = self.get_voice(voice_name)
        if voice is None:
            logger.warning(f"Voice '{voice_name}' not found")
            return False

        engine = self._ensure_ready()
        return engine.delete_voice(voice)

    # ─── Status ───────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get full status of the engine manager"""
        voices = []
        try:
            voices = self.list_voices()
        except Exception:
            pass

        engine_info = {}
        if self._active_engine and hasattr(self._active_engine, "get_model_info"):
            engine_info = self._active_engine.get_model_info()

        return {
            "ready": self.is_ready,
            "active_engine": engine_info,
            "available_engines": [
                {
                    "id": e.engine_id,
                    "name": e.name,
                    "status": e.status.value,
                }
                for e in self._engines
            ],
            "voices_count": len(voices),
            "voices_dir": str(self.voices_dir),
            "voiceclone_dir": str(self.voiceclone_dir),
        }

    # ─── Cleanup ──────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Unload all engines and free resources"""
        for engine in self._engines:
            try:
                engine.unload_model()
            except Exception:
                pass
        self._active_engine = None
        logger.info("Engine manager shut down")
