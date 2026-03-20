"""VoiceClone FastAPI Server — Local API for voice cloning and synthesis

This server runs on localhost:8765 and provides a REST API for:
- Voice cloning from audio files
- Speech synthesis with cloned voices
- Voice management (list, get, delete)
- Health checks

Security: Only binds to localhost. No authentication required.
Privacy: All processing is local. Nothing leaves the machine.

Reference: ~/clawd/projects/voiceclone/docs/arquitectura-completa.md
"""

import io
import logging
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_engine.base import AudioFormat, VoiceProfile
from voice_engine.manager import EngineManager

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Global state
# ═══════════════════════════════════════════════════════════════

_manager: Optional[EngineManager] = None
_start_time: float = 0


def get_manager() -> EngineManager:
    """Get the global engine manager"""
    if _manager is None:
        raise HTTPException(
            status_code=503,
            detail="Voice engine not initialized. Server is starting up.",
        )
    if not _manager.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Voice engine is loading. Please try again in a moment.",
        )
    return _manager


# ═══════════════════════════════════════════════════════════════
# App lifecycle
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engine on startup, cleanup on shutdown"""
    global _manager, _start_time
    
    _start_time = time.time()
    logger.info("🎤 VoiceClone API starting...")
    
    _manager = EngineManager()
    success = _manager.initialize()
    
    if success:
        voices = _manager.list_voices()
        logger.info(
            f"✅ VoiceClone API ready — "
            f"Engine: {_manager.engine_name}, "
            f"Voices: {len(voices)}"
        )
    else:
        logger.error("❌ No voice engine could be loaded!")
    
    yield
    
    # Shutdown
    if _manager:
        _manager.shutdown()
    logger.info("VoiceClone API shut down")


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="VoiceClone API",
    description=(
        "Local API for voice cloning and speech synthesis. "
        "100% private — all processing happens on your computer."
    ),
    version="0.1.0-dev",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for local web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://localhost:8765",      # Self
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════

class SpeakRequest(BaseModel):
    """Request to synthesize text with a cloned voice"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: str = Field(..., description="Voice name or ID")
    format: str = Field("wav", description="Output format: wav, ogg, mp3")
    exaggeration: float = Field(0.5, ge=0.0, le=1.0, description="Emotion intensity")
    cfg: float = Field(0.5, ge=0.0, le=1.0, description="Voice adherence strength")


class VoiceResponse(BaseModel):
    """Voice profile response"""
    name: str
    voice_id: str
    language: str
    quality_score: Optional[float]
    duration_seconds: Optional[float]
    engine: str
    has_personality: bool
    created_at: str
    sample_rate: int


class CloneResponse(BaseModel):
    """Response after successful voice cloning"""
    voice_id: str
    name: str
    quality_score: Optional[float]
    duration_seconds: Optional[float]
    engine: str
    message: str


class HealthResponse(BaseModel):
    """Server health check response"""
    status: str
    engine: Optional[str]
    model_loaded: bool
    voices_count: int
    uptime_seconds: int
    version: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse, tags=["status"])
async def health_check():
    """Check server health and engine status
    
    Returns the current status of the VoiceClone service,
    including which engine is active and how many voices are available.
    """
    global _manager, _start_time

    if _manager is None or not _manager.is_ready:
        return HealthResponse(
            status="loading",
            engine=None,
            model_loaded=False,
            voices_count=0,
            uptime_seconds=int(time.time() - _start_time),
            version="0.1.0-dev",
        )

    voices = _manager.list_voices()
    return HealthResponse(
        status="ok",
        engine=_manager.engine_name,
        model_loaded=True,
        voices_count=len(voices),
        uptime_seconds=int(time.time() - _start_time),
        version="0.1.0-dev",
    )


@app.post(
    "/clone",
    response_model=CloneResponse,
    tags=["cloning"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def clone_voice(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, ogg, m4a, flac)"),
    name: str = Form(None, description="Name for the cloned voice (auto-generated if empty)"),
):
    """Clone a voice from an audio file
    
    Upload an audio file (5-120 seconds of clear speech) to create
    a voice clone. The voice can then be used with /speak.
    
    Supported formats: wav, mp3, ogg, m4a, flac, webm
    Recommended: 10-30 seconds, clear speech, no background noise
    """
    manager = get_manager()

    # Generate name if not provided
    if not name:
        import uuid
        name = f"voice-{str(uuid.uuid4())[:6]}"

    # Save uploaded file to temp
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        profile = manager.clone_voice(tmp_path, name)

        return CloneResponse(
            voice_id=profile.voice_id,
            name=profile.name,
            quality_score=profile.quality_score,
            duration_seconds=profile.duration_seconds,
            engine=profile.engine,
            message=f'Voice "{profile.name}" cloned successfully',
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Cloning failed: {e}")
    finally:
        # Cleanup temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass


@app.post(
    "/speak",
    tags=["synthesis"],
    responses={
        200: {"content": {"audio/wav": {}, "audio/ogg": {}, "audio/mpeg": {}}},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def speak(request: SpeakRequest):
    """Synthesize text with a cloned voice
    
    Returns audio in the requested format (wav, ogg, or mp3).
    
    Supports paralinguistic tags in text:
    - [laugh] — laughter
    - [chuckle] — soft laugh
    - [cough] — cough sound
    
    Parameters:
    - exaggeration: Emotion intensity (0=flat, 1=dramatic). Default 0.5
    - cfg: Voice adherence (0=creative, 1=strict). Default 0.5
    """
    manager = get_manager()

    # Find voice
    voice = manager.get_voice(request.voice_id)
    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f'Voice "{request.voice_id}" not found. Use GET /voices to list available voices.',
        )

    # Map format
    format_map = {
        "wav": AudioFormat.WAV,
        "ogg": AudioFormat.OGG,
        "mp3": AudioFormat.MP3,
    }
    output_format = format_map.get(request.format, AudioFormat.WAV)

    # Content type mapping
    content_type_map = {
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "mp3": "audio/mpeg",
    }

    try:
        result = manager.synthesize(
            text=request.text,
            voice=voice,
            output_format=output_format,
            exaggeration=request.exaggeration,
            cfg=request.cfg,
        )

        content_type = content_type_map.get(request.format, "audio/wav")

        return Response(
            content=result.audio_data,
            media_type=content_type,
            headers={
                "X-Duration-Seconds": f"{result.duration_seconds:.2f}",
                "X-Voice-Name": result.voice_name,
                "X-Sample-Rate": str(result.sample_rate),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {e}")


@app.get(
    "/voices",
    response_model=list[VoiceResponse],
    tags=["voices"],
)
async def list_voices():
    """List all available cloned voices
    
    Returns metadata for each voice including name, quality score,
    which engine created it, and whether personality is configured.
    """
    manager = get_manager()
    voices = manager.list_voices()

    return [
        VoiceResponse(
            name=v.name,
            voice_id=v.voice_id,
            language=v.language,
            quality_score=v.quality_score,
            duration_seconds=v.duration_seconds,
            engine=v.engine,
            has_personality=v.has_personality,
            created_at=v.created_at,
            sample_rate=v.sample_rate,
        )
        for v in voices
    ]


@app.get(
    "/voices/{voice_id}",
    response_model=VoiceResponse,
    tags=["voices"],
    responses={404: {"model": ErrorResponse}},
)
async def get_voice(voice_id: str):
    """Get details of a specific voice"""
    manager = get_manager()
    voice = manager.get_voice(voice_id)

    if voice is None:
        raise HTTPException(status_code=404, detail=f'Voice "{voice_id}" not found')

    return VoiceResponse(
        name=voice.name,
        voice_id=voice.voice_id,
        language=voice.language,
        quality_score=voice.quality_score,
        duration_seconds=voice.duration_seconds,
        engine=voice.engine,
        has_personality=voice.has_personality,
        created_at=voice.created_at,
        sample_rate=voice.sample_rate,
    )


@app.delete(
    "/voices/{voice_id}",
    tags=["voices"],
    responses={404: {"model": ErrorResponse}},
    status_code=204,
)
async def delete_voice(voice_id: str):
    """Delete a cloned voice and all its data
    
    ⚠️  This permanently deletes the voice, its reference audio,
    personality profile, and all generated samples.
    This action cannot be undone.
    """
    manager = get_manager()

    if not manager.delete_voice(voice_id):
        raise HTTPException(status_code=404, detail=f'Voice "{voice_id}" not found')

    return Response(status_code=204)


# ═══════════════════════════════════════════════════════════════
# Personality endpoints (stub for Task 3.5)
# ═══════════════════════════════════════════════════════════════

class PersonalitySpeakRequest(BaseModel):
    """Request for personality-enhanced speech"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str
    personality: bool = True
    format: str = "wav"


@app.post(
    "/personality/speak",
    tags=["personality"],
    responses={
        200: {"content": {"audio/wav": {}}},
        501: {"model": ErrorResponse},
    },
)
async def personality_speak(request: PersonalitySpeakRequest):
    """Synthesize speech with personality (Capa 3)
    
    Takes the input text, rewrites it using the voice's personality
    profile via LLM, then synthesizes with the cloned voice.
    
    ⚠️  This endpoint will be fully implemented in Task 3.5.
    Currently falls back to regular /speak without personality.
    """
    # For now, fall back to regular synthesis
    speak_request = SpeakRequest(
        text=request.text,
        voice_id=request.voice_id,
        format=request.format,
    )
    return await speak(speak_request)


class PersonalitySetupRequest(BaseModel):
    """Request to set up personality for a voice"""
    voice_id: str
    questionnaire: dict = Field(default_factory=dict)
    examples: list[str] = Field(default_factory=list)


@app.post(
    "/personality/setup",
    tags=["personality"],
    responses={501: {"model": ErrorResponse}},
)
async def personality_setup(request: PersonalitySetupRequest):
    """Set up personality profile for a voice
    
    ⚠️  Will be fully implemented in Task 3.5.
    """
    raise HTTPException(
        status_code=501,
        detail="Personality setup not yet implemented. Coming in next release.",
    )


# ═══════════════════════════════════════════════════════════════
# Entry point (for direct execution)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.server:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
    )
