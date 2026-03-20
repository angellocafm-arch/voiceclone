# QA — Flujo de Onboarding

**Date:** 2026-03-20 23:31
**Status:** ✅ Code review passed (server not running for live test)

## Componentes verificados

### OnboardingScreen.tsx
- ✅ WebSocket connection a `ws://localhost:8765/ws/chat`
- ✅ 7 pasos con progress bar visual (welcome→voice→clone→test→personality→channels→complete)
- ✅ Chat streaming con LLM (chat_stream + chat_stream_end events)
- ✅ Grabación de voz inline via MediaRecorder API
- ✅ Upload de audio como alternativa
- ✅ Clonación de voz via POST /api/clone
- ✅ Botón "Empezar a usar VoiceClone" al completar
- ✅ Error handling: conexión fallida, micrófono no disponible, clone error
- ✅ WCAG AA: aria labels, roles, min-height 56px targets

### Flujo esperado
1. **Welcome** — LLM saluda, se presenta
2. **Voice** — Botón grabar (MediaRecorder) o subir audio
3. **Clone** — POST /api/clone con FormData
4. **Test** — LLM reproduce la voz clonada
5. **Personality** — LLM pregunta preferencias (opcional)
6. **Channels** — Configurar Telegram/WhatsApp (opcional)
7. **Complete** — Botón final → transición a app principal

### Post-onboarding
- ✅ page.tsx detecta voces existentes via API
- ✅ Si hay voz → directo a app con 4 módulos
- ✅ Si no hay voz → onboarding
- ✅ Health check periódico cada 10s

## Accesibilidad
- ✅ Targets ≥56px (botones de acción ≥64px)
- ✅ aria-label en todos los controles
- ✅ role="progressbar" en indicador de pasos
- ✅ Texto placeholder descriptivo
- ✅ Animación bounce para streaming indicator

## Notas
- Test live requiere servidor FastAPI corriendo en puerto 8765
- Test live requiere Ollama con modelo cargado
- Test live de clonación requiere motor de voz (Chatterbox TTS)
- Para test manual: `cd src/web && npm run dev` + servidor FastAPI
