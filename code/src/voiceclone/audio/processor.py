"""Audio processing pipeline: normalize → noise reduce → VAD → resample.

Critical for ELA users: voice may be weak, environment noisy, mic poorly 
positioned. This pipeline ensures the best possible input for voice cloning.
"""

import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 24_000  # Chatterbox expects 24kHz


class AudioProcessor:
    """Process audio for optimal voice cloning quality.
    
    Pipeline:
    1. Load & convert to mono float32
    2. Normalize volume
    3. Reduce background noise
    4. Voice Activity Detection (trim silence)
    5. Resample to target rate (24kHz for Chatterbox)
    """

    def __init__(self, target_sr: int = TARGET_SAMPLE_RATE) -> None:
        self.target_sr = target_sr

    def process(
        self,
        audio: np.ndarray,
        sample_rate: int,
        noise_reduce: bool = True,
        trim_silence: bool = True,
    ) -> tuple[np.ndarray, int]:
        """Full processing pipeline.
        
        Args:
            audio: Raw audio data (any format numpy supports).
            sample_rate: Original sample rate.
            noise_reduce: Apply noise reduction (recommended for noisy env).
            trim_silence: Trim silent segments.
            
        Returns:
            Tuple of (processed_audio, target_sample_rate).
        """
        logger.info(
            "Processing audio: %.1fs at %dHz",
            len(audio) / sample_rate, sample_rate
        )
        
        # Step 1: Convert to mono float32
        audio = self._to_mono_float32(audio)
        
        # Step 2: Normalize volume
        audio = self._normalize(audio)
        
        # Step 3: Noise reduction
        if noise_reduce:
            audio = self._reduce_noise(audio, sample_rate)
        
        # Step 4: Trim silence (VAD)
        if trim_silence:
            audio = self._trim_silence(audio, sample_rate)
        
        # Step 5: Resample
        if sample_rate != self.target_sr:
            audio = self._resample(audio, sample_rate, self.target_sr)
        
        duration = len(audio) / self.target_sr
        logger.info("Processed: %.1fs at %dHz", duration, self.target_sr)
        
        return audio, self.target_sr

    def load_file(self, path: Path) -> tuple[np.ndarray, int]:
        """Load audio from file (wav, mp3, ogg, m4a, flac).
        
        Uses librosa for broad format support.
        """
        import librosa
        audio, sr = librosa.load(str(path), sr=None, mono=True)
        logger.info("Loaded %s: %.1fs at %dHz", path.name, len(audio) / sr, sr)
        return audio, sr

    def _to_mono_float32(self, audio: np.ndarray) -> np.ndarray:
        """Convert to mono float32."""
        # Handle stereo
        if audio.ndim > 1:
            audio = np.mean(audio, axis=-1)
        
        # Convert to float32
        if audio.dtype != np.float32:
            if np.issubdtype(audio.dtype, np.integer):
                # Integer audio (e.g., int16): normalize to [-1, 1]
                max_val = np.iinfo(audio.dtype).max
                audio = audio.astype(np.float32) / max_val
            else:
                audio = audio.astype(np.float32)
        
        return audio

    def _normalize(self, audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        """Normalize audio to target dB level.
        
        Uses peak normalization to avoid clipping.
        """
        peak = np.max(np.abs(audio))
        if peak == 0:
            logger.warning("Audio is silent (all zeros)")
            return audio
        
        # Target amplitude from dB
        target_amp = 10 ** (target_db / 20)
        audio = audio * (target_amp / peak)
        
        return audio

    def _reduce_noise(
        self,
        audio: np.ndarray,
        sample_rate: int,
    ) -> np.ndarray:
        """Reduce background noise using spectral gating.
        
        Uses noisereduce library — lightweight, CPU-friendly.
        Important for hospital/noisy environments.
        """
        try:
            import noisereduce as nr
            
            reduced = nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                prop_decrease=0.8,  # Moderate noise reduction
                n_fft=2048,
                stationary=True,  # Assume stationary noise (fans, AC)
            )
            
            logger.info("Noise reduction applied")
            return reduced
            
        except ImportError:
            logger.warning("noisereduce not installed, skipping noise reduction")
            return audio

    def _trim_silence(
        self,
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -40.0,
        min_silence_ms: int = 300,
    ) -> np.ndarray:
        """Trim leading/trailing silence and long internal pauses.
        
        Keeps natural pauses (important for speaker embedding)
        but removes dead air.
        """
        try:
            import librosa
            
            # Trim leading/trailing silence
            audio_trimmed, _ = librosa.effects.trim(
                audio,
                top_db=abs(threshold_db),
                frame_length=2048,
                hop_length=512,
            )
            
            trimmed_duration = (len(audio) - len(audio_trimmed)) / sample_rate
            if trimmed_duration > 0.5:
                logger.info("Trimmed %.1fs of silence", trimmed_duration)
            
            return audio_trimmed
            
        except ImportError:
            logger.warning("librosa not installed, skipping silence trimming")
            return audio

    def _resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int,
    ) -> np.ndarray:
        """Resample audio to target sample rate."""
        try:
            import librosa
            resampled = librosa.resample(
                audio, orig_sr=orig_sr, target_sr=target_sr
            )
            logger.info("Resampled from %dHz to %dHz", orig_sr, target_sr)
            return resampled
        except ImportError:
            # Fallback: scipy
            from scipy.signal import resample
            num_samples = int(len(audio) * target_sr / orig_sr)
            resampled = resample(audio, num_samples)
            return resampled.astype(np.float32)

    def get_duration(self, audio: np.ndarray, sample_rate: int) -> float:
        """Get audio duration in seconds."""
        return len(audio) / sample_rate

    def get_rms_db(self, audio: np.ndarray) -> float:
        """Get RMS level in dB."""
        rms = np.sqrt(np.mean(audio ** 2))
        if rms == 0:
            return -100.0
        return float(20 * np.log10(rms))
