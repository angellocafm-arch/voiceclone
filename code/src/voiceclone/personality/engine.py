"""Personality engine — transforms text to match a person's communication style.

Uses few-shot prompting with an LLM to rewrite text "as the person would say it".
The rewritten text is then passed to the TTS engine for synthesis.

Pipeline: user text → LLM (personality) → personalized text → TTS → audio

Supports:
- Local LLM (Mistral 7B, Llama 3 8B via llama.cpp or similar)
- Cloud LLM (Claude API, OpenAI API) — requires user opt-in
"""

import logging
from typing import Optional

from voiceclone.personality.profile import PersonalityProfile

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """Transform text to match a person's communication style.
    
    Uses few-shot prompting: the LLM receives the person's profile,
    examples of how they speak, and the input text, then rewrites
    it in their style.
    """

    def __init__(self, llm_backend: str = "local") -> None:
        """Initialize personality engine.
        
        Args:
            llm_backend: "local" (default), "claude", or "openai"
        """
        self.llm_backend = llm_backend
        self._client = None

    def build_system_prompt(self, profile: PersonalityProfile) -> str:
        """Build the system prompt for personality rewriting.
        
        This is the core of the few-shot approach: the prompt includes
        the person's profile and examples, instructing the LLM to
        rewrite text in their style.
        """
        examples_text = ""
        if profile.examples:
            examples_text = "\n".join(
                f"  - \"{ex}\"" for ex in profile.examples[:5]
            )
            examples_text = f"\n\nEjemplos de cómo habla {profile.name}:\n{examples_text}"
        
        phrases_text = ""
        if profile.favorite_phrases:
            phrases_text = "\n".join(
                f"  - \"{ph}\"" for ph in profile.favorite_phrases[:10]
            )
            phrases_text = f"\n\nFrases favoritas:\n{phrases_text}"
        
        description = ""
        if profile.self_description:
            description = f"\n\nCómo se describe: {profile.self_description}"
        
        return f"""Eres {profile.name}. Tu trabajo es reformular el texto que te den 
como lo diría {profile.name}.

Personalidad:
- Tono: {profile.tone}
- Formalidad: {profile.formality}
- Humor: {profile.humor_style}{description}{examples_text}{phrases_text}

REGLAS:
1. Reformula el texto manteniendo el significado exacto
2. Usa el vocabulario y estilo de {profile.name}
3. Responde SOLO con el texto reformulado, nada más
4. No añadas explicaciones ni metadata
5. Si el texto ya suena como {profile.name}, devuélvelo sin cambios
6. Mantén la longitud similar (no expandas innecesariamente)"""

    async def personalize(
        self,
        text: str,
        profile: PersonalityProfile,
    ) -> str:
        """Rewrite text in the person's style.
        
        Args:
            text: Input text to personalize.
            profile: The person's personality profile.
            
        Returns:
            Text rewritten in the person's style.
        """
        system_prompt = self.build_system_prompt(profile)
        
        if self.llm_backend == "claude":
            return await self._personalize_claude(text, system_prompt)
        elif self.llm_backend == "openai":
            return await self._personalize_openai(text, system_prompt)
        else:
            return await self._personalize_local(text, system_prompt)

    async def _personalize_claude(self, text: str, system_prompt: str) -> str:
        """Use Claude API for personality rewriting."""
        try:
            import anthropic
            
            if self._client is None:
                self._client = anthropic.AsyncAnthropic()
            
            response = await self._client.messages.create(
                model="claude-3-haiku-20240307",  # Fast + cheap for rewriting
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": text}],
            )
            
            result = response.content[0].text.strip()
            logger.info("Personalized via Claude: '%s' → '%s'", text[:50], result[:50])
            return result
            
        except Exception as e:
            logger.error("Claude API failed: %s. Returning original text.", e)
            return text

    async def _personalize_openai(self, text: str, system_prompt: str) -> str:
        """Use OpenAI API for personality rewriting."""
        try:
            from openai import AsyncOpenAI
            
            if self._client is None:
                self._client = AsyncOpenAI()
            
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=500,
            )
            
            result = response.choices[0].message.content.strip()
            logger.info("Personalized via OpenAI: '%s' → '%s'", text[:50], result[:50])
            return result
            
        except Exception as e:
            logger.error("OpenAI API failed: %s. Returning original text.", e)
            return text

    async def _personalize_local(self, text: str, system_prompt: str) -> str:
        """Use local LLM for personality rewriting.
        
        Attempts to connect to a local LLM server (llama.cpp, Ollama, etc.)
        at localhost:11434 (Ollama default) or localhost:8080 (llama.cpp).
        
        Falls back to returning original text if no local LLM is available.
        """
        import httpx
        
        # Try Ollama first (most common local LLM server)
        for base_url in ["http://localhost:11434", "http://localhost:8080"]:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{base_url}/api/generate",
                        json={
                            "model": "mistral",
                            "system": system_prompt,
                            "prompt": text,
                            "stream": False,
                        },
                    )
                    
                    if response.status_code == 200:
                        result = response.json().get("response", text).strip()
                        logger.info(
                            "Personalized via local LLM (%s): '%s' → '%s'",
                            base_url, text[:50], result[:50]
                        )
                        return result
                        
            except Exception:
                continue
        
        logger.warning(
            "No local LLM available. Returning original text. "
            "Install Ollama (ollama.ai) for local personality."
        )
        return text

    async def generate_cached_phrases(
        self,
        profile: PersonalityProfile,
        phrases: Optional[list[str]] = None,
    ) -> list[str]:
        """Generate personalized versions of common AAC phrases.
        
        Pre-generates text for instant TTS synthesis later.
        These are the ~50 most common phrases people use in AAC.
        """
        if phrases is None:
            phrases = get_default_aac_phrases()
        
        personalized = []
        for phrase in phrases:
            personalized_text = await self.personalize(phrase, profile)
            personalized.append(personalized_text)
        
        logger.info(
            "Generated %d cached phrases for voice %s",
            len(personalized), profile.voice_id
        )
        return personalized


def get_default_aac_phrases() -> list[str]:
    """Default AAC phrases for pre-generation.
    
    Based on common communication needs for AAC users.
    Organized by category.
    """
    return [
        # Basic needs
        "Tengo sed",
        "Tengo hambre",
        "Necesito ir al baño",
        "Tengo frío",
        "Tengo calor",
        "Me duele",
        "Necesito ayuda",
        "Estoy cansado",
        
        # Social
        "Hola",
        "Adiós",
        "Buenos días",
        "Buenas noches",
        "Gracias",
        "De nada",
        "Por favor",
        "Lo siento",
        
        # Communication
        "Sí",
        "No",
        "No lo sé",
        "Espera un momento",
        "Repite eso, por favor",
        "No he entendido",
        "Quiero decir algo",
        "Déjame pensar",
        
        # Emotions
        "Estoy bien",
        "Estoy contento",
        "Estoy triste",
        "Estoy enfadado",
        "Te quiero",
        "Te echo de menos",
        
        # Medical
        "Necesito mis medicinas",
        "Llama al doctor",
        "Me encuentro mal",
        "Necesito descansar",
        
        # Daily life
        "Pon la tele",
        "Quita la tele",
        "Sube el volumen",
        "Baja el volumen",
        "Abre la ventana",
        "Cierra la ventana",
        "Enciende la luz",
        "Apaga la luz",
        
        # Conversation
        "Cuéntame más",
        "Qué interesante",
        "Estoy de acuerdo",
        "No estoy de acuerdo",
        "Eso me parece bien",
        "Vamos a hablar de otra cosa",
    ]
