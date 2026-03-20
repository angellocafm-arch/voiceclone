"""FastAPI application for VoiceClone API"""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import io

from ..voice_engine import ChatterboxEngine
from .models import (
    CloneVoiceRequest, SynthesizeRequest, VoiceInfoResponse,
    ListVoicesResponse, ErrorResponse
)

logger = logging.getLogger(__name__)


def create_app(model_path: Path | None = None, cache_dir: Path | None = None) -> FastAPI:
    """Create and configure FastAPI application
    
    Args:
        model_path: Path to Chatterbox model
        cache_dir: Cache directory for cloned voices
        
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="VoiceClone API",
        description="Voice cloning + personality AI for accessibility",
        version="0.1.0",
    )
    
    # Initialize voice engine
    engine = ChatterboxEngine(model_path=model_path, cache_dir=cache_dir)
    
    # ============================================================================
    # HEALTH CHECK
    # ============================================================================
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok", "service": "voiceclone-api"}
    
    
    # ============================================================================
    # VOICE CLONING
    # ============================================================================
    
    @app.post("/clone")
    async def clone_voice(
        request: CloneVoiceRequest,
        audio: UploadFile = File(...),
    ) -> VoiceInfoResponse:
        """Clone a voice from uploaded audio
        
        Args:
            request: Clone request with voice name
            audio: Audio file (wav, m4a, mp3)
            
        Returns:
            VoiceInfoResponse with cloned voice info
        """
        try:
            # Save uploaded file temporarily
            temp_path = Path(f"/tmp/{audio.filename}")
            with open(temp_path, "wb") as f:
                contents = await audio.read()
                f.write(contents)
            
            # Clone voice
            voice_profile = engine.clone_voice(temp_path, request.voice_name)
            
            # Clean up temp file
            temp_path.unlink()
            
            logger.info(f"Cloned voice: {request.voice_name}")
            
            return VoiceInfoResponse(
                name=voice_profile.name,
                language=voice_profile.language,
                quality_score=voice_profile.quality_score,
                created_at=voice_profile.created_at,
            )
        
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    # ============================================================================
    # SYNTHESIS
    # ============================================================================
    
    @app.post("/speak")
    async def synthesize(request: SynthesizeRequest) -> StreamingResponse:
        """Synthesize text with cloned voice
        
        Args:
            request: Synthesis request
            
        Returns:
            Audio stream (wav)
        """
        try:
            # Get voice profile
            voices = engine.list_voices()
            voice_profile = next(
                (v for v in voices if v.name == request.voice_name),
                None
            )
            
            if not voice_profile:
                raise ValueError(f"Voice '{request.voice_name}' not found")
            
            # Synthesize
            audio_bytes = engine.synthesize(request.text, voice_profile)
            
            # Return as stream
            audio_stream = io.BytesIO(audio_bytes)
            
            return StreamingResponse(
                iter([audio_stream.getvalue()]),
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=output.wav"}
            )
        
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    # ============================================================================
    # VOICE MANAGEMENT
    # ============================================================================
    
    @app.get("/voices", response_model=ListVoicesResponse)
    async def list_voices() -> ListVoicesResponse:
        """List all cloned voices"""
        try:
            voices = engine.list_voices()
            return ListVoicesResponse(
                voices=[
                    VoiceInfoResponse(
                        name=v.name,
                        language=v.language,
                        quality_score=v.quality_score,
                        created_at=v.created_at,
                    )
                    for v in voices
                ],
                total=len(voices),
            )
        except Exception as e:
            logger.error(f"List voices failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    @app.delete("/voices/{voice_name}")
    async def delete_voice(voice_name: str) -> dict:
        """Delete a cloned voice"""
        try:
            success = engine.delete_voice(voice_name)
            if not success:
                raise ValueError(f"Voice '{voice_name}' not found")
            
            logger.info(f"Deleted voice: {voice_name}")
            return {"status": "deleted", "voice": voice_name}
        
        except Exception as e:
            logger.error(f"Delete voice failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8765)
