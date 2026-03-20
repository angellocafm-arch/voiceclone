"use client";

import { useState, useEffect, useRef } from "react";

interface InstallScreenProps {
  onComplete: () => void;
  onCancel: () => void;
}

interface InstallStep {
  id: number;
  label: string;
  description: string;
  status: "pending" | "active" | "done";
}

/**
 * Pantalla 2: Descarga + Instalación (Progress)
 *
 * No requiere interacción — el usuario solo espera.
 * Progress bar grande + pasos numerados + mensaje de privacidad.
 * Eye tracking: solo lectura pasiva + cancel button.
 *
 * NOTE: In MVP, this simulates the installation process.
 * In production, this would control the actual installer.
 */
export function InstallScreen({
  onComplete,
  onCancel,
}: InstallScreenProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [steps, setSteps] = useState<InstallStep[]>([
    {
      id: 1,
      label: "Entorno Python",
      description: "Instalando Python y dependencias...",
      status: "active",
    },
    {
      id: 2,
      label: "Modelo Chatterbox TTS",
      description: "Descargando modelo de clonación de voz (~2.5 GB)...",
      status: "pending",
    },
    {
      id: 3,
      label: "Servicio local",
      description: "Configurando servidor de voz en tu ordenador...",
      status: "pending",
    },
    {
      id: 4,
      label: "Verificación",
      description: "Comprobando que todo funciona correctamente...",
      status: "pending",
    },
  ]);

  const completedRef = useRef(false);

  // Simulate installation progress
  useEffect(() => {
    if (completedRef.current) return;

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + Math.random() * 2 + 0.5;

        if (next >= 100) {
          clearInterval(timer);
          completedRef.current = true;

          // Mark all steps done
          setSteps((s) =>
            s.map((step) => ({ ...step, status: "done" as const }))
          );
          setCurrentStep(4);

          // Auto-advance after a beat
          setTimeout(onComplete, 1500);
          return 100;
        }

        // Update step states based on progress
        const stepIdx = Math.floor(next / 25);
        if (stepIdx !== currentStep) {
          setCurrentStep(stepIdx);
          setSteps((s) =>
            s.map((step, i) => ({
              ...step,
              status:
                i < stepIdx
                  ? ("done" as const)
                  : i === stepIdx
                  ? ("active" as const)
                  : ("pending" as const),
            }))
          );
        }

        return next;
      });
    }, 200);

    return () => clearInterval(timer);
  }, [currentStep, onComplete]);

  const progressPct = Math.round(progress);
  const downloadedGB = ((progress / 100) * 2.5).toFixed(1);
  const totalGB = "2.5";
  const minutesLeft = Math.max(0, Math.ceil(((100 - progress) / 100) * 3));

  return (
    <div className="wizard-container" role="region" aria-label="Instalación de VoiceClone">
      {/* Header */}
      <header className="wizard-header">
        <div
          className="text-4xl mb-3"
          role="img"
          aria-label="Micrófono"
        >
          🎤
        </div>
        <h1 className="wizard-title">VoiceClone</h1>
        <h2
          className="text-2xl font-semibold"
          style={{ color: "var(--vc-text-primary)" }}
        >
          Instalando VoiceClone...
        </h2>
      </header>

      {/* Current step label */}
      <p
        className="text-center text-lg mb-6"
        style={{ color: "var(--vc-text-secondary)" }}
        aria-live="polite"
      >
        Paso {Math.min(currentStep + 1, 4)} de 4:{" "}
        {steps[Math.min(currentStep, 3)]?.label}
      </p>

      {/* Progress bar */}
      <div
        className="progress-bar mb-3"
        role="progressbar"
        aria-valuenow={progressPct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progreso de instalación: ${progressPct}%`}
      >
        <div
          className="progress-bar-fill"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Progress details */}
      <p
        className="text-center text-base mb-8"
        style={{ color: "var(--vc-text-muted)" }}
      >
        {downloadedGB} GB de {totalGB} GB · ~{minutesLeft} minuto
        {minutesLeft !== 1 ? "s" : ""} restante{minutesLeft !== 1 ? "s" : ""}
      </p>

      {/* Step list */}
      <div className="flex flex-col gap-3 mb-8" role="list" aria-label="Pasos de instalación">
        {steps.map((step) => (
          <div
            key={step.id}
            className="flex items-center gap-3 text-lg"
            role="listitem"
            aria-current={step.status === "active" ? "step" : undefined}
          >
            {/* Step icon */}
            <span
              className="text-xl flex-shrink-0"
              aria-hidden="true"
            >
              {step.status === "done" && "✅"}
              {step.status === "active" && "⏳"}
              {step.status === "pending" && "○"}
            </span>
            <span
              style={{
                color:
                  step.status === "done"
                    ? "var(--vc-accent-green)"
                    : step.status === "active"
                    ? "var(--vc-text-primary)"
                    : "var(--vc-text-muted)",
                fontWeight: step.status === "active" ? 600 : 400,
              }}
            >
              Paso {step.id}: {step.label}
            </span>
            {/* Screen reader only: status */}
            <span className="sr-only">
              {step.status === "done"
                ? "Completado"
                : step.status === "active"
                ? "En progreso"
                : "Pendiente"}
            </span>
          </div>
        ))}
      </div>

      {/* Privacy message */}
      <div className="privacy-msg">
        <p>Todo se instala en tu ordenador.</p>
        <p>Nada se envía a internet.</p>
        <p className="font-semibold mt-1">Tu voz será solo tuya.</p>
      </div>

      {/* Cancel button — discrete */}
      <div className="mt-8">
        <button
          className="btn-danger"
          onClick={onCancel}
          aria-label="Cancelar instalación y volver a la página principal"
        >
          <span aria-hidden="true">✕</span>
          Cancelar instalación
        </button>
      </div>

      {/* Hidden sr-only live region for screen readers */}
      <div className="sr-only" aria-live="assertive" role="status">
        Instalación en progreso. {progressPct}% completado.
      </div>
    </div>
  );
}
