# VoiceClone — Estado del Proyecto
## Última actualización: 2026-03-20 23:50
## Sesión: Ángel + Tanke, grupo "Clonar Voz"

---

## ¿Qué es el proyecto?

**Asistente de vida completo para personas con ELA y dificultades motoras.**

- Habla con la voz clonada de la persona (100% local)
- Controla todo el ordenador por la vista (eye tracking)
- Se comunica por Telegram/WhatsApp desde el móvil
- LLM adaptativo según hardware del usuario (3B → 70B)
- Sin nube, sin base de datos, sin suscripción, sin internet después de instalar
- Open source MIT en GitHub

---

## Infraestructura — lo que NO necesitamos

| Servicio | ¿Necesario? | Por qué |
|---------|------------|---------|
| Supabase / Postgres | ❌ NO | Todo se guarda en archivos locales en ~/.voiceclone/ |
| Vercel (app) | ❌ NO | La web app corre en localhost:8765 del usuario |
| Redis / cache | ❌ NO | Caché en memoria + archivos JSON |
| CDN | ❌ NO | No hay assets que servir remotamente |
| Auth service | ❌ NO | Sistema local, un solo usuario |
| **GitHub** | ✅ SÍ | Código fuente del proyecto (angellocafm-arch/voiceclone) |
| **Vercel (landing)** | ✅ PENDIENTE | Solo la página de marketing + botón de descarga |

---

## Dónde vive cada cosa

```
GitHub (angellocafm-arch/voiceclone)
└── Código fuente completo (MIT)

Ordenador del usuario (después de instalar)
├── ~/.voiceclone/
│   ├── voices/          ← Voces clonadas (archivos .wav)
│   ├── models/          ← Modelos descargados (via Ollama)
│   ├── config.json      ← Configuración del sistema
│   ├── personality/     ← Perfil de personalidad (JSON)
│   ├── rag/             ← Vectores FAISS para personalización
│   └── history/         ← Historial de frases y conversaciones
├── Ollama (daemon local)
│   └── Modelos LLM (3B → 70B según hardware)
└── localhost:8765
    ├── FastAPI (backend)
    └── Next.js (interfaz web en Chrome)
```

---

## Estado del código (v0.3.0)

### ✅ COMPLETADO
- `src/voice_engine/` — Chatterbox + XTTS v2 wrapper (arquitectura correcta)
- `src/llm/ollama_client.py` — cliente Ollama con tool use, streaming, embeddings
- `src/llm/onboarding_agent.py` — onboarding conversacional 8 pasos
- `src/llm/phrase_predictor.py` — predicción de frases (frecuencia + contexto)
- `src/system/` — control del SO: archivos, browser, apps, email (seguridad 4 niveles)
- `src/channels/` — Telegram + WhatsApp (arquitectura OpenClaw)
- `src/rag/` — RAG local con FAISS (WhatsApp export, PDF, TXT)
- `src/api/main.py` — FastAPI 20+ endpoints + WebSocket eye tracking
- `src/web/` — Next.js 4 módulos (comunicación, control SO, productividad, canales)
- `src/web/GazeTracker.tsx` — eye tracking WebSocket + dwell 800ms + fallback ratón
- `src/landing/` — landing page con detección de hardware + botón descarga
- `scripts/install.sh` — installer macOS + Linux (abre Chrome solo, sin terminal)
- `scripts/install.sh` — auto-selección modelo según RAM
- 117 tests, build Next.js OK, 0 credenciales en código

### ⚠️ PENDIENTE (para MVP funcional)
1. **Añadir Chatterbox TTS al installer** — la librería `chatterbox-tts` no está en el script de instalación. El código que la llama está correcto, solo falta `pip install chatterbox-tts` en install.sh. ~30 min de trabajo.
2. **Test end-to-end en máquina limpia** — probar el installer desde cero en un Mac sin dependencias previas.
3. **Deploy landing en Vercel** — cuando Ángel decida (cuenta openparty2026@gmail.com).

### 📋 FASE 2 (futura)
- Integración directa con Grid 3 (contactar Smartbox para API)
- Integración directa con Proloquo2Go (AssistiveWare)
- Soporte Windows (actualmente macOS + Linux)
- GUI de escritorio opcional (Electron)

---

## Compatibilidad eye tracking y AAC

| Sistema | Estado | Cómo se integra |
|---------|--------|-----------------|
| **Tobii** (cualquier modelo) | ✅ Compatible | Via WebSocket local (driver Tobii expone WS) |
| **Cualquier eye tracker con WS** | ✅ Compatible | Protocolo estándar `{x, y, fixation, timestamp}` |
| **Ratón como fallback** | ✅ Compatible | Automático si no hay eye tracker |
| **Grid 3** (Smartbox) | ⚠️ Parcial | Via voz del sistema OS (Fase 1) / API directa (Fase 2) |
| **Proloquo2Go** | ⚠️ Parcial | Via voz del sistema OS (Fase 1) / API directa (Fase 2) |
| **Snap Core First** | ⚠️ Parcial | Via voz del sistema OS |
| **Teclado (switch access)** | ✅ Compatible | Navegación completa por teclado implementada |

**Integración "voz del sistema":** La voz clonada se puede registrar como voz nativa del OS (macOS Speech / Windows SAPI / Linux eSpeak-ng). Cualquier software AAC que use voces del sistema la puede usar sin cambiar nada.

---

## Repositorio GitHub

- **URL:** https://github.com/angellocafm-arch/voiceclone
- **Cuenta:** openparty2026@gmail.com / angellocafm-arch
- **Token:** ver TOOLS.md en ~/clawd/ (no se almacena en GitHub)
- **Licencia:** MIT
- **Versión actual:** v0.3.0 (tag)
- **Commits:** 14+

---

## Equipo virtual (9 expertos)

Todos en `~/clawd/projects/voiceclone/equipo/`:
1. Orquestador (basado en 10 referentes tech leads)
2. Comunicador IA
3. Experto Voz IA (Chatterbox, XTTS, modelos de voz)
4. Experto UX (accesibilidad, no-tech users)
5. Experto DevOps (installer, distribución)
6. Experto Audio (procesamiento de audio)
7. Experto Accesibilidad (Tobii, AAC, WCAG)
8. Experto Personalidad IA (LLM context, RAG)
9. **Experto Sistemas Locales** ← nuevo (Ollama, control SO, offline-first)
   - Referente #1: **Peter Steinberger** (creador de OpenClaw, ahora en OpenAI)

---

## Arquitectura técnica (resumen)

```
WEB DESCARGA (Vercel — pendiente)
  └── Detecta hardware → recomienda modelo → descarga installer

INSTALLER (scripts/install.sh)
  ├── Instala Python, Ollama, dependencias
  ├── Descarga modelo LLM según RAM (3B→70B)
  ├── Descarga Chatterbox TTS (PENDIENTE añadir)
  ├── Arranca FastAPI en localhost:8765
  └── Abre Chrome automáticamente

SISTEMA LOCAL (localhost:8765)
  ├── FastAPI (backend Python)
  │   ├── /speak — texto → voz clonada
  │   ├── /control/* — acciones del SO
  │   ├── /channels/* — Telegram/WhatsApp
  │   ├── /onboarding/* — setup conversacional
  │   ├── /predict — predicción de frases
  │   └── /ws/gaze — WebSocket eye tracking
  └── Next.js (frontend Chrome)
      ├── 💬 Comunicación (frases + voz)
      ├── 🖥️ Control SO (archivos, email, browser)
      ├── 📝 Productividad (dictado, resúmenes)
      └── 📱 Canales (Telegram, WhatsApp)

DATOS (~/.voiceclone/ — todo local)
  ├── Voces clonadas (WAV)
  ├── Modelos LLM (via Ollama)
  ├── Perfil personalidad (JSON)
  ├── Vectores RAG (FAISS)
  └── Historial frases (JSON)
```

---

## Decisión pendiente — Base de datos

**Contexto (modelo Peter Steinberger / OpenClaw):**
- OpenClaw usa **SQLite** por defecto para embeddings y búsqueda semántica de memoria
- Para despliegues avanzados: **PostgreSQL + pgvector**
- Alternativa local moderna: **LanceDB** (sin daemon, archivos `.lance`)

**Estado actual de VoiceClone:**
- Memoria y RAG: archivos JSON + FAISS (funciona, pero menos robusto)
- Para MVP: suficiente
- Para escalar/comunidad: migrar a SQLite como Peter

**Decisión a tomar con Ángel:**
- ¿Añadimos SQLite ahora (más robusto, sigue siendo local) o dejamos JSON para MVP?
- Recomendación: SQLite para la memoria y embeddings, igual que OpenClaw

**Sobre código abierto vs gratuito:**
- **Código abierto (MIT):** cualquiera puede ver, modificar, contribuir → ✅ ya lo tenemos
- **Gratuito para usuarios:** no pagan para descargarlo ni usarlo → ✅ por diseño
- **Ambas cosas a la vez:** como OpenClaw → ✅ ese es el modelo

---

## Próxima sesión de trabajo — por dónde empezar

**Tarea inmediata más importante:**
Añadir a `scripts/install.sh`:
```bash
pip install chatterbox-tts torch torchaudio
```
Esto cierra el gap entre "arquitectura lista" y "funciona de verdad".

**Luego:**
- Test end-to-end en Mac limpio
- Deploy landing en Vercel
- Comunicar el proyecto

---
*Documentado por Tanke — Vertex Developer*
*Retomar en: grupo Telegram "Clonar Voz" o DM con Ángel*
