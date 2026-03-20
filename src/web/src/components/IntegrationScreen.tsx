"use client";

import { useState } from "react";

interface IntegrationScreenProps {
  voiceName: string;
  onDone: () => void;
  onBack: () => void;
}

export function IntegrationScreen({
  voiceName,
  onDone,
  onBack,
}: IntegrationScreenProps) {
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(
    null
  );

  const integrations = [
    {
      id: "system",
      name: "Voz del Sistema",
      description: "Usa como voz por defecto en macOS/Linux",
      icon: "🖥️",
    },
    {
      id: "grid3",
      name: "Grid 3 (AAC)",
      description: "Integración con Grid 3 de Smartbox",
      icon: "📱",
    },
    {
      id: "proloquo",
      name: "Proloquo2Go",
      description: "Aplicación AAC de AssistiveWare",
      icon: "💬",
    },
    {
      id: "tobii",
      name: "Control por Mirada (Tobii)",
      description: "Compatible con Tobii eye tracking",
      icon: "👁️",
    },
  ];

  return (
    <div className="screen-container">
      <h1 className="screen-title">Integración</h1>

      <div className="wizard-step">
        <p className="screen-description">
          Conecta tu voz clonada con tu software. Puedes saltarte este paso ahora.
        </p>

        <div className="integration-grid">
          {integrations.map((integration) => (
            <button
              key={integration.id}
              className={`integration-card ${
                selectedIntegration === integration.id ? "selected" : ""
              }`}
              onClick={() => setSelectedIntegration(integration.id)}
            >
              <div className="integration-icon">{integration.icon}</div>
              <h3>{integration.name}</h3>
              <p>{integration.description}</p>
            </button>
          ))}
        </div>

        <div className="button-group">
          <button className="btn btn-secondary" onClick={onDone}>
            ⏭️ Saltar
          </button>
          <button
            className="btn btn-primary mega-target"
            onClick={onDone}
            disabled={!selectedIntegration}
          >
            ✓ Continuar
          </button>
        </div>

        <button className="btn btn-tertiary float-left" onClick={onBack}>
          ← Atrás
        </button>
      </div>
    </div>
  );
}
