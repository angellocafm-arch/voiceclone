"""
VoiceClone — Onboarding Agent

Conversational agent that guides new users through the initial setup:
1. Welcome and introduction
2. Voice recording or audio upload
3. Voice cloning
4. Voice test (user hears their cloned voice)
5. Channel configuration (optional)
6. Completion

The agent uses the LLM to have a natural conversation, not forms.
State is persistent so onboarding can be resumed if interrupted.

MIT License — Vertex Developer 2026
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Steps in the onboarding flow."""
    WELCOME = "welcome"
    VOICE_INTRO = "voice_intro"
    VOICE_RECORD = "voice_record"
    VOICE_UPLOAD = "voice_upload"
    VOICE_CLONE = "voice_clone"
    VOICE_TEST = "voice_test"
    PERSONALITY = "personality"
    CHANNELS = "channels"
    COMPLETE = "complete"


# Step order for progression
STEP_ORDER = [
    OnboardingStep.WELCOME,
    OnboardingStep.VOICE_INTRO,
    OnboardingStep.VOICE_RECORD,
    OnboardingStep.VOICE_CLONE,
    OnboardingStep.VOICE_TEST,
    OnboardingStep.PERSONALITY,
    OnboardingStep.CHANNELS,
    OnboardingStep.COMPLETE,
]


@dataclass
class OnboardingState:
    """Persistent state for the onboarding flow."""
    current_step: OnboardingStep = OnboardingStep.WELCOME
    completed_steps: list[str] = field(default_factory=list)
    user_name: Optional[str] = None
    voice_id: Optional[str] = None
    voice_audio_paths: list[str] = field(default_factory=list)
    voice_quality_score: Optional[float] = None
    personality_notes: Optional[str] = None
    channels_configured: list[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    conversation_history: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dict."""
        return {
            "current_step": self.current_step.value,
            "completed_steps": self.completed_steps,
            "user_name": self.user_name,
            "voice_id": self.voice_id,
            "voice_audio_paths": self.voice_audio_paths,
            "voice_quality_score": self.voice_quality_score,
            "personality_notes": self.personality_notes,
            "channels_configured": self.channels_configured,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OnboardingState:
        """Deserialize state from dict."""
        state = cls()
        state.current_step = OnboardingStep(data.get("current_step", "welcome"))
        state.completed_steps = data.get("completed_steps", [])
        state.user_name = data.get("user_name")
        state.voice_id = data.get("voice_id")
        state.voice_audio_paths = data.get("voice_audio_paths", [])
        state.voice_quality_score = data.get("voice_quality_score")
        state.personality_notes = data.get("personality_notes")
        state.channels_configured = data.get("channels_configured", [])
        state.started_at = data.get("started_at")
        state.completed_at = data.get("completed_at")
        return state

    @property
    def is_complete(self) -> bool:
        """Whether onboarding is finished."""
        return self.current_step == OnboardingStep.COMPLETE

    @property
    def progress_percent(self) -> int:
        """Current progress as a percentage."""
        if self.is_complete:
            return 100
        try:
            idx = STEP_ORDER.index(self.current_step)
            return int((idx / (len(STEP_ORDER) - 1)) * 100)
        except ValueError:
            return 0


# ─── System Prompts per Step ──────────────────────────────

STEP_PROMPTS: dict[OnboardingStep, str] = {
    OnboardingStep.WELCOME: """
Eres el asistente VoiceClone. Estás saludando a una persona que acaba de instalar
el sistema. Esta persona puede tener ELA u otra enfermedad que dificulta el habla.

Tu tono es: cálido, cercano, esperanzador pero NO condescendiente.
NUNCA digas "lo siento por tu condición" ni nada paternalista.
Trátale como un adulto inteligente que necesita una herramienta.

Preséntate brevemente. Explica que vais a:
1. Guardar su voz (grabación o audios que ya tenga)
2. Hacer una prueba rápida
3. Configurar cómo quiere comunicarse

Pregunta cómo se llama.
Máximo 3-4 frases cortas.
""",

    OnboardingStep.VOICE_INTRO: """
Ya sabes el nombre del usuario. Ahora explícale que el siguiente paso es guardar
su voz. Tiene dos opciones:

1. GRABAR ahora — solo necesita hablar 10-15 segundos
2. SUBIR audios que ya tenga (WhatsApp, notas de voz, vídeos familiares)

Si la persona ya no puede hablar bien, los audios antiguos son perfectos.
Explica que con 5-10 segundos de audio ya puede funcionar.

Pregunta qué prefiere: grabar o subir audios.
""",

    OnboardingStep.VOICE_RECORD: """
El usuario quiere grabar su voz. Guíale:

1. "Cuando estés listo, pulsa el botón rojo de grabar"
2. "Lee este texto o di lo que quieras, solo necesito 10-15 segundos"
3. Texto sugerido: "Hola, me llamo [nombre]. Esta es mi voz y quiero que
   mi ordenador la recuerde siempre."

Sé paciente. Si tarda, espera. Si el audio es corto, dile que está bien.
""",

    OnboardingStep.VOICE_CLONE: """
El audio se está procesando. Informa al usuario:
- "Estoy aprendiendo tu voz, solo serán unos segundos..."
- Cuando termine: "¡Listo! Ya tengo tu voz guardada."
- Si falla: "Necesito un poco más de audio. ¿Puedes grabar otra vez?"
""",

    OnboardingStep.VOICE_TEST: """
La voz está clonada. Ahora haz una prueba:
- Genera una frase con la voz clonada del usuario
- Frase sugerida: "Hola [nombre], esta es tu voz en VoiceClone."
- Pregunta: "¿Suena bien? ¿Te reconoces?"
- Si dice que sí: avanza
- Si dice que no: ofrece regrabar o ajustar
""",

    OnboardingStep.PERSONALITY: """
(Opcional) Pregunta si quiere que el asistente aprenda cómo habla:
- "¿Quieres compartir textos, mensajes o audios tuyos para que aprenda tu estilo?"
- "Esto es opcional — ayuda a predecir frases que dirías"
- Si dice sí: pide que comparta (WhatsApp export, textos, lo que sea)
- Si dice no: "Perfecto, siempre puedes hacerlo después"
""",

    OnboardingStep.CHANNELS: """
(Opcional) Configurar canales de mensajería:
- "¿Quieres recibir mensajes de Telegram o WhatsApp con tu voz?"
- "Cuando alguien te escriba, sonaré con tu voz para leerte el mensaje"
- Si dice sí: guía para configurar el token de Telegram
- Si dice no: "Puedes configurarlo cuando quieras desde el menú"
""",

    OnboardingStep.COMPLETE: """
¡Onboarding completado! Haz un resumen emotivo pero breve:
- "Ya estamos listos, [nombre]."
- Resume lo que se configuró
- "Tu voz está guardada. A partir de ahora, estoy aquí para ayudarte."
- "Si necesitas algo, solo tienes que mirar y seleccionar."

IMPORTANTE: habla con la voz clonada del usuario en este mensaje final.
""",
}


class OnboardingAgent:
    """
    Manages the onboarding conversational flow.

    Uses the LLM to have a natural conversation while guiding through
    structured steps. State is persistent and survives restarts.
    """

    def __init__(
        self,
        state_path: str | Path = "~/.voiceclone/data/onboarding_state.json",
    ) -> None:
        self.state_path = Path(state_path).expanduser()
        self.state = self._load_state()

    def _load_state(self) -> OnboardingState:
        """Load state from disk or create new."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text())
                logger.info("Loaded onboarding state: step=%s", data.get("current_step"))
                return OnboardingState.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load onboarding state: %s", e)
        return OnboardingState()

    def _save_state(self) -> None:
        """Persist state to disk."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state.to_dict(), indent=2))

    def get_system_prompt(self) -> str:
        """Get the system prompt for the current step."""
        base_context = f"""
Eres el asistente VoiceClone. Estás en el paso de onboarding: {self.state.current_step.value}.
"""
        if self.state.user_name:
            base_context += f"El usuario se llama: {self.state.user_name}\n"
        if self.state.voice_id:
            base_context += "La voz ya está clonada.\n"

        step_prompt = STEP_PROMPTS.get(self.state.current_step, "")
        return base_context + step_prompt

    def advance_step(self) -> OnboardingStep:
        """
        Move to the next step in the flow.

        Returns:
            The new current step.
        """
        self.state.completed_steps.append(self.state.current_step.value)

        try:
            current_idx = STEP_ORDER.index(self.state.current_step)
            if current_idx < len(STEP_ORDER) - 1:
                self.state.current_step = STEP_ORDER[current_idx + 1]
            else:
                self.state.current_step = OnboardingStep.COMPLETE
                self.state.completed_at = time.time()
        except ValueError:
            self.state.current_step = OnboardingStep.COMPLETE

        self._save_state()
        logger.info("Advanced to step: %s", self.state.current_step.value)
        return self.state.current_step

    def skip_to_step(self, step: OnboardingStep) -> None:
        """Jump to a specific step (for testing or recovery)."""
        self.state.current_step = step
        self._save_state()

    def set_user_name(self, name: str) -> None:
        """Record the user's name."""
        self.state.user_name = name
        self._save_state()

    def set_voice_cloned(self, voice_id: str, quality_score: float = 0.0) -> None:
        """Record that the voice has been cloned."""
        self.state.voice_id = voice_id
        self.state.voice_quality_score = quality_score
        self._save_state()

    def add_voice_audio(self, audio_path: str) -> None:
        """Add an audio file path for voice cloning."""
        self.state.voice_audio_paths.append(audio_path)
        self._save_state()

    def add_channel(self, channel_type: str) -> None:
        """Record a configured channel."""
        if channel_type not in self.state.channels_configured:
            self.state.channels_configured.append(channel_type)
            self._save_state()

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.state.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        # Keep history manageable
        if len(self.state.conversation_history) > 100:
            self.state.conversation_history = self.state.conversation_history[-50:]
        self._save_state()

    def get_status(self) -> dict[str, Any]:
        """Get current onboarding status for the frontend."""
        return {
            "step": self.state.current_step.value,
            "progress": self.state.progress_percent,
            "completed": self.state.completed_steps,
            "next": self._get_next_step_name(),
            "user_name": self.state.user_name,
            "voice_cloned": self.state.voice_id is not None,
            "channels": self.state.channels_configured,
            "is_complete": self.state.is_complete,
        }

    def _get_next_step_name(self) -> Optional[str]:
        """Get the name of the next step."""
        try:
            idx = STEP_ORDER.index(self.state.current_step)
            if idx < len(STEP_ORDER) - 1:
                return STEP_ORDER[idx + 1].value
            return None
        except ValueError:
            return None

    def reset(self) -> None:
        """Reset onboarding to start from scratch."""
        self.state = OnboardingState()
        self.state.started_at = time.time()
        self._save_state()
        logger.info("Onboarding reset")
