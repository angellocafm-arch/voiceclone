# Mockups CLI — VoiceClone

## Fecha: 2026-03-20
## Autor: Equipo VoiceClone (Experto UX + Experto DevOps)

---

## Principios CLI

- **Mensajes amigables** — no errores crípticos
- **Progress bars** en operaciones largas (Rich library)
- **Colores y emojis** para feedback visual
- **Confirmaciones claras** ✅ ❌
- **Ayuda contextual** — `--help` en cada subcomando
- **Tab completion** para voces disponibles

---

## 1. Instalación

```bash
$ curl -fsSL https://voiceclone.dev/install.sh | bash

  🎤 VoiceClone — Instalación
  ────────────────────────────────

  Detectando sistema...
  ✅ macOS 15.2 (Apple Silicon M2)
  ✅ Python 3.12.1

  Instalando VoiceClone...
  ████████████████████████████████ 100%

  Descargando modelo Chatterbox TTS (2.1 GB)...
  ████████████████░░░░░░░░░░░░░░░░ 52%  1.1GB/2.1GB  ~2min

  ...

  ✅ VoiceClone instalado correctamente

  Tu voz, tu ordenador, tu privacidad.

  Empieza con:
    voiceclone clone myvoice     Clona tu voz
    voiceclone speak "Hola"      Habla con voz clonada
    voiceclone --help             Ver todos los comandos

  API local disponible en: http://localhost:8765
```

---

## 2. Clonar una voz — `voiceclone clone`

### Opción A: Grabar desde micrófono

```bash
$ voiceclone clone maria

  🎤 Clonación de Voz — "maria"
  ────────────────────────────────

  Vamos a clonar tu voz. Lee el siguiente texto en voz alta:

  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │  "El sol de la mañana ilumina las calles de la ciudad.     │
  │   Los pájaros cantan mientras la gente pasea               │
  │   tranquilamente por el parque. Me gusta este momento      │
  │   del día, cuando todo está en calma y puedo pensar        │
  │   con claridad."                                           │
  │                                                            │
  └────────────────────────────────────────────────────────────┘

  Pulsa ENTER para empezar a grabar...

  ● Grabando...  18s / 30s
  ████████████████████░░░░░░░░░░░░ 

  [ENTER para parar]

  ✅ Grabación completada (24 segundos)

  Procesando voz...
  ████████████████████████████████ 100%

  ✅ Voz "maria" clonada correctamente

  Probando... Escucha:
  🔊 "Hola, esta es la voz clonada de María"

  ¿Suena bien? (s/n): s

  ✅ Voz "maria" guardada en ~/.voiceclone/voices/maria/

  Usa tu voz con:
    voiceclone speak "tu texto" --voice maria
```

### Opción B: Desde archivo de audio

```bash
$ voiceclone clone abuela --from ~/Desktop/nota-de-voz-abuela.ogg

  🎤 Clonación de Voz — "abuela"
  ────────────────────────────────

  Analizando audio: nota-de-voz-abuela.ogg
  ✅ Duración: 45 segundos
  ✅ Calidad: Buena (SNR 18dB)
  ✅ Voz detectada: 1 persona

  Extrayendo voz...
  ████████████████████████████████ 100%

  ✅ Voz "abuela" clonada correctamente

  Probando... Escucha:
  🔊 "Hola, esta es la voz clonada"

  ¿Suena bien? (s/n): s

  ✅ Voz "abuela" guardada
```

---

## 3. Sintetizar texto — `voiceclone speak`

### Uso básico

```bash
$ voiceclone speak "Buenos días, ¿cómo estás?" --voice maria

  🔊 Reproduciendo...
  "Buenos días, ¿cómo estás?"
  ▶ ████████████████ 2.1s
```

### Con personalidad (Capa 3)

```bash
$ voiceclone speak "Buenos días" --voice maria --personality

  ✨ Personalizando... (usando perfil de María)
  
  Original:  "Buenos días"
  Con estilo: "¡Buenas! ¿Qué tal, eh? Ya amaneció 🌅"

  🔊 Reproduciendo...
  ▶ ████████████████ 3.4s
```

### Guardar en archivo

```bash
$ voiceclone speak "Este es un mensaje para mi familia" \
    --voice maria --output mensaje.wav

  🔊 Audio guardado: mensaje.wav (4.2s, 67KB)
```

### Desde stdin (pipe)

```bash
$ echo "Texto desde pipe" | voiceclone speak --voice maria

  🔊 Reproduciendo...
  ▶ ████████████████ 1.8s
```

---

## 4. Personalidad — `voiceclone personality`

### Setup inicial

```bash
$ voiceclone personality set --voice maria

  ✨ Configuración de Personalidad — "maria"
  ────────────────────────────────────────────

  Responde estas preguntas para capturar tu estilo:

  1/5 ¿Cómo te describes?
  > Soy alegre, cercana, me gusta bromear

  2/5 ¿Eres más formal o casual?
  > Muy casual, tuteo a todo el mundo

  3/5 ¿Tienes frases o muletillas típicas?
  > "¿Sabes?", "Venga", "No me líes"

  4/5 ¿Usas humor? ¿De qué tipo?
  > Sí, humor cotidiano, cosas del día a día

  5/5 ¿Qué temas te importan?
  > Mi familia, cocina, el barrio

  Generando perfil...
  ████████████████████████████████ 100%

  Prueba — ¿Esto suena como tú?:

  1. "¡Venga, que nos vamos!"
  2. "Oye, ¿sabes qué? Me encanta esto"
  3. "No me líes, que es facilísimo"

  ¿Apruebas? (s/n/ajustar): s

  ✅ Personalidad de "maria" configurada
  
  Usa --personality con speak para activarla:
    voiceclone speak "Hola" --voice maria --personality
```

### Importar textos

```bash
$ voiceclone personality import --voice maria --from ~/whatsapp-export.txt

  📝 Analizando textos de María...
  ✅ 342 mensajes analizados
  ✅ Vocabulario extraído: 156 palabras frecuentes
  ✅ Patrones detectados: casual, emojis, frases cortas
  
  Perfil actualizado con datos de WhatsApp.
```

### Ver perfil

```bash
$ voiceclone personality show --voice maria

  ✨ Perfil de Personalidad — "maria"
  ────────────────────────────────────

  Tono: Casual, cercano, alegre
  Humor: Cotidiano
  Muletillas: "¿Sabes?", "Venga", "No me líes"
  Temas: Familia, cocina, barrio
  Fuentes: Cuestionario + 342 mensajes WhatsApp
  
  Archivo: ~/.voiceclone/personality/maria/profile.md
```

---

## 5. Gestión de voces — `voiceclone voices`

```bash
$ voiceclone voices

  🎤 Voces Disponibles
  ────────────────────────

  NOMBRE      CREADA          PERSONALIDAD    MOTOR
  maria       2026-03-20      ✅ Activada     Chatterbox
  abuela      2026-03-20      ❌ No           Chatterbox
  papa        2026-03-19      ✅ Activada     XTTS v2

  3 voces · Motor activo: Chatterbox TTS
```

```bash
$ voiceclone voices delete papa

  ⚠️  ¿Eliminar la voz "papa" y todos sus datos?
  Esto incluye: audio original, embedding, personalidad.
  Esta acción no se puede deshacer.

  Escribe "papa" para confirmar: papa

  ✅ Voz "papa" eliminada
```

---

## 6. Servidor API — `voiceclone server`

```bash
$ voiceclone server

  🌐 VoiceClone API Server
  ────────────────────────────

  ✅ Motor: Chatterbox TTS
  ✅ Voces cargadas: 3
  ✅ API: http://localhost:8765
  
  Endpoints:
    POST /clone        Clonar voz
    POST /speak        Sintetizar texto
    GET  /voices       Listar voces
    GET  /health       Estado del servicio

  Logs:
  [17:30:01] POST /speak → 200 (1.8s) voice=maria
  [17:30:15] GET  /voices → 200
  [17:31:02] POST /speak → 200 (2.1s) voice=abuela
  
  Ctrl+C para parar
```

---

## 7. Ayuda general

```bash
$ voiceclone --help

  🎤 VoiceClone — Tu voz. Para siempre.

  Uso: voiceclone <comando> [opciones]

  Comandos:
    clone       Clonar una voz desde micrófono o archivo
    speak       Sintetizar texto con voz clonada
    voices      Gestionar voces (listar, eliminar)
    personality Configurar personalidad de voz
    server      Iniciar servidor API local
    config      Ver/editar configuración
    update      Actualizar VoiceClone
    uninstall   Desinstalar VoiceClone

  Opciones globales:
    --help       Mostrar ayuda
    --version    Mostrar versión
    --verbose    Modo detallado
    --quiet      Sin output visual

  Más info: https://voiceclone.dev/docs
  Código:   https://github.com/angellocafm-arch/voiceclone
```

---

## Notas de Implementación

- **CLI framework:** Click (Python) — ergonomía + autocompletion
- **UI terminal:** Rich (Python) — progress bars, panels, colors, tables
- **Audio playback:** sounddevice o playsound
- **Config:** ~/.voiceclone/config.json
- **Tab completion:** Click integra shell completion para bash/zsh/fish

---

*Mockups CLI — Proyecto VoiceClone*  
*Vertex Developer — 2026*  
*"voiceclone speak 'Tu voz. Para siempre.'"*
