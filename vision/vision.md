# VoiceClone — Visión del Producto
## Versión 3.0 — Validada por Ángel Fernández
## Fecha: 2026-03-20 22:14

---

## ¿Qué es VoiceClone?

**Un sistema operativo accesible por la vista, con la voz de la persona, para personas con ELA y dificultades motoras.**

No es solo un clonador de voz. Es un asistente de vida completo que:
- Habla con la voz de la persona
- Controla todo el ordenador mediante la mirada
- Corre 100% en local, sin internet, sin nube, sin suscripción

**La inspiración directa:** La arquitectura de OpenClaw. Un comando / un botón → todo eclosiona en el ordenador del usuario. El sistema nace solo, se configura solo, y está listo para usar.

---

## El Problema Real

Una persona con ELA en fase avanzada:
- No puede hablar
- No puede usar teclado ni ratón
- Solo puede mover los ojos
- Usa software AAC (tableros de comunicación) con eye tracking
- Ese software solo sirve para comunicarse — no para controlar el ordenador
- Para el resto (crear archivos, escribir emails, navegar) necesita ayuda de otra persona

**VoiceClone les devuelve la independencia digital completa.**

---

## La Solución: Dos Modelos, Un Sistema

### MODELO 1: LLM Principal (el cerebro)
El modelo de lenguaje más potente que puede correr en el ordenador del usuario.

**Función:** Todo lo que hace OpenClaw/Claude:
- Controlar el ordenador (crear carpetas, mover archivos, abrir programas)
- Redactar documentos, emails, mensajes
- Buscar y resumir información
- Crear aplicaciones simples
- Responder preguntas, ayudar a pensar
- Leer archivos de texto en voz alta con la voz del usuario
- Confirmar acciones en voz: "Carpeta creada", "Email enviado"

**Selección automática según hardware:**
```
4GB RAM   → Llama 3.2 3B   (básico, funcional)
8GB RAM   → Mistral 7B / Llama 3.1 8B
16GB RAM  → Llama 3.1 13B / Mistral Nemo
32GB RAM  → Llama 3.1 32B / Mixtral 8x7B
64GB+ / GPU → Llama 3.1 70B / Llama 3.3 70B
```

**Runtime:** Ollama (local, sin internet después de descarga)

### MODELO 2: Motor de Voz (la boca)
El motor que clona la voz de la persona y la reproduce.

**Función:**
- Sintetizar CUALQUIER texto con la voz exacta de la persona
- El LLM principal usa este motor para hablar
- El usuario lo usa para comunicarse (modo AAC)
- Leer archivos en voz alta con su propia voz

**Motor:** Chatterbox TTS (MIT) con XTTS v2 como fallback CPU
**Zero-shot:** 5-10 segundos de audio bastan para clonar la voz

---

## La Web de Descarga

**URL:** voiceclone.io (o dominio final)
**Plataforma:** Chrome y navegadores modernos

### Lo que hace la web ANTES de descargar:
1. Detecta hardware del visitante via JavaScript:
   - RAM disponible (navigator.deviceMemory)
   - CPU cores (navigator.hardwareConcurrency)
   - GPU capabilities (WebGL renderer string)
   - SO (navigator.platform / userAgent)
2. Determina el modelo LLM más potente viable
3. Muestra al usuario: "Tu ordenador puede correr [Modelo X] — [descripción en lenguaje normal]"
4. Botón: "Descargar para [macOS/Windows/Linux]"

### La instalación (un clic):
```
Usuario pulsa "Descargar"
       ↓
Descarga installer (.pkg / .exe / .deb)
       ↓
Usuario ejecuta el installer (doble clic)
       ↓
El installer:
  - Instala Python 3.10+ si falta
  - Instala Ollama
  - Descarga el modelo LLM seleccionado (~4-40GB según modelo)
  - Descarga motor de voz Chatterbox (~2GB)
  - Instala dependencias
  - Arranca servidor local (puerto 8765)
  - Abre Chrome en http://localhost:8765
       ↓
El LLM saluda y empieza el onboarding
```

---

## El Sistema Instalado — Interfaz Local en Chrome

### Pantalla de bienvenida (onboarding)
El LLM habla con el usuario en lenguaje natural:
- "Hola, soy tu asistente. Antes de empezar, vamos a guardar tu voz."
- Guía la grabación (o carga de audios anteriores)
- Clona la voz en local
- Prueba: "Di algo para confirmar que suena bien"
- Aprende la personalidad (opcional): "¿Quieres compartir textos tuyos para que aprenda cómo hablas?"
- Todo sin formularios, sin parámetros técnicos

### Módulo 1: COMUNICACIÓN (eye tracking + voz)
- Tablero de frases frecuentes (selección por mirada)
- Campo de texto libre (teclado virtual o eye tracking)
- El texto seleccionado → motor de voz → audio con su voz
- Leer archivos de texto en su voz (arrastrar PDF/TXT → lee en voz alta)
- Predicción de frases basada en historial y contexto

### Módulo 2: CONTROL DEL ORDENADOR (eye tracking + LLM)
- Panel de acciones rápidas: Crear carpeta / Abrir archivo / Email / Buscar
- Campo de instrucción libre: "Crea una carpeta en el escritorio llamada Médicos 2026"
- El LLM ejecuta la acción y confirma en voz del usuario
- Navegación web por comandos: "Abre el correo y léeme los mensajes nuevos"
- Todo accesible con la vista

### Módulo 3: PRODUCTIVIDAD
- Dictado de documentos (el usuario dicta por eye tracking → LLM redacta)
- Resumen de documentos en voz alta
- Gestión de agenda y recordatorios
- Crear y ejecutar tareas automatizadas

### Navegación entre módulos
- Gaze gesture: mirar esquina 2 segundos → menú de módulos
- Switch access: 1-2 pulsadores para navegar
- Teclado: navegación completa por teclado también
- Sin ratón necesario en ningún momento

---

## Stack Técnico

### Backend (Python)
```
src/
├── voice_engine/         # Motor de voz (Chatterbox + XTTS)
├── llm/                  # Cliente Ollama + agentes
│   ├── ollama_client.py  # Comunicación con Ollama local
│   ├── onboarding.py     # Agente de setup conversacional
│   ├── computer_control.py # Control del SO (shell commands, archivos)
│   ├── phrase_predictor.py # Predicción de frases
│   └── synthesizer_annotator.py # Metadatos de síntesis
├── rag/                  # Personalización desde documentos
│   ├── ingester.py       # WhatsApp, PDF, TXT, email
│   ├── vector_store.py   # FAISS local
│   └── retriever.py      # Búsqueda semántica
├── api/                  # FastAPI (puerto 8765)
│   └── routes/           # Endpoints: speak, chat, control, voices
└── system/               # Control del SO
    ├── file_manager.py   # Archivos y carpetas
    ├── browser_control.py # Control de Chrome
    └── app_launcher.py   # Abrir aplicaciones
```

### Frontend (Next.js → sirve en localhost:8765)
```
src/web/
├── app/
│   ├── communication/    # Módulo de comunicación + voz
│   ├── control/          # Módulo control del ordenador
│   ├── productivity/     # Módulo productividad
│   └── onboarding/       # Setup inicial conversacional
├── components/
│   ├── GazeInput.tsx     # Input por eye tracking (WebSocket)
│   ├── VoicePlayer.tsx   # Reproductor de audio generado
│   ├── PhraseBoard.tsx   # Tablero de frases frecuentes
│   ├── ChatInterface.tsx # Chat con el LLM (onboarding + control)
│   └── ActionGrid.tsx    # Grid de acciones (control del SO)
└── marketing/            # Mockups anteriores (para web pública)
```

### Installer
```
scripts/
├── install.sh            # macOS + Linux
├── install_windows.ps1   # Windows
└── hardware_detect.js    # Detección de hardware (web)
```

### Web de descarga
```
src/landing/
├── index.html            # Una pantalla, un botón
├── hardware.js           # Detección RAM/CPU/GPU
└── download.js           # Lógica de descarga según OS + hardware
```

---

## Lo que NO es VoiceClone

- ❌ No es un servicio cloud (todo local)
- ❌ No requiere suscripción
- ❌ No envía datos a ningún servidor
- ❌ No es solo para comunicación (es control completo del ordenador)
- ❌ No requiere conocimientos técnicos para instalar ni usar

---

## Criterios de Éxito del MVP

1. **Instalación:** Un usuario sin conocimientos técnicos instala el sistema en <20 minutos
2. **Clonación de voz:** La voz clonada es reconocible como la persona en un test ciego
3. **Comunicación:** Un usuario con eye tracking puede decir una frase en <10 segundos
4. **Control del ordenador:** El LLM puede crear una carpeta, escribir un documento y abrir el correo por comandos de voz/texto
5. **Privacidad:** Cero peticiones de red después de la instalación inicial (verificable con Wireshark)

---

## Diferenciadores vs Competencia

| Aspecto | VoiceClone | Alternativas |
|---------|-----------|--------------|
| Voz propia clonada | ✅ | ElevenLabs (cloud, pago) |
| Control completo del PC | ✅ | Ninguno (solo comunicación) |
| 100% local / privado | ✅ | Todo en cloud |
| Hardware adaptativo | ✅ | Ninguno |
| Open source | ✅ MIT | Todos son cerrados |
| Sin suscripción | ✅ | $20-50/mes típico |
| Eye tracking nativo | ✅ | Requiere software separado |

---

*Última actualización: 2026-03-20 22:14*
*Autor: Ángel Fernández + Tanke (Vertex Developer)*
