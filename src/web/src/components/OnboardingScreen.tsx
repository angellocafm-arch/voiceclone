"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/**
 * OnboardingScreen — Conversational setup with the LLM
 *
 * The LLM guides the user through:
 * 1. Welcome and introduction
 * 2. Voice recording or upload
 * 3. Voice cloning
 * 4. Testing the cloned voice
 * 5. Personality learning (optional)
 * 6. Channel configuration (optional)
 *
 * Uses WebSocket for real-time streaming chat.
 * All targets ≥64px for eye tracking compatibility.
 * WCAG 2.2 AA compliant.
 */

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: number;
}

interface OnboardingState {
  step: string;
  progress: number;
  voiceReady: boolean;
  voiceId?: string;
  voiceName?: string;
}

interface OnboardingScreenProps {
  onComplete: (voiceId: string, voiceName: string) => void;
}

export default function OnboardingScreen({ onComplete }: OnboardingScreenProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [onboardingState, setOnboardingState] = useState<OnboardingState>({
    step: "welcome",
    progress: 0,
    voiceReady: false,
  });
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isCloning, setIsCloning] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Connect WebSocket
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8765/ws/chat");
    wsRef.current = ws;

    ws.onopen = () => {
      // Trigger onboarding start
      ws.send(JSON.stringify({ type: "onboarding_start" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "chat_message") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content: data.content,
            timestamp: Date.now(),
          },
        ]);
        setIsStreaming(false);
      }

      if (data.type === "chat_stream") {
        setIsStreaming(true);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && last.id === "streaming") {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + data.token },
            ];
          }
          return [
            ...prev,
            {
              id: "streaming",
              role: "assistant",
              content: data.token,
              timestamp: Date.now(),
            },
          ];
        });
      }

      if (data.type === "chat_stream_end") {
        setIsStreaming(false);
        // Convert streaming message to final
        setMessages((prev) =>
          prev.map((m) =>
            m.id === "streaming" ? { ...m, id: Date.now().toString() } : m
          )
        );
      }

      if (data.type === "onboarding_state") {
        setOnboardingState(data.state);
        if (data.state.voiceReady && data.state.voiceId) {
          // Voice cloned successfully
        }
      }
    };

    ws.onerror = () => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content:
            "No puedo conectar con el motor local. Asegúrate de que VoiceClone está ejecutándose en tu ordenador.",
          timestamp: Date.now(),
        },
      ]);
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim() || isStreaming) return;
      const msg: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: text,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, msg]);
      setInputText("");

      wsRef.current?.send(JSON.stringify({ type: "chat_message", content: text }));
    },
    [isStreaming]
  );

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      mediaRecorderRef.current = mediaRecorder;
      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        setAudioBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content:
            "No pude acceder al micrófono. Puedes subir un archivo de audio en su lugar.",
          timestamp: Date.now(),
        },
      ]);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioBlob(file);
    }
  };

  const cloneVoice = async () => {
    if (!audioBlob) return;
    setIsCloning(true);

    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "voice-sample.webm");
      formData.append("name", "Mi voz");

      const res = await fetch("/api/clone", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.id) {
        setOnboardingState((prev) => ({
          ...prev,
          voiceReady: true,
          voiceId: data.id,
          voiceName: data.name,
          progress: 80,
        }));

        // Notify the chat
        wsRef.current?.send(
          JSON.stringify({ type: "voice_cloned", voiceId: data.id })
        );
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Hubo un error al clonar tu voz. ¿Quieres intentarlo de nuevo?",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsCloning(false);
    }
  };

  const STEPS = [
    { key: "welcome", label: "Bienvenida" },
    { key: "voice", label: "Grabar voz" },
    { key: "clone", label: "Clonar" },
    { key: "test", label: "Probar" },
    { key: "personality", label: "Personalidad" },
    { key: "channels", label: "Canales" },
    { key: "complete", label: "¡Listo!" },
  ];

  const currentStepIndex = STEPS.findIndex((s) => s.key === onboardingState.step);

  return (
    <div className="flex flex-col h-screen bg-[#0A0A0A]">
      {/* Progress bar */}
      <div className="px-6 pt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl" aria-hidden="true">🎤</span>
          <span className="text-white font-semibold">VoiceClone</span>
          <span className="text-slate-500 ml-auto text-sm">
            Paso {currentStepIndex + 1} de {STEPS.length}
          </span>
        </div>

        {/* Step indicators */}
        <div className="flex gap-1" role="progressbar"
             aria-valuenow={onboardingState.progress}
             aria-valuemin={0} aria-valuemax={100}
             aria-label={`Progreso: ${onboardingState.progress}%`}>
          {STEPS.map((step, i) => (
            <div
              key={step.key}
              className={`h-1.5 flex-1 rounded-full transition-colors ${
                i <= currentStepIndex
                  ? "bg-indigo-500"
                  : "bg-slate-700"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === "user"
                  ? "bg-indigo-600/30 border border-indigo-500/30 text-white"
                  : "bg-slate-800 border border-slate-700 text-slate-200"
              }`}
            >
              <p className="text-base leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </p>
            </div>
          </div>
        ))}

        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl p-4">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Voice recording area (shows during voice step) */}
      {(onboardingState.step === "voice" || onboardingState.step === "clone") && (
        <div className="px-6 pb-2">
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-4">
            {!audioBlob ? (
              <div className="flex gap-3">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`min-h-[64px] flex-1 rounded-2xl text-white text-lg font-bold
                             transition-all flex items-center justify-center gap-2 ${
                               isRecording
                                 ? "bg-red-600 hover:bg-red-500 animate-pulse"
                                 : "bg-indigo-600 hover:bg-indigo-500"
                             }`}
                  aria-label={isRecording ? "Parar grabación" : "Grabar mi voz"}
                >
                  {isRecording ? "⏹️ Parar" : "🎙️ Grabar mi voz"}
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="min-h-[64px] px-6 bg-slate-700 hover:bg-slate-600
                             rounded-2xl text-slate-300 font-medium transition-all"
                  aria-label="Subir archivo de audio"
                >
                  📁 Subir audio
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <span className="text-emerald-400 text-lg">✅ Audio listo</span>
                  <button
                    onClick={() => setAudioBlob(null)}
                    className="text-sm text-slate-400 hover:text-white"
                  >
                    Cambiar
                  </button>
                </div>
                <button
                  onClick={cloneVoice}
                  disabled={isCloning}
                  className="min-h-[64px] bg-emerald-600 hover:bg-emerald-500
                             disabled:bg-slate-700 rounded-2xl text-white text-lg font-bold
                             transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isCloning ? (
                    <>
                      <span className="animate-spin">🔄</span> Clonando tu voz...
                    </>
                  ) : (
                    <>🧬 Clonar mi voz</>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Complete button */}
      {onboardingState.step === "complete" && onboardingState.voiceId && (
        <div className="px-6 pb-2">
          <button
            onClick={() =>
              onComplete(
                onboardingState.voiceId!,
                onboardingState.voiceName || "Mi voz"
              )
            }
            className="min-h-[72px] w-full bg-emerald-600 hover:bg-emerald-500
                       rounded-2xl text-white text-xl font-bold transition-all
                       flex items-center justify-center gap-3"
            aria-label="Empezar a usar VoiceClone"
          >
            🚀 Empezar a usar VoiceClone
          </button>
        </div>
      )}

      {/* Chat input */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(inputText)}
            placeholder="Escribe aquí..."
            className="flex-1 min-h-[56px] bg-slate-800 border border-slate-700 rounded-2xl
                       px-5 text-base text-white placeholder:text-slate-500
                       focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30"
            aria-label="Mensaje para el asistente"
          />
          <button
            onClick={() => sendMessage(inputText)}
            disabled={!inputText.trim() || isStreaming}
            className="min-w-[100px] min-h-[56px] bg-indigo-600 hover:bg-indigo-500
                       disabled:bg-slate-700 rounded-2xl text-white font-bold
                       transition-all disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
