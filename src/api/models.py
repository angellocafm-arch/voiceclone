"""Pydantic models for API requests/responses"""

from pydantic import BaseModel, Field
from typing import Optional


class CloneVoiceRequest(BaseModel):
    """Request to clone a voice"""
    voice_name: str = Field(..., description="Name for the cloned voice")
    language: str = Field(default="es", description="Language code (es, en, fr, etc.)")
    description: Optional[str] = Field(None, description="Optional description")


class SynthesizeRequest(BaseModel):
    """Request to synthesize text"""
    text: str = Field(..., description="Text to synthesize")
    voice_name: str = Field(..., description="Name of cloned voice to use")
    language: Optional[str] = Field(default="es", description="Language code")


class VoiceInfoResponse(BaseModel):
    """Information about a cloned voice"""
    name: str
    language: str
    quality_score: Optional[float] = None
    created_at: Optional[str] = None


class ListVoicesResponse(BaseModel):
    """Response containing list of voices"""
    voices: list[VoiceInfoResponse]
    total: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: str
