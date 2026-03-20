"""Audio recording utilities for voice cloning"""

import logging
from pathlib import Path
from typing import Optional, Callable

import numpy as np
import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)


class VoiceRecorder:
    """Record audio for voice cloning"""
    
    def __init__(self, 
                 sample_rate: int = 22050,
                 channels: int = 1,
                 dtype: str = "float32"):
        """Initialize recorder
        
        Args:
            sample_rate: Sample rate in Hz (22050 for Chatterbox)
            channels: Number of channels (1 for mono)
            dtype: Audio data type (float32)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.is_recording = False
        self._audio_buffer: Optional[np.ndarray] = None
    
    def record(self, 
               duration: float,
               progress_callback: Optional[Callable[[float], None]] = None) -> np.ndarray:
        """Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            progress_callback: Optional callback for progress (0.0 to 1.0)
            
        Returns:
            Audio data as numpy array
        """
        logger.info(f"Starting recording ({duration}s @ {self.sample_rate}Hz)")
        self.is_recording = True
        
        frames = []
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks for callbacks
        
        try:
            # Record in chunks to allow progress updates
            num_chunks = int(duration / (chunk_size / self.sample_rate))
            
            for i in range(num_chunks):
                chunk = sd.rec(frames=chunk_size,
                              samplerate=self.sample_rate,
                              channels=self.channels,
                              dtype=self.dtype)
                sd.wait()  # Wait for recording to finish
                frames.append(chunk)
                
                if progress_callback:
                    progress = (i + 1) / num_chunks
                    progress_callback(progress)
                
                logger.debug(f"Recorded chunk {i+1}/{num_chunks}")
            
            audio = np.concatenate(frames, axis=0)
            self._audio_buffer = audio
            logger.info(f"Recording complete: {audio.shape[0] / self.sample_rate:.1f}s")
            
            return audio
        
        finally:
            self.is_recording = False
    
    def save(self, audio: np.ndarray, output_path: Path) -> Path:
        """Save audio to file
        
        Args:
            audio: Audio data
            output_path: Output file path (wav, m4a, mp3)
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        sf.write(str(output_path), audio, self.sample_rate)
        logger.info(f"Saved audio to {output_path}")
        
        return output_path
    
    def stop(self):
        """Stop recording if in progress"""
        if self.is_recording:
            sd.stop()
            self.is_recording = False
            logger.info("Recording stopped")
