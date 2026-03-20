"""Audio processing utilities for VoiceClone

Handles format conversion, validation, recording, and quality analysis.
All audio processing is done locally — nothing leaves the machine.
"""

import io
import logging
import struct
import wave
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum reference audio duration for decent cloning (seconds)
MIN_REFERENCE_DURATION = 3.0
# Recommended reference audio duration
RECOMMENDED_DURATION = 10.0
# Maximum reference audio duration (longer doesn't help much)
MAX_REFERENCE_DURATION = 120.0
# Default sample rate for Chatterbox
DEFAULT_SAMPLE_RATE = 24000


def validate_audio_file(audio_path: Path) -> dict:
    """Validate an audio file for voice cloning
    
    Checks: exists, readable, sufficient duration, supported format.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "duration_seconds": float,
            "sample_rate": int,
            "channels": int,
            "format": str,
            "errors": [str],
            "warnings": [str],
        }
    """
    result = {
        "valid": True,
        "duration_seconds": 0.0,
        "sample_rate": 0,
        "channels": 0,
        "format": "",
        "errors": [],
        "warnings": [],
    }

    # Check existence
    if not audio_path.exists():
        result["valid"] = False
        result["errors"].append(f"File not found: {audio_path}")
        return result

    # Check format first (before size check)
    suffix = audio_path.suffix.lower()
    supported = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".webm"}
    
    if suffix not in supported:
        result["valid"] = False
        result["errors"].append(
            f"Unsupported format '{suffix}'. Supported: {', '.join(sorted(supported))}"
        )
        return result

    result["format"] = suffix.lstrip(".")

    # Check file size (empty or suspiciously small)
    file_size = audio_path.stat().st_size
    if file_size < 1000:  # Less than 1KB
        result["valid"] = False
        result["errors"].append(f"File too small ({file_size} bytes) — likely corrupt")
        return result

    # Try to get duration and properties
    try:
        duration, sr, channels = _get_audio_info(audio_path)
        result["duration_seconds"] = duration
        result["sample_rate"] = sr
        result["channels"] = channels
    except Exception as e:
        # If we can't read properties, still allow it — 
        # the conversion step will handle or fail gracefully
        result["warnings"].append(f"Could not read audio properties: {e}")
        result["duration_seconds"] = -1  # Unknown

    # Duration checks
    if result["duration_seconds"] > 0:
        if result["duration_seconds"] < MIN_REFERENCE_DURATION:
            result["valid"] = False
            result["errors"].append(
                f"Audio too short ({result['duration_seconds']:.1f}s). "
                f"Minimum: {MIN_REFERENCE_DURATION}s for voice cloning."
            )
        elif result["duration_seconds"] < RECOMMENDED_DURATION:
            result["warnings"].append(
                f"Audio is {result['duration_seconds']:.1f}s. "
                f"Recommend {RECOMMENDED_DURATION}s+ for best quality."
            )
        elif result["duration_seconds"] > MAX_REFERENCE_DURATION:
            result["warnings"].append(
                f"Audio is {result['duration_seconds']:.1f}s. "
                f"Only first {MAX_REFERENCE_DURATION}s will be used."
            )

    return result


def _get_audio_info(audio_path: Path) -> tuple[float, int, int]:
    """Get duration, sample rate, and channels from audio file
    
    Uses soundfile for WAV/FLAC, falls back to ffprobe for others.
    
    Returns:
        (duration_seconds, sample_rate, channels)
    """
    suffix = audio_path.suffix.lower()

    if suffix == ".wav":
        return _get_wav_info(audio_path)
    
    # For non-WAV formats, try soundfile first
    try:
        import soundfile as sf
        info = sf.info(str(audio_path))
        return info.duration, info.samplerate, info.channels
    except Exception:
        pass

    # Fallback: use ffprobe if available
    try:
        return _get_info_ffprobe(audio_path)
    except Exception:
        pass

    # Last resort: estimate from file size (very rough)
    return -1.0, 0, 0


def _get_wav_info(audio_path: Path) -> tuple[float, int, int]:
    """Get info from WAV file using standard library"""
    with wave.open(str(audio_path), "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        frames = wf.getnframes()
        duration = frames / sr if sr > 0 else 0
        return duration, sr, channels


def _get_info_ffprobe(audio_path: Path) -> tuple[float, int, int]:
    """Get audio info using ffprobe"""
    import subprocess
    import json

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    
    duration = float(data.get("format", {}).get("duration", 0))
    
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break

    sr = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0
    channels = int(audio_stream.get("channels", 0)) if audio_stream else 0

    return duration, sr, channels


def convert_to_wav(
    input_path: Path,
    output_path: Path,
    target_sr: int = DEFAULT_SAMPLE_RATE,
    mono: bool = True,
) -> Path:
    """Convert any audio format to WAV suitable for voice cloning
    
    Args:
        input_path: Source audio file (any supported format)
        output_path: Destination WAV file path
        target_sr: Target sample rate (24000 for Chatterbox)
        mono: Convert to mono (recommended for cloning)
        
    Returns:
        Path to converted WAV file
        
    Raises:
        RuntimeError: If conversion fails
    """
    suffix = input_path.suffix.lower()
    
    # If already WAV with correct properties, try to just copy
    if suffix == ".wav":
        try:
            _, sr, channels = _get_wav_info(input_path)
            if sr == target_sr and (not mono or channels == 1):
                import shutil
                shutil.copy2(input_path, output_path)
                logger.debug(f"WAV already correct format, copied directly")
                return output_path
        except Exception:
            pass

    # Use librosa for reliable conversion (handles most formats)
    try:
        import numpy as np
        import soundfile as sf
        
        # Try librosa first (best format support)
        try:
            import librosa
            audio, sr = librosa.load(str(input_path), sr=target_sr, mono=mono)
        except ImportError:
            # Fallback to soundfile
            audio, sr = sf.read(str(input_path))
            if mono and audio.ndim > 1:
                audio = audio.mean(axis=1)
            if sr != target_sr:
                # Simple resampling via scipy
                from scipy import signal
                num_samples = int(len(audio) * target_sr / sr)
                audio = signal.resample(audio, num_samples)
                sr = target_sr

        # Ensure float32, normalized
        audio = np.asarray(audio, dtype=np.float32)
        if audio.max() > 1.0 or audio.min() < -1.0:
            audio = audio / max(abs(audio.max()), abs(audio.min()))

        sf.write(str(output_path), audio, target_sr, subtype="FLOAT")
        logger.info(f"Converted {input_path.name} → {output_path.name} ({target_sr}Hz, mono={mono})")
        return output_path
        
    except ImportError:
        pass

    # Final fallback: ffmpeg
    return _convert_ffmpeg(input_path, output_path, target_sr, mono)


def _convert_ffmpeg(
    input_path: Path,
    output_path: Path,
    target_sr: int,
    mono: bool,
) -> Path:
    """Convert audio using ffmpeg as fallback"""
    import subprocess

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-ar", str(target_sr),
    ]
    if mono:
        cmd.extend(["-ac", "1"])
    cmd.extend(["-f", "wav", str(output_path)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    logger.info(f"Converted via ffmpeg: {input_path.name} → {output_path.name}")
    return output_path


def wav_bytes_to_format(
    wav_data: bytes,
    sample_rate: int,
    target_format: str = "wav",
) -> bytes:
    """Convert WAV bytes to target format
    
    Args:
        wav_data: Raw audio samples as bytes (float32 or int16)
        sample_rate: Sample rate of the audio
        target_format: "wav", "ogg", or "mp3"
        
    Returns:
        Encoded audio bytes in target format
    """
    if target_format == "wav":
        return wav_data

    # For ogg/mp3, need to use soundfile or ffmpeg pipe
    try:
        import numpy as np
        import soundfile as sf

        # Parse the wav data
        audio_array = np.frombuffer(wav_data, dtype=np.float32)

        buf = io.BytesIO()
        if target_format == "ogg":
            sf.write(buf, audio_array, sample_rate, format="OGG", subtype="VORBIS")
        elif target_format == "mp3":
            # soundfile doesn't support mp3 writing, use ffmpeg
            return _convert_bytes_ffmpeg(wav_data, sample_rate, "mp3")
        else:
            raise ValueError(f"Unsupported format: {target_format}")

        buf.seek(0)
        return buf.read()

    except ImportError:
        return _convert_bytes_ffmpeg(wav_data, sample_rate, target_format)


def _convert_bytes_ffmpeg(
    audio_data: bytes,
    sample_rate: int,
    target_format: str,
) -> bytes:
    """Convert raw audio bytes to target format using ffmpeg pipe"""
    import subprocess

    format_map = {
        "ogg": ["-f", "ogg", "-acodec", "libvorbis"],
        "mp3": ["-f", "mp3", "-acodec", "libmp3lame", "-q:a", "2"],
    }

    if target_format not in format_map:
        raise ValueError(f"Unsupported format: {target_format}")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "f32le", "-ar", str(sample_rate), "-ac", "1",
        "-i", "pipe:0",
        *format_map[target_format],
        "pipe:1",
    ]

    result = subprocess.run(
        cmd, input=audio_data, capture_output=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg encoding failed: {result.stderr.decode()}")

    return result.stdout


def record_audio(
    duration_seconds: float = 30.0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    device: Optional[int] = None,
) -> bytes:
    """Record audio from microphone
    
    Args:
        duration_seconds: Maximum recording duration
        sample_rate: Recording sample rate
        device: Audio device index (None = default)
        
    Returns:
        Audio data as float32 WAV bytes
        
    Raises:
        RuntimeError: If no microphone available
    """
    try:
        import sounddevice as sd
        import numpy as np

        logger.info(f"Recording {duration_seconds}s at {sample_rate}Hz...")
        audio = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=device,
        )
        sd.wait()  # Block until recording is done

        # Trim silence from end
        audio = audio.flatten()
        
        # Convert to WAV bytes
        buf = io.BytesIO()
        import soundfile as sf
        sf.write(buf, audio, sample_rate, format="WAV", subtype="FLOAT")
        buf.seek(0)
        return buf.read()

    except ImportError:
        raise RuntimeError(
            "sounddevice not installed. Install with: pip install sounddevice"
        )
    except Exception as e:
        raise RuntimeError(f"Recording failed: {e}")


def estimate_quality(audio_path: Path) -> float:
    """Estimate audio quality for voice cloning (0.0-1.0)
    
    Checks:
    - Signal-to-noise ratio
    - Silence ratio
    - Clipping
    - Duration adequacy
    
    Returns:
        Quality score 0.0 (unusable) to 1.0 (excellent)
    """
    try:
        import numpy as np
        import soundfile as sf

        audio, sr = sf.read(str(audio_path))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        score = 1.0

        # Check duration
        duration = len(audio) / sr
        if duration < MIN_REFERENCE_DURATION:
            return 0.0
        elif duration < RECOMMENDED_DURATION:
            score -= 0.2

        # Check for silence (more than 50% silence = bad)
        rms = np.sqrt(np.mean(audio ** 2))
        silence_threshold = rms * 0.1
        silence_ratio = np.mean(np.abs(audio) < silence_threshold)
        if silence_ratio > 0.5:
            score -= 0.3

        # Check for clipping
        clip_threshold = 0.99
        clip_ratio = np.mean(np.abs(audio) > clip_threshold)
        if clip_ratio > 0.01:
            score -= 0.2

        # Check SNR (rough estimate)
        if rms < 0.01:
            score -= 0.3  # Very quiet recording

        return max(0.0, min(1.0, score))

    except Exception as e:
        logger.warning(f"Could not estimate quality: {e}")
        return 0.5  # Unknown quality
