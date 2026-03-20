"""XTTS v2 engine implementation — Fallback voice engine for VoiceClone

XTTS v2 by Coqui AI:
- Zero-shot voice cloning from short reference audio
- Supports 17 languages
- Works well on CPU (slower but functional)
- Apache 2.0 compatible license
- Good fallback when Chatterbox is unavailable

API: TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
- tts.tts_to_file(text, speaker_wav=..., language=..., file_path=...)
- wav = tts.tts(text, speaker_wav=..., language=...)

Reference: https://github.com/coqui-ai/TTS
Note: Original Coqui AI dissolved, but the library is maintained by community forks.
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import (
    AudioFormat,
    EngineStatus,
    SynthesisResult,
    VoiceEngine,
    VoiceProfile,
)
from .audio_utils import (
    convert_to_wav,
    estimate_quality,
    validate_audio_file,
    wav_bytes_to_format,
)

logger = logging.getLogger(__name__)

# XTTS v2 native sample rate
XTTS_SR = 24000

# Model identifier
XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

# Supported languages (ISO 639-1 codes)
XTTS_LANGUAGES = {
    "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru",
    "nl", "cs", "ar", "zh", "ja", "hu", "ko",
}


class XTTSEngine(VoiceEngine):
    """Voice engine using XTTS v2 (Coqui TTS) — fallback engine
    
    Used when Chatterbox TTS is not available (e.g., GPU too old,
    dependency conflicts, or user preference).
    
    Slightly lower quality than Chatterbox but more battle-tested
    and works reliably on CPU.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        model_dir: Optional[Path] = None,
    ):
        self._device = device
        self._model_dir = model_dir
        self._model = None  # TTS instance
        self._status = EngineStatus.UNINITIALIZED
        self._detected_device = None

    # ─── Properties ───────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "XTTS v2"

    @property
    def engine_id(self) -> str:
        return "xtts-v2"

    @property
    def status(self) -> EngineStatus:
        return self._status

    @property
    def sample_rate(self) -> int:
        return XTTS_SR

    @property
    def device(self) -> str:
        if self._detected_device:
            return self._detected_device
        return self._device or "auto"

    # ─── Model Management ─────────────────────────────────────────

    def load_model(self) -> bool:
        """Load XTTS v2 model
        
        Downloads model on first run (~1.8 GB).
        """
        if self._status == EngineStatus.READY and self._model is not None:
            return True

        self._status = EngineStatus.LOADING
        logger.info("Loading XTTS v2 model...")

        try:
            from TTS.api import TTS

            # Detect device
            device = self._detect_device()
            self._detected_device = device

            # Determine if GPU should be used
            use_gpu = device in ("cuda", "mps")

            # Load model
            self._model = TTS(model_name=XTTS_MODEL, gpu=use_gpu)

            self._status = EngineStatus.READY
            logger.info(f"✅ XTTS v2 loaded on {device}")
            return True

        except ImportError:
            self._status = EngineStatus.ERROR
            logger.error(
                "Coqui TTS not installed. Install with: pip install TTS"
            )
            return False

        except Exception as e:
            self._status = EngineStatus.ERROR
            logger.error(f"Failed to load XTTS v2: {e}")
            return False

    def _detect_device(self) -> str:
        """Detect best available compute device"""
        if self._device:
            return self._device

        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    def unload_model(self) -> None:
        """Unload model"""
        if self._model is not None:
            del self._model
            self._model = None
            self._status = EngineStatus.UNINITIALIZED
            logger.info("XTTS v2 model unloaded")

    def _ensure_loaded(self) -> None:
        if not self.is_ready():
            if not self.load_model():
                raise RuntimeError("XTTS v2 model could not be loaded")

    # ─── Voice Cloning ────────────────────────────────────────────

    def clone_voice(
        self,
        audio_path: Path,
        voice_name: str,
        output_dir: Path,
    ) -> VoiceProfile:
        """Clone voice using XTTS v2
        
        XTTS v2 uses reference audio directly (zero-shot), similar to 
        Chatterbox. No pre-training needed — just save the reference audio.
        """
        self._ensure_loaded()

        safe_name = voice_name.strip().lower().replace(" ", "-")
        if not safe_name:
            raise ValueError("Voice name cannot be empty")

        voice_dir = output_dir / safe_name
        voice_dir.mkdir(parents=True, exist_ok=True)

        # Validate
        validation = validate_audio_file(audio_path)
        if not validation["valid"]:
            raise ValueError(
                f"Audio validation failed: {'; '.join(validation['errors'])}"
            )

        # Convert to WAV
        reference_path = voice_dir / "reference.wav"
        convert_to_wav(audio_path, reference_path, target_sr=XTTS_SR, mono=True)

        # Quality estimate
        quality = estimate_quality(reference_path)

        # Create profile
        voice_id = str(uuid.uuid4())[:8]
        profile = VoiceProfile(
            name=safe_name,
            voice_id=voice_id,
            path=voice_dir,
            language="es",
            quality_score=quality,
            duration_seconds=validation.get("duration_seconds", 0),
            engine=self.engine_id,
            has_personality=False,
            created_at=datetime.now().isoformat(),
            sample_rate=XTTS_SR,
        )

        # Save metadata
        metadata_path = voice_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        (voice_dir / "samples").mkdir(exist_ok=True)

        logger.info(f"✅ Voice '{safe_name}' cloned with XTTS v2")
        return profile

    # ─── Synthesis ────────────────────────────────────────────────

    def synthesize(
        self,
        text: str,
        voice: VoiceProfile,
        output_format: AudioFormat = AudioFormat.WAV,
        exaggeration: float = 0.5,  # Not used by XTTS, kept for interface compat
        cfg: float = 0.5,  # Not used by XTTS
    ) -> SynthesisResult:
        """Synthesize speech using XTTS v2"""
        self._ensure_loaded()

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        reference_path = voice.path / "reference.wav"
        if not reference_path.exists():
            raise FileNotFoundError(
                f"Reference audio not found: {reference_path}"
            )

        # Determine language code
        lang = voice.language if voice.language in XTTS_LANGUAGES else "en"

        logger.info(
            f"Synthesizing with XTTS v2: {len(text)} chars, "
            f"voice='{voice.name}', lang='{lang}'"
        )

        try:
            import numpy as np

            # XTTS tts() returns a list of floats
            wav_list = self._model.tts(
                text=text,
                speaker_wav=str(reference_path),
                language=lang,
            )

            wav_array = np.array(wav_list, dtype=np.float32)
            duration = len(wav_array) / XTTS_SR

            audio_bytes = wav_array.tobytes()

            if output_format != AudioFormat.WAV:
                audio_bytes = wav_bytes_to_format(
                    audio_bytes, XTTS_SR, output_format.value
                )

            return SynthesisResult(
                audio_data=audio_bytes,
                sample_rate=XTTS_SR,
                duration_seconds=duration,
                format=output_format,
                voice_name=voice.name,
                text=text,
            )

        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            raise RuntimeError(f"XTTS v2 synthesis failed: {e}") from e

    def synthesize_to_file(
        self,
        text: str,
        voice: VoiceProfile,
        output_path: Path,
    ) -> Path:
        """Synthesize and save to file using XTTS native file output"""
        self._ensure_loaded()

        reference_path = voice.path / "reference.wav"
        if not reference_path.exists():
            raise FileNotFoundError(f"Reference audio not found: {reference_path}")

        lang = voice.language if voice.language in XTTS_LANGUAGES else "en"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._model.tts_to_file(
            text=text,
            speaker_wav=str(reference_path),
            language=lang,
            file_path=str(output_path),
        )

        logger.info(f"✅ Saved XTTS audio to {output_path}")
        return output_path

    # ─── Voice Management ─────────────────────────────────────────

    def list_voices(self, voices_dir: Path) -> list[VoiceProfile]:
        """List all cloned voices"""
        voices = []
        if not voices_dir.exists():
            return voices

        for voice_dir in sorted(voices_dir.iterdir()):
            if not voice_dir.is_dir():
                continue
            metadata_path = voice_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                voices.append(VoiceProfile.from_dict(data))
            except Exception as e:
                logger.warning(f"Could not load voice from {voice_dir}: {e}")

        return voices

    def delete_voice(self, voice: VoiceProfile) -> bool:
        """Delete voice and files"""
        if voice.path.exists():
            shutil.rmtree(voice.path)
            logger.info(f"✅ Deleted voice '{voice.name}'")
            return True
        return False

    def get_model_info(self) -> dict:
        return {
            "engine": self.engine_id,
            "name": self.name,
            "status": self._status.value,
            "device": self.device,
            "sample_rate": XTTS_SR,
            "model_loaded": self._model is not None,
            "features": {
                "zero_shot_cloning": True,
                "emotion_control": False,
                "paralinguistic_tags": False,
                "watermarking": False,
                "languages": "17",
            },
        }
