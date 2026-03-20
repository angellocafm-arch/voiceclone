# Investigación de Arquitectura Técnica — VoiceClone

## Fecha: 2026-03-20
## Investigador: Tanke (Vertex Developer)

---

## 1. Proyectos Similares Analizados

### AllTalk TTS
- **Arquitectura:** Servidor local + Web UI (Gradio) + API REST
- **Multi-engine:** Soporta Coqui XTTS, F5-TTS, VITS, Piper simultáneamente
- **Clonación:** WAV 22050Hz, 6-30s de audio, carpeta `voices/` para cada voz
- **Integración:** API JSON para terceros (SillyTavern, text-generation-webui)
- **Lección:** El enfoque multi-engine es robusto pero complejo para usuario no técnico

### Coqui TTS CLI
- **Arquitectura:** Librería Python + CLI + Server opcional
- **Instalación:** `pip install TTS` — un comando
- **Uso:** `tts --text "Hello" --model_name tts_models/en/ljspeech/tacotron2` 
- **Clonación:** `tts --text "text" --speaker_wav my_voice.wav --model_name tts_models/multilingual/multi-dataset/xtts_v2`
- **Lección:** La simplicidad del CLI es el gold standard a seguir

### Qwen3-TTS (referencia 2026)
- **Instalación:** `pip install -U qwen-tts`
- **Clonación desde 3 segundos** de audio
- **Lección:** La tendencia es hacia menos audio necesario y pip install trivial

---

## 2. Integración con Sistema Operativo

### macOS — Reemplazar `say`
**Estado actual:** No es posible inyectar voces custom directamente en el sistema de voces de macOS. Las voces del sistema están gestionadas por Apple en `System Settings > Accessibility > Spoken Content`.

**Estrategia VoiceClone:**
1. **Wrapper script `voiceclone-say`** que reemplaza/complementa `say`:
   ```bash
   voiceclone say "Hola, esto es mi voz clonada"
   ```
2. El script:
   - Recibe texto como input
   - Genera audio con el modelo local + voz clonada del usuario
   - Reproduce con `afplay` (macOS nativo)
3. **Alias opcional:** El usuario puede hacer `alias say='voiceclone say'` en `.zshrc`
4. **Integración Shortcuts:** Crear un shortcut de macOS que capture texto seleccionado → envíe a VoiceClone → reproduzca

### Linux — Integración con Speech Dispatcher
**Estrategia más profunda posible:**
1. Módulo para `speech-dispatcher` que conecte con VoiceClone
2. Así cualquier app que use TTS del sistema (GNOME, KDE) usa la voz clonada
3. También un wrapper `voiceclone say` como en macOS

### Windows (futuro)
- SAPI 5 custom voice provider (complejo)
- Wrapper script `voiceclone.exe say "texto"` (pragmático)

---

## 3. Arquitectura Propuesta para VoiceClone

### Enfoque: Modular + CLI-first

```
┌────────────────────────────────────────┐
│              VoiceClone                 │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────┐  ┌──────────────────┐   │
│  │ CLI      │  │ API Server       │   │
│  │ (typer)  │  │ (FastAPI/uvicorn)│   │
│  └────┬─────┘  └────────┬─────────┘   │
│       │                  │             │
│  ┌────▼──────────────────▼─────────┐   │
│  │         VoiceClone Core         │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │   Model Manager         │    │   │
│  │  │   (download, load, run) │    │   │
│  │  └──────────┬──────────────┘    │   │
│  │             │                   │   │
│  │  ┌──────────▼──────────────┐    │   │
│  │  │   Engine Adapter        │    │   │
│  │  │   ┌───────────────┐     │    │   │
│  │  │   │ Chatterbox    │     │    │   │
│  │  │   │ (default)     │     │    │   │
│  │  │   ├───────────────┤     │    │   │
│  │  │   │ XTTS v2       │     │    │   │
│  │  │   │ (fallback)    │     │    │   │
│  │  │   └───────────────┘     │    │   │
│  │  └─────────────────────────┘    │   │
│  │                                 │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │   Audio Pipeline        │    │   │
│  │  │   - Record              │    │   │
│  │  │   - Process             │    │   │
│  │  │   - Play                │    │   │
│  │  └─────────────────────────┘    │   │
│  │                                 │   │
│  │  ┌─────────────────────────┐    │   │
│  │  │   Voice Store           │    │   │
│  │  │   ~/.voiceclone/voices/ │    │   │
│  │  └─────────────────────────┘    │   │
│  └─────────────────────────────────┘   │
│                                        │
└────────────────────────────────────────┘
```

### Componentes:

#### A. CLI (interfaz principal)
- **Framework:** Typer (Python) — auto-genera help, validaciones, bonito
- **Comandos:**
  ```bash
  voiceclone setup          # Primera vez: instala dependencias, descarga modelo
  voiceclone clone          # Grabación guiada + clonación
  voiceclone say "texto"    # Genera audio con tu voz y lo reproduce
  voiceclone serve          # Inicia API local (para integración)
  voiceclone voices         # Lista voces disponibles
  voiceclone export NAME    # Exporta voz para compartir
  ```

#### B. API Server (opcional, para integración)
- **Framework:** FastAPI + uvicorn
- **Endpoints:**
  ```
  POST /tts          → {"text": "Hola", "voice": "default"} → audio/wav
  GET  /voices       → lista de voces disponibles
  POST /clone        → upload audio → clona voz
  GET  /health       → status del servidor
  ```
- Se inicia con `voiceclone serve` (puerto 8100 por defecto)
- Permite que otros programas usen la voz clonada

#### C. Model Manager
- Descarga automática del modelo seleccionado (Chatterbox o XTTS)
- Cache en `~/.voiceclone/models/`
- Auto-detección de hardware: GPU (CUDA/MPS) → CPU fallback
- Lazy loading: modelo se carga solo cuando se necesita

#### D. Engine Adapter (patrón Strategy)
- Interfaz común para diferentes motores TTS
- Chatterbox como default
- XTTS v2 como fallback
- Fácil añadir nuevos motores en el futuro

#### E. Audio Pipeline
- **Grabación:** `sounddevice` (cross-platform)
- **Procesamiento:** `scipy` + `numpy` para normalización
- **Formato:** WAV 22050Hz mono como estándar interno
- **Playback:** `sounddevice` o `afplay` (macOS) / `aplay` (Linux)

#### F. Voice Store
- Directorio: `~/.voiceclone/voices/`
- Cada voz = carpeta con:
  - `reference.wav` (audio original del usuario)
  - `config.json` (metadata: nombre, idioma, modelo usado)
  - `model_cache/` (datos del modelo pre-procesados)

---

## 4. ¿Cómo hacer "Un Solo Comando"?

### Estrategia: Bootstrap script + pip

```bash
curl -fsSL https://voiceclone.dev/install.sh | bash
```

**El script de instalación:**
1. Detecta OS (macOS, Linux, Windows/WSL)
2. Verifica Python 3.10+ (lo instala si no está: brew/apt/winget)
3. Crea virtualenv en `~/.voiceclone/venv/`
4. `pip install voiceclone` dentro del venv
5. Crea symlink `voiceclone` en PATH (`/usr/local/bin/`)
6. Ejecuta `voiceclone setup` automáticamente:
   - Descarga modelo (~2GB)
   - Verifica hardware
   - Muestra mensaje de bienvenida

**Alternativa para usuarios con Python:**
```bash
pip install voiceclone && voiceclone setup
```

### Decisión: Instalación nativa vs Docker

| Aspecto | Nativa (pip) | Docker |
|---------|-------------|--------|
| Facilidad usuario no-técnico | ✅ Un comando | ❌ Instalar Docker primero |
| Acceso a micrófono | ✅ Directo | ⚠️ Complejo |
| Acceso a audio del sistema | ✅ Directo | ❌ Muy complejo |
| Peso total | ~3GB | ~5-8GB |
| Integración SO | ✅ Nativa | ❌ Aislado |
| Reproducibilidad | ⚠️ Variaciones | ✅ Idéntico |

**Decisión: Instalación nativa (pip + bootstrap script)**

Docker no tiene sentido para VoiceClone porque:
1. El usuario necesita acceder al micrófono (grabar su voz)
2. El audio debe reproducirse por los altavoces del sistema
3. La integración con `say`/Speech Dispatcher requiere acceso al SO
4. Docker añade complejidad innecesaria para el usuario objetivo

---

## 5. Stack Tecnológico Propuesto

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| Lenguaje | Python 3.10+ | Ecosistema ML, Chatterbox es Python |
| CLI Framework | Typer + Rich | CLI bonito, autocompletado, progress bars |
| API Server | FastAPI + uvicorn | Async, rápido, autodocumentación |
| TTS Engine 1 | Chatterbox TTS | Mejor calidad, MIT, zero-shot |
| TTS Engine 2 | XTTS v2 (fallback) | Mejor CPU, comunidad grande |
| Audio Recording | sounddevice | Cross-platform, simple |
| Audio Processing | scipy + numpy | Normalización, conversión formato |
| Modelo Distribution | Hugging Face Hub | Descarga automática de modelos |
| Packaging | PyPI (pip) | Distribución estándar Python |
| Installer Script | Bash (macOS/Linux) | Bootstrap para usuarios no-técnicos |
| Config | TOML (pyproject) | Estándar Python moderno |
| Tests | pytest | Estándar |

---

## 6. Flujo de Usuario Completo (Happy Path)

```
Usuario abre Terminal
         │
         ▼
curl -fsSL voiceclone.dev/install.sh | bash
         │
         ▼ (automático)
   Detecta macOS ARM64
   Verifica Python 3.11 ✓
   Crea ~/.voiceclone/
   pip install voiceclone
   Descarga modelo (2GB) ████████████ 100%
   ✅ VoiceClone instalado!
         │
         ▼
voiceclone clone
         │
         ▼
   "Vamos a clonar tu voz!"
   "Lee el siguiente texto en voz alta:"
   "El veloz murciélago hindú comía..."
   [GRABANDO] ██████████ 30s
   "Perfecto. Procesando tu voz..."
   [PROCESANDO] ████████ 100%
   ✅ "Tu voz 'mi-voz' está lista!"
         │
         ▼
voiceclone say "Hola, esta es mi voz clonada"
         │
         ▼
   [🔊 Audio reproduciéndose con tu voz]
```

---

## 7. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Calidad en CPU baja | Alto | Usar Chatterbox-Turbo optimizado; fallback a XTTS con MPS |
| Modelo grande (~2GB) | Medio | Download con progress bar, cache persistente |
| Dependencias Python conflicto | Medio | Virtualenv aislado, pinned versions |
| Grabación falla en Terminal | Medio | Guía clara, test de micrófono integrado |
| Chatterbox cambia licencia | Bajo | Arquitectura modular, XTTS como backup |
| Apple Silicon no soportado | Bajo | Chatterbox y XTTS ya soportan Apple Silicon |

---

## Fuentes

- AllTalk TTS (github.com/erew123/alltalk_tts)
- Coqui TTS CLI documentation
- FastAPI documentation (fastapi.tiangolo.com)
- Typer documentation (typer.tiangolo.com)
- macOS TTS: Apple Developer Documentation
- Linux Speech Dispatcher: freedesktop.org
- Multiple Reddit threads on voice cloning architecture
