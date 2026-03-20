"""Personality Engine — Orchestrator for VoiceClone Layer 3

This is the main entry point for all personality operations.
It coordinates between:
- PersonalityManager (profile storage)
- PersonalityLLM (text generation/rewriting)
- Questionnaire (personality capture)

The engine provides the complete pipeline:
  Input text → Load profile → LLM rewrite → Output styled text

Then the voice engine takes over:
  Styled text → TTS with cloned voice → Audio

Usage:
    engine = PersonalityEngine()
    engine.initialize()
    
    # Setup personality via questionnaire
    questionnaire = engine.start_questionnaire(voice_name)
    questionnaire.submit_response("description", "Soy alegre y directa")
    ...
    profile = engine.finalize_questionnaire(voice_name, questionnaire)
    
    # Use personality
    styled = engine.apply_personality("Necesito ayuda", voice_name)
    # → "Oye, ¿me echas una mano? Venga, que es rapidito"
"""

import logging
from pathlib import Path
from typing import Optional

from .llm import PersonalityLLM, create_llm
from .profile import PersonalityManager, PersonalityProfile
from .questionnaire import Questionnaire

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """Main orchestrator for personality capture and application

    Lifecycle:
    1. initialize() — set up LLM backend and storage
    2. start_questionnaire() → answer questions → finalize_questionnaire()
    3. apply_personality() — rewrite text in the person's style
    4. generate_samples() — create sample phrases for validation

    Thread-safe: each call is stateless (reads profile from disk).
    """

    def __init__(
        self,
        personality_dir: Optional[Path] = None,
        llm_backend: str = "auto",
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        """
        Args:
            personality_dir: Where to store personality profiles
            llm_backend: "claude", "ollama", "identity", or "auto"
            llm_api_key: API key for cloud LLMs (Claude)
            llm_model: Override model name
        """
        self._personality_dir = personality_dir
        self._llm_backend = llm_backend
        self._llm_api_key = llm_api_key
        self._llm_model = llm_model

        self._manager: Optional[PersonalityManager] = None
        self._llm: Optional[PersonalityLLM] = None
        self._active_questionnaires: dict[str, Questionnaire] = {}

    # ─── Initialization ──────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize the personality engine

        Sets up profile storage and LLM backend.

        Returns:
            True if initialization succeeded
        """
        try:
            self._manager = PersonalityManager(self._personality_dir)
            self._llm = create_llm(
                backend=self._llm_backend,
                api_key=self._llm_api_key,
                model=self._llm_model,
            )
            logger.info(
                f"Personality engine initialized — "
                f"LLM: {type(self._llm).__name__}, "
                f"Profiles dir: {self._manager.personality_dir}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize personality engine: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        """Check if the engine is initialized and ready"""
        return self._manager is not None and self._llm is not None

    def _ensure_ready(self):
        """Ensure engine is initialized"""
        if not self.is_ready:
            raise RuntimeError(
                "Personality engine not initialized. Call initialize() first."
            )

    # ─── Questionnaire Flow ──────────────────────────────────

    def start_questionnaire(self, voice_name: str) -> Questionnaire:
        """Start a new personality questionnaire for a voice

        Returns:
            Questionnaire instance to collect answers
        """
        self._ensure_ready()
        q = Questionnaire()
        self._active_questionnaires[voice_name] = q
        logger.info(f"Started personality questionnaire for '{voice_name}'")
        return q

    def finalize_questionnaire(
        self,
        voice_name: str,
        questionnaire: Optional[Questionnaire] = None,
    ) -> PersonalityProfile:
        """Finalize questionnaire and create personality profile

        Builds profile from answers, saves to disk, generates
        initial sample phrases for validation.

        Args:
            voice_name: Voice to attach personality to
            questionnaire: Questionnaire with answers (or uses active one)

        Returns:
            Completed PersonalityProfile
        """
        self._ensure_ready()

        q = questionnaire or self._active_questionnaires.get(voice_name)
        if q is None:
            raise ValueError(
                f"No active questionnaire for '{voice_name}'. "
                "Call start_questionnaire() first."
            )

        # Build profile from answers
        profile = q.build_profile(voice_name)

        # Generate initial sample phrases if LLM is available
        try:
            samples = self._llm.generate_samples(profile, count=5)
            if samples:
                profile.sample_phrases.extend(samples)
                logger.info(f"Generated {len(samples)} sample phrases for validation")
        except Exception as e:
            logger.warning(f"Could not generate samples: {e}")

        # Save profile
        self._manager.save_profile(profile)

        # Clean up active questionnaire
        self._active_questionnaires.pop(voice_name, None)

        logger.info(f"Finalized personality profile for '{voice_name}'")
        return profile

    # ─── Personality Application ─────────────────────────────

    def apply_personality(
        self,
        text: str,
        voice_name: str,
        max_tokens: int = 500,
    ) -> str:
        """Apply personality to text — rewrite in the person's style

        This is the core function of Layer 3.
        Takes generic text and rewrites it as the person would say it.

        Args:
            text: Input text/intention
            voice_name: Voice whose personality to apply
            max_tokens: Max output length

        Returns:
            Text rewritten in the person's style.
            Returns original text if personality is not configured
            or LLM fails.
        """
        self._ensure_ready()

        # Load profile
        profile = self._manager.load_profile(voice_name)
        if profile is None:
            logger.debug(f"No personality for '{voice_name}', returning original text")
            return text

        # Rewrite with LLM
        try:
            result = self._llm.rewrite(text, profile, max_tokens)
            logger.info(
                f"Personality applied for '{voice_name}': "
                f"'{text[:40]}...' → '{result[:40]}...'"
            )
            return result
        except Exception as e:
            logger.error(f"Personality rewrite failed: {e}")
            return text  # Graceful degradation

    def generate_samples(
        self,
        voice_name: str,
        count: int = 5,
    ) -> list[str]:
        """Generate sample phrases for a personality

        Used to validate the personality profile:
        "Do these phrases sound like you?"

        Args:
            voice_name: Voice to generate samples for
            count: Number of phrases to generate

        Returns:
            List of sample phrases, empty if failed
        """
        self._ensure_ready()

        profile = self._manager.load_profile(voice_name)
        if profile is None:
            raise ValueError(f"No personality profile for '{voice_name}'")

        try:
            return self._llm.generate_samples(profile, count)
        except Exception as e:
            logger.error(f"Sample generation failed: {e}")
            return []

    # ─── Profile Management ──────────────────────────────────

    def get_profile(self, voice_name: str) -> Optional[PersonalityProfile]:
        """Get personality profile for a voice"""
        self._ensure_ready()
        return self._manager.load_profile(voice_name)

    def has_personality(self, voice_name: str) -> bool:
        """Check if a voice has a personality profile"""
        self._ensure_ready()
        return self._manager.has_personality(voice_name)

    def update_profile(
        self,
        voice_name: str,
        updates: dict,
    ) -> Optional[PersonalityProfile]:
        """Update specific fields of a personality profile

        Args:
            voice_name: Voice to update
            updates: Dict of fields to update

        Returns:
            Updated profile, or None if voice not found
        """
        self._ensure_ready()

        profile = self._manager.load_profile(voice_name)
        if profile is None:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.version += 1
        self._manager.save_profile(profile)
        logger.info(f"Updated personality for '{voice_name}' (v{profile.version})")
        return profile

    def delete_personality(self, voice_name: str) -> bool:
        """Delete personality profile for a voice"""
        self._ensure_ready()
        return self._manager.delete_profile(voice_name)

    def list_personalities(self) -> list[PersonalityProfile]:
        """List all personality profiles"""
        self._ensure_ready()
        return self._manager.list_profiles()

    # ─── Text Analysis / Import ──────────────────────────────

    def import_texts(
        self,
        voice_name: str,
        texts: list[str],
        source: str = "manual",
    ) -> dict:
        """Import example texts and analyze for personality patterns

        Saves texts and enriches the existing profile with
        discovered patterns.

        Args:
            voice_name: Voice to enrich
            texts: List of text messages/paragraphs
            source: Source identifier (e.g., "whatsapp", "email")

        Returns:
            Analysis results dict
        """
        self._ensure_ready()

        # Save example texts
        count = self._manager.save_examples(voice_name, texts, source)

        # Analyze texts
        analysis = Questionnaire.analyze_texts(texts)

        # Enrich profile if it exists
        profile = self._manager.load_profile(voice_name)
        if profile:
            q = Questionnaire()
            profile = q.enrich_profile_from_texts(profile, texts)
            self._manager.save_profile(profile)

        analysis["texts_saved"] = count
        return analysis

    def import_whatsapp(
        self,
        voice_name: str,
        file_path: Path,
    ) -> dict:
        """Import personality data from WhatsApp export

        Args:
            voice_name: Voice to enrich
            file_path: Path to WhatsApp export .txt file

        Returns:
            Analysis results
        """
        texts = Questionnaire.import_whatsapp_export(file_path)
        return self.import_texts(voice_name, texts, source="whatsapp")

    # ─── Feedback Loop ───────────────────────────────────────

    def submit_feedback(
        self,
        voice_name: str,
        phrase_feedback: list[dict],
    ) -> Optional[PersonalityProfile]:
        """Submit feedback on generated sample phrases

        Used during setup validation:
        User reviews samples and says which sound accurate.

        Args:
            voice_name: Voice being validated
            phrase_feedback: List of {phrase_index: int, is_accurate: bool, comment: str}

        Returns:
            Updated profile with refined parameters
        """
        self._ensure_ready()

        profile = self._manager.load_profile(voice_name)
        if profile is None:
            return None

        # Count accuracy
        accurate = sum(1 for f in phrase_feedback if f.get("is_accurate", False))
        total = len(phrase_feedback)

        if total == 0:
            return profile

        accuracy = accurate / total

        # If accuracy is low, add comments as guidance
        comments = [
            f.get("comment", "")
            for f in phrase_feedback
            if f.get("comment") and not f.get("is_accurate", False)
        ]
        if comments:
            # Append feedback to description for context
            feedback_note = " | Feedback: " + "; ".join(comments)
            profile.description += feedback_note

        # Keep only the phrases marked as accurate
        if profile.sample_phrases and phrase_feedback:
            accurate_indices = {
                f["phrase_index"]
                for f in phrase_feedback
                if f.get("is_accurate", False)
            }
            profile.sample_phrases = [
                p for i, p in enumerate(profile.sample_phrases)
                if i in accurate_indices
            ]

        profile.version += 1
        self._manager.save_profile(profile)

        logger.info(
            f"Feedback for '{voice_name}': "
            f"{accurate}/{total} accurate ({accuracy:.0%})"
        )
        return profile

    # ─── Status ──────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get engine status"""
        profiles = []
        if self._manager:
            try:
                profiles = self._manager.list_profiles()
            except Exception:
                pass

        return {
            "ready": self.is_ready,
            "llm_backend": type(self._llm).__name__ if self._llm else None,
            "profiles_count": len(profiles),
            "active_questionnaires": list(self._active_questionnaires.keys()),
            "personality_dir": str(self._manager.personality_dir) if self._manager else None,
        }

    def shutdown(self):
        """Cleanup resources"""
        self._active_questionnaires.clear()
        logger.info("Personality engine shut down")
