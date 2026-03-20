"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";

interface CloneScreenProps {
  onDone: (voiceId: string, voiceName: string) => void;
  onBack: () => void;
}

export function CloneScreen({ onDone, onBack }: CloneScreenProps) {
  const [step, setStep] = useState<"choice" | "record" | "uploading" | "done">(
    "choice"
  );
  const [voiceName, setVoiceName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/wav" });
        await cloneVoice(audioBlob);
        chunksRef.current = [];
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setStep("record");
    } catch (error) {
      alert("No se puede acceder al micrófono: " + String(error));
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
    setStep("uploading");
  };

  const cloneVoice = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "voice.wav");
      formData.append("name", voiceName || "Mi Voz");

      const result = await api.cloneVoice(formData);
      onDone(result.id, result.name);
      setStep("done");
    } catch (error) {
      alert("Error al clonar voz: " + String(error));
      setStep("choice");
    }
  };

  return (
    <div className="screen-container">
      <h1 className="screen-title">Clona Tu Voz</h1>

      {step === "choice" && (
        <div className="wizard-step">
          <p className="screen-description">
            Graba 2-3 minutos de tu voz o sube una grabación anterior.
          </p>

          <div className="button-group">
            <button
              className="btn btn-primary mega-target"
              onClick={startRecording}
            >
              🎤 Grabar Ahora
            </button>
            <button className="btn btn-secondary">📁 Subir Archivo</button>
          </div>

          <button
            className="btn btn-tertiary float-left"
            onClick={onBack}
          >
            ← Atrás
          </button>
        </div>
      )}

      {step === "record" && (
        <div className="wizard-step recording-active">
          <p className="recording-indicator">⏺️ Grabando...</p>
          <p className="timer">0:00</p>
          <p className="guidance">Lee en voz alta los textos que aparecen.</p>

          <button
            className="btn btn-danger mega-target"
            onClick={stopRecording}
          >
            ⏹️ Detener Grabación
          </button>
        </div>
      )}

      {step === "uploading" && (
        <div className="wizard-step">
          <div className="spinner"></div>
          <p>Procesando tu voz...</p>
          <p className="text-muted">Esto puede tomar 1-2 minutos</p>
        </div>
      )}

      {step === "done" && (
        <div className="wizard-step success">
          <div className="success-icon">✅</div>
          <p>¡Tu voz está lista!</p>
          <p className="text-muted">{voiceName || "Mi Voz"}</p>
        </div>
      )}
    </div>
  );
}
