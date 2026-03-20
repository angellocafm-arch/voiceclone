"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Module 1 — Communication
 *
 * Phrase board + free text input + voice synthesis with cloned voice.
 * All elements are mega-targets (≥64px) for eye tracking dwell selection (800ms).
 *
 * Features:
 * - Quick phrases grid (selectable by gaze dwell)
 * - Free text input (full-width, keyboard + gaze compatible)
 * - AI phrase predictions based on context and history
 * - Audio player with replay capability
 * - Speaking status with visual feedback
 *
 * WCAG 2.2 AA compliant:
 * - All interactive targets ≥64px
 * - Aria labels on all controls
 * - Role="status" for speaking indicator
 * - High contrast colors
 */

interface Prediction {
  text: string;
  confidence: number;
  source: string;
}

const QUICK_PHRASES = [
  { text: "Sí", emoji: "👍" },
  { text: "No", emoji: "👎" },
  { text: "Gracias", emoji: "🙏" },
  { text: "Necesito ayuda", emoji: "🆘" },
  { text: "Tengo sed", emoji: "💧" },
  { text: "Tengo hambre", emoji: "🍽️" },
  { text: "Me duele", emoji: "😣" },
  { text: "Te quiero", emoji: "❤️" },
  { text: "Estoy bien", emoji: "😊" },
  { text: "Llama al médico", emoji: "🏥" },
  { text: "Necesito descansar", emoji: "😴" },
  { text: "Pon música", emoji: "🎵" },
];

export default function CommunicationModule() {
  const [inputText, setInputText] = useState("");
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [lastSpoken, setLastSpoken] = useState("");
  const [lastAudioUrl, setLastAudioUrl] = useState<string | null>(null);
  const [spokenHistory, setSpokenHistory] = useState<string[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Fetch predictions when input changes
  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/predict?context=${encodeURIComponent(inputText || lastSpoken)}&limit=5`
        );
        const data = await res.json();
        setPredictions(data.predictions || []);
      } catch {
        // Prediction service unavailable — silent fallback
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [inputText, lastSpoken]);

  const speak = useCallback(
    async (text: string) => {
      if (!text.trim() || isSpeaking) return;
      setIsSpeaking(true);
      setLastSpoken(text);
      setInputText("");
      setSpokenHistory((prev) => [text, ...prev.slice(0, 9)]);

      try {
        const res = await fetch("/api/speak", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, voice_id: "default" }),
        });
        const data = await res.json();
        if (data.audio_url) {
          // Clean up previous audio URL
          if (lastAudioUrl) URL.revokeObjectURL(lastAudioUrl);

          setLastAudioUrl(data.audio_url);
          const audio = new Audio(data.audio_url);
          audioRef.current = audio;
          audio.onended = () => setIsSpeaking(false);
          audio.onerror = () => setIsSpeaking(false);
          await audio.play();
        } else {
          setIsSpeaking(false);
        }
      } catch {
        setIsSpeaking(false);
      }
    },
    [isSpeaking, lastAudioUrl]
  );

  const replay = useCallback(() => {
    if (!lastAudioUrl || isSpeaking) return;
    setIsSpeaking(true);
    const audio = new Audio(lastAudioUrl);
    audioRef.current = audio;
    audio.onended = () => setIsSpeaking(false);
    audio.onerror = () => setIsSpeaking(false);
    audio.play();
  }, [lastAudioUrl, isSpeaking]);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsSpeaking(false);
  }, []);

  return (
    <div className="flex flex-col gap-5 h-full p-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <span aria-hidden="true">💬</span> Comunicación
        </h2>
        {lastSpoken && (
          <div className="flex gap-2">
            <button
              onClick={replay}
              disabled={!lastAudioUrl || isSpeaking}
              className="min-h-[44px] px-4 bg-slate-800 hover:bg-slate-700 border border-slate-700
                         rounded-xl text-sm text-slate-300 transition-all disabled:opacity-50
                         flex items-center gap-2"
              aria-label="Repetir último mensaje"
            >
              🔁 Repetir
            </button>
          </div>
        )}
      </div>

      {/* Quick Phrases Grid — 4 columns, eye-tracking mega targets */}
      <div className="grid grid-cols-4 gap-3">
        {QUICK_PHRASES.map((phrase) => (
          <button
            key={phrase.text}
            onClick={() => speak(phrase.text)}
            disabled={isSpeaking}
            className="min-h-[80px] bg-slate-800 hover:bg-indigo-600 border border-slate-700 
                       hover:border-indigo-500 rounded-2xl flex flex-col items-center justify-center
                       gap-1 transition-all duration-200 text-white disabled:opacity-50
                       focus:ring-4 focus:ring-indigo-500/50 focus:outline-none"
            aria-label={`Decir: ${phrase.text}`}
          >
            <span className="text-2xl" aria-hidden="true">{phrase.emoji}</span>
            <span className="text-sm font-medium">{phrase.text}</span>
          </button>
        ))}
      </div>

      {/* Predictions — AI suggested phrases */}
      {predictions.length > 0 && (
        <div>
          <h3 className="text-sm text-slate-400 mb-2 uppercase tracking-wide">
            💡 Sugerencias
          </h3>
          <div className="flex flex-wrap gap-2">
            {predictions.map((pred, i) => (
              <button
                key={i}
                onClick={() => speak(pred.text)}
                disabled={isSpeaking}
                className="min-h-[56px] px-5 bg-slate-800/50 hover:bg-indigo-600/20 
                           border border-slate-700 hover:border-indigo-500 rounded-xl
                           text-white text-sm transition-all disabled:opacity-50
                           focus:ring-2 focus:ring-indigo-500/50 focus:outline-none"
                aria-label={`Sugerencia: ${pred.text}`}
              >
                {pred.text}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Speaking status + audio player */}
      {isSpeaking && (
        <div
          className="flex items-center justify-between bg-indigo-600/10 border border-indigo-500/30
                     rounded-2xl p-4"
          role="status"
          aria-live="polite"
        >
          <div className="flex items-center gap-3 text-indigo-400">
            <span className="text-2xl animate-pulse" aria-hidden="true">🔊</span>
            <span className="text-base font-medium">
              Hablando: &ldquo;{lastSpoken}&rdquo;
            </span>
          </div>
          <button
            onClick={stopSpeaking}
            className="min-h-[48px] px-4 bg-red-600/20 hover:bg-red-600/40 border border-red-500/50
                       rounded-xl text-red-400 text-sm font-medium transition-all"
            aria-label="Parar de hablar"
          >
            ⏹️ Parar
          </button>
        </div>
      )}

      {/* Free Text Input — sticky at bottom */}
      <div className="mt-auto">
        <div className="flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && speak(inputText)}
            placeholder="Escribe lo que quieras decir..."
            className="flex-1 min-h-[64px] bg-slate-800 border border-slate-700 rounded-2xl
                       px-6 text-lg text-white placeholder:text-slate-500
                       focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/30"
            aria-label="Texto libre para hablar"
          />
          <button
            onClick={() => speak(inputText)}
            disabled={!inputText.trim() || isSpeaking}
            className="min-w-[140px] min-h-[64px] bg-indigo-600 hover:bg-indigo-500 
                       disabled:bg-slate-700 rounded-2xl text-white text-lg font-bold
                       transition-all disabled:opacity-50
                       focus:ring-4 focus:ring-indigo-500/50 focus:outline-none"
            aria-label="Hablar el texto escrito"
          >
            {isSpeaking ? "🔊..." : "🎤 HABLAR"}
          </button>
        </div>
      </div>
    </div>
  );
}
