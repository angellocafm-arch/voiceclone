"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface DashboardScreenProps {
  voiceId: string | null;
  voiceName: string | null;
  hasPersonality: boolean;
  apiAvailable: boolean;
  onNewVoice: () => void;
  onEditPersonality: () => void;
}

/**
 * Pantalla 6: Dashboard — "Tu voz está lista"
 *
 * Hub central: prueba tu voz, estadísticas, próximos pasos.
 * Text-to-speech test box con reproducción.
 * Cards de estado para voz + personalidad.
 * WCAG AA: labels, status, focus management.
 */
export function DashboardScreen({
  voiceId,
  voiceName,
  hasPersonality,
  apiAvailable,
  onNewVoice,
  onEditPersonality,
}: DashboardScreenProps) {
  const [testText, setTestText] = useState(
    "Hola, esto es una prueba de mi voz clonada."
  );
  const [synthesizing, setSynthesizing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const testVoice = async () => {
    if (!voiceId || !testText.trim()) return;

    setSynthesizing(true);
    setErrorMsg(null);

    try {
      const audioData = hasPersonality
        ? await api.synthesizeWithPersonality(testText, voiceId)
        : await api.synthesize(testText, voiceId);

      const blob = new Blob([audioData], { type: "audio/wav" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      audio.onended = () => {
        URL.revokeObjectURL(url);
      };

      await audio.play();
    } catch (error) {
      setErrorMsg("Error al sintetizar: " + String(error));
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div className="wizard-container" role="region" aria-label="Dashboard de VoiceClone">
      {/* Header */}
      <header className="wizard-header">
        <div className="text-5xl mb-3" role="img" aria-label="Micrófono">🎤</div>
        <h1 className="wizard-title">Tu Voz Está Lista</h1>
        {voiceName && (
          <p className="wizard-subtitle">
            <span
              className="status-dot status-dot-active"
              aria-hidden="true"
            />
            {voiceName}
          </p>
        )}
      </header>

      {/* API status */}
      {!apiAvailable && (
        <div
          className="tip-box mb-6"
          role="alert"
          style={{
            background: "rgba(231, 76, 60, 0.08)",
            borderColor: "rgba(231, 76, 60, 0.25)",
          }}
        >
          <strong style={{ color: "var(--vc-accent-red)" }}>
            ⚠️ Motor desconectado.
          </strong>{" "}
          El servidor de voz local no responde. Asegúrate de que VoiceClone
          está instalado y ejecutándose.
        </div>
      )}

      {/* Error message */}
      {errorMsg && (
        <div
          className="tip-box mb-4"
          role="alert"
          style={{
            background: "rgba(231, 76, 60, 0.08)",
            borderColor: "rgba(231, 76, 60, 0.25)",
          }}
        >
          <strong style={{ color: "var(--vc-accent-red)" }}>⚠️</strong>{" "}
          {errorMsg}
        </div>
      )}

      {/* Voice card */}
      <div className="audio-preview mb-6">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-3xl" aria-hidden="true">🎤</span>
          <div>
            <h2
              className="text-xl font-bold"
              style={{ color: "var(--vc-text-primary)" }}
            >
              {voiceName || "Sin voz"}
            </h2>
            <p
              className="text-sm"
              style={{ color: "var(--vc-accent-green)" }}
            >
              ✓ Lista para usar
              {hasPersonality && " · Con personalidad"}
            </p>
          </div>
        </div>

        {/* Status cards */}
        <div className="flex gap-3 mb-4">
          <div
            className="flex-1 p-3 rounded-xl text-center"
            style={{
              background: "var(--vc-bg-input)",
              border: "1px solid var(--vc-border)",
            }}
          >
            <div
              className="text-2xl font-bold"
              style={{ color: "var(--vc-text-primary)" }}
            >
              ✓
            </div>
            <div
              className="text-sm"
              style={{ color: "var(--vc-text-muted)" }}
            >
              Voz clonada
            </div>
          </div>
          <div
            className="flex-1 p-3 rounded-xl text-center"
            style={{
              background: "var(--vc-bg-input)",
              border: "1px solid var(--vc-border)",
            }}
          >
            <div
              className="text-2xl font-bold"
              style={{
                color: hasPersonality
                  ? "var(--vc-accent-green)"
                  : "var(--vc-text-muted)",
              }}
            >
              {hasPersonality ? "✓" : "—"}
            </div>
            <div
              className="text-sm"
              style={{ color: "var(--vc-text-muted)" }}
            >
              Personalidad
            </div>
          </div>
          <div
            className="flex-1 p-3 rounded-xl text-center"
            style={{
              background: "var(--vc-bg-input)",
              border: "1px solid var(--vc-border)",
            }}
          >
            <div
              className="text-2xl font-bold"
              style={{ color: "var(--vc-accent-green)" }}
            >
              100%
            </div>
            <div
              className="text-sm"
              style={{ color: "var(--vc-text-muted)" }}
            >
              Privacidad
            </div>
          </div>
        </div>
      </div>

      {/* Test your voice */}
      <div className="mb-6">
        <h3
          className="text-lg font-semibold mb-3"
          style={{ color: "var(--vc-text-secondary)" }}
        >
          Prueba Tu Voz
        </h3>
        <label htmlFor="test-text" className="sr-only">
          Texto para sintetizar con tu voz clonada
        </label>
        <textarea
          id="test-text"
          className="w-full p-4 rounded-xl text-lg mb-3"
          style={{
            background: "var(--vc-bg-input)",
            color: "var(--vc-text-primary)",
            border: "2px solid var(--vc-border)",
            minHeight: "100px",
            resize: "vertical",
            fontFamily: "var(--vc-font-sans)",
          }}
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="Escribe algo para escucharlo con tu voz..."
          aria-label="Texto para probar tu voz clonada"
        />
        <button
          className="btn-primary"
          onClick={testVoice}
          disabled={synthesizing || !apiAvailable || !voiceId}
          aria-label={
            synthesizing
              ? "Sintetizando voz..."
              : "Reproducir el texto con tu voz clonada"
          }
        >
          {synthesizing ? (
            <>
              <span
                aria-hidden="true"
                style={{ animation: "spin 1s linear infinite", display: "inline-block" }}
              >
                🔄
              </span>
              Sintetizando...
            </>
          ) : (
            <>
              <span aria-hidden="true">▶️</span>
              Escuchar
            </>
          )}
        </button>
      </div>

      {/* Next steps */}
      <div className="mb-6">
        <h3
          className="text-lg font-semibold mb-3"
          style={{ color: "var(--vc-text-secondary)" }}
        >
          Próximos Pasos
        </h3>
        <div className="flex flex-col gap-2">
          <div
            className="flex items-center gap-3 p-3 rounded-xl"
            style={{ background: "var(--vc-bg-card)" }}
          >
            <span style={{ color: "var(--vc-accent-green)" }}>✓</span>
            <span>Voz clonada</span>
          </div>
          <div
            className="flex items-center gap-3 p-3 rounded-xl"
            style={{ background: "var(--vc-bg-card)" }}
          >
            <span
              style={{
                color: hasPersonality
                  ? "var(--vc-accent-green)"
                  : "var(--vc-text-muted)",
              }}
            >
              {hasPersonality ? "✓" : "○"}
            </span>
            <span>{hasPersonality ? "Personalidad configurada" : "Configurar personalidad"}</span>
            {!hasPersonality && (
              <button
                className="ml-auto text-sm px-3 py-1 rounded-lg"
                style={{
                  background: "var(--vc-accent-blue)",
                  color: "var(--vc-text-primary)",
                }}
                onClick={onEditPersonality}
                aria-label="Configurar personalidad de tu voz"
              >
                Configurar
              </button>
            )}
          </div>
          <div
            className="flex items-center gap-3 p-3 rounded-xl"
            style={{ background: "var(--vc-bg-card)" }}
          >
            <span style={{ color: "var(--vc-text-muted)" }}>○</span>
            <span>Integrar con AAC (Grid 3, Proloquo2Go)</span>
          </div>
          <div
            className="flex items-center gap-3 p-3 rounded-xl"
            style={{ background: "var(--vc-bg-card)" }}
          >
            <span style={{ color: "var(--vc-text-muted)" }}>○</span>
            <span>Configurar eye tracking (Tobii)</span>
          </div>
        </div>
      </div>

      {/* Help section */}
      <div className="tip-box mb-6">
        <strong>¿Necesitas ayuda?</strong>
        <ul className="mt-2 flex flex-col gap-1">
          <li>🖱️ <strong>Teclado:</strong> Tab para navegar, Enter para confirmar</li>
          <li>👁️ <strong>Mirada:</strong> Mira 1-2 segundos para activar</li>
          <li>🔘 <strong>Switch:</strong> 1-2 pulsadores para navegación completa</li>
        </ul>
      </div>

      {/* Action buttons */}
      <div className="flex flex-col gap-3">
        <button
          className="btn-secondary"
          onClick={onNewVoice}
          aria-label="Clonar otra voz nueva"
        >
          <span aria-hidden="true">➕</span>
          Clonar otra voz
        </button>
      </div>

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
