"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Module 4 — Messaging Channels
 *
 * Telegram, WhatsApp, Signal integration — inspired by OpenClaw channel architecture.
 * Messages arrive and can be read aloud with the user's cloned voice.
 * All elements are mega-targets (≥64px) for eye tracking dwell selection.
 */

interface Channel {
  id: string;
  type: "telegram" | "whatsapp" | "signal" | "imessage";
  name: string;
  connected: boolean;
  lastMessage?: string;
  lastMessageTime?: string;
  unread: number;
}

interface Message {
  id: string;
  channelId: string;
  from: string;
  text: string;
  timestamp: string;
  isIncoming: boolean;
  read: boolean;
}

const CHANNEL_ICONS: Record<string, string> = {
  telegram: "✈️",
  whatsapp: "💬",
  signal: "🔒",
  imessage: "💬",
};

const CHANNEL_COLORS: Record<string, string> = {
  telegram: "rgb(38, 166, 222)",
  whatsapp: "rgb(37, 211, 102)",
  signal: "rgb(60, 118, 249)",
  imessage: "rgb(52, 199, 89)",
};

export default function ChannelsModule() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [replyText, setReplyText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [configToken, setConfigToken] = useState("");
  const [configType, setConfigType] = useState<"telegram" | "whatsapp">("telegram");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch channels
  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const res = await fetch("/api/channels");
        const data = await res.json();
        setChannels(data.channels || []);
      } catch {
        // Backend may not be running; show empty state
      }
    };
    fetchChannels();
    const interval = setInterval(fetchChannels, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch messages for selected channel
  useEffect(() => {
    if (!selectedChannel) return;
    const fetchMessages = async () => {
      try {
        const res = await fetch(`/api/channels/${selectedChannel}/messages?limit=20`);
        const data = await res.json();
        setMessages(data.messages || []);
      } catch {
        // silent fail
      }
    };
    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [selectedChannel]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !selectedChannel || isSending) return;
      setIsSending(true);
      setReplyText("");

      try {
        await fetch(`/api/channels/${selectedChannel}/send`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, use_voice: true }),
        });
      } catch {
        // Error handling
      } finally {
        setIsSending(false);
      }
    },
    [selectedChannel, isSending]
  );

  const readAloud = useCallback(async (text: string) => {
    setIsReading(true);
    try {
      const res = await fetch("/api/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice_id: "default" }),
      });
      const data = await res.json();
      if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.onended = () => setIsReading(false);
        await audio.play();
      } else {
        setIsReading(false);
      }
    } catch {
      setIsReading(false);
    }
  }, []);

  const addChannel = async () => {
    if (!configToken.trim()) return;
    try {
      await fetch("/api/channels/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: configType, token: configToken }),
      });
      setShowConfig(false);
      setConfigToken("");
    } catch {
      // Error handling
    }
  };

  const selectedChannelData = channels.find((c) => c.id === selectedChannel);

  // ═══ No channels configured ═══
  if (channels.length === 0 && !showConfig) {
    return (
      <div className="flex flex-col gap-6 h-full p-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          📱 Mensajería
        </h2>

        <div className="flex-1 flex flex-col items-center justify-center gap-6">
          <div className="text-6xl" aria-hidden="true">📱</div>
          <h3 className="text-xl font-semibold text-white text-center">
            Conecta tus canales de mensajería
          </h3>
          <p className="text-slate-400 text-center max-w-md">
            Recibe y envía mensajes desde Telegram, WhatsApp o Signal.
            Los mensajes se leen con tu voz clonada.
          </p>

          <button
            onClick={() => setShowConfig(true)}
            className="min-h-[64px] min-w-[280px] bg-violet-600 hover:bg-violet-500
                       rounded-2xl text-white text-lg font-bold transition-all
                       flex items-center justify-center gap-3"
            aria-label="Configurar primer canal de mensajería"
          >
            <span aria-hidden="true">➕</span>
            Añadir canal
          </button>

          <div className="flex gap-6 mt-4">
            {Object.entries(CHANNEL_ICONS).map(([type, icon]) => (
              <div key={type} className="flex flex-col items-center gap-1">
                <span className="text-3xl opacity-40">{icon}</span>
                <span className="text-xs text-slate-500 capitalize">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ═══ Channel configuration modal ═══
  if (showConfig) {
    return (
      <div className="flex flex-col gap-6 h-full p-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          📱 Añadir Canal
        </h2>

        <div className="flex-1 flex flex-col gap-4 max-w-lg">
          <h3 className="text-lg text-slate-300">Elige el tipo de canal</h3>

          <div className="grid grid-cols-2 gap-3">
            {(["telegram", "whatsapp"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setConfigType(type)}
                className={`min-h-[80px] rounded-2xl flex flex-col items-center justify-center gap-2
                           border-2 transition-all ${
                             configType === type
                               ? "border-violet-500 bg-violet-600/20"
                               : "border-slate-700 bg-slate-800 hover:border-slate-500"
                           }`}
                aria-pressed={configType === type}
              >
                <span className="text-2xl">{CHANNEL_ICONS[type]}</span>
                <span className="text-white font-medium capitalize">{type}</span>
              </button>
            ))}
          </div>

          <div>
            <label className="text-sm text-slate-400 mb-2 block" htmlFor="channel-token">
              {configType === "telegram"
                ? "Token del bot de Telegram"
                : "Número de teléfono de WhatsApp"}
            </label>
            <input
              id="channel-token"
              type="text"
              value={configToken}
              onChange={(e) => setConfigToken(e.target.value)}
              placeholder={
                configType === "telegram"
                  ? "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                  : "+34 600 123 456"
              }
              className="w-full min-h-[64px] bg-slate-800 border border-slate-700 rounded-2xl
                         px-6 text-lg text-white placeholder:text-slate-500
                         focus:outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/30"
            />
          </div>

          {configType === "telegram" && (
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
              <p className="text-sm text-slate-400">
                <strong className="text-slate-300">¿Cómo obtener un token?</strong>
                <br />
                1. Abre Telegram y busca @BotFather
                <br />
                2. Envía /newbot y sigue las instrucciones
                <br />
                3. Copia el token que te da BotFather
              </p>
            </div>
          )}

          <div className="flex gap-3 mt-4">
            <button
              onClick={addChannel}
              disabled={!configToken.trim()}
              className="min-h-[64px] flex-1 bg-violet-600 hover:bg-violet-500
                         disabled:bg-slate-700 rounded-2xl text-white text-lg font-bold
                         transition-all disabled:opacity-50"
            >
              ✅ Conectar
            </button>
            <button
              onClick={() => {
                setShowConfig(false);
                setConfigToken("");
              }}
              className="min-h-[64px] px-8 bg-slate-700 hover:bg-slate-600
                         rounded-2xl text-slate-300 text-lg font-medium transition-all"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ═══ Main channels view ═══
  return (
    <div className="flex h-full">
      {/* Channel list sidebar */}
      <div className="w-[280px] border-r border-slate-700 flex flex-col">
        <div className="p-3 border-b border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">📱 Canales</h2>
          <button
            onClick={() => setShowConfig(true)}
            className="min-h-[44px] min-w-[44px] bg-slate-700 hover:bg-slate-600 
                       rounded-xl text-white flex items-center justify-center"
            aria-label="Añadir nuevo canal"
          >
            ➕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {channels.map((channel) => (
            <button
              key={channel.id}
              onClick={() => setSelectedChannel(channel.id)}
              className={`w-full min-h-[72px] px-4 flex items-center gap-3 border-b border-slate-800
                         transition-all ${
                           selectedChannel === channel.id
                             ? "bg-slate-700"
                             : "bg-transparent hover:bg-slate-800"
                         }`}
              aria-current={selectedChannel === channel.id ? "true" : undefined}
              aria-label={`${channel.name} — ${channel.unread} mensajes sin leer`}
            >
              <span
                className="text-2xl"
                style={{ color: CHANNEL_COLORS[channel.type] || "#fff" }}
              >
                {CHANNEL_ICONS[channel.type] || "💬"}
              </span>
              <div className="flex-1 text-left">
                <div className="text-white font-medium text-sm">{channel.name}</div>
                {channel.lastMessage && (
                  <div className="text-slate-500 text-xs truncate max-w-[160px]">
                    {channel.lastMessage}
                  </div>
                )}
              </div>
              {channel.unread > 0 && (
                <span
                  className="min-w-[24px] h-[24px] rounded-full flex items-center justify-center text-xs font-bold text-white"
                  style={{ background: CHANNEL_COLORS[channel.type] || "rgb(139, 92, 246)" }}
                >
                  {channel.unread}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Message area */}
      <div className="flex-1 flex flex-col">
        {!selectedChannel ? (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-slate-500 text-lg">
              Selecciona un canal para ver los mensajes
            </p>
          </div>
        ) : (
          <>
            {/* Channel header */}
            <div className="p-4 border-b border-slate-700 flex items-center gap-3">
              <span className="text-xl">
                {CHANNEL_ICONS[selectedChannelData?.type || "telegram"]}
              </span>
              <h3 className="text-white font-semibold flex-1">
                {selectedChannelData?.name || "Canal"}
              </h3>
              <span
                className={`text-xs px-2 py-1 rounded-full ${
                  selectedChannelData?.connected
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-red-500/20 text-red-400"
                }`}
              >
                {selectedChannelData?.connected ? "Conectado" : "Desconectado"}
              </span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 ? (
                <p className="text-slate-500 text-center mt-8">
                  No hay mensajes aún
                </p>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.isIncoming ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-2xl p-3 ${
                        msg.isIncoming
                          ? "bg-slate-800 border border-slate-700"
                          : "bg-violet-600/30 border border-violet-500/30"
                      }`}
                    >
                      {msg.isIncoming && (
                        <div className="text-xs text-slate-500 mb-1 font-medium">
                          {msg.from}
                        </div>
                      )}
                      <p className="text-white text-sm">{msg.text}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-500">
                          {msg.timestamp}
                        </span>
                        {msg.isIncoming && (
                          <button
                            onClick={() => readAloud(msg.text)}
                            disabled={isReading}
                            className="text-xs text-violet-400 hover:text-violet-300 
                                       disabled:opacity-50 transition-colors"
                            aria-label={`Leer en voz alta: ${msg.text}`}
                          >
                            🔊 Leer
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply input */}
            <div className="p-3 border-t border-slate-700">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage(replyText)}
                  placeholder="Escribe un mensaje..."
                  className="flex-1 min-h-[56px] bg-slate-800 border border-slate-700 rounded-2xl
                             px-5 text-base text-white placeholder:text-slate-500
                             focus:outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/30"
                  aria-label="Escribir respuesta"
                />
                <button
                  onClick={() => sendMessage(replyText)}
                  disabled={!replyText.trim() || isSending}
                  className="min-w-[100px] min-h-[56px] bg-violet-600 hover:bg-violet-500
                             disabled:bg-slate-700 rounded-2xl text-white font-bold
                             transition-all disabled:opacity-50"
                  aria-label="Enviar mensaje"
                >
                  {isSending ? "⏳" : "📤 Enviar"}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
