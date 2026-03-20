"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface DashboardScreenProps {
  voiceId: string;
  voiceName: string;
}

export function DashboardScreen({ voiceId, voiceName }: DashboardScreenProps) {
  const [synthesizing, setSynthesizing] = useState(false);
  const [testText, setTestText] = useState("Hola, esto es una prueba de mi voz clonada.");
  const [stats, setStats] = useState({
    synthesisCount: 0,
    lastUsed: new Date().toISOString(),
  });

  const testVoice = async () => {
    setSynthesizing(true);
    try {
      const audio = await api.synthesize(testText, voiceId);
      // Play audio
      const url = URL.createObjectURL(new Blob([audio], { type: "audio/wav" }));
      const audioElement = new Audio(url);
      audioElement.play();
    } catch (error) {
      alert("Error: " + String(error));
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div className="screen-container">
      <h1 className="screen-title">Tu Voz Está Lista</h1>

      <div className="dashboard-container">
        <div className="voice-card">
          <div className="voice-icon">🎤</div>
          <h2>{voiceName}</h2>
          <p className="voice-status">✓ Lista para usar</p>
        </div>

        <div className="dashboard-section">
          <h3>Prueba Tu Voz</h3>
          <textarea
            className="input-field textarea"
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            placeholder="Escribe algo para probar..."
          />
          <button
            className="btn btn-primary mega-target"
            onClick={testVoice}
            disabled={synthesizing}
          >
            {synthesizing ? "🔄 Sintetizando..." : "▶️ Escuchar"}
          </button>
        </div>

        <div className="dashboard-section">
          <h3>Estadísticas</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.synthesisCount}</div>
              <div className="stat-label">Síntesis realizadas</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">100%</div>
              <div className="stat-label">Privacidad local</div>
            </div>
          </div>
        </div>

        <div className="dashboard-section">
          <h3>Próximos Pasos</h3>
          <ul className="steps-list">
            <li>✓ Voz clonada</li>
            <li>✓ Perfil de personalidad</li>
            <li>Integrar con AAC (Grid 3, Proloquo2Go)</li>
            <li>Configurar eye tracking (Tobii)</li>
            <li>Compartir voz con familia</li>
          </ul>
        </div>

        <div className="dashboard-section help">
          <h3>¿Necesitas Ayuda?</h3>
          <p>
            VoiceClone está diseñado para ser accesible. Si tienes problemas:
          </p>
          <ul>
            <li>Control por teclado: Tab para navegar, Enter para confirmar</li>
            <li>Control por mirada: Mira durante 1-2 segundos para activar</li>
            <li>Switch access: 1-2 botones para navegación completa</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
