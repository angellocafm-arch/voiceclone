"""Audio recording from microphone.

Designed for simplicity and accessibility:
- No complex config needed
- Clear visual feedback via Rich
- Graceful handling of missing/broken mic
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 44_100
DEFAULT_CHANNELS = 1


class AudioRecorder:
    """Record audio from microphone.
    
    For CLI usage and as backend for the web app's recording feature.
    """

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        channels: int = DEFAULT_CHANNELS,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._recording = False
        self._audio_data: list[np.ndarray] = []

    def check_microphone(self) -> dict:
        """Check if a microphone is available and accessible.
        
        Returns dict with:
            available: bool
            device_name: str
            sample_rate: int
            error: Optional[str]
        """
        try:
            import sounddevice as sd
            
            device_info = sd.query_devices(kind="input")
            return {
                "available": True,
                "device_name": device_info["name"],
                "sample_rate": int(device_info["default_samplerate"]),
                "error": None,
            }
        except Exception as e:
            return {
                "available": False,
                "device_name": "",
                "sample_rate": 0,
                "error": str(e),
            }

    def record(self, duration_seconds: Optional[float] = None) -> tuple[np.ndarray, int]:
        """Record audio from microphone.
        
        Args:
            duration_seconds: Max recording duration. If None, records until
                              stop() is called (for interactive mode).
        
        Returns:
            Tuple of (audio_array, sample_rate).
        """
        import sounddevice as sd
        
        if duration_seconds:
            # Fixed duration recording
            logger.info("Recording for %.1f seconds...", duration_seconds)
            num_samples = int(self.sample_rate * duration_seconds)
            audio = sd.rec(
                num_samples,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            )
            sd.wait()
            logger.info("Recording complete: %.1fs", duration_seconds)
            return audio.squeeze(), self.sample_rate
        else:
            # Interactive recording (start/stop)
            raise NotImplementedError(
                "Interactive recording not yet implemented. "
                "Use duration_seconds parameter."
            )

    def record_with_callback(
        self,
        callback: Optional[callable] = None,
        max_duration: float = 300.0,
    ) -> tuple[np.ndarray, int]:
        """Record with real-time callback for level monitoring.
        
        Args:
            callback: Called with (current_duration, rms_level) each frame.
            max_duration: Safety limit in seconds (default 5 min).
            
        Returns:
            Tuple of (audio_array, sample_rate).
        """
        import sounddevice as sd
        import threading
        
        self._audio_data = []
        self._recording = True
        stop_event = threading.Event()
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning("Recording status: %s", status)
            
            self._audio_data.append(indata.copy())
            
            if callback:
                duration = sum(len(chunk) for chunk in self._audio_data) / self.sample_rate
                rms = np.sqrt(np.mean(indata ** 2))
                callback(duration, float(rms))
            
            if not self._recording or stop_event.is_set():
                raise sd.CallbackAbort()
        
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=audio_callback,
        ):
            # Wait until stopped or max duration
            stop_event.wait(timeout=max_duration)
        
        if not self._audio_data:
            raise RuntimeError("No audio recorded")
        
        audio = np.concatenate(self._audio_data, axis=0).squeeze()
        duration = len(audio) / self.sample_rate
        logger.info("Recording complete: %.1fs", duration)
        
        return audio, self.sample_rate

    def stop(self) -> None:
        """Stop an ongoing recording."""
        self._recording = False
