# Referencia de Arquitectura OpenClaw — Para VoiceClone v4

## Fecha: 2026-03-20
## Propósito: Documentar cómo OpenClaw implementa las funcionalidades que VoiceClone reutilizará

---

## 1. Arquitectura General de OpenClaw

### Gateway (Daemon Central)
- Un **único proceso Gateway** por host que gestiona TODO:
  - Canales de mensajería (WhatsApp/Baileys, Telegram/grammY, Discord, Signal, iMessage...)
  - Conexiones WebSocket para clientes (macOS app, CLI, web UI)
  - Conexiones WebSocket para nodos (dispositivos remotos)
  - Servidor HTTP en puerto configurable (default `18789`)

### Protocolo de Comunicación
- **WebSocket** con frames JSON sobre texto
- Primer frame SIEMPRE es `connect` (handshake obligatorio)
- Después: requests (`{type:"req", id, method, params}`) y events (`{type:"event", event, payload}`)
- Token de autenticación configurable

### Relevancia para VoiceClone
**Podemos adaptar esta arquitectura:**
- El daemon Gateway → se convierte en nuestro servidor FastAPI local
- Los canales de mensajería → reutilizar concepto de plugins de canal
- Las conexiones WebSocket → para eye tracking en tiempo real + streaming de voz

---

## 2. Sistema de Canales de Mensajería

### Arquitectura de Canales
- Cada canal es un **plugin independiente** con su propia configuración
- Canales soportados: Telegram (grammY), WhatsApp (Baileys), Discord, Signal, iMessage, Slack, Matrix, IRC, etc.
- Los canales se registran como plugins con: `enabled`, `config`, `actions`

### Pipeline de Mensajes
```
Mensaje entrante → Canal (plugin) → Normalización → Enqueue → Agent Loop → Respuesta → Canal
```

### Telegram (Referencia Principal)
- Usa **grammY** (framework TypeScript para Telegram Bot API)
- Modo: Long polling (default) o Webhook
- Acciones: sendMessage, editMessage, deleteMessage, react
- Formatos: HTML parse mode, voice notes, stickers, inline buttons
- Streaming: edita mensajes en vivo mientras genera respuesta

### WhatsApp
- Usa **Baileys** (biblioteca Node.js para WhatsApp Web)
- UNA sesión de WhatsApp por host
- Requiere escaneo QR o pairing code

### Adaptación para VoiceClone
**Lo que reutilizamos:**
- Concepto de plugins de canal con interfaz común
- Pipeline de normalización de mensajes
- Streaming de respuestas

**Lo que cambiamos:**
- En lugar de TypeScript/Node.js → Python (para integrar con LLM + TTS)
- En lugar de grammY → python-telegram-bot o telethon
- En lugar de Baileys → whatsapp-web.js (Python wrapper) o servicio bridge
- AÑADIMOS: síntesis de voz en el pipeline de respuesta

---

## 3. Agent Loop (Cómo ejecuta herramientas)

### Pipeline del Agent Loop
```
1. Recepción de mensaje
2. Resolución de sesión
3. Carga de skills/tools
4. Construcción de system prompt (AGENTS.md, SOUL.md, skills...)
5. Inferencia del modelo (streaming)
6. Ejecución de tools (si el modelo lo pide)
7. Streaming de respuesta al canal
8. Persistencia en transcript
```

### Tool Use
- Las tools se registran con: `name`, `description`, `parameters` (JSON Schema), `execute()`
- El LLM decide cuándo llamar tools basándose en el system prompt
- Tools disponibles: exec (shell), read/write files, browser, web search, etc.
- Pipeline: `before_tool_call` → execute → `after_tool_call` → result

### Adaptación para VoiceClone (Control del SO)
**Nuestro equivalente:**
- Tools Python registradas en Ollama via tool use API
- `file_manager`: crear/mover/leer archivos → equivalente a exec + read/write
- `browser_control`: abrir URLs → equivalente a browser tool
- `app_launcher`: abrir apps → equivalente a exec
- `email_manager`: gestión de email → equivalente a message tool

**Pipeline de seguridad:**
- Lista blanca de acciones sin confirmación (leer archivos, listar, buscar)
- Confirmación VOCAL obligatoria para acciones destructivas (eliminar, enviar email)

---

## 4. Sistema de Plugins

### Estructura
- Los plugins registran tools con `api.registerTool()`
- Pueden ser `required` (siempre activos) o `optional` (opt-in)
- Configuración por agente: `agents.list[].tools.allow`
- Hooks disponibles: before_model_resolve, before_tool_call, after_tool_call, etc.

### Relevancia
- VoiceClone puede usar una arquitectura de plugins similar
- Cada módulo (comunicación, control SO, productividad, canales) es un "plugin"
- Se registran tools en el LLM via Ollama tool use

---

## 5. Decisiones de Diseño para VoiceClone

### Reutilizar Directamente (MIT)
1. **Concepto de Gateway como daemon local** → FastAPI en :8765
2. **Arquitectura de plugins de canal** → módulos Python independientes
3. **Pipeline de agent loop** → Ollama con tool use
4. **Sistema de sesiones** → estado persistente por usuario

### Reimplementar en Python
1. **Motor de canales** → Python nativo (python-telegram-bot, etc.)
2. **Tool execution** → wrapper Python sobre Ollama tool use API
3. **Streaming** → WebSocket + Server-Sent Events

### NO Reutilizar (Diferente)
1. **Multi-usuario** → VoiceClone es monousuario local
2. **Pairing/auth** → No necesario (100% local)
3. **Multi-agente** → Un solo agente con múltiples tools
4. **Cloud providers** → Todo local con Ollama

---

## 6. Contratos Clave de Ollama (Tool Use)

### Format de Tool Registration
```python
tools = [{
    "type": "function",
    "function": {
        "name": "create_folder",
        "description": "Crea una carpeta en el sistema",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta de la carpeta"}
            },
            "required": ["path"]
        }
    }
}]

response = ollama.chat(
    model="mistral:7b",
    messages=messages,
    tools=tools
)
```

### Format de Tool Call Response
```python
if response['message'].get('tool_calls'):
    for tool_call in response['message']['tool_calls']:
        func_name = tool_call['function']['name']
        func_args = tool_call['function']['arguments']
        result = execute_tool(func_name, func_args)
        messages.append({
            "role": "tool",
            "content": json.dumps(result)
        })
```

---

## Fuentes
- `/usr/local/lib/node_modules/openclaw/docs/concepts/architecture.md`
- `/usr/local/lib/node_modules/openclaw/docs/concepts/agent.md`
- `/usr/local/lib/node_modules/openclaw/docs/concepts/agent-loop.md`
- `/usr/local/lib/node_modules/openclaw/docs/channels/telegram.md`
- `/usr/local/lib/node_modules/openclaw/docs/plugins/agent-tools.md`
- GitHub: https://github.com/openclaw/openclaw (MIT License)
