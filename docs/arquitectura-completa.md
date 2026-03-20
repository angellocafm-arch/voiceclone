# Arquitectura Completa — VoiceClone (3 Capas Integradas)

## Fecha: 2026-03-20
## Autor: Equipo VoiceClone (Orquestador + equipo completo)
## Estado: Diseño aprobado en reunión de revisión

---

## Diagrama General del Sistema

```
╔══════════════════════════════════════════════════════════════════════╗
║                     VOICECLONE — ARQUITECTURA                       ║
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐    ║
║  │                    CAPA 2: WEB APP (Next.js)                 │    ║
║  │                                                              │    ║
║  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │    ║
║  │  │ Landing  │→ │ Descarga │→ │ Clonación│→ │ Personal.│    │    ║
║  │  │          │  │ + Install│  │ de Voz   │  │ (opt.)   │    │    ║
║  │  └──────────┘  └──────────┘  └────┬─────┘  └────┬─────┘    │    ║
║  │                                    │             │          │    ║
║  │  ┌──────────┐  ┌──────────┐       │             │          │    ║
║  │  │Dashboard │← │Integrac. │←──────┼─────────────┘          │    ║
║  │  │          │  │AAC/System│       │                         │    ║
║  │  └──────────┘  └──────────┘       │                         │    ║
║  │                                    │                         │    ║
║  │  WCAG AA · 64px targets · Wizard  │ HTTP API calls          │    ║
║  │  Eye tracking compatible · Switch │                         │    ║
║  └──────────────────────────────────┼─────────────────────────┘    ║
║                                      │                              ║
║                          ┌───────────┘                              ║
║                          ▼                                          ║
║  ┌──────────────────────────────────────────────────────────────┐    ║
║  │              CAPA 1: MOTOR LOCAL (Python + FastAPI)           │    ║
║  │              Puerto: localhost:8765                           │    ║
║  │                                                              │    ║
║  │  ┌───────────────────────────────────────────────────────┐   │    ║
║  │  │                   FastAPI Server                       │   │    ║
║  │  │                                                       │   │    ║
║  │  │  POST /clone    → Clona voz desde audio               │   │    ║
║  │  │  POST /speak    → Sintetiza texto con voz clonada     │   │    ║
║  │  │  GET  /voices   → Lista voces disponibles             │   │    ║
║  │  │  GET  /health   → Status del servicio                 │   │    ║
║  │  │  POST /personality/speak → Speak con personalidad     │   │    ║
║  │  └───────────┬───────────────────────┬───────────────────┘   │    ║
║  │              │                       │                       │    ║
║  │              ▼                       ▼                       │    ║
║  │  ┌─────────────────┐    ┌─────────────────────────────┐     │    ║
║  │  │  Engine Adapter  │    │     Personality Engine       │     │    ║
║  │  │                 │    │     (OPCIONAL — Capa 3)      │     │    ║
║  │  │  ┌───────────┐ │    │                             │     │    ║
║  │  │  │Chatterbox │ │    │  profile.md                 │     │    ║
║  │  │  │  (MIT)    │ │    │  vocabulary.md              │     │    ║
║  │  │  └───────────┘ │    │  examples/*.txt             │     │    ║
║  │  │  ┌───────────┐ │    │       │                     │     │    ║
║  │  │  │ XTTS v2   │ │    │       ▼                     │     │    ║
║  │  │  │(fallback) │ │    │  ┌──────────────┐           │     │    ║
║  │  │  └───────────┘ │    │  │ LLM Engine   │           │     │    ║
║  │  │  ┌───────────┐ │    │  │ (local/cloud)│           │     │    ║
║  │  │  │  Future   │ │    │  │ Mistral 7B   │           │     │    ║
║  │  │  │  models   │ │    │  │ or Claude API│           │     │    ║
║  │  │  └───────────┘ │    │  └──────────────┘           │     │    ║
║  │  └─────────────────┘    └─────────────────────────────┘     │    ║
║  │                                                              │    ║
║  │  ┌───────────────────────────────────────────────────────┐   │    ║
║  │  │                    Storage                             │   │    ║
║  │  │  ~/.voiceclone/                                        │   │    ║
║  │  │  ├── voices/              ← Voces clonadas             │   │    ║
║  │  │  │   └── {voice_id}/                                   │   │    ║
║  │  │  │       ├── reference.wav    ← Audio original         │   │    ║
║  │  │  │       ├── embedding.pt     ← Speaker embedding      │   │    ║
║  │  │  │       └── metadata.json    ← Info de la voz         │   │    ║
║  │  │  ├── personality/         ← Perfiles de personalidad   │   │    ║
║  │  │  │   └── {voice_id}/                                   │   │    ║
║  │  │  │       ├── profile.md       ← Quién es               │   │    ║
║  │  │  │       ├── vocabulary.md    ← Vocabulario frecuente   │   │    ║
║  │  │  │       └── examples/        ← Textos ejemplo          │   │    ║
║  │  │  ├── models/              ← Modelos descargados         │   │    ║
║  │  │  │   ├── chatterbox/                                   │   │    ║
║  │  │  │   └── xtts-v2/                                      │   │    ║
║  │  │  └── config.json          ← Configuración global        │   │    ║
║  │  └───────────────────────────────────────────────────────┘   │    ║
║  └──────────────────────────────────────────────────────────────┘    ║
║                                                                      ║
║  ┌──────────────────────────────────────────────────────────────┐    ║
║  │                INTEGRACIÓN EXTERNA                            │    ║
║  │                                                              │    ║
║  │  AAC Software ──HTTP──→ localhost:8765/speak                 │    ║
║  │  (Grid 3, Snap Core)                                         │    ║
║  │                                                              │    ║
║  │  CLI ──────────→ voiceclone speak / voiceclone clone         │    ║
║  │                                                              │    ║
║  │  Sistema (futuro) ──SAPI5/Personal Voice──→ Voz del OS      │    ║
║  └──────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Flujo Completo: Usuario abre web → Clona voz → Captura personalidad → Usa en AAC

### Paso 1: Landing y Descarga

```
┌─────────────────────────────────────────────┐
│              WEB: voiceclone.dev              │
│                                             │
│  "Preserva tu voz. Para siempre."           │
│                                             │
│  [ ▶ Descargar para macOS ]  ← boton grande │
│  [ ▶ Descargar para Windows ]               │
│  [ ▶ Descargar para Linux ]                 │
│                                             │
│  Click → descarga installer                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        INSTALLER (nativo por OS)             │
│                                             │
│  macOS:  VoiceClone.pkg                     │
│  Windows: VoiceClone-Setup.exe              │
│  Linux:  voiceclone.deb / curl | bash       │
│                                             │
│  El installer:                               │
│  1. Instala Python runtime (bundled)         │
│  2. Instala VoiceClone + dependencias        │
│  3. Descarga modelo Chatterbox (~2GB)        │
│  4. Crea servicio en localhost:8765           │
│  5. Abre web app local o redirige a web      │
│                                             │
│  Tiempo estimado: 3-5 minutos               │
│  Interacción usuario: CERO (solo esperar)   │
│  Progress bar visible todo el tiempo        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
```

### Paso 2: Clonación de Voz

```
┌─────────────────────────────────────────────┐
│         WEB APP: Clonación de Voz            │
│                                             │
│  "Vamos a clonar tu voz"                    │
│                                             │
│  Opción A: [ 🎤 Grabar ahora ]             │
│  → Graba 5-30 segundos leyendo un texto     │
│  → Audio se procesa localmente              │
│  → Chatterbox extrae speaker embedding      │
│  → Voz clonada lista en ~30 segundos        │
│                                             │
│  Opción B: [ 📁 Subir grabación ]           │
│  → Arrastra audio antiguo (mp3, wav, ogg)   │
│  → Mínimo 5 segundos de voz clara           │
│  → Puede ser nota de voz, video, podcast    │
│  → Se extrae la voz automáticamente         │
│                                             │
│  [ ▶ Probar mi voz ] → sintetiza ejemplo    │
│  [ ✅ Suena bien ]  [ 🔄 Repetir ]         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
```

### Paso 3: Captura de Personalidad (OPCIONAL)

```
┌─────────────────────────────────────────────┐
│     WEB APP: Captura de Personalidad         │
│     (Feature avanzada — puede saltarse)      │
│                                             │
│  "¿Cómo hablas normalmente?"                │
│                                             │
│  Cuestionario guiado (5-10 min):            │
│  1. ¿Cómo te describes?                    │
│  2. ¿Eres formal o casual?                 │
│  3. ¿Tienes frases favoritas?              │
│  4. ¿Usas humor? ¿De qué tipo?            │
│  5. ¿Qué temas te importan?               │
│                                             │
│  + Opción: subir textos (WhatsApp export)   │
│                                             │
│  → LLM genera 5 frases ejemplo             │
│  → "¿Suena como tú?" → feedback            │
│  → 2-3 rondas de ajuste                    │
│                                             │
│  [ ✅ Así soy yo ] [ ⏭ Saltar ]            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
```

### Paso 4: Integración con Sistema

```
┌─────────────────────────────────────────────┐
│       WEB APP: Integración                   │
│                                             │
│  "Conecta tu voz con tu sistema"            │
│                                             │
│  Tu voz ya está disponible en:              │
│                                             │
│  ✅ API local (localhost:8765)              │
│     Cualquier app puede usarla              │
│                                             │
│  ✅ CLI: voiceclone speak "texto"           │
│     Desde terminal                          │
│                                             │
│  ⚙️ Software AAC:                          │
│     [ Configurar Grid 3 ]                   │
│     → Instrucciones paso a paso             │
│     [ Configurar Snap Core ]                │
│     → Instrucciones paso a paso             │
│                                             │
│  ⚙️ Voz del sistema (post-MVP):            │
│     [ Registrar como voz SAPI5 ]            │
│     [ Integrar con Apple Personal Voice ]   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
```

### Paso 5: Dashboard

```
┌─────────────────────────────────────────────┐
│           WEB APP: Dashboard                 │
│                                             │
│  "Tu voz está lista ✅"                     │
│                                             │
│  Voz: "María García"                        │
│  Modelo: Chatterbox TTS                     │
│  Personalidad: Activada ✅                  │
│  API: localhost:8765 🟢                     │
│                                             │
│  [ 🔊 Probar ] [ ✏️ Editar personalidad ]  │
│  [ ➕ Clonar otra voz ] [ ⚙️ Configurar ]  │
│                                             │
│  Uso reciente:                               │
│  - 142 frases generadas hoy                │
│  - Última: hace 5 minutos                  │
│  - Modelo activo: Chatterbox               │
└─────────────────────────────────────────────┘
```

---

## Cómo la Web App descarga e instala el Motor Local (sin terminal)

### Flujo de Instalación por OS

#### macOS (.pkg installer)
```
1. Usuario click "Descargar para macOS" en web
2. Descarga VoiceClone-1.0.0.pkg (~50MB)
3. Doble click → macOS Installer se abre
4. Click "Continuar" → "Instalar"
5. El .pkg:
   a. Instala Python 3.12 embebido en /opt/voiceclone/
   b. Instala voiceclone package + dependencias
   c. Descarga modelo Chatterbox (~2GB) con progress
   d. Crea LaunchAgent para auto-start del servicio
   e. Abre http://localhost:8765 en Safari
6. Tiempo total: 3-5 min (depende de conexión)
7. Desinstalar: /opt/voiceclone/uninstall.sh
```

#### Windows (.exe installer — NSIS)
```
1. Usuario click "Descargar para Windows"
2. Descarga VoiceClone-Setup-1.0.0.exe (~60MB)
3. Doble click → Windows Installer
4. "Siguiente" → "Instalar" (sin opciones complicadas)
5. El installer:
   a. Instala Python 3.12 embebido en C:\VoiceClone\
   b. Instala voiceclone + dependencias
   c. Descarga Chatterbox (~2GB)
   d. Crea servicio Windows o tarea programada
   e. Crea acceso directo en Escritorio
   f. Abre http://localhost:8765
6. Desinstalar: Panel de control → Programas
```

#### Linux (script bash)
```bash
curl -fsSL https://voiceclone.dev/install.sh | bash
# Script hace todo automáticamente:
# 1. Detecta distro (Debian, Ubuntu, Fedora, Arch)
# 2. Instala Python 3.12 si no existe
# 3. Crea virtualenv en ~/.voiceclone/
# 4. Instala voiceclone via pip
# 5. Descarga modelo Chatterbox
# 6. Crea systemd service
# 7. Abre http://localhost:8765
```

---

## Cómo la Capa 3 (Personalidad) se integra con la Capa 1 (Motor)

### Pipeline detallado

```
┌──────────────────────────────────────────────────────────────┐
│                 PIPELINE COMPLETO                             │
│                                                              │
│  1. INPUT                                                    │
│     ├── Desde web app: usuario escribe texto                 │
│     ├── Desde AAC: Grid 3 envía texto via HTTP               │
│     └── Desde CLI: voiceclone speak "texto" --voice maria    │
│                                                              │
│  2. PERSONALITY ENGINE (si activada)                         │
│     ├── Carga profile.md del usuario                         │
│     ├── Busca ejemplos similares (RAG: cosine similarity)    │
│     ├── Construye system prompt:                             │
│     │   "Eres María. Hablas así: {profile}                   │
│     │    Ejemplos: {ejemplos_similares}                      │
│     │    Genera el texto como lo diría María.                │
│     │    Solo texto, nada más."                              │
│     ├── Envía a LLM (local Mistral o Claude API)             │
│     └── Recibe texto personalizado                           │
│                                                              │
│  3. VOICE ENGINE                                             │
│     ├── Carga speaker embedding de ~/.voiceclone/voices/     │
│     ├── Chatterbox TTS sintetiza texto → audio               │
│     │   (Si Chatterbox falla → fallback a XTTS v2)          │
│     └── Audio WAV/OGG generado                               │
│                                                              │
│  4. OUTPUT                                                   │
│     ├── Hacia web app: audio se reproduce en browser         │
│     ├── Hacia AAC: audio WAV se devuelve via HTTP             │
│     └── Hacia CLI: audio se reproduce o guarda en archivo    │
└──────────────────────────────────────────────────────────────┘
```

### API Endpoints Detallados

```yaml
# Endpoint base: http://localhost:8765

POST /clone
  Description: Clona voz desde audio
  Body: multipart/form-data
    - audio: archivo de audio (wav, mp3, ogg, m4a)
    - name: nombre para la voz (opcional)
  Response:
    - voice_id: string
    - name: string
    - duration_seconds: float
    - quality_score: float (0-1)

POST /speak
  Description: Sintetiza texto con voz clonada (sin personalidad)
  Body: application/json
    - text: string (texto a sintetizar)
    - voice_id: string (ID de la voz clonada)
    - format: "wav" | "ogg" | "mp3" (default: wav)
  Response: audio/wav (o formato solicitado)

POST /personality/speak
  Description: Sintetiza con personalidad (Capa 3)
  Body: application/json
    - text: string (intención/texto base)
    - voice_id: string
    - personality: bool (default: true)
    - format: "wav" | "ogg" | "mp3"
  Response: audio/wav
  Note: Más lento que /speak (incluye paso LLM)

GET /voices
  Description: Lista voces clonadas disponibles
  Response: application/json
    - voices: [{voice_id, name, created_at, has_personality}]

GET /voices/{voice_id}
  Description: Detalle de una voz
  Response: application/json (metadata + personality status)

DELETE /voices/{voice_id}
  Description: Elimina una voz clonada (y su personalidad)
  Response: 204 No Content

POST /personality/setup
  Description: Configura personalidad para una voz
  Body: application/json
    - voice_id: string
    - questionnaire: object (respuestas del cuestionario)
    - examples: [string] (textos ejemplo, opcional)
  Response:
    - personality_id: string
    - sample_phrases: [string] (5 frases generadas para validar)

POST /personality/validate
  Description: Feedback sobre frases generadas
  Body: application/json
    - personality_id: string
    - feedback: [{phrase_index, is_accurate: bool, comment: string}]
  Response:
    - updated: bool
    - new_sample_phrases: [string] (regeneradas si necesario)

GET /health
  Description: Status del servicio
  Response: application/json
    - status: "ok" | "loading" | "error"
    - engine: "chatterbox" | "xtts-v2"
    - model_loaded: bool
    - voices_count: int
    - uptime_seconds: int
```

---

## Stack Tecnológico Detallado

### Backend (Motor — Capa 1 + Capa 3)
```
Python 3.12+
├── FastAPI 0.100+        ← API HTTP local
├── uvicorn               ← ASGI server
├── chatterbox-tts        ← Motor de voz principal
├── TTS (coqui)           ← XTTS v2 fallback
├── sounddevice           ← Grabación de audio
├── librosa               ← Procesamiento de audio
├── numpy                 ← Cálculos
├── torch (CPU)           ← Inference engine
├── sentence-transformers ← RAG embeddings (Capa 3)
├── anthropic             ← Claude API (Capa 3, opcional)
└── click                 ← CLI framework
```

### Frontend (Web App — Capa 2)
```
Next.js 14+
├── React 18+             ← UI framework
├── Radix UI              ← Accessible components base
├── Tailwind CSS          ← Styling
├── next-themes           ← Dark/light/high-contrast
├── react-audio-player    ← Reproducción de audio
├── use-sound             ← Sound effects
└── swr                   ← API fetching (localhost:8765)
```

### Instalación / Packaging
```
macOS:  pkgbuild + productbuild (.pkg)
Windows: NSIS (.exe) o Inno Setup
Linux:  dpkg-deb (.deb) + bash script
All:    PyInstaller para binario standalone
```

---

## Estructura del Proyecto (Código)

```
voiceclone/
├── README.md
├── LICENSE                     ← MIT
├── pyproject.toml              ← Python package config
├── setup.cfg
│
├── src/
│   ├── voiceclone/
│   │   ├── __init__.py
│   │   ├── cli.py              ← CLI (click)
│   │   ├── server.py           ← FastAPI server
│   │   │
│   │   ├── engine/             ← Capa 1: Voice Engine
│   │   │   ├── __init__.py
│   │   │   ├── base.py         ← VoiceEngine ABC
│   │   │   ├── chatterbox.py   ← Chatterbox adapter
│   │   │   ├── xtts.py         ← XTTS v2 adapter
│   │   │   └── manager.py      ← Engine selection + fallback
│   │   │
│   │   ├── personality/        ← Capa 3: Personality Engine
│   │   │   ├── __init__.py
│   │   │   ├── profile.py      ← Profile management
│   │   │   ├── llm.py          ← LLM integration (local/cloud)
│   │   │   ├── rag.py          ← RAG for examples
│   │   │   └── questionnaire.py← Questionnaire logic
│   │   │
│   │   ├── audio/              ← Audio processing
│   │   │   ├── __init__.py
│   │   │   ├── recorder.py     ← Mic recording
│   │   │   ├── processor.py    ← Audio cleanup/conversion
│   │   │   └── player.py       ← Audio playback
│   │   │
│   │   └── storage/            ← File management
│   │       ├── __init__.py
│   │       └── voices.py       ← Voice storage (~/.voiceclone/)
│   │
│   └── web/                    ← Capa 2: Web App (Next.js)
│       ├── package.json
│       ├── next.config.js
│       ├── tailwind.config.js
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx        ← Landing
│       │   ├── download/
│       │   ├── clone/
│       │   ├── personality/
│       │   ├── integrate/
│       │   └── dashboard/
│       ├── components/
│       │   ├── ui/             ← Accessible components
│       │   ├── audio/          ← Audio recorder/player
│       │   └── wizard/         ← Wizard navigation
│       └── lib/
│           └── api.ts          ← API client (localhost:8765)
│
├── installers/
│   ├── macos/                  ← .pkg builder
│   ├── windows/                ← NSIS script
│   └── linux/                  ← .deb builder + bash script
│
├── tests/
│   ├── test_engine.py
│   ├── test_personality.py
│   ├── test_api.py
│   └── test_cli.py
│
└── docs/
    ├── getting-started.md
    ├── api-reference.md
    ├── aac-integration.md
    └── personality-guide.md
```

---

## Seguridad y Privacidad

### Datos que NUNCA salen del ordenador
- Audio de voz original
- Speaker embedding (vector de voz)
- Personality profile
- Textos ejemplo
- Audio sintetizado

### Datos que PUEDEN salir (solo con consentimiento explícito)
- Texto enviado a Claude API (si el usuario elige Cloud LLM para Capa 3)
- Telemetría: NINGUNA por defecto

### Medidas de seguridad
- API solo escucha en localhost (no expuesta a red)
- No requiere autenticación (es local)
- Archivos almacenados en ~/.voiceclone/ con permisos 700
- Opción de cifrado de voces almacenadas (post-MVP)

---

*Arquitectura completa — Proyecto VoiceClone*  
*Vertex Developer — 2026*  
*"Tres capas. Un propósito. Tu voz."*
