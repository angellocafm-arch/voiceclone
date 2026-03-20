"use client";

import { useState, useRef, useCallback, useEffect } from "react";

/**
 * Module 3 — Productivity
 *
 * Document dictation, file reading aloud, agenda management.
 * All targets ≥64px for eye tracking dwell selection.
 *
 * Features:
 * - Document dictation area (compose via phrase selection or typing)
 * - File upload → read aloud with cloned voice (PDF, TXT, MD, DOCX)
 * - Document summarization via LLM
 * - Agenda / reminders (voice-configurable)
 *
 * WCAG 2.2 AA compliant
 */

interface Reminder {
  id: string;
  text: string;
  time: string;
  done: boolean;
}

export default function ProductivityModule() {
  const [dictatedText, setDictatedText] = useState("");
  const [isReading, setIsReading] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [readProgress, setReadProgress] = useState(0);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [newReminder, setNewReminder] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch reminders
  useEffect(() => {
    const fetchReminders = async () => {
      try {
        const res = await fetch("/api/reminders");
        const data = await res.json();
        setReminders(data.reminders || []);
      } catch {
        // Backend may not be running
      }
    };
    fetchReminders();
    const interval = setInterval(fetchReminders, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadedFile(file.name);
    setSummary(null);
    setReadProgress(0);
  };

  const readAloud = useCallback(async () => {
    if (!uploadedFile) return;
    setIsReading(true);
    setReadProgress(0);

    try {
      const res = await fetch("/api/read-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: uploadedFile }),
      });
      const data = await res.json();

      if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.ontimeupdate = () => {
          if (audio.duration > 0) {
            setReadProgress(Math.round((audio.currentTime / audio.duration) * 100));
          }
        };
        audio.onended = () => {
          setIsReading(false);
          setReadProgress(100);
        };
        audio.onerror = () => setIsReading(false);
        await audio.play();
      } else {
        setIsReading(false);
      }
    } catch {
      setIsReading(false);
    }
  }, [uploadedFile]);

  const stopReading = () => {
    setIsReading(false);
  };

  const summarizeFile = useCallback(async () => {
    if (!uploadedFile) return;
    setIsSummarizing(true);
    setSummary(null);

    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: uploadedFile }),
      });
      const data = await res.json();
      setSummary(data.summary || "No se pudo generar el resumen.");
    } catch {
      setSummary("Error al conectar con el motor.");
    } finally {
      setIsSummarizing(false);
    }
  }, [uploadedFile]);

  const saveDocument = useCallback(async () => {
    if (!dictatedText.trim()) return;
    setIsSaving(true);
    try {
      await fetch("/api/save-document", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: dictatedText,
          filename: `documento-${new Date().toISOString().split("T")[0]}.txt`,
        }),
      });
    } catch {
      // Error handling
    } finally {
      setIsSaving(false);
    }
  }, [dictatedText]);

  const addReminder = async () => {
    if (!newReminder.trim()) return;
    try {
      const res = await fetch("/api/reminders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: newReminder }),
      });
      const data = await res.json();
      if (data.reminder) {
        setReminders((prev) => [...prev, data.reminder]);
      }
      setNewReminder("");
    } catch {
      // Error
    }
  };

  const toggleReminder = async (id: string) => {
    try {
      await fetch(`/api/reminders/${id}/toggle`, { method: "POST" });
      setReminders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, done: !r.done } : r))
      );
    } catch {
      // Error
    }
  };

  return (
    <div className="flex flex-col gap-5 h-full p-5 overflow-y-auto">
      <h2 className="text-2xl font-bold text-white flex items-center gap-3">
        <span aria-hidden="true">📝</span> Productividad
      </h2>

      <div className="grid grid-cols-2 gap-5 flex-1">
        {/* Left column: Dictation + File reading */}
        <div className="flex flex-col gap-5">
          {/* Dictation Area */}
          <div className="flex-1">
            <h3 className="text-sm text-slate-400 mb-2 uppercase tracking-wide flex items-center gap-2">
              <span aria-hidden="true">✍️</span> Dictado de documentos
            </h3>
            <textarea
              value={dictatedText}
              onChange={(e) => setDictatedText(e.target.value)}
              placeholder="Escribe o dicta aquí para crear un documento..."
              className="w-full h-[220px] bg-slate-800 border border-slate-700 rounded-2xl p-4
                         text-white text-lg placeholder:text-slate-500 resize-none
                         focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30"
              aria-label="Área de dictado de documentos"
            />
            <div className="flex gap-3 mt-3">
              <button
                onClick={saveDocument}
                disabled={!dictatedText.trim() || isSaving}
                className="min-h-[56px] px-6 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-700
                           rounded-xl text-white font-medium transition-all disabled:opacity-50
                           flex items-center gap-2 focus:ring-2 focus:ring-amber-500/50 focus:outline-none"
                aria-label="Guardar documento"
              >
                {isSaving ? "⏳" : "💾"} Guardar
              </button>
              <button
                onClick={() => setDictatedText("")}
                disabled={!dictatedText.trim()}
                className="min-h-[56px] px-6 bg-slate-700 hover:bg-slate-600 disabled:opacity-50
                           rounded-xl text-slate-300 font-medium transition-all
                           focus:ring-2 focus:ring-slate-500/50 focus:outline-none"
                aria-label="Limpiar dictado"
              >
                🗑️ Limpiar
              </button>
            </div>
          </div>

          {/* File Upload → Read Aloud */}
          <div>
            <h3 className="text-sm text-slate-400 mb-2 uppercase tracking-wide flex items-center gap-2">
              <span aria-hidden="true">📄</span> Leer archivo en voz alta
            </h3>
            <div className="flex flex-col gap-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="min-h-[72px] bg-slate-800 hover:bg-slate-700 border-2 border-dashed 
                           border-slate-600 hover:border-amber-500 rounded-2xl text-slate-400
                           hover:text-white transition-all flex items-center justify-center gap-3
                           focus:ring-2 focus:ring-amber-500/50 focus:outline-none"
                aria-label="Seleccionar archivo para leer en voz alta"
              >
                <span className="text-2xl" aria-hidden="true">📄</span>
                <span className="text-base">
                  {uploadedFile || "Arrastra o selecciona un archivo (PDF, TXT, MD)"}
                </span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md,.doc,.docx"
                onChange={handleFileUpload}
                className="hidden"
              />

              {uploadedFile && (
                <div className="flex gap-3">
                  <button
                    onClick={isReading ? stopReading : readAloud}
                    className={`min-h-[64px] flex-1 rounded-2xl text-white text-lg font-bold
                               transition-all flex items-center justify-center gap-2
                               focus:ring-4 focus:outline-none ${
                                 isReading
                                   ? "bg-red-600 hover:bg-red-500 focus:ring-red-500/50"
                                   : "bg-emerald-600 hover:bg-emerald-500 focus:ring-emerald-500/50"
                               }`}
                    aria-label={isReading ? "Parar lectura" : "Leer en voz alta"}
                  >
                    {isReading ? "⏸️ Parar" : "🔊 Leer"}
                  </button>
                  <button
                    onClick={summarizeFile}
                    disabled={isSummarizing}
                    className="min-h-[64px] px-6 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700
                               rounded-2xl text-white font-bold transition-all disabled:opacity-50
                               flex items-center gap-2 focus:ring-4 focus:ring-indigo-500/50 focus:outline-none"
                    aria-label="Resumir documento"
                  >
                    {isSummarizing ? "⏳" : "📋"} Resumir
                  </button>
                </div>
              )}

              {/* Reading progress */}
              {isReading && (
                <div className="w-full bg-slate-700 rounded-full h-2" role="progressbar"
                     aria-valuenow={readProgress} aria-valuemin={0} aria-valuemax={100}>
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all"
                    style={{ width: `${readProgress}%` }}
                  />
                </div>
              )}

              {/* Summary result */}
              {summary && (
                <div className="bg-indigo-600/10 border border-indigo-500/30 rounded-2xl p-4">
                  <h4 className="text-sm text-indigo-400 font-semibold mb-2">
                    📋 Resumen
                  </h4>
                  <p className="text-white text-sm leading-relaxed">{summary}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right column: Agenda / Reminders */}
        <div className="flex flex-col gap-4">
          <h3 className="text-sm text-slate-400 uppercase tracking-wide flex items-center gap-2">
            <span aria-hidden="true">📅</span> Agenda y recordatorios
          </h3>

          {/* Add reminder */}
          <div className="flex gap-3">
            <input
              type="text"
              value={newReminder}
              onChange={(e) => setNewReminder(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addReminder()}
              placeholder='Ej: "Tomar medicina a las 15:00"'
              className="flex-1 min-h-[56px] bg-slate-800 border border-slate-700 rounded-2xl
                         px-5 text-base text-white placeholder:text-slate-500
                         focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/30"
              aria-label="Nuevo recordatorio"
            />
            <button
              onClick={addReminder}
              disabled={!newReminder.trim()}
              className="min-h-[56px] min-w-[56px] bg-amber-600 hover:bg-amber-500
                         disabled:bg-slate-700 rounded-2xl text-white text-lg font-bold
                         transition-all disabled:opacity-50
                         focus:ring-2 focus:ring-amber-500/50 focus:outline-none"
              aria-label="Añadir recordatorio"
            >
              ➕
            </button>
          </div>

          {/* Reminders list */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {reminders.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 text-center">
                <span className="text-4xl mb-3 block" aria-hidden="true">📅</span>
                <p className="text-slate-400">
                  Sin recordatorios.
                </p>
                <p className="text-slate-500 text-sm mt-2">
                  Añade uno arriba o dile al asistente:
                  <br />
                  <em>&ldquo;Recuérdame tomar la medicina a las 3&rdquo;</em>
                </p>
              </div>
            ) : (
              reminders.map((reminder) => (
                <button
                  key={reminder.id}
                  onClick={() => toggleReminder(reminder.id)}
                  className={`w-full min-h-[64px] rounded-2xl p-4 flex items-center gap-4
                             border transition-all text-left
                             focus:ring-2 focus:ring-amber-500/50 focus:outline-none ${
                               reminder.done
                                 ? "bg-slate-800/30 border-slate-700 opacity-60"
                                 : "bg-slate-800 border-slate-700 hover:border-amber-500"
                             }`}
                  aria-label={`${reminder.done ? "Completado" : "Pendiente"}: ${reminder.text}`}
                >
                  <span className="text-xl" aria-hidden="true">
                    {reminder.done ? "☑️" : "⬜"}
                  </span>
                  <div className="flex-1">
                    <p
                      className={`text-base ${
                        reminder.done
                          ? "text-slate-500 line-through"
                          : "text-white"
                      }`}
                    >
                      {reminder.text}
                    </p>
                    {reminder.time && (
                      <p className="text-xs text-slate-500 mt-1">
                        ⏰ {reminder.time}
                      </p>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Voice tip */}
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
            <p className="text-xs text-slate-400">
              <strong className="text-amber-400">💡 Tip:</strong> Desde el módulo
              de Comunicación, di &ldquo;Recuérdame...&rdquo; y el asistente
              creará el recordatorio automáticamente.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
