# 🎤 VoiceClone — Tu voz, para siempre

![Version](https://img.shields.io/badge/version-0.3.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

**Un asistente de vida completo para personas con ELA y dificultades motoras.**

VoiceClone clona tu voz con solo 5 segundos de audio y la convierte en tu herramienta para seguir comunicándote, controlando tu ordenador, leyendo documentos y enviando mensajes — todo con tu propia voz.

100% gratis. 100% privado. 100% local. Sin internet, sin nube, sin suscripción.

---

## ⚡ Instalación rápida (3 comandos)

**macOS / Linux:**
```bash
curl -fsSL https://github.com/angellocafm-arch/voiceclone/releases/latest/download/install.sh | bash
```

**Windows (PowerShell como Administrador):**
```powershell
irm https://github.com/angellocafm-arch/voiceclone/releases/latest/download/install_windows.ps1 | iex
```

**¿Qué necesito?** Un ordenador con 4GB+ de RAM y 5GB de espacio libre. Nada más.

**¿Qué se instala?** Python, un modelo de IA local (Ollama), y el motor de voz Chatterbox TTS. Todo se queda en tu ordenador. Nada va a la nube.

---

## ¿Qué hace VoiceClone?

### 💬 Comunicación
Selecciona frases rápidas o escribe texto libre. VoiceClone lo dice en voz alta con **tu voz clonada**.

- Tablero de frases frecuentes (seleccionables con la mirada)
- Teclado virtual adaptado
- Predicción inteligente de frases basada en tu historial
- Tu voz suena exactamente como tú

### 🖥️ Control del Ordenador
Dale instrucciones en lenguaje natural y VoiceClone ejecuta:

- *"Crea una carpeta llamada Médicos 2026"*
- *"Abre el navegador en Google"*
- *"Lee mi último email"*
- *"Busca el archivo de la receta"*

Todo con confirmación por seguridad. Nada se ejecuta sin tu permiso.

### 📝 Productividad
- Dicta documentos con tu voz
- Arrastra un PDF o TXT y VoiceClone lo lee en voz alta
- Agenda y recordatorios
- Resúmenes automáticos de documentos

### 📱 Mensajería
Envía y recibe mensajes por tus canales habituales:

- **Telegram** — Completamente funcional
- **WhatsApp** — En desarrollo
- **Signal** — En desarrollo

Los mensajes entrantes se leen con tu voz. Respondes desde la interfaz.

---

## Instalación

### macOS (Apple Silicon o Intel)
```bash
curl -fsSL https://raw.githubusercontent.com/angellocafm-arch/voiceclone/main/scripts/install.sh | bash
```

### Linux (Ubuntu/Debian/Fedora)
```bash
curl -fsSL https://raw.githubusercontent.com/angellocafm-arch/voiceclone/main/scripts/install.sh | bash
```

### Lo que hace el instalador:
1. Detecta tu hardware (RAM, CPU, GPU)
2. Descarga el modelo de IA más potente que tu ordenador pueda correr
3. Instala el motor de voz
4. Abre Chrome en `http://localhost:8765`
5. Te guía por el proceso de clonar tu voz — sin formularios, solo hablando

### Requisitos mínimos
- **4 GB de RAM** (recomendado 8 GB o más)
- **macOS 12+** o **Linux** (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- **2 GB de espacio en disco** (modelos incluidos)

---

## Los 4 Módulos

| Módulo | Qué hace | Cómo se usa |
|--------|----------|-------------|
| 💬 Comunicación | Habla con tu voz clonada | Selecciona frases o escribe texto |
| 🖥️ Control | Controla el ordenador | Dale instrucciones naturales |
| 📝 Productividad | Dicta, lee, organiza | Arrastra archivos, dicta texto |
| 📱 Mensajería | Telegram, WhatsApp, Signal | Lee y responde mensajes |

---

## Accesibilidad

VoiceClone está diseñado para personas con movilidad reducida:

- **Eye tracking:** Controla todo con la mirada (compatible con Tobii y otros)
- **Selección por fijación:** Mira un botón 800ms para activarlo (configurable)
- **Targets grandes:** Todos los botones miden al menos 64px
- **Alto contraste:** Tema oscuro optimizado, soporte para alto contraste
- **Teclado:** Navegación completa con Tab + Enter
- **Atajos:** ⌘1-4 para cambiar entre módulos
- **Screen readers:** Compatible con VoiceOver y NVDA

---

## Tecnología

| Componente | Tecnología | Licencia |
|------------|------------|----------|
| Voz | [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) + XTTS v2 | MIT / LGPL |
| IA | [Ollama](https://ollama.ai) + Llama/Mistral | MIT |
| Frontend | Next.js 16 + React 19 + Tailwind | MIT |
| Backend | FastAPI + Python 3.10+ | MIT |
| Canales | Arquitectura inspirada en [OpenClaw](https://github.com/openclaw/openclaw) | MIT |

### Modelos según hardware

| RAM disponible | Modelo seleccionado |
|----------------|---------------------|
| 4 GB | Llama 3.2 3B |
| 8 GB | Mistral 7B |
| 16 GB | Llama 3.1 13B |
| 32 GB | Llama 3.1 32B |
| 64 GB+ GPU | Llama 3.1 70B |

El instalador detecta tu hardware automáticamente y descarga el modelo óptimo.

---

## Privacidad

- **Sin internet:** Funciona completamente offline después de la instalación
- **Sin nube:** Tu voz nunca sale de tu ordenador
- **Sin cuenta:** No necesitas registrarte en nada
- **Sin telemetría:** No enviamos datos de uso
- **Código abierto:** Puedes verificar exactamente qué hace

---

## Para desarrolladores

### Estructura del proyecto

```
src/
├── api/          # FastAPI server (puerto 8765)
├── llm/          # Ollama client, onboarding agent, predictor
├── system/       # Control del SO (archivos, browser, apps, email)
├── channels/     # Canales de mensajería (Telegram, WhatsApp)
├── rag/          # Ingesta y búsqueda vectorial
├── voice_engine/ # Motor de voz (Chatterbox + XTTS)
├── landing/      # Página de descarga (detección hardware)
└── web/          # Frontend Next.js (app principal)
    └── src/
        ├── app/          # Next.js app router
        ├── components/
        │   ├── AppShell.tsx        # Layout con sidebar
        │   ├── GazeTracker.tsx     # Eye tracking
        │   ├── OnboardingScreen.tsx # Setup conversacional
        │   └── modules/
        │       ├── CommunicationModule.tsx
        │       ├── ControlModule.tsx
        │       ├── ProductivityModule.tsx
        │       └── ChannelsModule.tsx
        └── lib/          # API client, utils
```

### Ejecutar en desarrollo

```bash
# Backend
cd src && python -m api.main

# Frontend
cd src/web && npm install && npm run dev

# Ollama (en otra terminal)
ollama serve
```

---

## Licencia

MIT — Úsalo, modifícalo, compártelo. Es tuyo.

---

## Créditos

Proyecto de [Vertex Developer](https://vertexdeveloper.com) — Ángel Fernández & Enrique Alonso.

Inspirado por la comunidad de personas con ELA y sus familias. 
Construido con cariño y con la convicción de que la tecnología debe servir a todos.

---

*Tu voz es tuya. Para siempre.*
