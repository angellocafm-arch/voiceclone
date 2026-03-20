"""XTTS v2 engine adapter — fallback voice engine.

XTTS v2 by Coqui/Idiap (MPL 2.0 license):
- Zero-shot voice cloning from 6+ seconds
- 17 languages
- Good CPU performance
- Downloaded on-demand (not included in default install)
"""

import logging
from pathlib import Path
import numpy as np

from voiceclone.engine.base import VoiceEngine, VoiceProfile, EngineInfo

logger = logging.getLogger(__name__)

XTTS_SAMPLE_RATE = 24_000


class XTTSEngine(VoiceEngine):
    """XTTS v2 engine — fallback voice cloning engine.
    
    Used when Chatterbox is unavailable or the user requests it.
    Downloaded on demand to keep initial install size small.
    """

    def __init__(self) -> None:
        self._model = None
        self._initialized = False

    async def initialize(self, model_path: Path) -> None:
        """Load XTTS v2 model."""
        try:
            from TTS.api import TTS
            logger.info("Loading XTTS v2 model...")
            self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            self._initialized = True
            logger.info("XTTS v2 loaded successfully")
        except ImportError:
            raise RuntimeError(
                "XTTS v2 is not installed. "
                "Install with: pip install TTS"
            )

    async def clone_voice(
        self,
        audio: np.ndarray,
        sample_rate: int,
        name: str,
    ) -> VoiceProfile:
        """Clone voice using XTTS v2."""
        if not self._initialized:
            raise RuntimeError("XTTS v2 not initialized.")
        
        import uuid
        from datetime import datetime, timezone
        
        voice_id = str(uuid.uuid4())[:8]
        voice_dir = Path.home() / ".voiceclone" / "voices" / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Save reference audio
        import soundfile as sf
        ref_path = voice_dir / "reference.wav"
        sf.write(str(ref_path), audio, sample_rate)
        
        duration = len(audio) / sample_rate
        
        return VoiceProfile(
            voice_id=voice_id,
            name=name,
            engine="xtts-v2",
            reference_audio_path=ref_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration,
            quality_score=min(1.0, duration / 30.0),
        )

    async def synthesize(
        self,
        text: str,
        voice: VoiceProfile,
        output_format: str = "wav",
    ) -> tuple[np.ndarray, int]:
        """Synthesize text with XTTS v2."""
        if not self._initialized:
            raise RuntimeError("XTTS v2 not initialized.")
        
        # XTTS v2 uses the reference audio file directly
        wav = self._model.tts(
            text=text,
            speaker_wav=str(voice.reference_audio_path),
            language="es",
        )
        
        audio_out = np.array(wav, dtype=np.float32)
        return audio_out, XTTS_SAMPLE_RATE

    def get_info(self) -> EngineInfo:
        return EngineInfo(
            name="XTTS v2",
            version="2.0.0",
            license="MPL-2.0",
            languages=[
                "en", "es", "fr", "de", "it", "pt", "pl", "tr",
                "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko", "hi",
            ],
            model_size_mb=1800,
            requires_gpu=False,
            supports_streaming=False,
        )

    def is_available(self) -> bool:
        try:
            import TTS  # noqa: F401
            return self._initialized
        except ImportError:
            return False

    async def estimate_quality(
        self,
        original_audio: np.ndarray,
        synthesized_audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """Basic quality estimation."""
        min_len = min(len(original_audio), len(synthesized_audio))
        if min_len == 0:
            return 0.0
        orig_rms = np.sqrt(np.mean(original_audio[:min_len] ** 2))
        synth_rms = np.sqrt(np.mean(synthesized_audio[:min_len] ** 2))
        if orig_rms == 0 or synth_rms == 0:
            return 0.0
        return float(min(orig_rms, synth_rms) / max(orig_rms, synth_rms))
