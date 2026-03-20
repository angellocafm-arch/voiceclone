"use client";

import { useEffect, useState } from "react";

interface LandingScreenProps {
  apiAvailable: boolean;
  hasVoice: boolean;
  onDownload: () => void;
  onOpenApp: () => void;
  onStartClone: () => void;
}

/**
 * Pantalla 1: Landing — "Preserva tu voz"
 *
 * Emotivo pero empoderador. No victimista.
 * 3 botones de descarga (autodetecta OS) + link para usuarios que vuelven.
 * WCAG AA: targets 64px+, alto contraste, tabulación clara.
 */
export function LandingScreen({
  apiAvailable,
  hasVoice,
  onDownload,
  onOpenApp,
  onStartClone,
}: LandingScreenProps) {
  const [detectedOS, setDetectedOS] = useState<"macos" | "windows" | "linux">(
    "macos"
  );

  useEffect(() => {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes("win")) setDetectedOS("windows");
    else if (ua.includes("linux")) setDetectedOS("linux");
    else setDetectedOS("macos");
  }, []);

  const osButtons: Array<{
    id: "macos" | "windows" | "linux";
    icon: string;
    label: string;
    sub: string;
  }> = [
    {
      id: "macos",
      icon: "🍎",
      label: "Descargar para macOS",
      sub: "Apple Silicon + Intel",
    },
    {
      id: "windows",
      icon: "🪟",
      label: "Descargar para Windows",
      sub: "Windows 10+",
    },
    {
      id: "linux",
      icon: "🐧",
      label: "Descargar para Linux",
      sub: "Ubuntu, Debian, Fedora",
    },
  ];

  // Sort to put detected OS first
  const sortedButtons = [
    ...osButtons.filter((b) => b.id === detectedOS),
    ...osButtons.filter((b) => b.id !== detectedOS),
  ];

  return (
    <div className="wizard-container" role="region" aria-label="Página principal de VoiceClone">
      {/* Logo & Title */}
      <header className="wizard-header">
        <div
          className="text-5xl mb-4"
          role="img"
          aria-label="Micrófono — logo de VoiceClone"
        >
          🎤
        </div>
        <h1
          className="text-4xl font-extrabold tracking-tight mb-2"
          style={{ color: "var(--vc-text-primary)" }}
        >
          VoiceClone
        </h1>
      </header>

      {/* Tagline */}
      <div className="text-center mb-8">
        <p
          className="text-3xl font-bold mb-1"
          style={{ color: "var(--vc-text-primary)" }}
        >
          Preserva tu voz.
        </p>
        <p
          className="text-3xl font-bold mb-6"
          style={{ color: "var(--vc-text-primary)" }}
        >
          Para siempre.
        </p>
        <p
          className="text-lg mb-2"
          style={{ color: "var(--vc-text-secondary)" }}
        >
          Tu voz es tuya. Clónala en tu ordenador.
        </p>
        <p
          className="text-lg mb-2"
          style={{ color: "var(--vc-text-secondary)" }}
        >
          100% gratis. 100% privado. 100% local.
        </p>
        <p
          className="text-base mt-4"
          style={{ color: "var(--vc-text-muted)" }}
        >
          Diseñado para personas con ELA y enfermedades que afectan al habla.
        </p>
      </div>

      {/* Action area */}
      <div className="flex flex-col gap-4" role="group" aria-label="Opciones de descarga">
        {/* If API is already running, show "start clone" as primary */}
        {apiAvailable ? (
          <button
            className="btn-success"
            onClick={onStartClone}
            aria-label="Empezar a clonar tu voz — el motor ya está instalado"
          >
            <span aria-hidden="true">✅</span>
            Motor instalado — Clonar mi voz
          </button>
        ) : (
          // Download buttons
          sortedButtons.map((btn) => (
            <button
              key={btn.id}
              className={
                btn.id === detectedOS ? "btn-primary" : "btn-secondary"
              }
              onClick={onDownload}
              aria-label={`${btn.label} — ${btn.sub}`}
            >
              <span aria-hidden="true">{btn.icon}</span>
              <span className="flex flex-col items-start">
                <span className="font-semibold">{btn.label}</span>
                <span
                  className="text-sm"
                  style={{
                    color:
                      btn.id === detectedOS
                        ? "var(--vc-text-secondary)"
                        : "var(--vc-text-muted)",
                  }}
                >
                  ({btn.sub})
                </span>
              </span>
            </button>
          ))
        )}
      </div>

      {/* Return user link */}
      {hasVoice && apiAvailable && (
        <div className="text-center mt-6">
          <button
            className="btn-secondary"
            onClick={onOpenApp}
            style={{ maxWidth: "400px", margin: "0 auto" }}
            aria-label="Ir al dashboard — ya tienes una voz clonada"
          >
            <span aria-hidden="true">→</span>
            Abrir VoiceClone
          </button>
        </div>
      )}

      {/* Footer */}
      <footer className="text-center mt-12" role="contentinfo">
        <div
          className="flex items-center justify-center gap-4 text-sm"
          style={{ color: "var(--vc-text-muted)" }}
        >
          <span>Open Source (MIT)</span>
          <span aria-hidden="true">·</span>
          <a
            href="https://github.com/angellocafm-arch/voiceclone"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:no-underline"
            style={{ color: "var(--vc-text-muted)" }}
          >
            GitHub
          </a>
          <span aria-hidden="true">·</span>
          <a
            href="#docs"
            className="underline hover:no-underline"
            style={{ color: "var(--vc-text-muted)" }}
          >
            Documentación
          </a>
        </div>
      </footer>
    </div>
  );
}
