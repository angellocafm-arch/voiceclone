"use client";

import { useState } from "react";

interface IntegrationScreenProps {
  voiceName: string;
  onUseDirect: () => void;
  onBack: () => void;
}

/**
 * Pantalla 5: Integración
 *
 * Conectar la voz clonada con software AAC/eye tracking.
 * Cards clicables para cada integración disponible.
 * Skip siempre disponible — la integración se puede hacer después.
 * WCAG AA: focus, labels, descriptions.
 */

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: "available" | "coming-soon";
  instructions: string;
}

const INTEGRATIONS: Integration[] = [
  {
    id: "system",
    name: "Voz del Sistema",
    description: "Registrar como voz por defecto en macOS o Linux",
    icon: "🖥️",
    status: "available",
    instructions:
      "VoiceClone puede registrar tu voz clonada como una voz del sistema. Así cualquier app que use Text-to-Speech usará TU voz.",
  },
  {
    id: "grid3",
    name: "Grid 3 (Smartbox)",
    description: "Comunicador AAC — añade tu voz como opción de habla",
    icon: "📱",
    status: "coming-soon",
    instructions:
      "Grid 3 permite voces personalizadas via SAPI5. VoiceClone generará un archivo de voz compatible.",
  },
  {
    id: "proloquo",
    name: "Proloquo2Go",
    description: "App AAC de AssistiveWare para iOS",
    icon: "💬",
    status: "coming-soon",
    instructions:
      "Proloquo2Go permite importar voces personalizadas. Exporta tu voz y cárgala desde la app.",
  },
  {
    id: "tobii",
    name: "Tobii Dynavox",
    description: "Control por mirada — usa tu voz con eye tracking",
    icon: "👁️",
    status: "coming-soon",
    instructions:
      "Los dispositivos Tobii Dynavox soportan voces SAPI5 personalizadas. Compatible con Snap Core First y Communicator 5.",
  },
  {
    id: "snap",
    name: "Snap Core First",
    description: "Software AAC de Tobii Dynavox",
    icon: "🔲",
    status: "coming-soon",
    instructions:
      "Snap Core First puede usar voces SAPI5 del sistema. Registra tu voz y selecciónala desde ajustes.",
  },
];

export function IntegrationScreen({
  voiceName,
  onUseDirect,
  onBack,
}: IntegrationScreenProps) {
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const selectedItem = INTEGRATIONS.find((i) => i.id === selectedIntegration);

  const handleSelect = (id: string) => {
    if (selectedIntegration === id) {
      setSelectedIntegration(null);
      setShowDetails(false);
    } else {
      setSelectedIntegration(id);
      setShowDetails(true);
    }
  };

  return (
    <div className="wizard-container" role="region" aria-label="Integración de voz">
      {/* Header */}
      <header className="wizard-header">
        <div className="text-4xl mb-3" role="img" aria-label="Puzzle">🧩</div>
        <h1 className="wizard-title">Integración</h1>
        <p className="wizard-subtitle">
          Conecta <strong>{voiceName}</strong> con tu software.
          Puedes saltarte este paso y hacerlo después.
        </p>
      </header>

      {/* Integration cards */}
      <div
        className="flex flex-col gap-3 mb-6"
        role="listbox"
        aria-label="Integraciones disponibles"
      >
        {INTEGRATIONS.map((integration) => (
          <button
            key={integration.id}
            className="card-option"
            role="option"
            aria-selected={selectedIntegration === integration.id}
            onClick={() => handleSelect(integration.id)}
            style={{
              borderColor:
                selectedIntegration === integration.id
                  ? "var(--vc-accent-blue)"
                  : "var(--vc-border)",
              opacity: integration.status === "coming-soon" ? 0.7 : 1,
            }}
          >
            <div className="card-option-title">
              <span aria-hidden="true">{integration.icon}</span>
              {integration.name}
              {integration.status === "coming-soon" && (
                <span
                  className="text-xs px-2 py-1 rounded-full"
                  style={{
                    background: "var(--vc-bg-input)",
                    color: "var(--vc-accent-orange)",
                    border: "1px solid var(--vc-accent-orange)",
                    fontSize: "12px",
                  }}
                >
                  Próximamente
                </span>
              )}
            </div>
            <p className="card-option-desc">{integration.description}</p>
          </button>
        ))}
      </div>

      {/* Selected integration details */}
      {showDetails && selectedItem && (
        <div className="tip-box mb-6" role="region" aria-label="Detalles de integración">
          <strong>
            {selectedItem.icon} {selectedItem.name}
          </strong>
          <p className="mt-2">{selectedItem.instructions}</p>
          {selectedItem.status === "coming-soon" && (
            <p className="mt-2" style={{ color: "var(--vc-accent-orange)" }}>
              ⏳ Esta integración estará disponible próximamente.
            </p>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-col gap-3">
        <button
          className="btn-primary"
          onClick={onUseDirect}
          aria-label="Usar tu voz directamente sin integración adicional"
        >
          <span aria-hidden="true">✓</span>
          Usar Mi Voz Directamente
        </button>

        {/* Back */}
        <button
          className="btn-danger"
          onClick={onBack}
          aria-label="Volver al paso de personalidad"
        >
          <span aria-hidden="true">←</span>
          Atrás
        </button>
      </div>
    </div>
  );
}
