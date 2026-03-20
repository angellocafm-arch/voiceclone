# Contratos de Interfaz — VoiceClone v4

## Fecha: 2026-03-20
## Versión: 2.0 (visión final con 4 módulos + canales)

---

## 1. LLM (Ollama) ↔ Motor de Voz (Chatterbox/XTTS)

### Input: Texto a sintetizar
```python
@dataclass
class SpeechRequest:
    text: str                    # Texto plano a sintetizar
    voice_id: str                # ID del perfil de voz clonada
    speed: float = 1.0           # 0.5 - 2.0
    emotion: str = "neutral"     # neutral, happy, sad, urgent (si el motor lo soporta)
    output_format: str = "wav"   # wav, ogg, mp3
```

### Output: Audio generado
```python
@dataclass
class SpeechResponse:
    audio_path: str              # Ruta al archivo de audio generado
    duration_seconds: float      # Duración del audio
    sample_rate: int             # Hz (normalmente 22050 o 24000)
    format: str                  # wav, ogg, mp3
    voice_id: str                # Perfil de voz usado
```

### Formato de Anotaciones de Voz
```
[VOZ:normal] Hola, ¿cómo estás?
[VOZ:enfasis] Esto es importante.
[PAUSA:500ms]
[VOZ:normal] Seguimos.
```
El motor de voz parsea estas anotaciones y ajusta prosodia.

---

## 2. LLM ↔ Control del SO (Tool Use via Ollama)

### Tools Registradas en Ollama

#### file_manager
```python
class FileManagerTools:
    @tool("create_folder")
    def create_folder(path: str) -> dict:
        """Crea una carpeta en la ruta especificada."""
        # Returns: {"success": true, "path": "/Users/X/Documents/nueva"}

    @tool("list_directory")
    def list_directory(path: str, pattern: str = "*") -> dict:
        """Lista archivos y carpetas en un directorio."""
        # Returns: {"items": [{"name": "x", "type": "file|dir", "size": 1024}]}

    @tool("read_file")
    def read_file(path: str, max_chars: int = 5000) -> dict:
        """Lee contenido de un archivo de texto."""
        # Returns: {"content": "...", "truncated": false}

    @tool("move_file")
    def move_file(source: str, destination: str) -> dict:
        """Mueve un archivo o carpeta. REQUIERE CONFIRMACIÓN."""
        # Returns: {"success": true, "from": "...", "to": "..."}

    @tool("delete_file")
    def delete_file(path: str) -> dict:
        """Elimina un archivo (a la papelera). REQUIERE CONFIRMACIÓN VOCAL."""
        # Returns: {"success": true, "path": "...", "moved_to_trash": true}

    @tool("copy_file")
    def copy_file(source: str, destination: str) -> dict:
        """Copia un archivo o carpeta."""
        # Returns: {"success": true, "from": "...", "to": "..."}

    @tool("search_files")
    def search_files(query: str, path: str = "~", max_results: int = 20) -> dict:
        """Busca archivos por nombre o contenido."""
        # Returns: {"results": [{"path": "...", "name": "...", "match": "..."}]}
```

#### browser_control
```python
class BrowserTools:
    @tool("open_url")
    def open_url(url: str) -> dict:
        """Abre una URL en Chrome."""
        # Returns: {"success": true, "url": "https://..."}

    @tool("search_web")
    def search_web(query: str) -> dict:
        """Busca en Google y devuelve resultados."""
        # Returns: {"results": [{"title": "...", "url": "...", "snippet": "..."}]}

    @tool("read_webpage")
    def read_webpage(url: str, max_chars: int = 5000) -> dict:
        """Lee el contenido textual de una página web."""
        # Returns: {"title": "...", "content": "...", "url": "..."}
```

#### app_launcher
```python
class AppTools:
    @tool("open_app")
    def open_app(app_name: str) -> dict:
        """Abre una aplicación del sistema."""
        # Returns: {"success": true, "app": "Safari", "pid": 1234}

    @tool("list_running_apps")
    def list_running_apps() -> dict:
        """Lista aplicaciones en ejecución."""
        # Returns: {"apps": [{"name": "Safari", "pid": 1234}]}
```

#### email_manager
```python
class EmailTools:
    @tool("read_inbox")
    def read_inbox(limit: int = 10, unread_only: bool = True) -> dict:
        """Lee los últimos emails del inbox."""
        # Returns: {"emails": [{"from": "...", "subject": "...", "preview": "...", "date": "..."}]}

    @tool("send_email")
    def send_email(to: str, subject: str, body: str) -> dict:
        """Envía un email. REQUIERE CONFIRMACIÓN VOCAL DOBLE."""
        # Returns: {"success": true, "to": "...", "subject": "..."}

    @tool("read_email")
    def read_email(email_id: str) -> dict:
        """Lee un email completo."""
        # Returns: {"from": "...", "subject": "...", "body": "...", "attachments": [...]}
```

### Niveles de Confirmación
```python
class ConfirmationLevel(Enum):
    NONE = "none"           # Leer, listar, buscar — sin confirmación
    SINGLE = "single"       # Mover, copiar — confirmación vocal simple
    DOUBLE = "double"       # Eliminar, enviar email — "¿Estás seguro? Di 'sí, confirmo'"
    BLOCKED = "blocked"     # Formatear disco, sudo — NUNCA permitido
```

---

## 3. LLM ↔ Canales de Mensajería

### Interfaz Común de Canal (Inspirada en OpenClaw)
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, AsyncIterator

@dataclass
class IncomingMessage:
    channel: str              # "telegram", "whatsapp", "signal"
    sender_id: str            # ID del remitente
    sender_name: str          # Nombre visible
    text: Optional[str]       # Texto del mensaje
    audio_path: Optional[str] # Path si es audio/voz
    media_path: Optional[str] # Path si es media (imagen, video)
    reply_to: Optional[str]   # ID del mensaje al que responde
    timestamp: float          # Unix timestamp

@dataclass
class OutgoingMessage:
    text: Optional[str]       # Texto a enviar
    audio_path: Optional[str] # Audio a enviar (voz clonada)
    as_voice: bool = False    # Enviar como nota de voz
    reply_to: Optional[str]   # Responder a mensaje específico

class ChannelPlugin(ABC):
    """Interfaz base para plugins de canal — inspirada en OpenClaw."""

    @abstractmethod
    async def start(self) -> None:
        """Inicializa la conexión al canal."""

    @abstractmethod
    async def stop(self) -> None:
        """Cierra la conexión limpiamente."""

    @abstractmethod
    async def send(self, to: str, message: OutgoingMessage) -> dict:
        """Envía un mensaje por el canal."""

    @abstractmethod
    async def listen(self) -> AsyncIterator[IncomingMessage]:
        """Escucha mensajes entrantes (async generator)."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Estado de la conexión."""
```

### Pipeline de Mensaje Entrante (Canal → Voz)
```
1. Canal recibe mensaje de texto
2. channel_manager.on_message(msg: IncomingMessage)
3. LLM procesa: "Tienes un mensaje de [nombre] en [canal]: [texto]"
4. LLM decide respuesta + acción
5. Motor de voz sintetiza respuesta con voz clonada
6. Audio se reproduce por altavoces
7. (Opcional) Respuesta de texto se envía por el canal
```

### Pipeline de Mensaje Saliente (Voz → Canal)
```
1. Usuario selecciona texto en tablero / escribe con eye tracking
2. API: POST /speak {"text": "...", "send_to": {"channel": "telegram", "contact": "..."}}
3. Motor de voz sintetiza
4. Audio se reproduce localmente
5. channel_manager.send(channel, contact, OutgoingMessage(text=texto))
```

---

## 4. Frontend Web ↔ API FastAPI

### Endpoints Completos

#### Voz y Comunicación
```
POST   /api/speak              # Texto → Audio (voz clonada)
         Body: {"text": str, "voice_id": str, "speed": float}
         Response: {"audio_url": str, "duration": float}

POST   /api/speak/stream       # Texto → Audio streaming (WebSocket upgrade)
GET    /api/voices              # Lista perfiles de voz disponibles
POST   /api/voices/clone       # Clonar voz desde audio
         Body: multipart/form-data {audio_file, name}
         Response: {"voice_id": str, "name": str, "quality_score": float}
```

#### Control del SO
```
POST   /api/control/execute    # Ejecutar acción del SO
         Body: {"instruction": str}  # Lenguaje natural
         Response: {"action": str, "result": dict, "confirmation_needed": bool}

POST   /api/control/confirm    # Confirmar acción pendiente
         Body: {"action_id": str, "confirmed": bool}
         Response: {"success": bool}

GET    /api/control/history     # Historial de acciones recientes
         Response: {"actions": [{"id": str, "instruction": str, "result": str, "timestamp": str}]}
```

#### Canales de Mensajería
```
GET    /api/channels            # Lista canales configurados
         Response: {"channels": [{"name": str, "type": str, "connected": bool}]}

POST   /api/channels/configure  # Configurar nuevo canal
         Body: {"type": "telegram", "config": {"bot_token": str}}
         Response: {"success": bool, "channel_id": str}

DELETE /api/channels/{id}       # Eliminar canal
GET    /api/channels/{id}/messages  # Mensajes recientes del canal
         Response: {"messages": [IncomingMessage]}

POST   /api/channels/{id}/send  # Enviar mensaje por canal
         Body: {"to": str, "text": str, "as_voice": bool}
```

#### LLM y Onboarding
```
POST   /api/chat                # Chat con el LLM
         Body: {"message": str, "context": str}
         Response: {"reply": str, "tools_used": list}

WS     /ws/chat                 # Chat streaming (WebSocket)
         In:  {"message": str}
         Out: {"delta": str, "done": bool}

GET    /api/onboarding/status   # Estado del onboarding
         Response: {"step": str, "completed": list, "next": str}

POST   /api/onboarding/advance  # Avanzar paso de onboarding
```

#### Predicción de Frases
```
GET    /api/predict             # Predecir frases
         Query: ?context=str&limit=5
         Response: {"predictions": [{"text": str, "confidence": float}]}
```

#### Eye Tracking
```
WS     /ws/gaze                 # Posición de mirada en tiempo real
         In:  {"x": float, "y": float, "timestamp": float}
         Out: {"dwell_target": str, "dwell_progress": float}
```

#### Sistema
```
GET    /api/health              # Health check
         Response: {"status": "ok", "ollama": bool, "voice_engine": bool, "channels": int}

GET    /api/system/info         # Info del sistema
         Response: {"ram_gb": int, "cpu_cores": int, "gpu": str, "model": str}
```

---

## 5. Tipos Compartidos (Python dataclasses)

```python
# src/types.py — Tipos compartidos por todos los módulos

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

class ModuleType(Enum):
    COMMUNICATION = "communication"
    CONTROL = "control"
    PRODUCTIVITY = "productivity"
    CHANNELS = "channels"

class ActionStatus(Enum):
    SUCCESS = "success"
    PENDING_CONFIRMATION = "pending_confirmation"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class UserProfile:
    name: str
    voice_id: Optional[str] = None
    preferred_phrases: List[str] = field(default_factory=list)
    channels_config: dict = field(default_factory=dict)

@dataclass
class ActionResult:
    status: ActionStatus
    message: str
    data: Optional[dict] = None
    confirmation_id: Optional[str] = None

@dataclass
class PhraseHistory:
    phrases: List[str] = field(default_factory=list)
    max_size: int = 500

    def add(self, phrase: str) -> None:
        self.phrases.append(phrase)
        if len(self.phrases) > self.max_size:
            self.phrases = self.phrases[-self.max_size:]
```

---

## Notas de Implementación

1. **Todos los endpoints devuelven JSON** con `Content-Type: application/json`
2. **Errores siguen formato estándar:** `{"error": str, "code": int, "detail": str}`
3. **WebSocket para tiempo real:** eye tracking, chat streaming, canal de mensajes
4. **Audio se sirve desde:** `/audio/{filename}` (static files)
5. **CORS:** Solo localhost (es una app local)
6. **Sin autenticación:** App 100% local, sin usuarios remotos
