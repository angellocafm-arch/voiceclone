"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface PersonalityScreenProps {
  voiceId: string;
  voiceName: string;
  onComplete: (didSetup: boolean) => void;
  onSkip: () => void;
  onBack: () => void;
}

/**
 * Pantalla 4: Captura de Personalidad
 *
 * Cuestionario guiado para capturar la esencia de la persona.
 * Progress bar + preguntas una a una (no overwhelm).
 * Skip disponible siempre — esto es opcional.
 * WCAG AA: labels, progress, live regions, focus management.
 */

interface Question {
  id: number;
  question: string;
  placeholder: string;
  tip: string;
}

const QUESTIONS: Question[] = [
  {
    id: 1,
    question: "¿Cómo te describirías en pocas palabras?",
    placeholder: "Ejemplo: Soy alegre, algo sarcástico, y me encanta hacer chistes malos...",
    tip: "No hay respuestas correctas. Sé tú mismo/a.",
  },
  {
    id: 2,
    question: "¿Cuáles son tus muletillas o expresiones favoritas?",
    placeholder: 'Ejemplo: "¿sabes?", "tío", "mola", "o sea"...',
    tip: "Esas palabras que usas sin darte cuenta. Las que tu familia reconocería.",
  },
  {
    id: 3,
    question: "¿Eres más formal o casual al hablar?",
    placeholder: "Ejemplo: Muy casual con amigos, algo más formal en el trabajo...",
    tip: "Piensa en cómo hablas con alguien de confianza.",
  },
  {
    id: 4,
    question: "¿Qué temas te apasionan?",
    placeholder: "Ejemplo: El fútbol, la cocina, los viajes, la tecnología...",
    tip: "Los temas de los que podrías hablar horas sin cansarte.",
  },
  {
    id: 5,
    question: "¿Cómo expresas cariño o afecto?",
    placeholder: 'Ejemplo: Con humor, con apodos cariñosos, diciendo "te quiero" directamente...',
    tip: "Esto ayuda a que tu voz suene auténtica en momentos emotivos.",
  },
  {
    id: 6,
    question: "¿Tienes alguna frase que repites mucho?",
    placeholder: 'Ejemplo: "Eso es lo que hay", "A ver, a ver...", "Venga va"...',
    tip: "Las frases que tus amigos o familia imitarían de ti.",
  },
];

export function PersonalityScreen({
  voiceId,
  voiceName,
  onComplete,
  onSkip,
  onBack,
}: PersonalityScreenProps) {
  const [step, setStep] = useState<"welcome" | "questions" | "saving" | "done">("welcome");
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleAnswer = (text: string) => {
    setAnswers((prev) => ({ ...prev, [currentQuestion]: text }));
  };

  const nextQuestion = () => {
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    } else {
      savePersonality();
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const savePersonality = async () => {
    setStep("saving");
    setErrorMsg(null);
    try {
      await api.setupPersonality(voiceId, answers);
      setStep("done");
      // Auto-advance after success
      setTimeout(() => {
        onComplete(true);
      }, 2000);
    } catch (error) {
      setErrorMsg("Error al guardar: " + String(error));
      setStep("questions");
    }
  };

  const progressPct = step === "questions"
    ? Math.round(((currentQuestion + 1) / QUESTIONS.length) * 100)
    : step === "done" ? 100 : 0;

  return (
    <div className="wizard-container" role="region" aria-label="Captura de personalidad">
      {/* Header */}
      <header className="wizard-header">
        <div className="text-4xl mb-3" role="img" aria-label="Cerebro">🧠</div>
        <h1 className="wizard-title">Tu Personalidad</h1>
        <p className="wizard-subtitle">
          Para que tu voz no solo suene como tú — sino que hable como tú.
        </p>
      </header>

      {/* Error message */}
      {errorMsg && (
        <div
          className="tip-box mb-6"
          role="alert"
          style={{
            background: "rgba(231, 76, 60, 0.08)",
            borderColor: "rgba(231, 76, 60, 0.25)",
          }}
        >
          <strong style={{ color: "var(--vc-accent-red)" }}>⚠️ Error:</strong>{" "}
          {errorMsg}
        </div>
      )}

      {/* Step: Welcome */}
      {step === "welcome" && (
        <div className="flex flex-col gap-4">
          <div className="tip-box mb-4">
            <strong>💡 ¿Para qué sirve esto?</strong>
            <p className="mt-2">
              Respondiendo unas preguntas, tu voz clonada no solo sonará como tú
              — también usará tus expresiones, tu estilo, tu forma de hablar.
            </p>
            <p className="mt-2">
              Es como enseñarle a tu voz digital a ser TÚ.
            </p>
          </div>

          <p className="text-center text-base" style={{ color: "var(--vc-text-muted)" }}>
            Voz: <strong>{voiceName}</strong> — {QUESTIONS.length} preguntas rápidas
          </p>

          <button
            className="btn-primary"
            onClick={() => setStep("questions")}
            aria-label="Empezar a responder las preguntas de personalidad"
          >
            <span aria-hidden="true">✨</span>
            Comenzar
          </button>

          <button
            className="btn-secondary"
            onClick={onSkip}
            aria-label="Saltar la captura de personalidad — puedes hacerlo después"
          >
            <span aria-hidden="true">⏭️</span>
            Saltar por ahora
          </button>

          <button
            className="btn-danger mt-2"
            onClick={onBack}
            aria-label="Volver a la clonación de voz"
          >
            <span aria-hidden="true">←</span>
            Atrás
          </button>
        </div>
      )}

      {/* Step: Questions */}
      {step === "questions" && (
        <div className="flex flex-col gap-4">
          {/* Progress bar */}
          <div
            className="progress-bar mb-2"
            role="progressbar"
            aria-valuenow={progressPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Pregunta ${currentQuestion + 1} de ${QUESTIONS.length}`}
          >
            <div
              className="progress-bar-fill"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <p className="text-center text-sm" style={{ color: "var(--vc-text-muted)" }}>
            Pregunta {currentQuestion + 1} de {QUESTIONS.length}
          </p>

          {/* Question */}
          <h2
            className="text-xl font-semibold mb-2"
            style={{ color: "var(--vc-text-primary)" }}
          >
            {QUESTIONS[currentQuestion].question}
          </h2>

          <div className="tip-box mb-2" style={{ fontSize: "14px" }}>
            💡 {QUESTIONS[currentQuestion].tip}
          </div>

          {/* Answer textarea */}
          <textarea
            className="w-full p-4 rounded-xl text-lg"
            style={{
              background: "var(--vc-bg-input)",
              color: "var(--vc-text-primary)",
              border: "2px solid var(--vc-border)",
              minHeight: "120px",
              resize: "vertical",
              fontFamily: "var(--vc-font-sans)",
            }}
            value={answers[currentQuestion] || ""}
            onChange={(e) => handleAnswer(e.target.value)}
            placeholder={QUESTIONS[currentQuestion].placeholder}
            aria-label={QUESTIONS[currentQuestion].question}
            aria-describedby="question-tip"
          />

          {/* Navigation buttons */}
          <div className="flex gap-3">
            {currentQuestion > 0 && (
              <button
                className="btn-secondary"
                onClick={prevQuestion}
                aria-label="Ir a la pregunta anterior"
                style={{ flex: "0 0 auto", width: "auto", padding: "16px 24px" }}
              >
                ←
              </button>
            )}
            <button
              className="btn-primary"
              onClick={nextQuestion}
              aria-label={
                currentQuestion === QUESTIONS.length - 1
                  ? "Guardar perfil de personalidad"
                  : "Siguiente pregunta"
              }
              style={{ flex: 1 }}
            >
              {currentQuestion === QUESTIONS.length - 1 ? (
                <>
                  <span aria-hidden="true">✓</span> Guardar Perfil
                </>
              ) : (
                <>
                  Siguiente <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {/* Skip option — always available */}
          <button
            className="btn-danger mt-2"
            onClick={onSkip}
            aria-label="Saltar el resto de preguntas"
          >
            <span aria-hidden="true">⏭️</span>
            Saltar — puedo hacerlo después
          </button>
        </div>
      )}

      {/* Step: Saving */}
      {step === "saving" && (
        <div className="flex flex-col items-center gap-6" role="status" aria-live="polite">
          <div
            className="text-6xl"
            style={{ animation: "spin 2s linear infinite" }}
            aria-hidden="true"
          >
            🔄
          </div>
          <p className="text-2xl font-semibold" style={{ color: "var(--vc-text-primary)" }}>
            Analizando tu perfil...
          </p>
          <p className="text-lg" style={{ color: "var(--vc-text-secondary)" }}>
            Creando tu personalidad digital.
          </p>
        </div>
      )}

      {/* Step: Done */}
      {step === "done" && (
        <div className="flex flex-col items-center gap-6" role="status" aria-live="assertive">
          <div className="text-6xl" aria-hidden="true">✅</div>
          <p className="text-3xl font-bold" style={{ color: "var(--vc-accent-green)" }}>
            ¡Tu perfil está listo!
          </p>
          <p className="text-lg" style={{ color: "var(--vc-text-secondary)" }}>
            Tu voz ahora hablará con tu estilo personal.
          </p>
          <p className="text-base" style={{ color: "var(--vc-text-muted)" }}>
            Continuando...
          </p>
        </div>
      )}

      {/* CSS animation */}
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
