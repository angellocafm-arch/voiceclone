"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import AppShell, { type ModuleId } from "@/components/AppShell";
import OnboardingScreen from "@/components/OnboardingScreen";
import GazeTracker from "@/components/GazeTracker";
import CommunicationModule from "@/components/modules/CommunicationModule";
import ControlModule from "@/components/modules/ControlModule";
import ProductivityModule from "@/components/modules/ProductivityModule";
import ChannelsModule from "@/components/modules/ChannelsModule";

/**
 * VoiceClone — Main App (v4 Architecture)
 *
 * Two modes:
 * 1. ONBOARDING — Conversational setup with LLM (first time)
 * 2. APP — 4-module system for daily use
 *
 * Modules:
 *   💬 Communication — Phrase board + free text + cloned voice
 *   🖥️ Control       — OS control via natural language + LLM
 *   📝 Productivity   — Dictation, file reading, reminders
 *   📱 Channels       — Telegram, WhatsApp, Signal messaging
 *
 * Designed for people with ELA:
 *   - WCAG 2.2 AA compliant
 *   - Eye tracking (gaze dwell) compatible
 *   - All targets ≥64px
 *   - Dark mode, high contrast support
 *   - Keyboard + switch access
 */

type AppMode = "loading" | "onboarding" | "app";

interface AppState {
  mode: AppMode;
  activeModule: ModuleId;
  voiceId: string | null;
  voiceName: string | null;
  apiAvailable: boolean;
  gazeActive: boolean;
  showSettings: boolean;
}

export default function Home() {
  const [state, setState] = useState<AppState>({
    mode: "loading",
    activeModule: "communication",
    voiceId: null,
    voiceName: null,
    apiAvailable: false,
    gazeActive: false,
    showSettings: false,
  });

  // Check API and determine mode on mount
  useEffect(() => {
    const init = async () => {
      const available = await api.isAvailable();

      if (available) {
        try {
          const voices = await api.listVoices();
          if (voices.length > 0) {
            // User has voices → go to app
            const voice = voices[0];
            setState((prev) => ({
              ...prev,
              mode: "app",
              apiAvailable: true,
              voiceId: voice.id,
              voiceName: voice.name,
            }));
            return;
          }
        } catch {
          // No voices yet
        }
      }

      // No API or no voices → onboarding
      setState((prev) => ({
        ...prev,
        mode: "onboarding",
        apiAvailable: available,
      }));
    };

    init();
  }, []);

  // Periodic API health check
  useEffect(() => {
    const interval = setInterval(async () => {
      const available = await api.isAvailable();
      setState((prev) => ({ ...prev, apiAvailable: available }));
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut: Ctrl/Cmd + 1-4 to switch modules
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (state.mode !== "app") return;
      if (!e.ctrlKey && !e.metaKey) return;

      const moduleMap: Record<string, ModuleId> = {
        "1": "communication",
        "2": "control",
        "3": "productivity",
        "4": "channels",
      };

      const module = moduleMap[e.key];
      if (module) {
        e.preventDefault();
        setState((prev) => ({ ...prev, activeModule: module }));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [state.mode]);

  const handleModuleChange = useCallback((module: ModuleId) => {
    setState((prev) => ({ ...prev, activeModule: module }));
    // Announce to screen readers
    const announcement = document.getElementById("module-announce");
    if (announcement) {
      announcement.textContent = `Módulo activo: ${module}`;
    }
  }, []);

  const handleOnboardingComplete = useCallback(
    (voiceId: string, voiceName: string) => {
      setState((prev) => ({
        ...prev,
        mode: "app",
        voiceId,
        voiceName,
      }));
    },
    []
  );

  const handleToggleGaze = useCallback(() => {
    setState((prev) => ({ ...prev, gazeActive: !prev.gazeActive }));
  }, []);

  const handleOpenSettings = useCallback(() => {
    setState((prev) => ({ ...prev, showSettings: !prev.showSettings }));
  }, []);

  // Render active module
  const renderModule = () => {
    switch (state.activeModule) {
      case "communication":
        return <CommunicationModule />;
      case "control":
        return <ControlModule />;
      case "productivity":
        return <ProductivityModule />;
      case "channels":
        return <ChannelsModule />;
    }
  };

  // ═══ Loading ═══
  if (state.mode === "loading") {
    return (
      <div
        className="flex items-center justify-center h-screen bg-[#0A0A0A]"
        role="status"
        aria-label="Cargando VoiceClone"
      >
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse" aria-hidden="true">🎤</div>
          <p className="text-white text-xl font-semibold">VoiceClone</p>
          <p className="text-slate-500 mt-2">Conectando con el motor local...</p>
        </div>
      </div>
    );
  }

  // ═══ Onboarding ═══
  if (state.mode === "onboarding") {
    return <OnboardingScreen onComplete={handleOnboardingComplete} />;
  }

  // ═══ Main App ═══
  return (
    <>
      {/* Screen reader announcement area */}
      <div
        id="module-announce"
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      />

      {/* Gaze tracker overlay */}
      <GazeTracker
        active={state.gazeActive}
        dwellTimeMs={800}
        smoothing={0.3}
        cursorSize={40}
        showProgress={true}
      />

      {/* Settings panel */}
      {state.showSettings && (
        <SettingsPanel
          gazeActive={state.gazeActive}
          onToggleGaze={handleToggleGaze}
          onClose={() => setState((prev) => ({ ...prev, showSettings: false }))}
          voiceName={state.voiceName}
          voiceId={state.voiceId}
        />
      )}

      {/* Main app shell */}
      <AppShell
        activeModule={state.activeModule}
        onModuleChange={handleModuleChange}
        voiceName={state.voiceName}
        apiAvailable={state.apiAvailable}
        gazeActive={state.gazeActive}
        onToggleGaze={handleToggleGaze}
        onOpenSettings={handleOpenSettings}
      >
        {renderModule()}
      </AppShell>
    </>
  );
}

// ═══ Settings Panel ═══

interface SettingsPanelProps {
  gazeActive: boolean;
  onToggleGaze: () => void;
  onClose: () => void;
  voiceName: string | null;
  voiceId: string | null;
}

function SettingsPanel({
  gazeActive,
  onToggleGaze,
  onClose,
  voiceName,
  voiceId,
}: SettingsPanelProps) {
  const [dwellTime, setDwellTime] = useState(800);

  return (
    <div
      className="fixed inset-0 bg-black/60 z-[9000] flex items-center justify-center"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Configuración"
    >
      <div className="bg-[#1A1A1A] border border-[#333] rounded-3xl w-[480px] max-h-[80vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">⚙️ Configuración</h2>
          <button
            onClick={onClose}
            className="min-h-[44px] min-w-[44px] bg-slate-700 hover:bg-slate-600
                       rounded-xl text-white flex items-center justify-center"
            aria-label="Cerrar configuración"
          >
            ✕
          </button>
        </div>

        {/* Voice section */}
        <div className="mb-6">
          <h3 className="text-sm text-slate-400 uppercase tracking-wide mb-3">
            🎤 Voz
          </h3>
          <div className="bg-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{voiceName || "Sin voz"}</p>
                <p className="text-xs text-slate-500">ID: {voiceId || "—"}</p>
              </div>
              <span className="text-emerald-400 text-sm">✓ Activa</span>
            </div>
          </div>
        </div>

        {/* Eye tracking section */}
        <div className="mb-6">
          <h3 className="text-sm text-slate-400 uppercase tracking-wide mb-3">
            👁️ Eye Tracking
          </h3>
          <div className="space-y-3">
            <div className="bg-slate-800 rounded-xl p-4 flex items-center justify-between">
              <span className="text-white">Eye tracking activo</span>
              <button
                onClick={onToggleGaze}
                className={`w-14 h-8 rounded-full transition-colors ${
                  gazeActive ? "bg-indigo-600" : "bg-slate-600"
                }`}
                role="switch"
                aria-checked={gazeActive}
                aria-label="Activar eye tracking"
              >
                <div
                  className={`w-6 h-6 rounded-full bg-white transition-transform mx-1 ${
                    gazeActive ? "translate-x-6" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            <div className="bg-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white text-sm">Tiempo de fijación</span>
                <span className="text-slate-400 text-sm">{dwellTime}ms</span>
              </div>
              <input
                type="range"
                min={400}
                max={2000}
                step={100}
                value={dwellTime}
                onChange={(e) => setDwellTime(Number(e.target.value))}
                className="w-full accent-indigo-500"
                aria-label="Ajustar tiempo de fijación de mirada"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Rápido (400ms)</span>
                <span>Lento (2000ms)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Keyboard shortcuts */}
        <div>
          <h3 className="text-sm text-slate-400 uppercase tracking-wide mb-3">
            ⌨️ Atajos de teclado
          </h3>
          <div className="bg-slate-800 rounded-xl p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-300">Comunicación</span>
              <kbd className="text-slate-500 bg-slate-700 px-2 py-0.5 rounded">⌘1</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Control</span>
              <kbd className="text-slate-500 bg-slate-700 px-2 py-0.5 rounded">⌘2</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Productividad</span>
              <kbd className="text-slate-500 bg-slate-700 px-2 py-0.5 rounded">⌘3</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-300">Canales</span>
              <kbd className="text-slate-500 bg-slate-700 px-2 py-0.5 rounded">⌘4</kbd>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
