"""LLM integration for personality-styled text generation

Takes input text and rewrites it in the person's communication style
using their PersonalityProfile as context.

Supports:
1. Cloud LLMs: Claude API (via anthropic package)
2. Local LLMs: Ollama (Mistral, Llama, etc.)
3. Fallback: Identity (returns text unchanged)

Pipeline:
  Input text → System prompt (from profile) → LLM → Styled text → TTS

Privacy note: If using Cloud LLMs, the text IS sent to the API.
Users are warned and can opt for local LLM instead.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from .profile import PersonalityProfile

logger = logging.getLogger(__name__)


class PersonalityLLM(ABC):
    """Abstract base for personality text generation"""

    @abstractmethod
    def rewrite(
        self,
        text: str,
        profile: PersonalityProfile,
        max_tokens: int = 500,
    ) -> str:
        """Rewrite text in the person's style
        
        Args:
            text: Original text/intention
            profile: Personality profile to apply
            max_tokens: Max output tokens
            
        Returns:
            Text rewritten in the person's style
        """
        pass

    @abstractmethod
    def generate_samples(
        self,
        profile: PersonalityProfile,
        count: int = 5,
    ) -> list[str]:
        """Generate sample phrases for personality validation
        
        Used during setup to ask "Does this sound like you?"
        """
        pass


class ClaudeLLM(PersonalityLLM):
    """Claude API integration for personality text generation
    
    Uses Anthropic's Claude API. Requires ANTHROPIC_API_KEY env var
    or explicit api_key parameter.
    
    ⚠️  Sends text to Anthropic's servers. Users are warned.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import anthropic

            api_key = self._api_key
            if not api_key:
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")

            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. "
                    "Set it in your environment or use local LLM."
                )

            self._client = anthropic.Anthropic(api_key=api_key)
            return self._client

        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

    def rewrite(
        self,
        text: str,
        profile: PersonalityProfile,
        max_tokens: int = 500,
    ) -> str:
        client = self._get_client()
        system_prompt = profile.to_system_prompt()

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Reescribe esto como lo dirías tú: {text}"}
                ],
            )
            result = response.content[0].text.strip()
            logger.info(f"Personality rewrite: '{text[:30]}...' → '{result[:30]}...'")
            return result

        except Exception as e:
            logger.error(f"Claude rewrite failed: {e}")
            return text  # Fallback: return original

    def generate_samples(
        self,
        profile: PersonalityProfile,
        count: int = 5,
    ) -> list[str]:
        client = self._get_client()
        system_prompt = profile.to_system_prompt()

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Genera {count} frases cortas como las que dirías en "
                            "tu día a día. Una por línea, sin numerar, sin comillas."
                        ),
                    }
                ],
            )
            text = response.content[0].text.strip()
            phrases = [line.strip() for line in text.split("\n") if line.strip()]
            return phrases[:count]

        except Exception as e:
            logger.error(f"Claude sample generation failed: {e}")
            return []


class OllamaLLM(PersonalityLLM):
    """Local LLM via Ollama for 100% private personality generation
    
    Requires Ollama running locally with a model pulled.
    Default: mistral (7B, good balance of quality/speed)
    
    100% private — nothing leaves the machine.
    """

    def __init__(
        self,
        model: str = "mistral",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self._base_url = base_url

    def rewrite(
        self,
        text: str,
        profile: PersonalityProfile,
        max_tokens: int = 500,
    ) -> str:
        system_prompt = profile.to_system_prompt()

        try:
            import requests

            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "system": system_prompt,
                    "prompt": f"Reescribe esto como lo dirías tú: {text}",
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7,
                    },
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()

            if not result:
                return text

            logger.info(f"Ollama rewrite: '{text[:30]}...' → '{result[:30]}...'")
            return result

        except ImportError:
            logger.error("requests package not installed")
            return text
        except Exception as e:
            logger.error(f"Ollama rewrite failed: {e}")
            return text

    def generate_samples(
        self,
        profile: PersonalityProfile,
        count: int = 5,
    ) -> list[str]:
        system_prompt = profile.to_system_prompt()

        try:
            import requests

            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "system": system_prompt,
                    "prompt": (
                        f"Genera {count} frases cortas como las que dirías en "
                        "tu día a día. Una por línea, sin numerar, sin comillas."
                    ),
                    "stream": False,
                    "options": {"temperature": 0.8},
                },
                timeout=30,
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            phrases = [line.strip() for line in text.split("\n") if line.strip()]
            return phrases[:count]

        except Exception as e:
            logger.error(f"Ollama sample generation failed: {e}")
            return []


class IdentityLLM(PersonalityLLM):
    """Identity/passthrough LLM — returns text unchanged
    
    Used when:
    - No LLM is configured
    - Personality is disabled
    - As a fallback when real LLMs fail
    """

    def rewrite(
        self,
        text: str,
        profile: PersonalityProfile,
        max_tokens: int = 500,
    ) -> str:
        return text

    def generate_samples(
        self,
        profile: PersonalityProfile,
        count: int = 5,
    ) -> list[str]:
        # Generate generic samples based on profile traits
        samples = []
        if profile.catchphrases:
            for phrase in profile.catchphrases[:count]:
                samples.append(f"{phrase}, ¡esto funciona genial!")
        
        while len(samples) < count:
            samples.append("Hola, esta es mi forma de hablar.")
        
        return samples[:count]


def create_llm(
    backend: str = "auto",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> PersonalityLLM:
    """Factory function to create the appropriate LLM backend
    
    Args:
        backend: "claude", "ollama", "identity", or "auto"
        api_key: API key for cloud providers
        model: Model name override
        
    Returns:
        PersonalityLLM instance
    """
    if backend == "identity":
        return IdentityLLM()

    if backend == "claude":
        return ClaudeLLM(api_key=api_key, model=model or "claude-sonnet-4-20250514")

    if backend == "ollama":
        return OllamaLLM(model=model or "mistral")

    # Auto-detect
    if backend == "auto":
        # Try Claude first (if API key available)
        import os
        if api_key or os.environ.get("ANTHROPIC_API_KEY"):
            logger.info("Using Claude API for personality")
            return ClaudeLLM(api_key=api_key)

        # Try Ollama
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                logger.info("Using Ollama for personality (local)")
                return OllamaLLM(model=model or "mistral")
        except Exception:
            pass

        # Fallback to identity
        logger.warning("No LLM available. Personality will be passthrough.")
        return IdentityLLM()

    raise ValueError(f"Unknown LLM backend: {backend}")
