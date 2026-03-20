"""Chatterbox TTS engine implementation — Primary voice engine for VoiceClone

Chatterbox TTS by Resemble AI (MIT License):
- Zero-shot voice cloning from 3-30s of reference audio
- 24kHz output, high quality (MOS ~4.2)
- Supports emotion exaggeration and CFG control
- Built-in watermarking (PerTh Watermarker)
- 23+ language support
- Paralinguistic tags: [laugh], [chuckle], [cough], etc.

API: chatterbox.tts.ChatterboxTTS
- model = ChatterboxTTS.from_pretrained(device="cuda"|"cpu"|"mps")
- wav = model.generate(text=..., audio_prompt_path=..., exaggeration=0.5, cfg=0.5)
- torchaudio.save(path, wav, model.sr)

Reference: https://github.com/resemble-ai/chatterbox
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
    DEFAULT_SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

# Chatterbox native sample rate
CHATTERBOX_SR = 24000

# Model size info for download progress
CHATTERBOX_MODEL_SIZE_GB = 2.1


class ChatterboxEngine(VoiceEngine):
    """Voice engine using Chatterbox TTS (MIT, SOTA voice cloning)
    
    This is the primary engine for VoiceClone. Falls back to XTTS v2
    via the EngineManager if Chatterbox is unavailable.
    
    Storage layout per voice:
        ~/.voiceclone/voices/{voice_name}/
        ├── reference.wav       ← Processed reference audio (24kHz mono)
        ├── metadata.json       ← VoiceProfile serialized
        └── samples/            ← Generated sample audio files
    """

    def __init__(
        self,
        device: Optional[str] = None,
        model_dir: Optional[Path] = None,
    ):
        """Initialize Chatterbox engine
        
        Args:
            device: Compute device — "cuda", "mps", "cpu", or None (auto-detect)
            model_dir: Directory for model files (default: ~/.voiceclone/models/chatterbox/)
        """
        self._device = device
        self._model_dir = model_dir
        self._model = None  # ChatterboxTTS instance (lazy loaded)
        self._status = EngineStatus.UNINITIALIZED
        self._detected_device = None

    # ─── Properties ───────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "Chatterbox TTS"

    @property
    def engine_id(self) -> str:
        return "chatterbox"

    @property
    def status(self) -> EngineStatus:
        return self._status

    @property
    def sample_rate(self) -> int:
        if self._model is not None:
            return self._model.sr
        return CHATTERBOX_SR

    @property
    def device(self) -> str:
        """Actual compute device being used"""
        if self._detected_device:
            return self._detected_device
        return self._device or "auto"

    # ─── Model Management ─────────────────────────────────────────

    def load_model(self) -> bool:
        """Load Chatterbox TTS model
        
        Auto-detects best available device:
        1. CUDA (NVIDIA GPU) — fastest
        2. MPS (Apple Silicon) — good performance
        3. CPU — slowest but always works
        
        Downloads model on first run (~2.1 GB).
        
        Returns:
            True if model loaded successfully
        """
        if self._status == EngineStatus.READY and self._model is not None:
            logger.info("Chatterbox model already loaded")
            return True

        self._status = EngineStatus.LOADING
        logger.info("Loading Chatterbox TTS model...")

        try:
            import torch
            from chatterbox.tts import ChatterboxTTS

            # Auto-detect best device
            device = self._detect_device()
            self._detected_device = device
            logger.info(f"Using device: {device}")

            # Load model (downloads on first run)
            self._model = ChatterboxTTS.from_pretrained(device=device)

            self._status = EngineStatus.READY
            logger.info(
                f"✅ Chatterbox loaded on {device} "
                f"(sample rate: {self._model.sr}Hz)"
            )
            return True

        except ImportError as e:
            self._status = EngineStatus.ERROR
            logger.error(
                f"Chatterbox TTS not installed: {e}. "
                f"Install with: pip install chatterbox-tts"
            )
            return False

        except Exception as e:
            self._status = EngineStatus.ERROR
            logger.error(f"Failed to load Chatterbox: {e}")
            return False

    def _detect_device(self) -> str:
        """Detect best available compute device"""
        if self._device:
            return self._device

        import torch

        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def unload_model(self) -> None:
        """Unload model to free memory"""
        if self._model is not None:
            del self._model
            self._model = None

            # Clear GPU memory if applicable
            try:
                import torch
                if self._detected_device == "cuda":
                    torch.cuda.empty_cache()
                elif self._detected_device == "mps":
                    torch.mps.empty_cache()
            except Exception:
                pass

            self._status = EngineStatus.UNINITIALIZED
            logger.info("Chatterbox model unloaded")

    def _ensure_loaded(self) -> None:
        """Ensure model is loaded, load if not"""
        if not self.is_ready():
            if not self.load_model():
                raise RuntimeError(
                    "Chatterbox model could not be loaded. "
                    "Check installation: pip install chatterbox-tts"
                )

    # ─── Voice Cloning ────────────────────────────────────────────

    def clone_voice(
        self,
        audio_path: Path,
        voice_name: str,
        output_dir: Path,
    ) -> VoiceProfile:
        """Clone a voice using Chatterbox zero-shot cloning
        
        Process:
        1. Validate input audio (format, duration, quality)
        2. Convert to WAV 24kHz mono if needed
        3. Save reference audio in voice directory
        4. Create metadata JSON
        5. Generate test sample to verify cloning
        
        The actual speaker embedding is computed on-the-fly by Chatterbox
        each time we synthesize — it uses the reference audio directly
        (no pre-computed embedding needed).
        
        Args:
            audio_path: Path to reference audio (3-120s, any supported format)
            voice_name: Name for the voice (e.g., "maria", "abuela")
            output_dir: Root voices directory (~/.voiceclone/voices/)
            
        Returns:
            VoiceProfile with voice metadata
        """
        self._ensure_loaded()

        # Sanitize voice name
        safe_name = voice_name.strip().lower().replace(" ", "-")
        if not safe_name:
            raise ValueError("Voice name cannot be empty")

        # Create voice directory
        voice_dir = output_dir / safe_name
        voice_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cloning voice '{safe_name}' from {audio_path.name}")

        # Step 1: Validate input audio
        validation = validate_audio_file(audio_path)
        if not validation["valid"]:
            raise ValueError(
                f"Audio validation failed: {'; '.join(validation['errors'])}"
            )
        for warning in validation.get("warnings", []):
            logger.warning(warning)

        # Step 2: Convert to WAV 24kHz mono
        reference_path = voice_dir / "reference.wav"
        convert_to_wav(
            audio_path,
            reference_path,
            target_sr=CHATTERBOX_SR,
            mono=True,
        )
        logger.info(f"Reference audio saved: {reference_path}")

        # Step 3: Estimate quality
        quality = estimate_quality(reference_path)
        logger.info(f"Audio quality score: {quality:.2f}")

        # Step 4: Create voice profile
        voice_id = str(uuid.uuid4())[:8]
        profile = VoiceProfile(
            name=safe_name,
            voice_id=voice_id,
            path=voice_dir,
            language="es",  # Default, could be auto-detected
            quality_score=quality,
            duration_seconds=validation.get("duration_seconds", 0),
            engine=self.engine_id,
            has_personality=False,
            created_at=datetime.now().isoformat(),
            sample_rate=CHATTERBOX_SR,
        )

        # Step 5: Save metadata
        metadata_path = voice_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        # Step 6: Create samples directory
        (voice_dir / "samples").mkdir(exist_ok=True)

        logger.info(f"✅ Voice '{safe_name}' cloned (id: {voice_id}, quality: {quality:.2f})")
        return profile

    # ─── Speech Synthesis ─────────────────────────────────────────

    def synthesize(
        self,
        text: str,
        voice: VoiceProfile,
        output_format: AudioFormat = AudioFormat.WAV,
        exaggeration: float = 0.5,
        cfg: float = 0.5,
    ) -> SynthesisResult:
        """Synthesize speech using Chatterbox TTS
        
        Pipeline:
        1. Load reference audio from voice profile
        2. Generate speech with Chatterbox model.generate()
        3. Convert to desired output format
        4. Return audio bytes with metadata
        
        Args:
            text: Text to speak (supports paralinguistic tags like [laugh])
            voice: VoiceProfile with reference audio
            output_format: WAV, OGG, or MP3
            exaggeration: Emotion intensity 0.0 (flat) to 1.0 (dramatic)
            cfg: Voice adherence 0.0 (creative) to 1.0 (strict match)
            
        Returns:
            SynthesisResult with audio data
        """
        self._ensure_loaded()

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Find reference audio
        reference_path = voice.path / "reference.wav"
        if not reference_path.exists():
            raise FileNotFoundError(
                f"Reference audio not found for voice '{voice.name}': {reference_path}"
            )

        logger.info(
            f"Synthesizing {len(text)} chars with voice '{voice.name}' "
            f"(exagg={exaggeration}, cfg={cfg})"
        )

        try:
            import torch
            import torchaudio
            import numpy as np

            # Generate speech
            wav_tensor = self._model.generate(
                text=text,
                audio_prompt_path=str(reference_path),
                exaggeration=exaggeration,
                cfg=cfg,
            )

            # Convert tensor to numpy array
            if isinstance(wav_tensor, torch.Tensor):
                wav_array = wav_tensor.cpu().numpy()
            else:
                wav_array = np.array(wav_tensor)

            # Ensure correct shape (1D or 2D with channels first)
            if wav_array.ndim == 2:
                wav_array = wav_array.squeeze()
            wav_array = wav_array.astype(np.float32)

            # Calculate duration
            duration = len(wav_array) / self._model.sr

            # Convert to bytes
            audio_bytes = wav_array.tobytes()

            # Convert format if needed
            if output_format != AudioFormat.WAV:
                audio_bytes = wav_bytes_to_format(
                    audio_bytes, self._model.sr, output_format.value
                )

            result = SynthesisResult(
                audio_data=audio_bytes,
                sample_rate=self._model.sr,
                duration_seconds=duration,
                format=output_format,
                voice_name=voice.name,
                text=text,
            )

            logger.info(
                f"✅ Synthesized {duration:.1f}s audio for '{voice.name}'"
            )
            return result

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise RuntimeError(f"Chatterbox synthesis failed: {e}") from e

    def synthesize_to_file(
        self,
        text: str,
        voice: VoiceProfile,
        output_path: Path,
        exaggeration: float = 0.5,
        cfg: float = 0.5,
    ) -> Path:
        """Synthesize speech and save directly to file
        
        More efficient than synthesize() when you know you want a file,
        because it uses torchaudio.save() directly.
        
        Args:
            text: Text to speak
            voice: VoiceProfile to use
            output_path: Where to save the audio file
            exaggeration: Emotion intensity
            cfg: Voice adherence
            
        Returns:
            Path to saved audio file
        """
        self._ensure_loaded()

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        reference_path = voice.path / "reference.wav"
        if not reference_path.exists():
            raise FileNotFoundError(
                f"Reference audio not found: {reference_path}"
            )

        try:
            import torchaudio

            wav_tensor = self._model.generate(
                text=text,
                audio_prompt_path=str(reference_path),
                exaggeration=exaggeration,
                cfg=cfg,
            )

            # Ensure tensor shape is correct for torchaudio.save
            if wav_tensor.ndim == 1:
                wav_tensor = wav_tensor.unsqueeze(0)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            torchaudio.save(str(output_path), wav_tensor, self._model.sr)

            logger.info(f"✅ Saved audio to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Synthesis to file failed: {e}")
            raise RuntimeError(f"Chatterbox synthesis failed: {e}") from e

    # ─── Voice Management ─────────────────────────────────────────

    def list_voices(self, voices_dir: Path) -> list[VoiceProfile]:
        """List all cloned voices in the voices directory"""
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
                profile = VoiceProfile.from_dict(data)
                voices.append(profile)
            except Exception as e:
                logger.warning(f"Could not load voice from {voice_dir}: {e}")
                continue

        return voices

    def get_voice(self, voice_name: str, voices_dir: Path) -> Optional[VoiceProfile]:
        """Get a specific voice by name"""
        voice_dir = voices_dir / voice_name
        metadata_path = voice_dir / "metadata.json"

        if not metadata_path.exists():
            return None

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return VoiceProfile.from_dict(data)

    def delete_voice(self, voice: VoiceProfile) -> bool:
        """Delete a cloned voice and all its files"""
        if voice.path.exists():
            shutil.rmtree(voice.path)
            logger.info(f"✅ Deleted voice '{voice.name}' from {voice.path}")
            return True
        return False

    # ─── Utility ──────────────────────────────────────────────────

    def generate_test_sample(
        self,
        voice: VoiceProfile,
        text: Optional[str] = None,
    ) -> Path:
        """Generate a test sample for a cloned voice
        
        Saves to voice_dir/samples/test.wav
        
        Args:
            voice: Voice to test
            text: Custom test text (or default greeting)
            
        Returns:
            Path to generated test sample
        """
        if text is None:
            text = "Hola, esta es mi voz clonada. ¿Suena bien?"

        sample_path = voice.path / "samples" / "test.wav"
        return self.synthesize_to_file(text, voice, sample_path)

    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return {
            "engine": self.engine_id,
            "name": self.name,
            "status": self._status.value,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "model_loaded": self._model is not None,
            "model_size_gb": CHATTERBOX_MODEL_SIZE_GB,
            "features": {
                "zero_shot_cloning": True,
                "emotion_control": True,
                "paralinguistic_tags": True,
                "watermarking": True,
                "languages": "23+",
            },
        }
