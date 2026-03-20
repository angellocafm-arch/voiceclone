"""Tests for VoiceClone Personality Engine (Layer 3)

Comprehensive tests covering:
- PersonalityProfile creation, serialization, system prompt generation
- PersonalityManager file operations (save, load, delete, list)
- Questionnaire flow (questions, responses, profile building)
- Text analysis (WhatsApp import, pattern extraction)
- LLM backends (Identity, Claude, Ollama)
- PersonalityEngine orchestrator
- API endpoint integration

All tests are fully local — no external API calls.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personality.profile import PersonalityProfile, PersonalityManager
from personality.questionnaire import Questionnaire, QuestionCategory
from personality.llm import (
    IdentityLLM,
    ClaudeLLM,
    OllamaLLM,
    create_llm,
    PersonalityLLM,
)
from personality.engine import PersonalityEngine


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test data"""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_profile():
    """Create a sample personality profile"""
    return PersonalityProfile(
        voice_name="maria",
        description="Soy alegre, me gusta bromear y siempre estoy de buen humor",
        formality="casual",
        humor_style="Cotidiano, chistes malos, juegos de palabras",
        catchphrases=["¿Sabes?", "Venga va", "Qué fuerte", "No me líes"],
        topics=["familia", "cocina", "viajes"],
        vocabulary_level="everyday",
        emoji_usage="moderate",
        sentence_length="short",
        directness="direct",
        warmth="warm",
        energy="high",
        sample_phrases=[
            "¿Qué tal? ¿Cómo va eso?",
            "Venga, vamos a ello que es viernes",
            "No me líes, ¿eh? Que me conozco",
            "¡Qué fuerte! No me lo puedo creer",
            "Bueno, pues nada, ¡a tope con todo!",
        ],
        sources=["questionnaire"],
    )


@pytest.fixture
def manager(tmp_dir):
    """Create a PersonalityManager with temp directory"""
    return PersonalityManager(tmp_dir / "personality")


@pytest.fixture
def filled_questionnaire():
    """Create a questionnaire with all answers"""
    q = Questionnaire()
    q.submit_response("description", "Soy alegre y directa")
    q.submit_response("formality", "Casual")
    q.submit_response("warmth", "Cálido/a — me gusta conectar")
    q.submit_response("energy", "Energético/a — me expreso con ganas")
    q.submit_response("sentence_length", "Cortos y directos — 'Vale, perfecto'")
    q.submit_response("directness", "Muy directo/a — sin rodeos")
    q.submit_response("catchphrases", "¿Sabes?, Venga va, Qué fuerte")
    q.submit_response("vocabulary_level", "Cotidiano — normal, del día a día")
    q.submit_response("humor_style", "Ironía suave y chistes malos")
    q.submit_response("emoji_usage", "Normal — los uso bastante")
    q.submit_response("topics", "familia, cocina, cine")
    q.submit_response(
        "sample_phrases",
        "¿Qué tal? ¿Cómo va eso?\nVenga, vamos a ello\nNo me líes, ¿eh?",
    )
    return q


# ═══════════════════════════════════════════════════════════════
# PersonalityProfile Tests
# ═══════════════════════════════════════════════════════════════


class TestPersonalityProfile:
    """Tests for PersonalityProfile dataclass"""

    def test_create_basic_profile(self):
        """Create a profile with minimal fields"""
        p = PersonalityProfile(voice_name="test")
        assert p.voice_name == "test"
        assert p.formality == "casual"
        assert p.warmth == "warm"
        assert p.version == 1

    def test_create_full_profile(self, sample_profile):
        """Create a profile with all fields"""
        assert sample_profile.voice_name == "maria"
        assert sample_profile.description.startswith("Soy alegre")
        assert len(sample_profile.catchphrases) == 4
        assert "familia" in sample_profile.topics

    def test_to_dict_and_back(self, sample_profile):
        """Test round-trip serialization"""
        d = sample_profile.to_dict()
        restored = PersonalityProfile.from_dict(d)

        assert restored.voice_name == sample_profile.voice_name
        assert restored.description == sample_profile.description
        assert restored.catchphrases == sample_profile.catchphrases
        assert restored.formality == sample_profile.formality
        assert restored.version == sample_profile.version

    def test_to_system_prompt(self, sample_profile):
        """Test system prompt generation"""
        prompt = sample_profile.to_system_prompt()

        assert "Eres maria" in prompt
        assert "Soy alegre" in prompt
        assert "casual" in prompt
        assert "¿Sabes?" in prompt
        assert "familia" in prompt
        assert "SOLO con el texto reescrito" in prompt
        assert "everyday" in prompt

    def test_system_prompt_minimal(self):
        """System prompt with minimal profile data"""
        p = PersonalityProfile(voice_name="test", description="Soy simple")
        prompt = p.to_system_prompt()

        assert "Eres test" in prompt
        assert "Soy simple" in prompt
        assert "Reglas:" in prompt

    def test_system_prompt_without_optional_fields(self):
        """System prompt handles empty optional fields gracefully"""
        p = PersonalityProfile(voice_name="test")
        prompt = p.to_system_prompt()
        # Should not crash, should still have rules
        assert "Reglas:" in prompt

    def test_serialization_has_all_fields(self, sample_profile):
        """Ensure to_dict includes all important fields"""
        d = sample_profile.to_dict()
        expected_keys = {
            "voice_name", "description", "formality", "humor_style",
            "catchphrases", "topics", "vocabulary_level", "emoji_usage",
            "sentence_length", "directness", "warmth", "energy",
            "sample_phrases", "sources", "created_at", "updated_at", "version",
        }
        assert expected_keys == set(d.keys())


# ═══════════════════════════════════════════════════════════════
# PersonalityManager Tests
# ═══════════════════════════════════════════════════════════════


class TestPersonalityManager:
    """Tests for profile storage operations"""

    def test_save_and_load(self, manager, sample_profile):
        """Save a profile and load it back"""
        manager.save_profile(sample_profile)
        loaded = manager.load_profile("maria")

        assert loaded is not None
        assert loaded.voice_name == "maria"
        assert loaded.description == sample_profile.description
        assert loaded.catchphrases == sample_profile.catchphrases

    def test_save_creates_json_and_markdown(self, manager, sample_profile):
        """Save creates both JSON and markdown files"""
        manager.save_profile(sample_profile)

        json_path = manager.personality_dir / "maria" / "profile.json"
        md_path = manager.personality_dir / "maria" / "profile.md"

        assert json_path.exists()
        assert md_path.exists()

        # Verify JSON is valid
        with open(json_path) as f:
            data = json.load(f)
        assert data["voice_name"] == "maria"

        # Verify markdown is readable
        md_content = md_path.read_text()
        assert "Personalidad de maria" in md_content
        assert "alegre" in md_content

    def test_load_nonexistent(self, manager):
        """Loading a non-existent profile returns None"""
        assert manager.load_profile("nonexistent") is None

    def test_has_personality(self, manager, sample_profile):
        """Check if a voice has a personality"""
        assert not manager.has_personality("maria")
        manager.save_profile(sample_profile)
        assert manager.has_personality("maria")

    def test_delete_profile(self, manager, sample_profile):
        """Delete a personality profile"""
        manager.save_profile(sample_profile)
        assert manager.has_personality("maria")

        result = manager.delete_profile("maria")
        assert result is True
        assert not manager.has_personality("maria")

    def test_delete_nonexistent(self, manager):
        """Deleting non-existent profile returns False"""
        assert manager.delete_profile("nonexistent") is False

    def test_list_profiles(self, manager):
        """List all profiles"""
        # Empty initially
        assert len(manager.list_profiles()) == 0

        # Add profiles
        p1 = PersonalityProfile(voice_name="maria", description="Test 1")
        p2 = PersonalityProfile(voice_name="pedro", description="Test 2")
        manager.save_profile(p1)
        manager.save_profile(p2)

        profiles = manager.list_profiles()
        assert len(profiles) == 2
        names = {p.voice_name for p in profiles}
        assert "maria" in names
        assert "pedro" in names

    def test_save_examples(self, manager):
        """Save and retrieve example texts"""
        texts = [
            "Hola, ¿qué tal?",
            "Venga, vamos a ello",
            "¡Qué fuerte! No me lo puedo creer",
        ]
        count = manager.save_examples("maria", texts, source="test")
        assert count == 3

        loaded = manager.get_examples("maria")
        assert len(loaded) == 3
        assert "Hola, ¿qué tal?" in loaded

    def test_save_examples_filters_empty(self, manager):
        """Save examples filters out empty strings"""
        texts = ["Hello", "", "  ", "World"]
        count = manager.save_examples("maria", texts, source="test")
        assert count == 2

    def test_get_examples_empty(self, manager):
        """Getting examples for non-existent voice returns empty list"""
        assert manager.get_examples("nonexistent") == []

    def test_save_updates_timestamp(self, manager, sample_profile):
        """Saving updates the updated_at timestamp"""
        original_updated = sample_profile.updated_at
        manager.save_profile(sample_profile)
        loaded = manager.load_profile("maria")
        # updated_at should be changed
        assert loaded.updated_at >= original_updated


# ═══════════════════════════════════════════════════════════════
# Questionnaire Tests
# ═══════════════════════════════════════════════════════════════


class TestQuestionnaire:
    """Tests for the personality capture questionnaire"""

    def test_get_all_questions(self):
        """Get all questions"""
        q = Questionnaire()
        questions = q.get_questions()
        assert len(questions) >= 10  # Should have at least 10 questions

    def test_get_required_questions(self):
        """Get only required questions"""
        q = Questionnaire()
        required = q.get_questions(include_optional=False)
        assert all(question.required for question in required)
        assert len(required) >= 4  # At least core questions

    def test_get_questions_by_category(self):
        """Filter questions by category"""
        q = Questionnaire()
        core = q.get_questions(category=QuestionCategory.CORE)
        assert all(question.category == QuestionCategory.CORE for question in core)
        assert len(core) >= 3

    def test_submit_text_response(self):
        """Submit a text response"""
        q = Questionnaire()
        result = q.submit_response("description", "Soy alegre y directa")
        assert result is True

    def test_submit_choice_response(self):
        """Submit a valid choice response"""
        q = Questionnaire()
        result = q.submit_response("formality", "Casual")
        assert result is True

    def test_submit_choice_by_index(self):
        """Submit choice by numeric index"""
        q = Questionnaire()
        result = q.submit_response("formality", "3")  # "Casual" is index 3
        assert result is True

    def test_submit_invalid_choice(self):
        """Invalid choice is rejected"""
        q = Questionnaire()
        result = q.submit_response("formality", "invalid_option")
        assert result is False

    def test_submit_unknown_question(self):
        """Unknown question ID is rejected"""
        q = Questionnaire()
        result = q.submit_response("nonexistent_q", "answer")
        assert result is False

    def test_is_complete_with_all_required(self, filled_questionnaire):
        """Questionnaire is complete when all required questions answered"""
        assert filled_questionnaire.is_complete() is True

    def test_is_incomplete_without_required(self):
        """Questionnaire is incomplete without required answers"""
        q = Questionnaire()
        q.submit_response("description", "Test")
        assert q.is_complete() is False

    def test_get_missing_questions(self):
        """Get list of unanswered required questions"""
        q = Questionnaire()
        q.submit_response("description", "Test")
        missing = q.get_missing()
        missing_ids = [m.id for m in missing]
        assert "formality" in missing_ids
        assert "warmth" in missing_ids
        assert "description" not in missing_ids

    def test_progress_tracking(self):
        """Track questionnaire progress"""
        q = Questionnaire()
        progress = q.get_progress()
        assert progress["answered"] == 0
        assert progress["is_complete"] is False

        q.submit_response("description", "Test")
        progress = q.get_progress()
        assert progress["answered"] == 1

    def test_build_profile(self, filled_questionnaire):
        """Build a profile from questionnaire answers"""
        profile = filled_questionnaire.build_profile("maria")

        assert profile.voice_name == "maria"
        assert profile.description == "Soy alegre y directa"
        assert profile.formality == "casual"
        assert profile.warmth == "warm"
        assert profile.energy == "high"
        assert profile.directness == "direct"
        assert profile.sentence_length == "short"
        assert "¿Sabes?" in profile.catchphrases
        assert "familia" in profile.topics
        assert len(profile.sample_phrases) >= 2
        assert "questionnaire" in profile.sources

    def test_build_profile_with_missing_optional(self):
        """Build profile works with only required answers"""
        q = Questionnaire()
        q.submit_response("description", "Test person")
        q.submit_response("formality", "Casual")
        q.submit_response("warmth", "Cálido/a — me gusta conectar")
        q.submit_response("energy", "Normal — ni muy arriba ni muy abajo")

        profile = q.build_profile("test_voice")
        assert profile.voice_name == "test_voice"
        assert profile.formality == "casual"

    def test_submit_all(self):
        """Submit multiple answers at once"""
        q = Questionnaire()
        results = q.submit_all({
            "description": "Test",
            "formality": "Casual",
            "nonexistent": "value",
        })

        assert results["description"] is True
        assert results["formality"] is True
        assert results["nonexistent"] is False

    def test_questionnaire_serialization(self, filled_questionnaire):
        """Serialize and restore questionnaire state"""
        data = filled_questionnaire.to_dict()
        restored = Questionnaire.from_dict(data)

        assert restored.is_complete() is True
        assert restored.get_progress()["answered"] == filled_questionnaire.get_progress()["answered"]


# ═══════════════════════════════════════════════════════════════
# Text Analysis Tests
# ═══════════════════════════════════════════════════════════════


class TestTextAnalysis:
    """Tests for text pattern analysis"""

    def test_analyze_basic_texts(self):
        """Analyze a set of basic texts"""
        texts = [
            "Hola, ¿qué tal?",
            "Venga, vamos a ello",
            "¡Qué fuerte! No me lo puedo creer",
            "Vale, perfecto, me parece bien",
            "Bueno, pues nada, hasta luego",
        ]
        analysis = Questionnaire.analyze_texts(texts)

        assert analysis["total_messages"] == 5
        assert analysis["total_words"] > 0
        assert analysis["avg_sentence_length"] > 0
        assert "sentence_length_category" in analysis

    def test_analyze_with_emojis(self):
        """Analysis detects emoji usage"""
        texts = [
            "Hola 😊",
            "Genial 🎉🎉🎉",
            "Me encanta ❤️❤️",
        ]
        analysis = Questionnaire.analyze_texts(texts)
        assert analysis["emoji_count"] > 0
        assert analysis["emoji_level"] in ("moderate", "heavy")

    def test_analyze_no_emojis(self):
        """Analysis detects no emojis"""
        texts = ["Hola", "Buenos días", "Hasta luego"]
        analysis = Questionnaire.analyze_texts(texts)
        assert analysis["emoji_count"] == 0
        assert analysis["emoji_level"] == "none"

    def test_analyze_formal_text(self):
        """Analysis detects formal language"""
        texts = [
            "Estimado señor, le remito la documentación adjunta.",
            "Cordialmente le solicito su atención mediante este escrito.",
            "Agradezco su pronta respuesta.",
        ]
        analysis = Questionnaire.analyze_texts(texts)
        assert analysis["inferred_formality"] == "formal"

    def test_analyze_informal_text(self):
        """Analysis detects informal language"""
        texts = [
            "Tío, mola mucho esto jaja",
            "Buah, qué guay, venga vale jaja",
            "Pues mola, tío, jajaja",
            "Venga va, tía, que mola",
        ]
        analysis = Questionnaire.analyze_texts(texts)
        assert analysis["inferred_formality"] == "casual"

    def test_analyze_empty_texts(self):
        """Empty text list returns error"""
        analysis = Questionnaire.analyze_texts([])
        assert "error" in analysis

    def test_analyze_extracts_frequent_words(self):
        """Analysis extracts frequently used words"""
        texts = [
            "genial genial genial",
            "perfecto genial",
            "genial, me parece genial",
        ]
        analysis = Questionnaire.analyze_texts(texts)
        assert "genial" in analysis["top_words"]

    def test_enrich_profile_from_texts(self, sample_profile):
        """Enrich profile with data from texts"""
        texts = [
            "Oye tío, mola mucho esto 😊",
            "Venga vale, vamos a ello 😊😊",
            "Pues mola bastante, ¿no? 🎉",
            "Tío, es genial genial genial",
            "Mola mola mola, qué bien",
        ]
        q = Questionnaire()
        enriched = q.enrich_profile_from_texts(sample_profile, texts)

        assert "text_analysis" in enriched.sources

    def test_import_whatsapp_format(self, tmp_dir):
        """Parse WhatsApp export format"""
        content = """[20/03/26, 10:15:30] María: Hola, ¿qué tal?
[20/03/26, 10:16:00] María: ¿Quedamos luego?
[20/03/26, 10:17:00] Pedro: Venga, vale
[20/03/26, 10:18:00] María: <Multimedia omitido>
[20/03/26, 10:19:00] María: Perfecto, a las 5
"""
        export_path = tmp_dir / "chat.txt"
        export_path.write_text(content, encoding="utf-8")

        messages = Questionnaire.import_whatsapp_export(export_path)
        assert len(messages) == 4  # 5 lines minus 1 multimedia
        assert "Hola, ¿qué tal?" in messages
        assert "Venga, vale" in messages

    def test_import_whatsapp_nonexistent(self):
        """Non-existent WhatsApp export raises error"""
        with pytest.raises(FileNotFoundError):
            Questionnaire.import_whatsapp_export(Path("/nonexistent/chat.txt"))


# ═══════════════════════════════════════════════════════════════
# LLM Backend Tests
# ═══════════════════════════════════════════════════════════════


class TestIdentityLLM:
    """Tests for the Identity (passthrough) LLM"""

    def test_rewrite_returns_original(self, sample_profile):
        """Identity LLM returns text unchanged"""
        llm = IdentityLLM()
        result = llm.rewrite("Hello world", sample_profile)
        assert result == "Hello world"

    def test_generate_samples(self, sample_profile):
        """Identity LLM generates basic samples"""
        llm = IdentityLLM()
        samples = llm.generate_samples(sample_profile, count=3)
        assert len(samples) == 3
        assert all(isinstance(s, str) for s in samples)

    def test_generate_samples_uses_catchphrases(self, sample_profile):
        """Identity LLM incorporates catchphrases into samples"""
        llm = IdentityLLM()
        samples = llm.generate_samples(sample_profile, count=2)
        # Should use catchphrases since profile has them
        assert any("¿Sabes?" in s or "Venga va" in s for s in samples)


class TestCreateLLM:
    """Tests for the LLM factory function"""

    def test_create_identity(self):
        """Create identity LLM"""
        llm = create_llm(backend="identity")
        assert isinstance(llm, IdentityLLM)

    def test_create_auto_fallback(self):
        """Auto falls back to Identity when no API key / Ollama"""
        # Without API key and without Ollama running, should get Identity
        import os
        original = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            llm = create_llm(backend="auto")
            # Should be either Claude (if key exists), Ollama (if running), or Identity
            assert isinstance(llm, PersonalityLLM)
        finally:
            if original:
                os.environ["ANTHROPIC_API_KEY"] = original

    def test_create_claude(self):
        """Create Claude LLM (doesn't call API)"""
        llm = create_llm(backend="claude", api_key="test-key")
        assert isinstance(llm, ClaudeLLM)

    def test_create_ollama(self):
        """Create Ollama LLM (doesn't call API)"""
        llm = create_llm(backend="ollama", model="mistral")
        assert isinstance(llm, OllamaLLM)

    def test_create_unknown_raises(self):
        """Unknown backend raises ValueError"""
        with pytest.raises(ValueError, match="Unknown LLM backend"):
            create_llm(backend="unknown")


# ═══════════════════════════════════════════════════════════════
# PersonalityEngine Tests
# ═══════════════════════════════════════════════════════════════


class TestPersonalityEngine:
    """Tests for the main personality engine orchestrator"""

    def test_initialize(self, tmp_dir):
        """Initialize engine successfully"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        assert engine.initialize() is True
        assert engine.is_ready is True

    def test_not_ready_before_init(self, tmp_dir):
        """Engine is not ready before initialization"""
        engine = PersonalityEngine(personality_dir=tmp_dir / "personality")
        assert engine.is_ready is False

    def test_full_questionnaire_flow(self, tmp_dir):
        """Complete questionnaire flow: start → answer → finalize"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        # Start questionnaire
        q = engine.start_questionnaire("maria")
        assert q is not None

        # Submit answers
        q.submit_response("description", "Soy alegre")
        q.submit_response("formality", "Casual")
        q.submit_response("warmth", "Cálido/a — me gusta conectar")
        q.submit_response("energy", "Energético/a — me expreso con ganas")

        # Finalize
        profile = engine.finalize_questionnaire("maria", q)
        assert profile.voice_name == "maria"
        assert profile.formality == "casual"
        assert engine.has_personality("maria")

    def test_apply_personality_with_identity_llm(self, tmp_dir, sample_profile):
        """Apply personality returns original text with Identity LLM"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        result = engine.apply_personality("Hola, necesito ayuda", "maria")
        assert result == "Hola, necesito ayuda"  # Identity returns unchanged

    def test_apply_personality_without_profile(self, tmp_dir):
        """Apply personality without profile returns original text"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        result = engine.apply_personality("Test text", "nonexistent")
        assert result == "Test text"

    def test_get_profile(self, tmp_dir, sample_profile):
        """Get profile by voice name"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        profile = engine.get_profile("maria")
        assert profile is not None
        assert profile.voice_name == "maria"

    def test_update_profile(self, tmp_dir, sample_profile):
        """Update specific profile fields"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        updated = engine.update_profile("maria", {
            "description": "Updated description",
            "energy": "low",
        })
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.energy == "low"
        assert updated.version == 2

    def test_delete_personality(self, tmp_dir, sample_profile):
        """Delete personality profile"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        assert engine.has_personality("maria")
        engine.delete_personality("maria")
        assert not engine.has_personality("maria")

    def test_list_personalities(self, tmp_dir):
        """List all personality profiles"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        p1 = PersonalityProfile(voice_name="maria", description="Test 1")
        p2 = PersonalityProfile(voice_name="pedro", description="Test 2")
        engine._manager.save_profile(p1)
        engine._manager.save_profile(p2)

        profiles = engine.list_personalities()
        assert len(profiles) == 2

    def test_import_texts(self, tmp_dir, sample_profile):
        """Import and analyze texts"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        texts = [
            "Hola tío, ¿qué tal?",
            "Mola mucho esto, ¿no?",
            "Venga vale, perfecto",
        ]
        analysis = engine.import_texts("maria", texts, source="test")
        assert analysis["total_messages"] == 3
        assert analysis["texts_saved"] == 3

    def test_submit_feedback(self, tmp_dir, sample_profile):
        """Submit validation feedback"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        feedback = [
            {"phrase_index": 0, "is_accurate": True, "comment": ""},
            {"phrase_index": 1, "is_accurate": True, "comment": ""},
            {"phrase_index": 2, "is_accurate": False, "comment": "Too formal"},
            {"phrase_index": 3, "is_accurate": True, "comment": ""},
            {"phrase_index": 4, "is_accurate": False, "comment": "Not my style"},
        ]
        updated = engine.submit_feedback("maria", feedback)
        assert updated is not None
        assert updated.version == 2

    def test_generate_samples(self, tmp_dir, sample_profile):
        """Generate sample phrases"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        samples = engine.generate_samples("maria", count=3)
        assert len(samples) == 3

    def test_generate_samples_no_profile(self, tmp_dir):
        """Generate samples without profile raises error"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        with pytest.raises(ValueError, match="No personality profile"):
            engine.generate_samples("nonexistent")

    def test_get_status(self, tmp_dir, sample_profile):
        """Get engine status"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine._manager.save_profile(sample_profile)

        status = engine.get_status()
        assert status["ready"] is True
        assert status["llm_backend"] == "IdentityLLM"
        assert status["profiles_count"] == 1

    def test_ensure_ready_raises(self, tmp_dir):
        """Operations on uninitialized engine raise error"""
        engine = PersonalityEngine(personality_dir=tmp_dir / "personality")

        with pytest.raises(RuntimeError, match="not initialized"):
            engine.apply_personality("test", "voice")

    def test_shutdown(self, tmp_dir):
        """Shutdown cleans up state"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()
        engine.start_questionnaire("test")
        assert len(engine._active_questionnaires) == 1

        engine.shutdown()
        assert len(engine._active_questionnaires) == 0


# ═══════════════════════════════════════════════════════════════
# Integration Test — Full Pipeline
# ═══════════════════════════════════════════════════════════════


class TestFullPipeline:
    """End-to-end integration tests for the personality pipeline"""

    def test_complete_flow(self, tmp_dir):
        """Test the complete personality capture + application flow

        Simulates a user:
        1. Starting the questionnaire
        2. Answering all questions
        3. Finalizing their personality profile
        4. Having text rewritten in their style
        5. Validating with feedback
        6. Importing additional texts
        """
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        # Step 1: Start questionnaire
        q = engine.start_questionnaire("abuela_carmen")

        # Step 2: Answer questions
        q.submit_response("description", "Soy cariñosa, tradicional, me preocupo mucho por la familia")
        q.submit_response("formality", "Casual")
        q.submit_response("warmth", "Muy cálido/a — siempre cercano/a y cariñoso/a")
        q.submit_response("energy", "Normal — ni muy arriba ni muy abajo")
        q.submit_response("sentence_length", "Cortos y directos — 'Vale, perfecto'")
        q.submit_response("directness", "Muy directo/a — sin rodeos")
        q.submit_response("catchphrases", "Hijo mío, ¿Has comido?, Dios mío, Ay mi niño")
        q.submit_response("vocabulary_level", "Cotidiano — normal, del día a día")
        q.submit_response("humor_style", "Humor suave, bromas familiares")
        q.submit_response("topics", "familia, comida, salud, nietos, tiempo")
        q.submit_response(
            "sample_phrases",
            "¿Has comido ya, hijo?\nTen cuidado, que hace frío\nAy, mi niño, qué alegría verte",
        )

        assert q.is_complete()
        progress = q.get_progress()
        assert progress["progress_percent"] > 80

        # Step 3: Finalize
        profile = engine.finalize_questionnaire("abuela_carmen", q)
        assert profile.voice_name == "abuela_carmen"
        assert "Hijo mío" in profile.catchphrases
        assert profile.warmth == "very_warm"
        assert "familia" in profile.topics

        # Step 4: Apply personality
        styled = engine.apply_personality("Necesito que vengas", "abuela_carmen")
        assert isinstance(styled, str)
        assert len(styled) > 0

        # Step 5: Feedback on samples
        if profile.sample_phrases:
            feedback = [
                {"phrase_index": i, "is_accurate": i % 2 == 0, "comment": ""}
                for i in range(min(5, len(profile.sample_phrases)))
            ]
            updated = engine.submit_feedback("abuela_carmen", feedback)
            assert updated.version == 2

        # Step 6: Import additional texts
        texts = [
            "¿Has comido ya? Que luego te duele el estómago",
            "Ay hijo, ten cuidado en la carretera",
            "¿Cuándo vienes a verme? Te hago tu comida favorita",
            "Dios mío, cómo han crecido los niños",
        ]
        analysis = engine.import_texts("abuela_carmen", texts, source="manual")
        assert analysis["total_messages"] == 4
        assert analysis["texts_saved"] == 4

        # Verify final state
        final_profile = engine.get_profile("abuela_carmen")
        assert final_profile is not None
        assert "text_analysis" in final_profile.sources
        assert len(final_profile.catchphrases) >= 3

    def test_multiple_voices(self, tmp_dir):
        """Test managing personalities for multiple voices"""
        engine = PersonalityEngine(
            personality_dir=tmp_dir / "personality",
            llm_backend="identity",
        )
        engine.initialize()

        # Create profiles for different voices
        voices = [
            ("formal_pedro", "Soy serio y profesional", "Muy formal", "Reservado/a — voy al grano"),
            ("casual_ana", "Soy divertida y cercana", "Muy casual / coloquial", "Muy cálido/a — siempre cercano/a y cariñoso/a"),
        ]

        for name, desc, formality, warmth in voices:
            q = engine.start_questionnaire(name)
            q.submit_response("description", desc)
            q.submit_response("formality", formality)
            q.submit_response("warmth", warmth)
            q.submit_response("energy", "Normal — ni muy arriba ni muy abajo")
            engine.finalize_questionnaire(name, q)

        profiles = engine.list_personalities()
        assert len(profiles) == 2

        pedro = engine.get_profile("formal_pedro")
        ana = engine.get_profile("casual_ana")
        assert pedro.formality == "formal"
        assert ana.formality == "casual"
        assert pedro.warmth == "cold"
        assert ana.warmth == "very_warm"


# ═══════════════════════════════════════════════════════════════
# Run tests
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])