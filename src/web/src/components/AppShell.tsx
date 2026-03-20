"use client";

import { useState, useCallback, useEffect, useRef } from "react";

/**
 * AppShell — Main application layout with 4-module navigation
 *
 * Designed for eye tracking (gaze gesture) navigation:
 * - Sidebar with mega-targets (≥80px per item)
 * - Active module indicator with high contrast
 * - Gaze dwell activation (configurable, default 800ms)
 * - Keyboard accessible (Tab + Enter/Space)
 * - WCAG 2.2 AA compliant
 *
 * Architecture:
 *   ┌─────────────────────────────────────────────┐
 *   │  Header (voice status + settings)            │
 *   ├──────────┬──────────────────────────────────┤
 *   │          │                                    │
 *   │ Sidebar  │       Active Module Content        │
 *   │  (nav)   │                                    │
 *   │          │                                    │
 *   │  80px+   │                                    │
 *   │ targets  │                                    │
 *   │          │                                    │
 *   └──────────┴──────────────────────────────────┘
 */

export type ModuleId = "communication" | "control" | "productivity" | "channels";

interface ModuleConfig {
  id: ModuleId;
  label: string;
  emoji: string;
  shortLabel: string;
  color: string;
  colorHover: string;
  description: string;
}

export const MODULES: ModuleConfig[] = [
  {
    id: "communication",
    label: "Comunicación",
    emoji: "💬",
    shortLabel: "Hablar",
    color: "rgb(99, 102, 241)",    // indigo
    colorHover: "rgb(129, 140, 248)",
    description: "Frases rápidas, texto libre y voz clonada",
  },
  {
    id: "control",
    label: "Control del Ordenador",
    emoji: "🖥️",
    shortLabel: "Control",
    color: "rgb(16, 185, 129)",    // emerald
    colorHover: "rgb(52, 211, 153)",
    description: "Controla tu ordenador con instrucciones naturales",
  },
  {
    id: "productivity",
    label: "Productividad",
    emoji: "📝",
    shortLabel: "Producir",
    color: "rgb(245, 158, 11)",    // amber
    colorHover: "rgb(251, 191, 36)",
    description: "Dictado, lectura en voz alta y recordatorios",
  },
  {
    id: "channels",
    label: "Mensajería",
    emoji: "📱",
    shortLabel: "Canales",
    color: "rgb(139, 92, 246)",    // violet
    colorHover: "rgb(167, 139, 250)",
    description: "Telegram, WhatsApp, Signal — con tu voz",
  },
];

interface AppShellProps {
  /** Currently active module */
  activeModule: ModuleId;
  /** Module change handler */
  onModuleChange: (module: ModuleId) => void;
  /** Voice name to display in header */
  voiceName: string | null;
  /** Whether the API/backend is available */
  apiAvailable: boolean;
  /** Whether gaze tracking is active */
  gazeActive: boolean;
  /** Callback to toggle gaze tracking */
  onToggleGaze: () => void;
  /** Callback to open settings */
  onOpenSettings: () => void;
  /** Children: the active module content */
  children: React.ReactNode;
}

export default function AppShell({
  activeModule,
  onModuleChange,
  voiceName,
  apiAvailable,
  gazeActive,
  onToggleGaze,
  onOpenSettings,
  children,
}: AppShellProps) {
  const [dwellTarget, setDwellTarget] = useState<ModuleId | null>(null);
  const [dwellProgress, setDwellProgress] = useState(0);
  const dwellTimerRef = useRef<NodeJS.Timeout | null>(null);
  const DWELL_TIME_MS = 800;
  const DWELL_TICK_MS = 50;

  /**
   * Gaze dwell activation: when user's gaze hovers over a nav item
   * for DWELL_TIME_MS, it activates. Progress indicator shows visually.
   */
  const startDwell = useCallback(
    (moduleId: ModuleId) => {
      if (!gazeActive || moduleId === activeModule) return;
      setDwellTarget(moduleId);
      setDwellProgress(0);

      let elapsed = 0;
      dwellTimerRef.current = setInterval(() => {
        elapsed += DWELL_TICK_MS;
        const progress = Math.min(elapsed / DWELL_TIME_MS, 1);
        setDwellProgress(progress);

        if (progress >= 1) {
          if (dwellTimerRef.current) clearInterval(dwellTimerRef.current);
          onModuleChange(moduleId);
          setDwellTarget(null);
          setDwellProgress(0);
        }
      }, DWELL_TICK_MS);
    },
    [gazeActive, activeModule, onModuleChange]
  );

  const cancelDwell = useCallback(() => {
    if (dwellTimerRef.current) {
      clearInterval(dwellTimerRef.current);
      dwellTimerRef.current = null;
    }
    setDwellTarget(null);
    setDwellProgress(0);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (dwellTimerRef.current) clearInterval(dwellTimerRef.current);
    };
  }, []);

  const activeModuleConfig = MODULES.find((m) => m.id === activeModule)!;

  return (
    <div className="app-shell" role="application" aria-label="VoiceClone">
      {/* ═══ Header ═══ */}
      <header className="app-header" role="banner">
        <div className="app-header-left">
          <span className="app-logo" aria-hidden="true">🎤</span>
          <h1 className="app-title">VoiceClone</h1>
          {voiceName && (
            <span className="app-voice-badge">
              <span
                className={`status-dot ${apiAvailable ? "status-dot-active" : "status-dot-inactive"}`}
                aria-hidden="true"
              />
              {voiceName}
            </span>
          )}
        </div>
        <div className="app-header-right">
          <button
            className="header-btn"
            onClick={onToggleGaze}
            aria-label={gazeActive ? "Desactivar eye tracking" : "Activar eye tracking"}
            aria-pressed={gazeActive}
            title={gazeActive ? "Eye tracking activo" : "Eye tracking inactivo"}
          >
            <span aria-hidden="true">{gazeActive ? "👁️" : "👁️‍🗨️"}</span>
            <span className="header-btn-label">
              {gazeActive ? "Mirada ON" : "Mirada OFF"}
            </span>
          </button>
          <button
            className="header-btn"
            onClick={onOpenSettings}
            aria-label="Abrir configuración"
            title="Configuración"
          >
            <span aria-hidden="true">⚙️</span>
          </button>
        </div>
      </header>

      <div className="app-body">
        {/* ═══ Sidebar Navigation ═══ */}
        <nav
          className="app-sidebar"
          role="navigation"
          aria-label="Módulos principales"
        >
          <ul className="sidebar-list" role="list">
            {MODULES.map((mod) => {
              const isActive = mod.id === activeModule;
              const isDwelling = dwellTarget === mod.id;

              return (
                <li key={mod.id} role="listitem">
                  <button
                    className={`sidebar-item ${isActive ? "sidebar-item-active" : ""}`}
                    onClick={() => onModuleChange(mod.id)}
                    onMouseEnter={() => startDwell(mod.id)}
                    onMouseLeave={cancelDwell}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={`${mod.label}: ${mod.description}`}
                    style={{
                      "--module-color": mod.color,
                      "--module-color-hover": mod.colorHover,
                    } as React.CSSProperties}
                  >
                    {/* Dwell progress indicator */}
                    {isDwelling && (
                      <div
                        className="dwell-progress"
                        style={{ width: `${dwellProgress * 100}%` }}
                        role="progressbar"
                        aria-valuenow={Math.round(dwellProgress * 100)}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-label="Progreso de selección por mirada"
                      />
                    )}

                    {/* Active indicator */}
                    {isActive && (
                      <div
                        className="sidebar-active-bar"
                        style={{ background: mod.color }}
                      />
                    )}

                    <span className="sidebar-emoji" aria-hidden="true">
                      {mod.emoji}
                    </span>
                    <div className="sidebar-text">
                      <span className="sidebar-label">{mod.label}</span>
                      <span className="sidebar-desc">{mod.description}</span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>

          {/* Connection status at bottom of sidebar */}
          <div className="sidebar-footer">
            <div className={`connection-status ${apiAvailable ? "connected" : "disconnected"}`}>
              <span
                className={`status-dot ${apiAvailable ? "status-dot-active" : "status-dot-inactive"}`}
                aria-hidden="true"
              />
              <span>{apiAvailable ? "Motor activo" : "Motor desconectado"}</span>
            </div>
          </div>
        </nav>

        {/* ═══ Main Content ═══ */}
        <main
          className="app-main"
          role="main"
          aria-label={`Módulo: ${activeModuleConfig.label}`}
          style={{
            "--active-module-color": activeModuleConfig.color,
          } as React.CSSProperties}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
