"""VoiceClone FastAPI Server — Local API for voice cloning and synthesis

This server runs on localhost:8765 and provides a REST API for:
- Voice cloning from audio files
- Speech synthesis with cloned voices
- Voice management (list, get, delete)
- Personality capture and styled speech (Layer 3)
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
from personality.engine import PersonalityEngine

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Global state
# ═══════════════════════════════════════════════════════════════

_manager: Optional[EngineManager] = None
_personality: Optional[PersonalityEngine] = None
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


def get_personality() -> PersonalityEngine:
    """Get the global personality engine"""
    if _personality is None or not _personality.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Personality engine not initialized.",
        )
    return _personality


# ═══════════════════════════════════════════════════════════════
# App lifecycle
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engine on startup, cleanup on shutdown"""
    global _manager, _personality, _start_time
    
    _start_time = time.time()
    logger.info("🎤 VoiceClone API starting...")
    
    # Initialize voice engine (Layer 1)
    _manager = EngineManager()
    success = _manager.initialize()
    
    if success:
        voices = _manager.list_voices()
        logger.info(
            f"✅ Voice engine ready — "
            f"Engine: {_manager.engine_name}, "
            f"Voices: {len(voices)}"
        )
    else:
        logger.error("❌ No voice engine could be loaded!")
    
    # Initialize personality engine (Layer 3)
    _personality = PersonalityEngine(
        personality_dir=_manager.voiceclone_dir / "personality" if _manager else None,
    )
    if _personality.initialize():
        logger.info("✅ Personality engine ready")
    else:
        logger.warning("⚠️  Personality engine failed to initialize (non-critical)")
    
    yield
    
    # Shutdown
    if _personality:
        _personality.shutdown()
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
    personality_engine: Optional[str]
    personalities_count: int
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
            personality_engine=None,
            personalities_count=0,
            uptime_seconds=int(time.time() - _start_time),
            version="0.1.0-dev",
        )

    voices = _manager.list_voices()
    
    # Personality status
    personality_status = None
    personalities_count = 0
    if _personality and _personality.is_ready:
        p_status = _personality.get_status()
        personality_status = p_status.get("llm_backend")
        personalities_count = p_status.get("profiles_count", 0)
    
    return HealthResponse(
        status="ok",
        engine=_manager.engine_name,
        model_loaded=True,
        voices_count=len(voices),
        personality_engine=personality_status,
        personalities_count=personalities_count,
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
# Personality endpoints (Layer 3 — full implementation)
# ═══════════════════════════════════════════════════════════════

class PersonalitySpeakRequest(BaseModel):
    """Request for personality-enhanced speech"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text/intention to express")
    voice_id: str = Field(..., description="Voice name or ID")
    personality: bool = Field(True, description="Apply personality rewriting (false = regular speak)")
    format: str = Field("wav", description="Output format: wav, ogg, mp3")
    exaggeration: float = Field(0.5, ge=0.0, le=1.0, description="Emotion intensity")
    cfg: float = Field(0.5, ge=0.0, le=1.0, description="Voice adherence strength")


class PersonalitySetupRequest(BaseModel):
    """Request to set up personality for a voice via questionnaire answers"""
    voice_id: str = Field(..., description="Voice to attach personality to")
    questionnaire: dict = Field(
        default_factory=dict,
        description=(
            "Questionnaire answers as {question_id: answer}. "
            "Required: description, formality, warmth, energy. "
            "Optional: sentence_length, directness, catchphrases, "
            "vocabulary_level, humor_style, emoji_usage, topics, sample_phrases."
        ),
    )
    examples: list[str] = Field(
        default_factory=list,
        description="Optional example texts for pattern analysis",
    )


class PersonalitySetupResponse(BaseModel):
    """Response after personality setup"""
    voice_id: str
    personality_configured: bool
    sample_phrases: list[str]
    profile_summary: dict
    message: str


class PersonalityValidateRequest(BaseModel):
    """Request to submit feedback on personality sample phrases"""
    voice_id: str = Field(..., description="Voice being validated")
    feedback: list[dict] = Field(
        ...,
        description=(
            "List of {phrase_index: int, is_accurate: bool, comment: str}. "
            "Mark each sample phrase as accurate or not."
        ),
    )


class PersonalityValidateResponse(BaseModel):
    """Response after validation feedback"""
    voice_id: str
    updated: bool
    accuracy_score: float
    new_sample_phrases: list[str]
    message: str


class PersonalityProfileResponse(BaseModel):
    """Full personality profile response"""
    voice_name: str
    description: str
    formality: str
    humor_style: str
    catchphrases: list[str]
    topics: list[str]
    vocabulary_level: str
    emoji_usage: str
    sentence_length: str
    directness: str
    warmth: str
    energy: str
    sample_phrases: list[str]
    sources: list[str]
    version: int


class QuestionResponse(BaseModel):
    """A single questionnaire question"""
    id: str
    text: str
    help_text: str
    category: str
    input_type: str
    choices: list[str]
    required: bool


class TextAnalysisRequest(BaseModel):
    """Request to analyze texts for personality patterns"""
    voice_id: str
    texts: list[str] = Field(..., min_length=1, description="List of text messages to analyze")
    source: str = Field("manual", description="Source identifier (manual, whatsapp, email)")


class TextAnalysisResponse(BaseModel):
    """Text analysis results"""
    voice_id: str
    total_messages: int
    total_words: int
    avg_sentence_length: float
    inferred_formality: str
    emoji_level: str
    top_words: dict
    potential_catchphrases: list[str]
    texts_saved: int
    profile_enriched: bool


@app.post(
    "/personality/speak",
    tags=["personality"],
    responses={
        200: {"content": {"audio/wav": {}, "audio/ogg": {}, "audio/mpeg": {}}},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def personality_speak(request: PersonalitySpeakRequest):
    """Synthesize speech with personality (Layer 3)

    Takes the input text, rewrites it using the voice's personality
    profile via LLM, then synthesizes with the cloned voice.

    Pipeline:
      Input text → LLM rewrite (personality) → TTS synthesis → Audio

    If personality is disabled or not configured for this voice,
    falls back to regular synthesis.

    Note: This endpoint is slower than /speak because it includes
    the LLM rewriting step. Use /speak for raw synthesis.
    """
    manager = get_manager()
    personality = get_personality()

    # Find voice
    voice = manager.get_voice(request.voice_id)
    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f'Voice "{request.voice_id}" not found. Use GET /voices to list available voices.',
        )

    # Apply personality rewriting if enabled
    styled_text = request.text
    personality_applied = False

    if request.personality and personality.has_personality(voice.name):
        try:
            styled_text = personality.apply_personality(request.text, voice.name)
            personality_applied = True
        except Exception as e:
            logger.warning(f"Personality rewrite failed, using original text: {e}")

    # Map format
    format_map = {
        "wav": AudioFormat.WAV,
        "ogg": AudioFormat.OGG,
        "mp3": AudioFormat.MP3,
    }
    output_format = format_map.get(request.format, AudioFormat.WAV)
    content_type_map = {
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "mp3": "audio/mpeg",
    }

    try:
        result = manager.synthesize(
            text=styled_text,
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
                "X-Personality-Applied": str(personality_applied).lower(),
                "X-Original-Text": request.text[:100],
                "X-Styled-Text": styled_text[:100],
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {e}")


@app.post(
    "/personality/setup",
    response_model=PersonalitySetupResponse,
    tags=["personality"],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def personality_setup(request: PersonalitySetupRequest):
    """Set up personality profile for a voice

    Submit questionnaire answers to create a personality profile.
    The system will generate sample phrases for validation.

    Required answers: description, formality, warmth, energy.
    Optional: sentence_length, directness, catchphrases,
    vocabulary_level, humor_style, emoji_usage, topics, sample_phrases.

    Use GET /personality/questions to see all available questions.
    """
    manager = get_manager()
    personality = get_personality()

    # Verify voice exists
    voice = manager.get_voice(request.voice_id)
    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f'Voice "{request.voice_id}" not found.',
        )

    # Start questionnaire and submit answers
    questionnaire = personality.start_questionnaire(voice.name)

    results = questionnaire.submit_all(request.questionnaire)
    failed = {k: v for k, v in results.items() if not v}
    if failed:
        logger.warning(f"Some answers were not accepted: {failed}")

    # Check if minimum required answers are present
    if not questionnaire.is_complete():
        missing = questionnaire.get_missing()
        missing_ids = [q.id for q in missing]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing required answers: {missing_ids}. "
                "Required: description, formality, warmth, energy."
            ),
        )

    # Finalize and create profile
    profile = personality.finalize_questionnaire(voice.name, questionnaire)

    # Import example texts if provided
    if request.examples:
        personality.import_texts(voice.name, request.examples, source="setup")

    # Update voice has_personality flag
    voice.has_personality = True

    return PersonalitySetupResponse(
        voice_id=voice.voice_id,
        personality_configured=True,
        sample_phrases=profile.sample_phrases[:5],
        profile_summary={
            "formality": profile.formality,
            "warmth": profile.warmth,
            "energy": profile.energy,
            "catchphrases_count": len(profile.catchphrases),
            "topics": profile.topics[:5],
            "version": profile.version,
        },
        message=(
            f'Personality configured for "{voice.name}". '
            f'Review the sample phrases — do they sound like you? '
            f'Use POST /personality/validate to give feedback.'
        ),
    )


@app.post(
    "/personality/validate",
    response_model=PersonalityValidateResponse,
    tags=["personality"],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def personality_validate(request: PersonalityValidateRequest):
    """Submit feedback on personality sample phrases

    After setup, review the generated sample phrases and tell us
    which ones sound like you.

    Send feedback as: [{phrase_index: 0, is_accurate: true/false, comment: "..."}]

    The system will refine the profile based on your feedback
    and generate new sample phrases.
    """
    personality = get_personality()

    # Find voice name from voice_id
    manager = get_manager()
    voice = manager.get_voice(request.voice_id)
    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f'Voice "{request.voice_id}" not found.',
        )

    if not personality.has_personality(voice.name):
        raise HTTPException(
            status_code=400,
            detail=f'No personality configured for "{voice.name}". Use POST /personality/setup first.',
        )

    # Submit feedback
    updated_profile = personality.submit_feedback(voice.name, request.feedback)
    if updated_profile is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to update personality profile.",
        )

    # Generate new sample phrases
    new_samples = personality.generate_samples(voice.name, count=5)

    # Calculate accuracy
    accurate = sum(1 for f in request.feedback if f.get("is_accurate", False))
    total = len(request.feedback)
    accuracy = accurate / total if total > 0 else 0

    return PersonalityValidateResponse(
        voice_id=voice.voice_id,
        updated=True,
        accuracy_score=accuracy,
        new_sample_phrases=new_samples,
        message=(
            f"Profile updated (v{updated_profile.version}). "
            f"Accuracy: {accuracy:.0%}. "
            + ("Looking good! " if accuracy >= 0.6 else "We'll keep refining. ")
            + "Review the new phrases above."
        ),
    )


@app.get(
    "/personality/questions",
    response_model=list[QuestionResponse],
    tags=["personality"],
)
async def personality_questions():
    """Get the personality questionnaire questions

    Returns all questions with their IDs, text, help text,
    and available choices.

    Use these question IDs when submitting answers to
    POST /personality/setup.
    """
    from personality.questionnaire import Questionnaire

    q = Questionnaire()
    questions = q.get_questions()

    return [
        QuestionResponse(
            id=question.id,
            text=question.text,
            help_text=question.help_text,
            category=question.category.value,
            input_type=question.input_type,
            choices=question.choices,
            required=question.required,
        )
        for question in questions
    ]


@app.get(
    "/personality/{voice_id}",
    response_model=PersonalityProfileResponse,
    tags=["personality"],
    responses={404: {"model": ErrorResponse}},
)
async def get_personality_profile(voice_id: str):
    """Get the personality profile for a voice

    Returns all personality data including traits,
    catchphrases, topics, and sample phrases.
    """
    personality_engine = get_personality()
    manager = get_manager()

    voice = manager.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f'Voice "{voice_id}" not found.')

    profile = personality_engine.get_profile(voice.name)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f'No personality configured for "{voice.name}".',
        )

    return PersonalityProfileResponse(
        voice_name=profile.voice_name,
        description=profile.description,
        formality=profile.formality,
        humor_style=profile.humor_style,
        catchphrases=profile.catchphrases,
        topics=profile.topics,
        vocabulary_level=profile.vocabulary_level,
        emoji_usage=profile.emoji_usage,
        sentence_length=profile.sentence_length,
        directness=profile.directness,
        warmth=profile.warmth,
        energy=profile.energy,
        sample_phrases=profile.sample_phrases,
        sources=profile.sources,
        version=profile.version,
    )


@app.delete(
    "/personality/{voice_id}",
    tags=["personality"],
    responses={404: {"model": ErrorResponse}},
    status_code=204,
)
async def delete_personality(voice_id: str):
    """Delete personality profile for a voice

    ⚠️  This permanently deletes the personality profile,
    all example texts, and vocabulary data.
    The cloned voice itself is NOT deleted.
    """
    personality_engine = get_personality()
    manager = get_manager()

    voice = manager.get_voice(voice_id)
    if voice is None:
        raise HTTPException(status_code=404, detail=f'Voice "{voice_id}" not found.')

    if not personality_engine.delete_personality(voice.name):
        raise HTTPException(
            status_code=404,
            detail=f'No personality configured for "{voice.name}".',
        )

    voice.has_personality = False
    return Response(status_code=204)


@app.post(
    "/personality/analyze",
    response_model=TextAnalysisResponse,
    tags=["personality"],
    responses={404: {"model": ErrorResponse}},
)
async def analyze_texts(request: TextAnalysisRequest):
    """Analyze texts to extract personality patterns

    Upload text messages (WhatsApp, emails, etc.) and the
    system will extract vocabulary, formality level, emoji usage,
    sentence patterns, and potential catchphrases.

    If the voice already has a personality profile, the
    discovered patterns will be merged into it.
    """
    personality_engine = get_personality()
    manager = get_manager()

    voice = manager.get_voice(request.voice_id)
    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f'Voice "{request.voice_id}" not found.',
        )

    analysis = personality_engine.import_texts(
        voice.name, request.texts, source=request.source,
    )

    has_profile = personality_engine.has_personality(voice.name)

    return TextAnalysisResponse(
        voice_id=voice.voice_id,
        total_messages=analysis.get("total_messages", 0),
        total_words=analysis.get("total_words", 0),
        avg_sentence_length=analysis.get("avg_sentence_length", 0),
        inferred_formality=analysis.get("inferred_formality", "unknown"),
        emoji_level=analysis.get("emoji_level", "unknown"),
        top_words=analysis.get("top_words", {}),
        potential_catchphrases=analysis.get("potential_catchphrases", []),
        texts_saved=analysis.get("texts_saved", 0),
        profile_enriched=has_profile,
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
