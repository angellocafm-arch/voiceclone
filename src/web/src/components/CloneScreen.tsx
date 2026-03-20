"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

interface CloneScreenProps {
  apiAvailable: boolean;
  onComplete: (voiceId: string, voiceName: string) => void;
  onBack: () => void;
}

/**
 * Pantalla 3: Clonación de Voz
 *
 * Dos opciones: grabar en vivo o subir grabación existente.
 * Mega-target para grabación (eye tracking friendly).
 * Guía con textos para leer en voz alta.
 * WCAG AA: progress, aria-live, focus management.
 */
export function CloneScreen({ apiAvailable, onComplete, onBack }: CloneScreenProps) {
  const [step, setStep] = useState<"choice" | "name" | "record" | "upload" | "processing" | "done">("choice");
  const [voiceName, setVoiceName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const startRecording = async () => {
    setErrorMsg(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        if (chunksRef.current.length > 0) {
          const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
          processVoice(audioBlob);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setStep("record");
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch {
      setErrorMsg(
        "No se puede acceder al micrófono. Verifica los permisos de tu navegador."
      );
    }
  };

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setErrorMsg(null);
      processVoice(file);
    }
  };

  const processVoice = async (audioBlob: Blob) => {
    setStep("processing");
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "voice.wav");
      formData.append("name", voiceName || "Mi Voz");

      const result = await api.cloneVoice(formData);
      setStep("done");
      // Small delay to show success before navigating
      setTimeout(() => {
        onComplete(result.id, result.name);
      }, 2000);
    } catch (error) {
      setErrorMsg("Error al procesar la voz: " + String(error));
      setStep("choice");
    }
  };

  // Reading prompts for voice recording
  const readingPrompts = [
    "El sol salía lentamente sobre las montañas, tiñendo el cielo de tonos dorados y anaranjados.",
    "Me gusta pasear por el parque cuando la tarde cae y el viento sopla suave entre los árboles.",
    "Ayer fui al mercado y compré frutas frescas, pan recién horneado y un ramo de flores para casa.",
  ];

  return (
    <div className="wizard-container" role="region" aria-label="Clonación de voz">
      {/* Header */}
      <header className="wizard-header">
        <div className="text-4xl mb-3" role="img" aria-label="Micrófono">🎤</div>
        <h1 className="wizard-title">Clona Tu Voz</h1>
        <p className="wizard-subtitle">
          Graba 2-3 minutos de tu voz o sube una grabación anterior.
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

      {/* Step: Choice */}
      {step === "choice" && (
        <div className="flex flex-col gap-4" role="group" aria-label="Opciones de clonación">
          {/* Voice name input */}
          <div className="mb-4">
            <label
              htmlFor="voice-name"
              className="block text-lg font-semibold mb-2"
              style={{ color: "var(--vc-text-secondary)" }}
            >
              Nombre de tu voz:
            </label>
            <input
              id="voice-name"
              type="text"
              className="w-full p-4 rounded-xl text-lg"
              style={{
                background: "var(--vc-bg-input)",
                color: "var(--vc-text-primary)",
                border: "2px solid var(--vc-border)",
                minHeight: "56px",
              }}
              value={voiceName}
              onChange={(e) => setVoiceName(e.target.value)}
              placeholder="Mi Voz"
              aria-describedby="voice-name-desc"
            />
            <p id="voice-name-desc" className="text-sm mt-1" style={{ color: "var(--vc-text-muted)" }}>
              Un nombre para identificar esta voz (opcional)
            </p>
          </div>

          {/* Record button — mega target */}
          <button
            className="btn-primary"
            onClick={startRecording}
            aria-label="Grabar tu voz ahora usando el micrófono"
            disabled={!apiAvailable}
          >
            <span aria-hidden="true" className="text-2xl">🎤</span>
            <span className="flex flex-col items-start">
              <span className="font-bold">Grabar Ahora</span>
              <span className="text-sm" style={{ color: "var(--vc-text-secondary)" }}>
                Lee en voz alta 2-3 minutos
              </span>
            </span>
          </button>

          {/* Upload button */}
          <button
            className="btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Subir una grabación de audio existente"
            disabled={!apiAvailable}
          >
            <span aria-hidden="true" className="text-2xl">📁</span>
            <span className="flex flex-col items-start">
              <span className="font-bold">Subir Archivo</span>
              <span className="text-sm" style={{ color: "var(--vc-text-muted)" }}>
                MP3, WAV, OGG — de cualquier grabación
              </span>
            </span>
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            onChange={handleFileUpload}
            className="hidden"
            aria-hidden="true"
            tabIndex={-1}
          />

          {!apiAvailable && (
            <div className="tip-box">
              <strong>💡 Motor no detectado.</strong> Instala VoiceClone primero para clonar tu voz.
            </div>
          )}

          {/* Back button */}
          <button
            className="btn-danger mt-4"
            onClick={onBack}
            aria-label="Volver a la página principal"
          >
            <span aria-hidden="true">←</span>
            Atrás
          </button>
        </div>
      )}

      {/* Step: Recording */}
      {step === "record" && (
        <div className="flex flex-col items-center gap-6">
          {/* Recording indicator */}
          <div
            className="text-center"
            role="status"
            aria-live="polite"
            aria-label={`Grabando: ${formatTime(recordingTime)}`}
          >
            <div
              className="text-6xl mb-4"
              style={{
                animation: "pulse 1.5s ease-in-out infinite",
                color: "var(--vc-accent-red)",
              }}
            >
              ⏺️
            </div>
            <p className="text-3xl font-bold mb-2" style={{ color: "var(--vc-text-primary)" }}>
              {formatTime(recordingTime)}
            </p>
            <p className="text-lg" style={{ color: "var(--vc-text-secondary)" }}>
              Grabando... Lee los textos de abajo en voz alta.
            </p>
          </div>

          {/* Quality indicator */}
          {recordingTime < 30 && (
            <div className="tip-box w-full">
              <strong>💡 Tip:</strong> Graba al menos 2 minutos para mejor calidad.
              Cuanto más grabes, mejor sonará tu voz clonada.
            </div>
          )}
          {recordingTime >= 30 && recordingTime < 120 && (
            <div className="tip-box w-full" style={{ background: "rgba(46, 204, 113, 0.08)", borderColor: "rgba(46, 204, 113, 0.25)" }}>
              <strong style={{ color: "var(--vc-accent-green)" }}>✓ Buena calidad.</strong> Puedes parar o seguir grabando para aún mejor resultado.
            </div>
          )}
          {recordingTime >= 120 && (
            <div className="tip-box w-full" style={{ background: "rgba(46, 204, 113, 0.08)", borderColor: "rgba(46, 204, 113, 0.25)" }}>
              <strong style={{ color: "var(--vc-accent-green)" }}>✓ Excelente.</strong> Ya tienes suficiente material. Puedes parar cuando quieras.
            </div>
          )}

          {/* Reading prompts */}
          <div className="w-full" role="region" aria-label="Textos para leer en voz alta">
            <h3 className="text-lg font-semibold mb-3" style={{ color: "var(--vc-text-secondary)" }}>
              Lee en voz alta:
            </h3>
            {readingPrompts.map((prompt, i) => (
              <div key={i} className="audio-preview mb-3">
                <p className="audio-text">&ldquo;{prompt}&rdquo;</p>
              </div>
            ))}
          </div>

          {/* Stop button — mega target */}
          <button
            className="btn-success w-full"
            onClick={stopRecording}
            aria-label="Detener la grabación y procesar tu voz"
            style={{
              background: "rgba(231, 76, 60, 0.15)",
              borderColor: "var(--vc-accent-red)",
            }}
          >
            <span aria-hidden="true" className="text-2xl">⏹️</span>
            <span className="font-bold">Detener Grabación</span>
          </button>
        </div>
      )}

      {/* Step: Processing */}
      {step === "processing" && (
        <div className="flex flex-col items-center gap-6" role="status" aria-live="polite">
          <div
            className="text-6xl"
            style={{ animation: "spin 2s linear infinite" }}
            aria-hidden="true"
          >
            🔄
          </div>
          <p className="text-2xl font-semibold" style={{ color: "var(--vc-text-primary)" }}>
            Procesando tu voz...
          </p>
          <p className="text-lg" style={{ color: "var(--vc-text-secondary)" }}>
            Esto puede tomar 1-2 minutos.
          </p>
          <div className="privacy-msg">
            <p>Todo se procesa en tu ordenador.</p>
            <p className="font-semibold">Tu voz no sale de aquí.</p>
          </div>
        </div>
      )}

      {/* Step: Done */}
      {step === "done" && (
        <div className="flex flex-col items-center gap-6" role="status" aria-live="assertive">
          <div className="text-6xl" aria-hidden="true">✅</div>
          <p className="text-3xl font-bold" style={{ color: "var(--vc-accent-green)" }}>
            ¡Tu voz está clonada!
          </p>
          <p className="text-lg" style={{ color: "var(--vc-text-secondary)" }}>
            {voiceName || "Mi Voz"} — lista para usar
          </p>
          <p className="text-base" style={{ color: "var(--vc-text-muted)" }}>
            Continuando al siguiente paso...
          </p>
        </div>
      )}

      {/* CSS animation for recording pulse */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.1); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
