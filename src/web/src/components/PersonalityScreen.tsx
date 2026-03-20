"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface PersonalityScreenProps {
  voiceId: string;
  onDone: () => void;
  onBack: () => void;
}

export function PersonalityScreen({
  voiceId,
  onDone,
  onBack,
}: PersonalityScreenProps) {
  const [step, setStep] = useState<"welcome" | "questions" | "saving" | "done">(
    "welcome"
  );
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const questions = [
    "¿Cómo te describirías en pocas palabras?",
    "¿Cuáles son tus expresiones favoritas o muletillas?",
    "¿Eres más formal o casual al hablar?",
    "¿Qué temas te apasionan?",
  ];

  const handleAnswer = (text: string) => {
    setAnswers((prev) => ({ ...prev, [currentQuestion]: text }));
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    } else {
      savePersonality();
    }
  };

  const savePersonality = async () => {
    setStep("saving");
    try {
      await api.setupPersonality(voiceId, answers);
      setStep("done");
    } catch (error) {
      alert("Error: " + String(error));
      setStep("questions");
    }
  };

  return (
    <div className="screen-container">
      <h1 className="screen-title">Tu Personalidad</h1>

      {step === "welcome" && (
        <div className="wizard-step">
          <p className="screen-description">
            Cuéntanos cómo eres. Así tu voz no solo sonarás como tú, sino que
            hablará como tú.
          </p>
          <button
            className="btn btn-primary mega-target"
            onClick={() => setStep("questions")}
          >
            Comenzar
          </button>
          <button className="btn btn-tertiary float-left" onClick={onBack}>
            ← Atrás
          </button>
        </div>
      )}

      {step === "questions" && (
        <div className="wizard-step">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${((currentQuestion + 1) / questions.length) * 100}%`,
              }}
            ></div>
          </div>

          <h2 className="question-title">
            {currentQuestion + 1}. {questions[currentQuestion]}
          </h2>

          <textarea
            className="input-field textarea"
            value={answers[currentQuestion] || ""}
            onChange={(e) => handleAnswer(e.target.value)}
            placeholder="Escribe tu respuesta..."
          />

          <button className="btn btn-primary mega-target" onClick={nextQuestion}>
            {currentQuestion === questions.length - 1 ? "Guardar" : "Siguiente"}
          </button>
        </div>
      )}

      {step === "saving" && (
        <div className="wizard-step">
          <div className="spinner"></div>
          <p>Guardando tu perfil...</p>
        </div>
      )}

      {step === "done" && (
        <div className="wizard-step success">
          <div className="success-icon">✅</div>
          <p>¡Tu perfil está listo!</p>
          <button className="btn btn-primary mega-target" onClick={onDone}>
            Continuar
          </button>
        </div>
      )}
    </div>
  );
}
