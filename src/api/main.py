"""
VoiceClone v4 — Main FastAPI Application

Unified API server integrating all 4 modules:
1. Communication (voice synthesis + phrase prediction)
2. Control (OS operations via LLM tool use)
3. Productivity (document dictation, agenda)
4. Channels (Telegram, WhatsApp messaging)

Plus:
- Onboarding conversational flow
- WebSocket for eye tracking + chat streaming
- Health monitoring

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# ─── App Configuration ────────────────────────────────────

logger = logging.getLogger(__name__)

INSTALL_DIR = Path(os.environ.get("VOICECLONE_DIR", "~/.voiceclone")).expanduser()
CONFIG_PATH = INSTALL_DIR / "config.json"


def load_config() -> dict[str, Any]:
    """Load VoiceClone configuration."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


# ─── Pydantic Models ─────────────────────────────────────

class SpeakRequest(BaseModel):
    """Request to synthesize speech."""
    text: str
    voice_id: str = "default"
    speed: float = Field(1.0, ge=0.5, le=2.0)


class ChatRequest(BaseModel):
    """Request to chat with the LLM."""
    message: str
    context: str = ""


class ControlRequest(BaseModel):
    """Request to execute an OS control action."""
    instruction: str


class ConfirmRequest(BaseModel):
    """Request to confirm a pending action."""
    action_id: str
    confirmed: bool


class ChannelConfigRequest(BaseModel):
    """Request to configure a messaging channel."""
    type: str
    config: dict[str, Any]


class ChannelSendRequest(BaseModel):
    """Request to send a message through a channel."""
    to: str
    text: str = ""
    as_voice: bool = False


class OnboardingAdvanceRequest(BaseModel):
    """Request to advance onboarding step."""
    user_input: str = ""


# ─── Create FastAPI App ──────────────────────────────────

app = FastAPI(
    title="VoiceClone",
    description="Asistente de vida completo para personas con ELA — 100% local",
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

# CORS: Only localhost (100% local app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static audio files
AUDIO_DIR = INSTALL_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

# ─── State (initialized on startup) ──────────────────────

_state: dict[str, Any] = {
    "ollama_client": None,
    "onboarding": None,
    "channel_manager": None,
    "phrase_predictor": None,
    "file_manager": None,
    "browser_control": None,
    "app_launcher": None,
    "email_manager": None,
    "pending_actions": {},
}


@app.on_event("startup")
async def startup() -> None:
    """Initialize all modules on server startup."""
    logger.info("VoiceClone v4 starting...")

    try:
        # LLM Client
        from src.llm.ollama_client import OllamaClient
        config = load_config()
        ollama_config = config.get("ollama", {})
        _state["ollama_client"] = OllamaClient(
            model=ollama_config.get("model", "mistral:7b"),
            host=ollama_config.get("host", "http://localhost:11434"),
        )

        # Onboarding Agent
        from src.llm.onboarding_agent import OnboardingAgent
        _state["onboarding"] = OnboardingAgent()

        # Phrase Predictor
        from src.llm.phrase_predictor import PhrasePredictor
        _state["phrase_predictor"] = PhrasePredictor()

        # System Control Modules
        from src.system.file_manager import FileManager
        from src.system.browser_control import BrowserControl
        from src.system.app_launcher import AppLauncher
        from src.system.email_manager import EmailManager

        _state["file_manager"] = FileManager()
        _state["browser_control"] = BrowserControl()
        _state["app_launcher"] = AppLauncher()
        _state["email_manager"] = EmailManager()

        # Channel Manager
        from src.channels.channel_manager import ChannelManager
        _state["channel_manager"] = ChannelManager(
            on_message=_on_channel_message,
        )

        logger.info("All modules initialized")

    except Exception as e:
        logger.error("Startup error: %s", e)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up on server shutdown."""
    if _state.get("ollama_client"):
        await _state["ollama_client"].close()
    if _state.get("channel_manager"):
        await _state["channel_manager"].stop_all()
    if _state.get("browser_control"):
        await _state["browser_control"].close()


async def _on_channel_message(msg: Any) -> None:
    """Callback when a channel message arrives."""
    logger.info("Channel message from %s: %s", msg.sender_name, msg.text or "[media]")
    # TODO: synthesize voice and play audio


# ═══════════════════════════════════════════════════════════
# HEALTH & SYSTEM
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """System health check."""
    ollama_ok = False
    if _state.get("ollama_client"):
        ollama_ok = await _state["ollama_client"].is_healthy()

    channels_active = 0
    if _state.get("channel_manager"):
        channels_active = len(_state["channel_manager"].channels)

    return {
        "status": "ok",
        "version": "4.0.0",
        "ollama": ollama_ok,
        "voice_engine": True,  # TODO: actual check
        "channels": channels_active,
        "timestamp": time.time(),
    }


@app.get("/api/system/info")
async def system_info() -> dict[str, Any]:
    """Get system hardware information."""
    import platform

    config = load_config()
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "model": config.get("ollama", {}).get("model", "unknown"),
        "install_dir": str(INSTALL_DIR),
    }


# ═══════════════════════════════════════════════════════════
# VOICE & COMMUNICATION (Module 1)
# ═══════════════════════════════════════════════════════════

@app.post("/api/speak")
async def speak(request: SpeakRequest) -> dict[str, Any]:
    """
    Synthesize text to speech using cloned voice.

    Returns URL to the generated audio file.
    """
    # TODO: integrate with voice engine
    return {
        "audio_url": f"/audio/output_{int(time.time())}.wav",
        "text": request.text,
        "voice_id": request.voice_id,
        "duration": 0.0,
        "status": "placeholder — voice engine integration pending",
    }


@app.get("/api/voices")
async def list_voices() -> dict[str, Any]:
    """List available voice profiles."""
    voices_dir = INSTALL_DIR / "voices"
    voices: list[dict[str, str]] = []

    if voices_dir.exists():
        for voice_dir in voices_dir.iterdir():
            if voice_dir.is_dir():
                voices.append({
                    "id": voice_dir.name,
                    "name": voice_dir.name.replace("_", " ").title(),
                    "path": str(voice_dir),
                })

    return {"voices": voices, "count": len(voices)}


@app.post("/api/voices/clone")
async def clone_voice(audio_file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Clone a voice from an audio file.

    Accepts: WAV, MP3, OGG, M4A
    """
    # Save uploaded file
    voices_dir = INSTALL_DIR / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)

    voice_id = f"voice_{int(time.time())}"
    voice_dir = voices_dir / voice_id
    voice_dir.mkdir(exist_ok=True)

    audio_path = voice_dir / f"reference{Path(audio_file.filename or '.wav').suffix}"
    content = await audio_file.read()
    audio_path.write_bytes(content)

    # TODO: actual cloning with Chatterbox/XTTS
    return {
        "voice_id": voice_id,
        "name": voice_id,
        "audio_path": str(audio_path),
        "quality_score": 0.0,
        "status": "placeholder — cloning engine integration pending",
    }


@app.get("/api/predict")
async def predict_phrases(
    context: str = "",
    limit: int = 5,
) -> dict[str, Any]:
    """Predict likely phrases based on context and history."""
    predictor = _state.get("phrase_predictor")
    if not predictor:
        raise HTTPException(500, "Phrase predictor not initialized")

    predictions = predictor.predict(context=context, limit=limit)
    return {
        "predictions": [p.to_dict() for p in predictions],
        "context": context,
    }


# ═══════════════════════════════════════════════════════════
# CONTROL (Module 2)
# ═══════════════════════════════════════════════════════════

@app.post("/api/control/execute")
async def control_execute(request: ControlRequest) -> dict[str, Any]:
    """
    Execute an OS control action via natural language instruction.

    The LLM interprets the instruction and calls the appropriate tool.
    """
    client = _state.get("ollama_client")
    if not client:
        raise HTTPException(503, "LLM not available")

    # TODO: wire up to ollama_client.agent_chat with system tools registered
    return {
        "instruction": request.instruction,
        "status": "placeholder — agent loop integration pending",
        "action": None,
        "result": None,
        "confirmation_needed": False,
    }


@app.post("/api/control/confirm")
async def control_confirm(request: ConfirmRequest) -> dict[str, Any]:
    """Confirm or deny a pending OS action."""
    pending = _state["pending_actions"].pop(request.action_id, None)
    if not pending:
        raise HTTPException(404, "No pending action with that ID")

    if request.confirmed:
        # TODO: execute the pending action
        return {"success": True, "message": "Action executed"}
    else:
        return {"success": True, "message": "Action cancelled"}


@app.get("/api/control/history")
async def control_history() -> dict[str, Any]:
    """Get recent control action history."""
    # TODO: maintain action history
    return {"actions": [], "count": 0}


# ═══════════════════════════════════════════════════════════
# CHANNELS (Module 4)
# ═══════════════════════════════════════════════════════════

@app.get("/api/channels")
async def list_channels() -> dict[str, Any]:
    """List configured messaging channels."""
    cm = _state.get("channel_manager")
    if not cm:
        return {"channels": [], "count": 0}

    statuses = cm.get_all_status()
    return {"channels": statuses, "count": len(statuses)}


@app.post("/api/channels/configure")
async def configure_channel(request: ChannelConfigRequest) -> dict[str, Any]:
    """Configure a new messaging channel."""
    cm = _state.get("channel_manager")
    if not cm:
        raise HTTPException(503, "Channel manager not initialized")

    return await cm.configure_channel(request.type, request.config)


@app.delete("/api/channels/{channel_id}")
async def remove_channel(channel_id: str) -> dict[str, Any]:
    """Remove a channel configuration."""
    cm = _state.get("channel_manager")
    if not cm:
        raise HTTPException(503, "Channel manager not initialized")

    return await cm.remove_channel(channel_id)


@app.get("/api/channels/{channel_id}/messages")
async def channel_messages(channel_id: str, limit: int = 20) -> dict[str, Any]:
    """Get recent messages from a channel."""
    cm = _state.get("channel_manager")
    if not cm:
        return {"messages": [], "count": 0}

    messages = cm.get_recent_messages(channel_type=channel_id, limit=limit)
    return {"messages": messages, "count": len(messages)}


@app.post("/api/channels/{channel_id}/send")
async def channel_send(channel_id: str, request: ChannelSendRequest) -> dict[str, Any]:
    """Send a message through a channel."""
    cm = _state.get("channel_manager")
    if not cm:
        raise HTTPException(503, "Channel manager not initialized")

    from src.channels.base import OutgoingMessage
    msg = OutgoingMessage(text=request.text, as_voice=request.as_voice)
    return await cm.send(channel_id, request.to, msg)


# ═══════════════════════════════════════════════════════════
# ONBOARDING
# ═══════════════════════════════════════════════════════════

@app.get("/api/onboarding/status")
async def onboarding_status() -> dict[str, Any]:
    """Get current onboarding status."""
    onboarding = _state.get("onboarding")
    if not onboarding:
        raise HTTPException(503, "Onboarding not initialized")

    return onboarding.get_status()


@app.post("/api/onboarding/advance")
async def onboarding_advance(request: OnboardingAdvanceRequest) -> dict[str, Any]:
    """Process user input and advance onboarding."""
    onboarding = _state.get("onboarding")
    if not onboarding:
        raise HTTPException(503, "Onboarding not initialized")

    # TODO: use LLM to process input and decide next step
    new_step = onboarding.advance_step()
    return {
        "step": new_step.value,
        "status": onboarding.get_status(),
    }


# ═══════════════════════════════════════════════════════════
# CHAT (LLM)
# ═══════════════════════════════════════════════════════════

@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """
    Chat with the LLM assistant.

    Returns the full response (non-streaming).
    """
    client = _state.get("ollama_client")
    if not client:
        raise HTTPException(503, "LLM not available. Is Ollama running?")

    from src.llm.ollama_client import ChatMessage

    messages = [
        ChatMessage(role="system", content=(
            "Eres VoiceClone, un asistente de vida para personas con ELA. "
            "Eres cálido, directo y servicial. Respondes en español."
        )),
        ChatMessage(role="user", content=request.message),
    ]

    try:
        response = await client.chat(messages)
        return {
            "reply": response.message.content,
            "model": response.model,
            "tools_used": [tc.get("function", {}).get("name") for tc in response.tool_calls],
            "duration_ms": response.duration_ms,
        }
    except ConnectionError as e:
        raise HTTPException(503, str(e))


# ═══════════════════════════════════════════════════════════
# WEBSOCKETS
# ═══════════════════════════════════════════════════════════

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    """
    WebSocket for streaming chat with the LLM.

    In: {"message": str}
    Out: {"delta": str, "done": bool}
    """
    await websocket.accept()

    client = _state.get("ollama_client")
    if not client:
        await websocket.send_json({"error": "LLM not available"})
        await websocket.close()
        return

    from src.llm.ollama_client import ChatMessage

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            messages = [
                ChatMessage(role="system", content=(
                    "Eres VoiceClone, asistente de vida para ELA. Español."
                )),
                ChatMessage(role="user", content=message),
            ]

            async for chunk in client.chat_stream(messages):
                await websocket.send_json({
                    "delta": chunk.content,
                    "done": chunk.done,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket chat error: %s", e)


@app.websocket("/ws/gaze")
async def ws_gaze(websocket: WebSocket) -> None:
    """
    WebSocket for eye tracking data.

    In: {"x": float, "y": float, "timestamp": float}
    Out: {"dwell_target": str|null, "dwell_progress": float}
    """
    await websocket.accept()

    # Dwell tracking state
    current_target: Optional[str] = None
    dwell_start: float = 0
    dwell_threshold: float = 0.8  # seconds

    try:
        while True:
            data = await websocket.receive_json()
            x = data.get("x", 0)
            y = data.get("y", 0)

            # TODO: map x,y to UI elements and track dwell
            # This is a placeholder for the eye tracking processing

            await websocket.send_json({
                "dwell_target": current_target,
                "dwell_progress": 0.0,
                "x": x,
                "y": y,
            })

    except WebSocketDisconnect:
        pass


# ═══════════════════════════════════════════════════════════
# SERVE WEB UI
# ═══════════════════════════════════════════════════════════

# Mount web UI (if available)
WEB_DIR = Path(__file__).parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
