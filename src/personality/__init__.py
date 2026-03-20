"""Personality Engine — Layer 3 of VoiceClone

Captures and reproduces a person's communication style:
- Profile management (who they are, how they speak)
- LLM integration (local or cloud) to rewrite text in their style
- Questionnaire system for personality capture
- Text analysis for vocabulary/patterns
- Engine orchestrator connecting all pieces

Pipeline:
  User text → Personality Engine (LLM rewrite) → Styled text → Voice Engine → Audio
"""

from .profile import PersonalityProfile, PersonalityManager
from .llm import PersonalityLLM, ClaudeLLM, OllamaLLM, IdentityLLM, create_llm
from .questionnaire import Questionnaire
from .engine import PersonalityEngine

__all__ = [
    "PersonalityProfile",
    "PersonalityManager",
    "PersonalityLLM",
    "ClaudeLLM",
    "OllamaLLM",
    "IdentityLLM",
    "create_llm",
    "Questionnaire",
    "PersonalityEngine",
]
