# Contratos de Interfaz — VoiceClone v2

**Fecha:** 2026-03-20 22:25
**Autor:** Tanke (Vertex Developer)
**Estado:** Definición inicial — base para implementación

---

## Contrato 1: LLM Local (Ollama) ↔ Motor de Voz (Chatterbox/XTTS)

### Dirección
LLM genera texto → Motor de voz sintetiza audio

### Formato de entrada al motor de voz

```python
@dataclass
class SynthesisRequest:
    """Petición del LLM al motor de voz."""
    text: str                          # Texto a sintetizar
    voice_id: str                      # ID del perfil de voz clonada
    annotations: SynthesisAnnotations  # Metadatos de prosodia
    priority: Literal["high", "normal", "low"] = "normal"
    stream: bool = True                # Streaming de audio (frase a frase)

@dataclass
class SynthesisAnnotations:
    """Metadatos que el LLM genera para guiar la síntesis."""
    speed: float = 1.0                 # 0.5 (lento) - 2.0 (rápido)
    emotion: str = "neutral"           # neutral, happy, sad, urgent, calm
    pauses: list[PauseMarker] = field(default_factory=list)

@dataclass
class PauseMarker:
    """Marcador de pausa en el texto."""
    after_word_index: int              # Insertar pausa después de palabra N
    duration_ms: int = 500             # Duración de la pausa
```

### Formato de salida del motor de voz

```python
@dataclass
class SynthesisResponse:
    """Respuesta del motor de voz al LLM/API."""
    audio_chunks: AsyncIterator[bytes] # Stream de audio PCM 22050Hz mono
    format: str = "wav"                # wav o ogg
    sample_rate: int = 22050
    duration_ms: int = 0               # Duración total (conocida al finalizar)
    voice_id: str = ""
    status: Literal["ok", "error"] = "ok"
    error: str | None = None
```

### Protocolo de streaming

```
1. LLM genera respuesta por frases (streaming)
2. Cada frase completa → SynthesisRequest al motor de voz
3. Motor genera audio chunk → reproduce inmediatamente
4. Si hay más frases → encola siguiente chunk
5. El usuario oye la primera frase mientras el LLM sigue generando
```

### Errores

| Error | Acción |
|-------|--------|
| `voice_not_found` | Usar voz por defecto del sistema |
| `model_not_loaded` | Cargar modelo Chatterbox → reintentar |
| `xtts_fallback` | Chatterbox falló → usar XTTS v2 automáticamente |
| `out_of_memory` | Reducir context → reintentar con texto más corto |

---

## Contrato 2: Interfaz Web Local ↔ API Backend (FastAPI)

### Base URL
`http://localhost:8765/api/v1`

### Autenticación
Ninguna (localhost only). Headers:
```
Content-Type: application/json
Accept: application/json
```

### Endpoints

#### Onboarding

```
POST /onboarding/start
  Request:  {}
  Response: {
    "session_id": "uuid",
    "message": "Hola, soy tu asistente. Vamos a clonar tu voz...",
    "audio_url": "/audio/{chunk_id}.wav"  // Mensaje en voz del sistema
  }

POST /onboarding/message
  Request:  {
    "session_id": "uuid",
    "text": "Sí, tengo 3 minutos",
    "audio_file": "base64_encoded_wav"    // Opcional: audio del usuario
  }
  Response: {
    "session_id": "uuid",
    "message": "Perfecto. Lee este texto en voz alta...",
    "audio_url": "/audio/{chunk_id}.wav",
    "step": "voice_recording",            // Paso actual del onboarding
    "progress": 0.3,                      // 0.0 - 1.0
    "actions": ["record", "skip", "upload_file"]
  }

POST /onboarding/upload-voice
  Request:  multipart/form-data {
    "session_id": "uuid",
    "audio": File (wav/mp3/ogg)
  }
  Response: {
    "voice_id": "uuid",
    "quality_score": 0.85,                // 0.0 - 1.0
    "message": "Tu voz se ha clonado. Vamos a probarla."
  }

GET /onboarding/status
  Response: {
    "completed": false,
    "current_step": "voice_recording",
    "steps_completed": ["welcome", "hardware_check"],
    "steps_remaining": ["voice_recording", "personality", "confirmation"]
  }
```

#### Comunicación (Módulo 1)

```
POST /speak
  Request:  {
    "text": "Hola, ¿cómo estás?",
    "voice_id": "uuid",                   // Default: voz principal del usuario
    "emotion": "happy",                   // Opcional
    "speed": 1.0                          // Opcional
  }
  Response: {
    "audio_url": "/audio/{chunk_id}.wav",
    "duration_ms": 2340,
    "text_annotated": "Hola, [pause:200ms] ¿cómo estás?"
  }

GET /predict
  Query:  ?context=últimas+3+frases&limit=5
  Response: {
    "predictions": [
      {"text": "Sí, estoy bien", "confidence": 0.85},
      {"text": "Necesito ayuda", "confidence": 0.72},
      {"text": "Gracias", "confidence": 0.68},
      {"text": "¿Me puedes repetir?", "confidence": 0.61},
      {"text": "No, gracias", "confidence": 0.55}
    ]
  }

GET /phrases/frequent
  Response: {
    "phrases": [
      {"text": "Sí", "count": 234},
      {"text": "No", "count": 198},
      {"text": "Gracias", "count": 167},
      ...
    ]
  }
```

#### Control del Ordenador (Módulo 2)

```
POST /control/execute
  Request:  {
    "instruction": "Crea una carpeta en el escritorio llamada Médicos 2026",
    "confirm_destructive": false          // True = ya confirmado por usuario
  }
  Response: {
    "action_id": "uuid",
    "action_type": "create_folder",
    "description": "Crear carpeta 'Médicos 2026' en ~/Desktop",
    "status": "completed",                // completed | needs_confirmation | error
    "result": "Carpeta creada en ~/Desktop/Médicos 2026",
    "audio_url": "/audio/{chunk_id}.wav", // Confirmación en voz del usuario
    "undoable": true
  }

POST /control/undo
  Request:  {"action_id": "uuid"}
  Response: {
    "status": "undone",
    "description": "Carpeta 'Médicos 2026' eliminada"
  }

GET /control/history
  Query:  ?limit=20&date=2026-03-20
  Response: {
    "actions": [
      {
        "action_id": "uuid",
        "timestamp": "2026-03-20T14:30:00",
        "instruction": "Crea una carpeta...",
        "result": "Carpeta creada",
        "undoable": true
      }
    ]
  }

GET /control/actions
  Response: {
    "quick_actions": [
      {"id": "create_folder", "label": "Crear carpeta", "icon": "📁"},
      {"id": "open_file", "label": "Abrir archivo", "icon": "📄"},
      {"id": "write_document", "label": "Escribir documento", "icon": "✏️"},
      {"id": "send_email", "label": "Enviar email", "icon": "📧"},
      {"id": "open_browser", "label": "Abrir navegador", "icon": "🌐"},
      {"id": "read_aloud", "label": "Leer en voz alta", "icon": "🔊"},
      {"id": "search_files", "label": "Buscar archivos", "icon": "🔍"},
      {"id": "agenda", "label": "Ver agenda", "icon": "📅"}
    ]
  }
```

#### Chat con LLM (transversal)

```
POST /chat
  Request:  {
    "message": "Resúmeme el último email de mi médico",
    "context": "productivity",            // communication | control | productivity
    "stream": true
  }
  Response (SSE stream):
    data: {"type": "text", "content": "El email de tu médico dice..."}
    data: {"type": "text", "content": " que la cita es el martes a las 10."}
    data: {"type": "audio", "url": "/audio/chunk1.wav"}
    data: {"type": "done", "full_text": "El email..."}

WebSocket /ws/chat
  → Bidireccional para streaming en tiempo real
  → Formato: JSON frames
```

#### Documentos / RAG (Módulo 3)

```
POST /documents/ingest
  Request:  multipart/form-data {
    "file": File (pdf/txt/whatsapp_export),
    "type": "whatsapp" | "text" | "pdf" | "email"
  }
  Response: {
    "document_id": "uuid",
    "chunks_created": 42,
    "preview": "Procesados 42 fragmentos del archivo..."
  }

GET /documents
  Response: {
    "documents": [
      {"id": "uuid", "name": "chat_whatsapp.txt", "chunks": 42, "ingested_at": "..."}
    ]
  }
```

#### Voces

```
GET /voices
  Response: {
    "voices": [
      {
        "id": "uuid",
        "name": "Mi voz",
        "is_default": true,
        "created_at": "2026-03-20T14:00:00",
        "sample_url": "/audio/samples/{voice_id}.wav",
        "quality_score": 0.87
      }
    ]
  }

POST /voices/clone
  Request:  multipart/form-data {
    "audio": File (wav, 5-30s),
    "name": "Mi voz"
  }
  Response: {
    "voice_id": "uuid",
    "quality_score": 0.85,
    "sample_url": "/audio/samples/{voice_id}.wav"
  }
```

#### Sistema

```
GET /health
  Response: {
    "status": "ok",
    "llm": {"status": "running", "model": "mistral:7b", "vram_used_gb": 4.2},
    "voice_engine": {"status": "ready", "engine": "chatterbox", "voices_loaded": 1},
    "uptime_seconds": 3600
  }

GET /hardware
  Response: {
    "ram_gb": 16,
    "cpu_cores": 10,
    "gpu": "Apple M2 Pro",
    "model_recommended": "mistral:7b",
    "model_loaded": "mistral:7b",
    "disk_free_gb": 120
  }
```

---

## Contrato 3: Sistema de Onboarding ↔ Perfil de Usuario

### Estructura del perfil de usuario

```python
@dataclass
class UserProfile:
    """Perfil completo del usuario, generado durante el onboarding."""

    # Identificación
    id: str                               # UUID
    name: str                             # Nombre del usuario
    created_at: datetime
    updated_at: datetime

    # Voz
    voice_profiles: list[VoiceProfile]    # Puede tener múltiples voces
    default_voice_id: str

    # Personalidad / comunicación
    personality: PersonalityProfile
    frequent_phrases: list[FrequentPhrase]
    custom_vocabulary: list[str]          # Palabras especiales (nombres, términos)

    # Hardware
    hardware: HardwareProfile
    llm_model: str                        # Modelo seleccionado (ej: "mistral:7b")

    # Preferencias
    preferences: UserPreferences

@dataclass
class VoiceProfile:
    id: str
    name: str
    reference_audio_path: str             # Audio de referencia para clonación
    quality_score: float                  # 0.0 - 1.0
    created_at: datetime
    engine: Literal["chatterbox", "xtts"] # Motor que lo generó

@dataclass
class PersonalityProfile:
    speaking_style: str                   # "formal", "informal", "mixed"
    common_expressions: list[str]         # Frases habituales detectadas
    topics_of_interest: list[str]         # Temas frecuentes en sus textos
    language: str                         # "es", "en", etc.
    dialect: str                          # "es-ES", "es-MX", etc.
    ingested_documents: list[str]         # IDs de documentos procesados

@dataclass
class HardwareProfile:
    os: str                               # "macOS", "Linux", "Windows"
    ram_gb: int
    cpu_cores: int
    gpu: str | None
    disk_free_gb: int
    detected_at: datetime

@dataclass
class UserPreferences:
    speech_speed: float = 1.0             # 0.5 - 2.0
    default_emotion: str = "neutral"
    theme: Literal["dark", "light"] = "dark"
    font_size: Literal["normal", "large", "xlarge"] = "large"
    dwell_time_ms: int = 800             # Tiempo de mirada para seleccionar
    confirmation_vocal: bool = True       # Confirmar acciones con voz
    auto_predict: bool = True             # Mostrar predicciones automáticamente

@dataclass
class FrequentPhrase:
    text: str
    count: int
    last_used: datetime
    context: str                          # "greeting", "medical", "daily", "custom"
```

### Almacenamiento

```
~/.voiceclone/
├── config.json              # Preferencias globales
├── profiles/
│   └── {user_id}/
│       ├── profile.json     # UserProfile serializado
│       ├── voices/
│       │   ├── {voice_id}/
│       │   │   ├── reference.wav   # Audio de referencia
│       │   │   └── metadata.json   # VoiceProfile
│       │   └── ...
│       ├── documents/
│       │   ├── {doc_id}.json       # Metadatos del documento
│       │   └── vectors/            # FAISS index
│       ├── history/
│       │   ├── phrases.jsonl       # Historial de frases dichas
│       │   └── actions.jsonl       # Historial de acciones del SO
│       └── personality/
│           └── personality.json     # PersonalityProfile
└── models/
    ├── llm/                # Symlink a modelos Ollama
    └── tts/                # Modelo Chatterbox/XTTS
```

### Flujo de datos en el onboarding

```
1. Inicio
   └→ Crear UserProfile con defaults
   └→ Detectar hardware → HardwareProfile
   └→ Seleccionar LLM model → llm_model

2. Clonación de voz
   └→ Grabar/subir audio → reference.wav
   └→ Procesar → VoiceProfile (quality_score)
   └→ Si quality_score < 0.6 → pedir más audio

3. Personalidad (opcional)
   └→ Usuario comparte documentos → ingester.py
   └→ Vectorizar → FAISS index
   └→ Extraer speaking_style, common_expressions
   └→ PersonalityProfile

4. Confirmación
   └→ Síntesis de prueba con voz clonada
   └→ "¿Suena como tú?" → ajustar si es necesario
   └→ Guardar profile.json

5. Listo
   └→ Redirigir a interfaz principal (Módulo 1)
```

---

## Notas de diseño

1. **Todos los endpoints devuelven audio_url** cuando el LLM habla → el frontend siempre puede reproducir la respuesta en voz clonada.

2. **WebSocket para chat streaming** — SSE como fallback. El frontend conecta a `/ws/chat` para latencia mínima.

3. **Idempotencia** — Todas las acciones del SO tienen `action_id` único. Undo es siempre posible si `undoable: true`.

4. **No hay autenticación** — El sistema corre en localhost. Solo accesible desde la misma máquina. Si en el futuro se necesita acceso remoto (cuidador), añadir token simple.

5. **Versionado de API** — `/api/v1/` desde el inicio. Permite evolucionar sin romper.

---

*Última actualización: 2026-03-20 22:25*
