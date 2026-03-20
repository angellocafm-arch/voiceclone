"""Tests for voice engine — Layer 1

Tests the base classes, audio utilities, engine adapter pattern,
and voice management without requiring actual TTS models.

Tests that require models are marked with @pytest.mark.slow
and skipped in CI unless models are available.
"""

import json
import struct
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_engine.base import (
    AudioFormat,
    EngineStatus,
    SynthesisResult,
    VoiceEngine,
    VoiceProfile,
)
from voice_engine.audio_utils import (
    validate_audio_file,
    estimate_quality,
    DEFAULT_SAMPLE_RATE,
    MIN_REFERENCE_DURATION,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_wav(temp_dir):
    """Create a valid WAV file (10 seconds of silence + slight noise)"""
    path = temp_dir / "test.wav"
    sr = 24000
    duration = 10  # seconds
    n_frames = sr * duration

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)
        # Generate slight noise (not pure silence, which would fail quality checks)
        import random
        frames = bytes(
            b for i in range(n_frames)
            for b in struct.pack("<h", random.randint(-500, 500))
        )
        wf.writeframes(frames)

    return path


@pytest.fixture
def short_wav(temp_dir):
    """Create a WAV file that's too short (1 second)"""
    path = temp_dir / "short.wav"
    sr = 24000
    n_frames = sr * 1  # 1 second

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytes(
            b for _ in range(n_frames)
            for b in struct.pack("<h", 0)
        )
        wf.writeframes(frames)

    return path


@pytest.fixture
def voice_profile(temp_dir):
    """Create a test VoiceProfile"""
    voice_dir = temp_dir / "voices" / "test-voice"
    voice_dir.mkdir(parents=True)

    return VoiceProfile(
        name="test-voice",
        voice_id="abc12345",
        path=voice_dir,
        language="es",
        quality_score=0.85,
        duration_seconds=15.0,
        engine="chatterbox",
        has_personality=False,
        sample_rate=24000,
    )


# ═══════════════════════════════════════════════════════════════
# VoiceProfile Tests
# ═══════════════════════════════════════════════════════════════

class TestVoiceProfile:
    """Test VoiceProfile dataclass"""

    def test_create_profile(self, temp_dir):
        profile = VoiceProfile(
            name="maria",
            voice_id="abc123",
            path=temp_dir / "maria",
        )
        assert profile.name == "maria"
        assert profile.language == "es"  # Default
        assert profile.sample_rate == 24000

    def test_serialize_deserialize(self, voice_profile):
        data = voice_profile.to_dict()
        assert data["name"] == "test-voice"
        assert data["voice_id"] == "abc12345"
        assert data["quality_score"] == 0.85

        restored = VoiceProfile.from_dict(data)
        assert restored.name == voice_profile.name
        assert restored.voice_id == voice_profile.voice_id
        assert isinstance(restored.path, Path)

    def test_to_dict_json_serializable(self, voice_profile):
        data = voice_profile.to_dict()
        # Should not raise
        json_str = json.dumps(data)
        assert '"name": "test-voice"' in json_str


# ═══════════════════════════════════════════════════════════════
# Audio Validation Tests
# ═══════════════════════════════════════════════════════════════

class TestAudioValidation:
    """Test audio file validation"""

    def test_valid_wav(self, sample_wav):
        result = validate_audio_file(sample_wav)
        assert result["valid"] is True
        assert result["duration_seconds"] >= 9.0  # ~10 seconds
        assert result["format"] == "wav"
        assert len(result["errors"]) == 0

    def test_nonexistent_file(self, temp_dir):
        result = validate_audio_file(temp_dir / "nope.wav")
        assert result["valid"] is False
        assert any("not found" in e.lower() for e in result["errors"])

    def test_unsupported_format(self, temp_dir):
        bad = temp_dir / "test.xyz"
        bad.write_text("not audio")
        result = validate_audio_file(bad)
        assert result["valid"] is False
        assert any("unsupported" in e.lower() for e in result["errors"])

    def test_too_short(self, short_wav):
        result = validate_audio_file(short_wav)
        assert result["valid"] is False
        assert any("too short" in e.lower() for e in result["errors"])

    def test_empty_file(self, temp_dir):
        empty = temp_dir / "empty.wav"
        empty.write_bytes(b"")
        result = validate_audio_file(empty)
        assert result["valid"] is False

    def test_small_file(self, temp_dir):
        small = temp_dir / "tiny.wav"
        small.write_bytes(b"RIFF" + b"\x00" * 10)
        result = validate_audio_file(small)
        assert result["valid"] is False


# ═══════════════════════════════════════════════════════════════
# SynthesisResult Tests
# ═══════════════════════════════════════════════════════════════

class TestSynthesisResult:
    """Test SynthesisResult dataclass"""

    def test_create(self):
        result = SynthesisResult(
            audio_data=b"\x00" * 1000,
            sample_rate=24000,
            duration_seconds=2.5,
        )
        assert result.sample_rate == 24000
        assert result.duration_seconds == 2.5
        assert len(result.audio_data) == 1000
        assert result.format == AudioFormat.WAV


# ═══════════════════════════════════════════════════════════════
# Engine Status Tests
# ═══════════════════════════════════════════════════════════════

class TestEngineStatus:
    """Test EngineStatus enum"""

    def test_values(self):
        assert EngineStatus.UNINITIALIZED.value == "uninitialized"
        assert EngineStatus.LOADING.value == "loading"
        assert EngineStatus.READY.value == "ready"
        assert EngineStatus.ERROR.value == "error"


# ═══════════════════════════════════════════════════════════════
# AudioFormat Tests
# ═══════════════════════════════════════════════════════════════

class TestAudioFormat:
    """Test AudioFormat enum"""

    def test_values(self):
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.OGG.value == "ogg"
        assert AudioFormat.MP3.value == "mp3"


# ═══════════════════════════════════════════════════════════════
# EngineManager Tests (with mocked engines)
# ═══════════════════════════════════════════════════════════════

class TestEngineManager:
    """Test EngineManager with mocked engines"""

    def test_initialize_creates_directories(self, temp_dir):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        assert (temp_dir / "vc" / "voices").exists()
        assert (temp_dir / "vc" / "models").exists()

    def test_status_without_init(self, temp_dir):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        status = manager.get_status()
        assert status["ready"] is False

    def test_ensure_ready_raises_without_init(self, temp_dir):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        with pytest.raises(RuntimeError, match="No voice engine loaded"):
            manager._ensure_ready()

    def test_get_voice_returns_none_for_missing(self, temp_dir):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        # Mock the active engine
        mock_engine = MagicMock()
        mock_engine.list_voices.return_value = []
        mock_engine.is_ready.return_value = True
        manager._active_engine = mock_engine
        
        voice = manager.get_voice("nonexistent")
        assert voice is None

    def test_list_voices_empty(self, temp_dir):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        mock_engine = MagicMock()
        mock_engine.list_voices.return_value = []
        mock_engine.is_ready.return_value = True
        manager._active_engine = mock_engine
        
        voices = manager.list_voices()
        assert voices == []


# ═══════════════════════════════════════════════════════════════
# ChatterboxEngine Tests (unit, no model)
# ═══════════════════════════════════════════════════════════════

class TestChatterboxEngine:
    """Test ChatterboxEngine without loading the actual model"""

    def test_properties(self):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        assert engine.name == "Chatterbox TTS"
        assert engine.engine_id == "chatterbox"
        assert engine.status == EngineStatus.UNINITIALIZED
        assert engine.sample_rate == 24000

    def test_is_ready_false_initially(self):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        assert engine.is_ready() is False

    def test_get_model_info(self):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        info = engine.get_model_info()
        assert info["engine"] == "chatterbox"
        assert info["features"]["zero_shot_cloning"] is True
        assert info["model_loaded"] is False

    def test_clone_voice_validates_audio(self, temp_dir):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        engine._status = EngineStatus.READY
        engine._model = MagicMock()
        engine._model.sr = 24000

        # Try to clone with non-existent file
        with pytest.raises(ValueError, match="not found"):
            engine.clone_voice(
                temp_dir / "nonexistent.wav",
                "test",
                temp_dir / "voices",
            )

    def test_clone_voice_rejects_empty_name(self, temp_dir, sample_wav):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        engine._status = EngineStatus.READY
        engine._model = MagicMock()
        engine._model.sr = 24000

        with pytest.raises(ValueError, match="empty"):
            engine.clone_voice(sample_wav, "  ", temp_dir / "voices")

    def test_synthesize_rejects_empty_text(self, voice_profile):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        engine._status = EngineStatus.READY
        engine._model = MagicMock()

        with pytest.raises(ValueError, match="empty"):
            engine.synthesize("", voice_profile)

    def test_delete_voice(self, voice_profile):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        
        # Create a dummy file in voice dir
        (voice_profile.path / "reference.wav").touch()
        assert voice_profile.path.exists()

        result = engine.delete_voice(voice_profile)
        assert result is True
        assert not voice_profile.path.exists()

    def test_delete_nonexistent_voice(self, temp_dir):
        from voice_engine.chatterbox_engine import ChatterboxEngine

        engine = ChatterboxEngine()
        profile = VoiceProfile(
            name="ghost",
            voice_id="nope",
            path=temp_dir / "nonexistent",
        )
        result = engine.delete_voice(profile)
        assert result is False


# ═══════════════════════════════════════════════════════════════
# XTTSEngine Tests (unit, no model)
# ═══════════════════════════════════════════════════════════════

class TestXTTSEngine:
    """Test XTTSEngine without loading the actual model"""

    def test_properties(self):
        from voice_engine.xtts_engine import XTTSEngine

        engine = XTTSEngine()
        assert engine.name == "XTTS v2"
        assert engine.engine_id == "xtts-v2"
        assert engine.status == EngineStatus.UNINITIALIZED

    def test_get_model_info(self):
        from voice_engine.xtts_engine import XTTSEngine

        engine = XTTSEngine()
        info = engine.get_model_info()
        assert info["engine"] == "xtts-v2"
        assert info["features"]["emotion_control"] is False


# ═══════════════════════════════════════════════════════════════
# Integration Tests (require models, skip if unavailable)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.slow
class TestIntegration:
    """Integration tests that require actual models"""

    @pytest.fixture(autouse=True)
    def check_models(self):
        """Skip if no TTS models available"""
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not installed")

        try:
            from chatterbox.tts import ChatterboxTTS
        except ImportError:
            try:
                from TTS.api import TTS
            except ImportError:
                pytest.skip("No TTS engine installed")

    def test_full_clone_and_speak(self, temp_dir, sample_wav):
        from voice_engine.manager import EngineManager

        manager = EngineManager(voiceclone_dir=temp_dir / "vc")
        assert manager.initialize()

        # Clone
        profile = manager.clone_voice(sample_wav, "test-voice")
        assert profile.name == "test-voice"
        assert profile.path.exists()

        # List
        voices = manager.list_voices()
        assert len(voices) == 1

        # Synthesize
        result = manager.synthesize("Hola, esto es una prueba", profile)
        assert result.duration_seconds > 0
        assert len(result.audio_data) > 0

        # Delete
        assert manager.delete_voice("test-voice")
        assert len(manager.list_voices()) == 0
