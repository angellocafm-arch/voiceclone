"""Tests for the VoiceClone FastAPI server

Tests API endpoints with mocked engine manager.
No real TTS models needed.
"""

import io
import json
import struct
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Check if fastapi/httpx are available
try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# Skip all tests if dependencies missing
pytestmark = pytest.mark.skipif(
    not HAS_FASTAPI,
    reason="FastAPI not installed",
)


from voice_engine.base import (
    AudioFormat,
    EngineStatus,
    SynthesisResult,
    VoiceProfile,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_manager():
    """Create a mock EngineManager"""
    manager = MagicMock()
    manager.is_ready = True
    manager.engine_name = "Chatterbox TTS"
    manager.list_voices.return_value = []
    return manager


@pytest.fixture
def sample_voice():
    """Create a sample VoiceProfile"""
    return VoiceProfile(
        name="maria",
        voice_id="abc123",
        path=Path("/tmp/voices/maria"),
        language="es",
        quality_score=0.85,
        duration_seconds=15.0,
        engine="chatterbox",
        has_personality=False,
        sample_rate=24000,
    )


@pytest.fixture
def client(mock_manager):
    """Create a test client with mocked engine
    
    We need to inject the mock manager before the lifespan runs,
    so we patch the EngineManager constructor to return our mock.
    """
    import api.server as server_module
    
    # Patch the lifespan to use our mock manager instead of creating a real one
    original_manager = server_module._manager
    original_start_time = server_module._start_time
    
    server_module._manager = mock_manager
    server_module._start_time = 1000000.0
    
    from api.server import app
    
    # Create a test app without lifespan to avoid real engine init
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    # Use the app but skip lifespan by directly creating TestClient
    # The mock_manager is already injected via server_module._manager
    with TestClient(app, raise_server_exceptions=True) as test_client:
        # Re-inject after lifespan may have overwritten
        server_module._manager = mock_manager
        server_module._start_time = 1000000.0
        yield test_client
    
    # Restore
    server_module._manager = original_manager
    server_module._start_time = original_start_time


@pytest.fixture
def sample_wav_bytes():
    """Generate a minimal valid WAV file in memory"""
    buf = io.BytesIO()
    sr = 24000
    duration = 10  # seconds
    n_frames = sr * duration

    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = b"\x00\x01" * n_frames
        wf.writeframes(frames)

    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════════
# Health Endpoint Tests
# ═══════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_ok(self, client, mock_manager):
        mock_manager.list_voices.return_value = [
            MagicMock(), MagicMock(), MagicMock()
        ]

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["engine"] == "Chatterbox TTS"
        assert data["model_loaded"] is True
        assert data["voices_count"] == 3
        assert data["version"] == "0.1.0-dev"

    def test_health_loading(self, client, mock_manager):
        mock_manager.is_ready = False

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "loading"


# ═══════════════════════════════════════════════════════════════
# Voices Endpoint Tests
# ═══════════════════════════════════════════════════════════════

class TestVoices:
    def test_list_empty(self, client, mock_manager):
        mock_manager.list_voices.return_value = []

        response = client.get("/voices")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_voices(self, client, mock_manager, sample_voice):
        mock_manager.list_voices.return_value = [sample_voice]

        response = client.get("/voices")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "maria"
        assert data[0]["voice_id"] == "abc123"
        assert data[0]["engine"] == "chatterbox"

    def test_get_voice(self, client, mock_manager, sample_voice):
        mock_manager.get_voice.return_value = sample_voice

        response = client.get("/voices/maria")
        assert response.status_code == 200
        assert response.json()["name"] == "maria"

    def test_get_voice_not_found(self, client, mock_manager):
        mock_manager.get_voice.return_value = None

        response = client.get("/voices/nonexistent")
        assert response.status_code == 404

    def test_delete_voice(self, client, mock_manager):
        mock_manager.delete_voice.return_value = True

        response = client.delete("/voices/maria")
        assert response.status_code == 204

    def test_delete_voice_not_found(self, client, mock_manager):
        mock_manager.delete_voice.return_value = False

        response = client.delete("/voices/ghost")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Speak Endpoint Tests
# ═══════════════════════════════════════════════════════════════

class TestSpeak:
    def test_speak_success(self, client, mock_manager, sample_voice):
        mock_manager.get_voice.return_value = sample_voice
        mock_manager.synthesize.return_value = SynthesisResult(
            audio_data=b"\x00" * 1000,
            sample_rate=24000,
            duration_seconds=2.5,
            format=AudioFormat.WAV,
            voice_name="maria",
            text="Hola",
        )

        response = client.post("/speak", json={
            "text": "Hola mundo",
            "voice_id": "maria",
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert float(response.headers["x-duration-seconds"]) == 2.5
        assert response.headers["x-voice-name"] == "maria"

    def test_speak_voice_not_found(self, client, mock_manager):
        mock_manager.get_voice.return_value = None

        response = client.post("/speak", json={
            "text": "Hello",
            "voice_id": "nonexistent",
        })
        assert response.status_code == 404

    def test_speak_empty_text(self, client):
        response = client.post("/speak", json={
            "text": "",
            "voice_id": "maria",
        })
        assert response.status_code == 422  # Validation error

    def test_speak_ogg_format(self, client, mock_manager, sample_voice):
        mock_manager.get_voice.return_value = sample_voice
        mock_manager.synthesize.return_value = SynthesisResult(
            audio_data=b"\x00" * 500,
            sample_rate=24000,
            duration_seconds=1.0,
            format=AudioFormat.OGG,
            voice_name="maria",
            text="test",
        )

        response = client.post("/speak", json={
            "text": "Test",
            "voice_id": "maria",
            "format": "ogg",
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/ogg"

    def test_speak_with_params(self, client, mock_manager, sample_voice):
        mock_manager.get_voice.return_value = sample_voice
        mock_manager.synthesize.return_value = SynthesisResult(
            audio_data=b"\x00" * 500,
            sample_rate=24000,
            duration_seconds=1.0,
        )

        response = client.post("/speak", json={
            "text": "Emotional text [laugh]",
            "voice_id": "maria",
            "exaggeration": 0.8,
            "cfg": 0.3,
        })
        assert response.status_code == 200

        # Verify params were passed to synthesize
        call_args = mock_manager.synthesize.call_args
        assert call_args.kwargs.get("exaggeration") == 0.8 or call_args[1].get("exaggeration") == 0.8


# ═══════════════════════════════════════════════════════════════
# Clone Endpoint Tests
# ═══════════════════════════════════════════════════════════════

class TestClone:
    def test_clone_success(self, client, mock_manager, sample_wav_bytes, sample_voice):
        mock_manager.clone_voice.return_value = sample_voice

        response = client.post(
            "/clone",
            files={"audio": ("test.wav", sample_wav_bytes, "audio/wav")},
            data={"name": "maria"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "maria"
        assert data["voice_id"] == "abc123"
        assert "cloned successfully" in data["message"]

    def test_clone_auto_name(self, client, mock_manager, sample_wav_bytes, sample_voice):
        mock_manager.clone_voice.return_value = sample_voice

        response = client.post(
            "/clone",
            files={"audio": ("test.wav", sample_wav_bytes, "audio/wav")},
        )
        assert response.status_code == 200

    def test_clone_validation_error(self, client, mock_manager, sample_wav_bytes):
        mock_manager.clone_voice.side_effect = ValueError("Audio too short")

        response = client.post(
            "/clone",
            files={"audio": ("test.wav", sample_wav_bytes, "audio/wav")},
            data={"name": "test"},
        )
        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════
# Personality Endpoint Tests (stubs)
# ═══════════════════════════════════════════════════════════════

class TestPersonality:
    def test_personality_speak_fallback(self, client, mock_manager, sample_voice):
        """Personality speak should fall back to regular speak for now"""
        mock_manager.get_voice.return_value = sample_voice
        mock_manager.synthesize.return_value = SynthesisResult(
            audio_data=b"\x00" * 500,
            sample_rate=24000,
            duration_seconds=1.0,
        )

        response = client.post("/personality/speak", json={
            "text": "Hola",
            "voice_id": "maria",
        })
        assert response.status_code == 200

    def test_personality_setup_missing_required(self, client):
        """Setup with empty questionnaire returns 400 (missing required answers)"""
        response = client.post("/personality/setup", json={
            "voice_id": "maria",
            "questionnaire": {},
        })
        assert response.status_code == 400
        assert "Missing required" in response.json()["detail"]

    def test_personality_setup_voice_not_found(self, client, mock_manager):
        """Setup with non-existent voice returns 404"""
        mock_manager.get_voice.return_value = None
        response = client.post("/personality/setup", json={
            "voice_id": "nonexistent",
            "questionnaire": {
                "description": "Test",
                "formality": "Casual",
                "warmth": "Cálido/a — me gusta conectar",
                "energy": "Normal — ni muy arriba ni muy abajo",
            },
        })
        assert response.status_code == 404

    def test_personality_questions(self, client):
        """Get personality questionnaire questions"""
        response = client.get("/personality/questions")
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) >= 10
        ids = [q["id"] for q in questions]
        assert "description" in ids
        assert "formality" in ids


# ═══════════════════════════════════════════════════════════════
# OpenAPI Docs Tests
# ═══════════════════════════════════════════════════════════════

class TestDocs:
    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "VoiceClone API"
        assert "/health" in data["paths"]
        assert "/speak" in data["paths"]
        assert "/clone" in data["paths"]
        assert "/voices" in data["paths"]
