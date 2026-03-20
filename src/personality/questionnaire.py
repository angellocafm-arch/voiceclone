"""Personality Capture Questionnaire — VoiceClone Capa 3

Guided questionnaire system that captures a person's communication style
through structured questions and example text analysis.

Designed for ELA patients and caregivers:
- Clear, simple questions
- Multiple input methods (text, voice, file import)
- Adaptive: skip irrelevant questions based on previous answers
- Validates with generated sample phrases

Flow:
  1. Core questions (5 min) → builds initial profile
  2. Optional: import texts (WhatsApp, emails) → extracts patterns
  3. Generate sample phrases → user validates "sounds like me?"
  4. 2-3 feedback rounds → finalized profile

Reference: ~/clawd/projects/voiceclone/equipo/experto-personalidad-ia.md
"""

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .profile import PersonalityProfile

logger = logging.getLogger(__name__)


class QuestionCategory(Enum):
    """Categories of personality questions"""
    CORE = "core"                # Essential questions (always asked)
    STYLE = "style"              # Communication style details
    VOCABULARY = "vocabulary"    # Language patterns and catchphrases
    EMOTIONAL = "emotional"      # Emotional expression preferences
    CONTEXT = "context"          # Topics and interests


@dataclass
class Question:
    """A single personality question"""
    id: str
    text: str
    help_text: str = ""           # Clarification for the question
    category: QuestionCategory = QuestionCategory.CORE
    input_type: str = "text"      # text | choice | multi_choice | scale
    choices: list[str] = field(default_factory=list)
    required: bool = True
    order: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "help_text": self.help_text,
            "category": self.category.value,
            "input_type": self.input_type,
            "choices": self.choices,
            "required": self.required,
            "order": self.order,
        }


@dataclass
class QuestionnaireResponse:
    """A user's answer to a question"""
    question_id: str
    answer: str                   # Text answer or selected choice
    answers: list[str] = field(default_factory=list)  # For multi_choice


class Questionnaire:
    """Personality capture questionnaire engine

    Manages the flow of questions, collects responses,
    and builds a PersonalityProfile from the answers.
    """

    def __init__(self):
        self._questions = self._build_questions()
        self._responses: dict[str, QuestionnaireResponse] = {}

    # ─── Questions Definition ──────────────────────────────────

    def _build_questions(self) -> list[Question]:
        """Build the full set of personality questions

        Designed to be:
        - Approachable (no technical jargon)
        - Quick (5-10 minutes total)
        - Comprehensive (covers all profile fields)
        """
        questions = [
            # === CORE (always asked) ===
            Question(
                id="description",
                text="¿Cómo te describirías a ti mismo/a en pocas palabras?",
                help_text=(
                    "Tu personalidad general. Por ejemplo: "
                    "'Soy alegre, me gusta bromear y siempre estoy de buen humor' "
                    "o 'Soy tranquilo, reflexivo, prefiero escuchar.'"
                ),
                category=QuestionCategory.CORE,
                input_type="text",
                order=1,
            ),
            Question(
                id="formality",
                text="¿Cómo sueles hablar normalmente?",
                help_text="Tu tono habitual en conversaciones del día a día.",
                category=QuestionCategory.CORE,
                input_type="choice",
                choices=["Muy formal", "Algo formal", "Casual", "Muy casual / coloquial"],
                order=2,
            ),
            Question(
                id="warmth",
                text="¿Cómo es tu manera de relacionarte con los demás?",
                help_text="Tu calidez en la comunicación.",
                category=QuestionCategory.CORE,
                input_type="choice",
                choices=[
                    "Reservado/a — voy al grano",
                    "Neutro — amable pero no efusivo/a",
                    "Cálido/a — me gusta conectar",
                    "Muy cálido/a — siempre cercano/a y cariñoso/a",
                ],
                order=3,
            ),
            Question(
                id="energy",
                text="¿Cómo es tu nivel de energía al hablar?",
                help_text="¿Hablas con mucha emoción o eres más tranquilo/a?",
                category=QuestionCategory.CORE,
                input_type="choice",
                choices=[
                    "Tranquilo/a — pausado, reflexivo",
                    "Normal — ni muy arriba ni muy abajo",
                    "Energético/a — me expreso con ganas",
                ],
                order=4,
            ),

            # === STYLE ===
            Question(
                id="sentence_length",
                text="¿Cómo son tus mensajes normalmente?",
                help_text="La longitud de tus frases típicas.",
                category=QuestionCategory.STYLE,
                input_type="choice",
                choices=[
                    "Cortos y directos — 'Vale, perfecto'",
                    "Normales — unas pocas frases",
                    "Largos y detallados — me gusta explicarme bien",
                ],
                order=5,
            ),
            Question(
                id="directness",
                text="¿Cómo dices las cosas?",
                help_text="¿Vas directo al grano o das rodeos?",
                category=QuestionCategory.STYLE,
                input_type="choice",
                choices=[
                    "Muy directo/a — sin rodeos",
                    "A veces directo, a veces con más tacto",
                    "Indirecto/a — prefiero suavizar las cosas",
                ],
                order=6,
            ),

            # === VOCABULARY ===
            Question(
                id="catchphrases",
                text="¿Tienes muletillas o frases que repites mucho?",
                help_text=(
                    "Frases típicas tuyas. Por ejemplo: "
                    "'¿Sabes?', 'Venga va', 'Qué fuerte', 'A ver...', "
                    "'Mola', 'Tío/a'. Escribe todas las que se te ocurran, "
                    "separadas por comas."
                ),
                category=QuestionCategory.VOCABULARY,
                input_type="text",
                required=False,
                order=7,
            ),
            Question(
                id="vocabulary_level",
                text="¿Cómo es tu vocabulario?",
                help_text="El tipo de palabras que usas normalmente.",
                category=QuestionCategory.VOCABULARY,
                input_type="choice",
                choices=[
                    "Coloquial — palabras de la calle",
                    "Cotidiano — normal, del día a día",
                    "Profesional — vocabulario más cuidado",
                    "Académico — me gusta usar palabras precisas",
                ],
                order=8,
            ),

            # === EMOTIONAL ===
            Question(
                id="humor_style",
                text="¿Usas humor? ¿De qué tipo?",
                help_text=(
                    "Describe tu sentido del humor. Por ejemplo: "
                    "'Ironía y sarcasmo', 'Humor blanco, chistes malos', "
                    "'Muy gracioso/a, siempre bromeando', 'No mucho humor'."
                ),
                category=QuestionCategory.EMOTIONAL,
                input_type="text",
                required=False,
                order=9,
            ),
            Question(
                id="emoji_usage",
                text="¿Usas emojis al escribir?",
                help_text="¿Cuántos emojis usas normalmente?",
                category=QuestionCategory.EMOTIONAL,
                input_type="choice",
                choices=[
                    "Nunca — solo texto",
                    "Poco — alguno de vez en cuando",
                    "Normal — los uso bastante",
                    "Mucho — soy muy de emojis 😄🎉",
                ],
                required=False,
                order=10,
            ),

            # === CONTEXT ===
            Question(
                id="topics",
                text="¿Qué temas te importan o sueles hablar?",
                help_text=(
                    "Las cosas de las que hablas en tu día a día. "
                    "Por ejemplo: 'familia, trabajo, fútbol, cocina, viajes'. "
                    "Sepáralos por comas."
                ),
                category=QuestionCategory.CONTEXT,
                input_type="text",
                required=False,
                order=11,
            ),
            Question(
                id="sample_phrases",
                text="Escribe 3-5 frases que dirías en tu día a día.",
                help_text=(
                    "Frases reales que digas a menudo. Por ejemplo:\n"
                    "- '¿Qué tal? ¿Cómo va eso?'\n"
                    "- 'Venga, vamos a ello'\n"
                    "- 'No me líes, ¿eh?'\n\n"
                    "Escribe cada frase en una línea nueva."
                ),
                category=QuestionCategory.CONTEXT,
                input_type="text",
                required=False,
                order=12,
            ),
        ]

        return sorted(questions, key=lambda q: q.order)

    # ─── Public API ────────────────────────────────────────────

    def get_questions(
        self,
        category: Optional[QuestionCategory] = None,
        include_optional: bool = True,
    ) -> list[Question]:
        """Get questions, optionally filtered by category"""
        questions = self._questions
        if category:
            questions = [q for q in questions if q.category == category]
        if not include_optional:
            questions = [q for q in questions if q.required]
        return questions

    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID"""
        for q in self._questions:
            if q.id == question_id:
                return q
        return None

    def submit_response(self, question_id: str, answer: str) -> bool:
        """Submit a response to a question

        Args:
            question_id: The question being answered
            answer: The user's answer text

        Returns:
            True if the response was accepted
        """
        question = self.get_question(question_id)
        if question is None:
            logger.warning(f"Unknown question: {question_id}")
            return False

        # Validate choice questions
        if question.input_type == "choice" and question.choices:
            # Accept the answer if it matches a choice or is a valid index
            if answer not in question.choices:
                try:
                    idx = int(answer) - 1
                    if 0 <= idx < len(question.choices):
                        answer = question.choices[idx]
                    else:
                        logger.warning(f"Invalid choice for {question_id}: {answer}")
                        return False
                except (ValueError, IndexError):
                    logger.warning(f"Invalid choice for {question_id}: {answer}")
                    return False

        self._responses[question_id] = QuestionnaireResponse(
            question_id=question_id,
            answer=answer.strip(),
        )
        return True

    def submit_all(self, answers: dict[str, str]) -> dict[str, bool]:
        """Submit multiple responses at once

        Args:
            answers: {question_id: answer_text}

        Returns:
            {question_id: accepted}
        """
        results = {}
        for qid, answer in answers.items():
            results[qid] = self.submit_response(qid, answer)
        return results

    def is_complete(self) -> bool:
        """Check if all required questions have been answered"""
        required_ids = {q.id for q in self._questions if q.required}
        answered_ids = set(self._responses.keys())
        return required_ids.issubset(answered_ids)

    def get_missing(self) -> list[Question]:
        """Get list of required questions not yet answered"""
        answered_ids = set(self._responses.keys())
        return [
            q for q in self._questions
            if q.required and q.id not in answered_ids
        ]

    def get_progress(self) -> dict:
        """Get questionnaire completion progress"""
        total = len(self._questions)
        required = len([q for q in self._questions if q.required])
        answered = len(self._responses)
        required_answered = len([
            r for r in self._responses.values()
            if self.get_question(r.question_id) and
            self.get_question(r.question_id).required
        ])

        return {
            "total_questions": total,
            "required_questions": required,
            "answered": answered,
            "required_answered": required_answered,
            "is_complete": self.is_complete(),
            "progress_percent": round((answered / total) * 100) if total > 0 else 0,
        }

    # ─── Profile Building ─────────────────────────────────────

    def build_profile(self, voice_name: str) -> PersonalityProfile:
        """Build a PersonalityProfile from questionnaire responses

        Maps questionnaire answers to profile fields.
        Extracts catchphrases, topics from comma-separated text.
        """
        if not self.is_complete():
            missing = self.get_missing()
            missing_names = [q.text for q in missing]
            logger.warning(
                f"Building profile with missing required answers: {missing_names}"
            )

        def get_answer(qid: str, default: str = "") -> str:
            resp = self._responses.get(qid)
            return resp.answer if resp else default

        # Parse choice → profile value mappings
        formality_map = {
            "Muy formal": "formal",
            "Algo formal": "formal",
            "Casual": "casual",
            "Muy casual / coloquial": "casual",
        }
        warmth_map = {
            "Reservado/a — voy al grano": "cold",
            "Neutro — amable pero no efusivo/a": "neutral",
            "Cálido/a — me gusta conectar": "warm",
            "Muy cálido/a — siempre cercano/a y cariñoso/a": "very_warm",
        }
        energy_map = {
            "Tranquilo/a — pausado, reflexivo": "low",
            "Normal — ni muy arriba ni muy abajo": "medium",
            "Energético/a — me expreso con ganas": "high",
        }
        sentence_map = {
            "Cortos y directos — 'Vale, perfecto'": "short",
            "Normales — unas pocas frases": "medium",
            "Largos y detallados — me gusta explicarme bien": "long",
        }
        directness_map = {
            "Muy directo/a — sin rodeos": "direct",
            "A veces directo, a veces con más tacto": "varies",
            "Indirecto/a — prefiero suavizar las cosas": "indirect",
        }
        emoji_map = {
            "Nunca — solo texto": "none",
            "Poco — alguno de vez en cuando": "minimal",
            "Normal — los uso bastante": "moderate",
            "Mucho — soy muy de emojis 😄🎉": "heavy",
        }
        vocab_map = {
            "Coloquial — palabras de la calle": "colloquial",
            "Cotidiano — normal, del día a día": "everyday",
            "Profesional — vocabulario más cuidado": "professional",
            "Académico — me gusta usar palabras precisas": "academic",
        }

        # Parse comma-separated fields
        catchphrases = self._parse_list(get_answer("catchphrases"))
        topics = self._parse_list(get_answer("topics"))
        sample_phrases = self._parse_phrases(get_answer("sample_phrases"))

        profile = PersonalityProfile(
            voice_name=voice_name,
            description=get_answer("description"),
            formality=formality_map.get(get_answer("formality"), "casual"),
            humor_style=get_answer("humor_style"),
            catchphrases=catchphrases,
            topics=topics,
            vocabulary_level=vocab_map.get(get_answer("vocabulary_level"), "everyday"),
            emoji_usage=emoji_map.get(get_answer("emoji_usage"), "moderate"),
            sentence_length=sentence_map.get(get_answer("sentence_length"), "medium"),
            directness=directness_map.get(get_answer("directness"), "direct"),
            warmth=warmth_map.get(get_answer("warmth"), "warm"),
            energy=energy_map.get(get_answer("energy"), "medium"),
            sample_phrases=sample_phrases,
            sources=["questionnaire"],
        )

        logger.info(
            f"Built personality profile for '{voice_name}': "
            f"{profile.formality}, {profile.warmth}, "
            f"{len(profile.catchphrases)} catchphrases, "
            f"{len(profile.sample_phrases)} samples"
        )
        return profile

    # ─── Text Analysis ─────────────────────────────────────────

    @staticmethod
    def analyze_texts(texts: list[str]) -> dict:
        """Analyze a collection of texts to extract personality patterns

        Useful for WhatsApp exports, emails, etc.
        Extracts vocabulary, sentence length, formality indicators.

        Args:
            texts: List of text messages/paragraphs

        Returns:
            Dict with extracted patterns and statistics
        """
        if not texts:
            return {"error": "No texts provided"}

        all_words = []
        sentence_lengths = []
        emoji_count = 0
        exclamation_count = 0
        question_count = 0
        total_chars = 0

        # Emoji regex (simplified)
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"  # dingbats
            "\U0001FA00-\U0001FA6F"  # chess symbols
            "\U0001FA70-\U0001FAFF"  # symbols extended
            "]+",
            flags=re.UNICODE,
        )

        for text in texts:
            text = text.strip()
            if not text:
                continue

            total_chars += len(text)

            # Count emojis
            emojis = emoji_pattern.findall(text)
            emoji_count += sum(len(e) for e in emojis)

            # Remove emojis for word analysis
            clean_text = emoji_pattern.sub("", text)

            # Split into words
            words = clean_text.split()
            all_words.extend(w.lower().strip(".,!?¿¡:;\"'()") for w in words)
            sentence_lengths.append(len(words))

            # Punctuation analysis
            exclamation_count += text.count("!")
            question_count += text.count("?")

        if not all_words:
            return {"error": "No meaningful text found"}

        # Frequency analysis
        word_freq = Counter(all_words)

        # Filter stopwords (basic Spanish)
        stopwords = {
            "de", "la", "el", "en", "y", "a", "los", "las", "un", "una",
            "es", "por", "que", "del", "se", "con", "no", "lo", "para",
            "al", "son", "me", "si", "mi", "ya", "pero", "como", "más",
            "o", "le", "ha", "muy", "te", "su", "fue", "este", "está",
        }
        meaningful_words = {
            w: c for w, c in word_freq.items()
            if w not in stopwords and len(w) > 2
        }

        avg_length = sum(sentence_lengths) / len(sentence_lengths)

        # Infer formality
        informal_markers = {"tío", "tía", "mola", "guay", "vale", "venga", "jaja",
                           "jeje", "xd", "lol", "pues", "buah", "uff", "hostia"}
        formal_markers = {"estimado", "cordialmente", "atentamente", "mediante",
                         "solicito", "adjunto", "remito", "agradezco"}

        informal_score = sum(word_freq.get(w, 0) for w in informal_markers)
        formal_score = sum(word_freq.get(w, 0) for w in formal_markers)

        if formal_score > informal_score:
            inferred_formality = "formal"
        elif informal_score > 3:
            inferred_formality = "casual"
        else:
            inferred_formality = "mixed"

        # Emoji usage level
        emoji_ratio = emoji_count / len(texts) if texts else 0
        if emoji_ratio == 0:
            emoji_level = "none"
        elif emoji_ratio < 0.3:
            emoji_level = "minimal"
        elif emoji_ratio < 1.0:
            emoji_level = "moderate"
        else:
            emoji_level = "heavy"

        # Sentence length category
        if avg_length < 6:
            length_category = "short"
        elif avg_length < 15:
            length_category = "medium"
        else:
            length_category = "long"

        return {
            "total_messages": len(texts),
            "total_words": len(all_words),
            "unique_words": len(set(all_words)),
            "avg_sentence_length": round(avg_length, 1),
            "sentence_length_category": length_category,
            "top_words": dict(Counter(meaningful_words).most_common(20)),
            "emoji_count": emoji_count,
            "emoji_ratio": round(emoji_ratio, 2),
            "emoji_level": emoji_level,
            "exclamation_ratio": round(exclamation_count / len(texts), 2) if texts else 0,
            "question_ratio": round(question_count / len(texts), 2) if texts else 0,
            "inferred_formality": inferred_formality,
            "potential_catchphrases": [
                w for w, c in Counter(meaningful_words).most_common(10)
                if c >= 3
            ],
        }

    def enrich_profile_from_texts(
        self,
        profile: PersonalityProfile,
        texts: list[str],
    ) -> PersonalityProfile:
        """Enrich an existing profile with patterns extracted from texts

        Merges extracted data with questionnaire data, preserving
        the user's explicit answers but adding discovered patterns.
        """
        analysis = self.analyze_texts(texts)
        if "error" in analysis:
            return profile

        # Add discovered catchphrases (don't overwrite user-provided ones)
        existing = set(p.lower() for p in profile.catchphrases)
        for phrase in analysis.get("potential_catchphrases", []):
            if phrase.lower() not in existing:
                profile.catchphrases.append(phrase)

        # Update emoji level if user didn't specify
        if profile.emoji_usage == "moderate":  # default
            profile.emoji_usage = analysis.get("emoji_level", "moderate")

        # Update sentence length if default
        if profile.sentence_length == "short":  # default
            profile.sentence_length = analysis.get("sentence_length_category", "medium")

        # Track source
        if "text_analysis" not in profile.sources:
            profile.sources.append("text_analysis")

        logger.info(
            f"Enriched profile for '{profile.voice_name}' "
            f"from {analysis['total_messages']} texts"
        )
        return profile

    # ─── Import Helpers ────────────────────────────────────────

    @staticmethod
    def import_whatsapp_export(file_path: Path) -> list[str]:
        """Parse a WhatsApp chat export file

        WhatsApp exports look like:
            [DD/MM/YY, HH:MM:SS] Name: Message text here

        Extracts only the message texts (no timestamps, no names).

        Args:
            file_path: Path to the exported .txt file

        Returns:
            List of message texts
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        messages = []

        # WhatsApp format: [DD/MM/YY, HH:MM:SS] Name: text
        pattern = re.compile(
            r'\[\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}(?::\d{2})?\]\s*'
            r'[^:]+:\s*(.+)'
        )

        for line in content.split("\n"):
            match = pattern.match(line.strip())
            if match:
                msg = match.group(1).strip()
                # Skip system messages and media placeholders
                if msg and not msg.startswith("<") and "omitido" not in msg.lower():
                    messages.append(msg)

        logger.info(f"Imported {len(messages)} messages from WhatsApp export")
        return messages

    # ─── Private Helpers ───────────────────────────────────────

    @staticmethod
    def _parse_list(text: str) -> list[str]:
        """Parse comma-separated text into a clean list"""
        if not text:
            return []
        items = [item.strip().strip('"\'') for item in text.split(",")]
        return [item for item in items if item]

    @staticmethod
    def _parse_phrases(text: str) -> list[str]:
        """Parse newline or dash-separated phrases"""
        if not text:
            return []

        phrases = []
        for line in text.split("\n"):
            line = line.strip().lstrip("-•*").strip().strip('"\'')
            if line:
                phrases.append(line)

        # If no newlines, try comma separation
        if not phrases and "," in text:
            phrases = [p.strip().strip('"\'') for p in text.split(",") if p.strip()]

        return phrases

    def to_dict(self) -> dict:
        """Serialize questionnaire state"""
        return {
            "responses": {
                qid: {"question_id": r.question_id, "answer": r.answer}
                for qid, r in self._responses.items()
            },
            "progress": self.get_progress(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Questionnaire":
        """Restore questionnaire state from dict"""
        q = cls()
        for qid, resp_data in data.get("responses", {}).items():
            q.submit_response(qid, resp_data["answer"])
        return q
