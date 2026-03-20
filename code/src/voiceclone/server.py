"""FastAPI server — local API for VoiceClone.

Runs on localhost:8765 by default. Exposes all VoiceClone functionality
via HTTP endpoints. Used by:
- Web app (Next.js frontend)
- AAC software (Grid 3, etc.)
- CLI (as backend)
- Eye tracking (WebSocket for gaze data)

SECURITY: Listens ONLY on localhost. Not exposed to network.
"""

import io
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import numpy as np

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceClone API",
    description="Local voice cloning + personality AI for people with ALS",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

# CORS: Allow web app at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (initialized on startup)
_engine_manager = None
_voice_store = None
_personality_engine = None
_audio_processor = None


@app.on_event("startup")
async def startup():
    """Initialize all components on server start."""
    global _engine_manager, _voice_store, _personality_engine, _audio_processor
    
    from voiceclone.engine.manager import EngineManager
    from voiceclone.storage.voices import VoiceStore
    from voiceclone.personality.engine import PersonalityEngine
    from voiceclone.audio.processor import AudioProcessor
    
    _voice_store = VoiceStore()
    _audio_processor = AudioProcessor()
    _personality_engine = PersonalityEngine(llm_backend="local")
    
    _engine_manager = EngineManager()
    try:
        await _engine_manager.initialize()
        logger.info("VoiceClone API ready on localhost:8765")
    except Exception as e:
        logger.error("Failed to initialize engine: %s", e)
        logger.warning("API running without voice engine (setup required)")


# ============================================================
# Health
# ============================================================

@app.get("/health")
async def health():
    """Service health check."""
    engine_info = None
    model_loaded = False
    
    if _engine_manager:
        try:
            info = _engine_manager.get_info()
            engine_info = info.name
            model_loaded = True
        except Exception:
            pass
    
    voices_count = len(_voice_store.list_voices()) if _voice_store else 0
    
    return {
        "status": "ok" if model_loaded else "no_model",
        "engine": engine_info,
        "model_loaded": model_loaded,
        "voices_count": voices_count,
        "version": "0.1.0",
    }


# ============================================================
# Voice Cloning
# ============================================================

@app.post("/clone")
async def clone_voice(
    audio: UploadFile = File(...),
    name: str = Form("my-voice"),
):
    """Clone a voice from an audio file.
    
    Accepts: wav, mp3, ogg, m4a, flac
    Minimum: 6 seconds of clear speech
    Recommended: 15-30 seconds
    """
    if not _engine_manager or not _audio_processor:
        raise HTTPException(503, "Engine not initialized. Run setup first.")
    
    # Read uploaded audio
    audio_bytes = await audio.read()
    
    # Save temp file for loading
    import tempfile
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = Path(tmp.name)
    
    try:
        # Load and process audio
        raw_audio, sr = _audio_processor.load_file(tmp_path)
        processed_audio, target_sr = _audio_processor.process(raw_audio, sr)
        
        # Clone voice
        engine = _engine_manager.active_engine
        profile = await engine.clone_voice(processed_audio, target_sr, name)
        
        # Save to store
        _voice_store.save(profile)
        
        return {
            "voice_id": profile.voice_id,
            "name": profile.name,
            "duration_seconds": profile.duration_seconds,
            "quality_score": profile.quality_score,
            "engine": profile.engine,
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/speak")
async def speak(
    text: str,
    voice_id: str,
    format: str = "wav",
):
    """Synthesize text with a cloned voice (no personality).
    
    Returns audio stream.
    """
    if not _engine_manager:
        raise HTTPException(503, "Engine not initialized.")
    
    # Load voice
    if not _voice_store.exists(voice_id):
        raise HTTPException(404, f"Voice not found: {voice_id}")
    
    voice = _voice_store.load(voice_id)
    
    # Synthesize
    engine = _engine_manager.active_engine
    audio, sr = await engine.synthesize(text, voice, format)
    
    # Convert to WAV bytes
    audio_bytes = _audio_to_wav_bytes(audio, sr)
    
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=speech.{format}"},
    )


@app.post("/personality/speak")
async def personality_speak(
    text: str,
    voice_id: str,
    personality: bool = True,
    format: str = "wav",
):
    """Synthesize text with personality (Capa 3).
    
    Pipeline: text → LLM personality → TTS → audio
    Slower than /speak but text sounds like the person.
    """
    if not _engine_manager:
        raise HTTPException(503, "Engine not initialized.")
    
    if not _voice_store.exists(voice_id):
        raise HTTPException(404, f"Voice not found: {voice_id}")
    
    voice = _voice_store.load(voice_id)
    
    # Apply personality if enabled and profile exists
    final_text = text
    if personality and _personality_engine:
        from voiceclone.personality.profile import load_profile
        profile = load_profile(voice_id, _voice_store.base_dir)
        if profile:
            final_text = await _personality_engine.personalize(text, profile)
    
    # Synthesize
    engine = _engine_manager.active_engine
    audio, sr = await engine.synthesize(final_text, voice, format)
    
    audio_bytes = _audio_to_wav_bytes(audio, sr)
    
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
    )


# ============================================================
# Voice Management
# ============================================================

@app.get("/voices")
async def list_voices():
    """List all cloned voices."""
    voices = _voice_store.list_voices() if _voice_store else []
    return {
        "voices": [
            {
                "voice_id": v.voice_id,
                "name": v.name,
                "engine": v.engine,
                "created_at": v.created_at,
                "duration_seconds": v.duration_seconds,
                "quality_score": v.quality_score,
            }
            for v in voices
        ]
    }


@app.get("/voices/{voice_id}")
async def get_voice(voice_id: str):
    """Get details of a specific voice."""
    if not _voice_store.exists(voice_id):
        raise HTTPException(404, f"Voice not found: {voice_id}")
    
    voice = _voice_store.load(voice_id)
    
    # Check personality
    from voiceclone.personality.profile import load_profile
    has_personality = load_profile(voice_id, _voice_store.base_dir) is not None
    
    return {
        "voice_id": voice.voice_id,
        "name": voice.name,
        "engine": voice.engine,
        "created_at": voice.created_at,
        "duration_seconds": voice.duration_seconds,
        "quality_score": voice.quality_score,
        "has_personality": has_personality,
    }


@app.delete("/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a cloned voice and its personality."""
    if not _voice_store.exists(voice_id):
        raise HTTPException(404, f"Voice not found: {voice_id}")
    
    _voice_store.delete(voice_id)
    return JSONResponse(status_code=204, content=None)


# ============================================================
# Personality Setup
# ============================================================

@app.post("/personality/setup")
async def setup_personality(
    voice_id: str,
    tone: str = "casual",
    formality: str = "informal",
    humor_style: str = "none",
    self_description: str = "",
    favorite_phrases: list[str] = [],
):
    """Set up personality profile for a voice."""
    if not _voice_store.exists(voice_id):
        raise HTTPException(404, f"Voice not found: {voice_id}")
    
    from datetime import datetime, timezone
    from voiceclone.personality.profile import PersonalityProfile, save_profile
    
    voice = _voice_store.load(voice_id)
    
    profile = PersonalityProfile(
        voice_id=voice_id,
        name=voice.name,
        tone=tone,
        formality=formality,
        humor_style=humor_style,
        self_description=self_description,
        favorite_phrases=favorite_phrases,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    
    save_profile(profile, _voice_store.base_dir)
    
    # Generate sample phrases for validation
    if _personality_engine:
        sample_texts = [
            "Hola, ¿qué tal?",
            "Me parece una buena idea",
            "No estoy de acuerdo con eso",
            "Vámonos de aquí",
            "Esto es genial",
        ]
        sample_phrases = []
        for text in sample_texts:
            personalized = await _personality_engine.personalize(text, profile)
            sample_phrases.append(personalized)
    else:
        sample_phrases = []
    
    return {
        "voice_id": voice_id,
        "personality_created": True,
        "sample_phrases": sample_phrases,
    }


# ============================================================
# Helpers
# ============================================================

def _audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Convert numpy audio to WAV bytes."""
    import struct
    
    # Normalize to int16
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Build WAV header
    num_samples = len(audio_int16)
    data_size = num_samples * 2  # 16-bit = 2 bytes per sample
    
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,  # PCM format size
        1,   # PCM format
        1,   # Mono
        sample_rate,
        sample_rate * 2,  # Byte rate
        2,   # Block align
        16,  # Bits per sample
        b'data',
        data_size,
    )
    
    return header + audio_int16.tobytes()


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the VoiceClone API server."""
    import uvicorn
    
    logger.info("Starting VoiceClone API on http://%s:%d", host, port)
    logger.info("API docs: http://%s:%d/docs", host, port)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
