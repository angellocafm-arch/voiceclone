# Brief Técnico — VoiceClone

## Fecha: 2026-03-20
## Versión: 2.0 (actualizado post-Fase 2 Diseño)
## Basado en: Reunión inicial + Reunión de revisión + Reunión de diseño

---

## 1. Descripción del Proyecto

**VoiceClone** es una plataforma open source de clonación de voz + personalidad IA diseñada para personas con ELA y enfermedades que afectan al habla. Permite clonar tu voz localmente, capturar tu personalidad, y usarla a través de software de comunicación aumentativa (AAC).

**Propósito:** Que una persona que va a perder su voz (o ya la perdió) pueda preservarla y seguir comunicándose con SU voz y SU forma de expresarse.

**Claim:** "Preserva tu voz. Para siempre. 100% gratis. 100% privado. 100% local."

### 3 Capas del Sistema

| Capa | Qué hace | Stack |
|------|----------|-------|
| **Capa 1 — Motor** | Clona voz + sintetiza audio | Python + Chatterbox TTS + FastAPI |
| **Capa 2 — Web App** | Interfaz accesible para usuarios | Next.js + WCAG AA + eye tracking |
| **Capa 3 — Personalidad** | Captura cómo habla la persona | LLM local/cloud + few-shot prompting |

### Diferenciadores vs. Competencia

| Feature | VoiceClone | ElevenLabs | Apple Personal Voice |
|---------|-----------|-----------|---------------------|
| Precio | Gratis (MIT) | $5-99/mes | Gratis (solo Apple) |
| Privacidad | 100% local | Cloud | Cloud (Apple) |
| Personalidad IA | ✅ Capa 3 | ❌ | ❌ |
| Eye tracking | ✅ Nativo | ❌ | ❌ |
| Switch access | ✅ Nativo | ❌ | ❌ |
| AAC compatible | ✅ Diseñado para | Parcial | Parcial (iOS only) |
| Multi-OS | macOS, Win, Linux | Web | Solo Apple |
| Open source | ✅ MIT | ❌ | ❌ |

---

## 2. Usuarios Objetivo

### Primarios
- **Personas con ELA** que quieren preservar su voz ANTES de perderla
- **Personas que ya perdieron la voz** y se comunican por ordenador
- **Familias** que quieren preservar la voz de un ser querido

### Secundarios
- Desarrolladores interesados en voice cloning open source
- Investigadores en AAC y síntesis de voz
- Otros pacientes: parálisis cerebral, esclerosis múltiple, etc.

### 4 Perfiles de Diseño

| Perfil | Capacidades | Input primario |
|--------|-----------|---------------|
| A: ELA Temprana | Voz deteriorada, manos limitadas | Ratón/teclado lento |
| B: ELA Avanzada | Sin voz, sin manos, solo ojos | Eye tracking + switch |
| C: Cuidador | Capacidades completas | Ratón/teclado estándar |
| D: Parálisis Cerebral | Movimientos involuntarios | Switch / head tracking |

**Caso de diseño:** Perfil B (ELA avanzada). Si funciona para B, funciona para todos.

---

## 3. Modelos de IA

### Motor principal: Chatterbox TTS (Turbo)

| Aspecto | Detalle |
|---------|---------|
| Modelo | Chatterbox-Turbo (~350M params) |
| Licencia | MIT |
| Clonación | Zero-shot desde 6s de audio (óptimo 15-30s) |
| Idiomas | 23+ nativos |
| Calidad | Superior a ElevenLabs en blind tests |
| Tamaño | ~2GB |
| Hardware | CPU funcional, MPS en Apple Silicon |

### Motor fallback: XTTS v2 (descarga bajo demanda)

| Aspecto | Detalle |
|---------|---------|
| Modelo | XTTS v2 |
| Licencia | MPL 2.0 |
| Clonación | Zero-shot desde 6s |
| Idiomas | 17 |
| Tamaño | ~1.8GB |
| Descarga | Solo si el usuario lo solicita o Chatterbox falla |

**DECISIÓN:** Instalación inicial solo Chatterbox (~2.5GB total con runtime). XTTS v2 descarga bajo demanda.

---

## 4. Arquitectura Técnica

### Diagrama de Sistema

```
┌────────────────────────────────────────────────────────────┐
│                     CAPA 2: WEB APP                        │
│  Next.js · WCAG AA · Eye tracking · Switch access          │
│  Landing → Instalar → Clonar → Personalidad → Dashboard   │
└──────────────────────────┬─────────────────────────────────┘
                           │ HTTP + WebSocket
                           ▼
┌────────────────────────────────────────────────────────────┐
│                 CAPA 1: MOTOR LOCAL                         │
│  FastAPI · localhost:8765                                   │
│                                                            │
│  POST /clone     → Clona voz                               │
│  POST /speak     → Sintetiza texto                         │
│  POST /personality/speak → Con personalidad (Capa 3)       │
│  GET  /voices    → Lista voces                             │
│  GET  /health    → Status                                  │
│  WS   /gaze      → Datos eye tracking (Tobii)             │
│  POST /gaze/calibrate → Calibración eye tracker            │
│                                                            │
│  ┌───────────────┐  ┌──────────────────────────────────┐   │
│  │ Engine Adapter │  │ Personality Engine (Capa 3, opt) │   │
│  │ Chatterbox    │  │ LLM few-shot + phrase caching    │   │
│  │ (XTTS v2)    │  └──────────────────────────────────┘   │
│  └───────────────┘                                         │
│                                                            │
│  Pipeline audio: normalizar → noise reduce → VAD → resample│
└────────────────────────────────────────────────────────────┘
```

### Pipeline de Clonación

```
Audio input (mic o archivo) → Normalización → Noise reduction
→ VAD (solo segmentos con voz) → Resampling (24kHz)
→ Chatterbox clone → Speaker embedding guardado
→ Validación con frase de prueba → Voz lista
```

### Pipeline de Síntesis (con personalidad)

```
Texto input → LLM personalidad (few-shot)
→ Texto personalizado → Chatterbox TTS + embedding
→ Audio WAV → Output (web/AAC/CLI)
```

### Pipeline de Síntesis (sin personalidad)

```
Texto input → Chatterbox TTS + embedding → Audio WAV → Output
```

### Phrase Caching (AAC en tiempo real)

Pre-generación de 50-100 frases AAC comunes con voz + personalidad. Almacenadas como audio. Reproducción instantánea (<100ms) para comunicación en tiempo real.

### Storage

```
~/.voiceclone/
├── voices/{voice_id}/
│   ├── reference.wav
│   ├── embedding.pt
│   └── metadata.json
├── personality/{voice_id}/
│   ├── profile.md
│   ├── vocabulary.md
│   └── cached_phrases/
├── models/chatterbox/
└── config.json
```

---

## 5. Diseño de Web App (6 Pantallas)

| # | Pantalla | Acciones | Eye tracking targets |
|---|----------|----------|---------------------|
| 1 | Landing | 3 descargas + badge accesibilidad | 4 |
| 2 | Instalación | Solo cancelar (proceso automático) | 1 |
| 3 | Clonación | Grabar / Subir + mega-target parar | 2-3 |
| 4 | Personalidad | 3 preguntas obligatorias + 2 opcionales | 3-4 |
| 5 | Integración | 4 destinos (app, AAC, CLI, dashboard) | 4 |
| 6 | Dashboard | 2 zonas: comunicación + configuración | 6 |

**Diseño:** Wizard-style, 1 decisión por pantalla, targets 64px+, fondo oscuro #0A0A0A, tipografía Inter 20px+.

Mockups detallados en: `mockups/web-app-mockups.md`

---

## 6. Accesibilidad

### Estándar: WCAG 2.2 AA + extensiones ELA

| Feature | Implementación |
|---------|---------------|
| Eye tracking | Dwell time 800ms (configurable 200-3000ms), gaze gestures, zonas neutras |
| Switch access | Escaneo automático 1-2 pulsadores, teclado virtual con predicción |
| Teclado | Tab navigation completa, shortcuts, focus visible #FFD700 |
| Voz a texto | Web Speech API para usuarios con voz residual |
| Screen readers | ARIA completo, VoiceOver/NVDA tested |
| Contraste | Todos los pares >4.5:1 (AA), modo alto contraste disponible |
| Emergency exit | Mirar esquina sup-derecha 2s = dashboard (universal) |
| Fatigue reminder | Aviso cada 15 min de uso continuo (desactivable) |

Documento completo: `docs/diseno-accesibilidad.md` (1166 líneas)

---

## 7. Stack Tecnológico

### Backend (Motor — Capa 1 + Capa 3)
```
Python 3.12+
├── FastAPI           ← API HTTP local
├── uvicorn           ← ASGI server
├── chatterbox-tts    ← Motor de voz principal
├── noisereduce       ← Noise reduction
├── silero-vad        ← Voice Activity Detection
├── sounddevice       ← Grabación de audio
├── librosa           ← Procesamiento de audio
├── torch (CPU)       ← Inference engine
├── sentence-transformers ← RAG embeddings (Capa 3)
└── click             ← CLI framework
```

### Frontend (Web App — Capa 2)
```
Next.js 14+
├── React 18+         ← UI framework
├── Radix UI          ← Accessible components
├── Tailwind CSS      ← Styling
├── Inter font        ← Tipografía
└── swr               ← API fetching
```

### Instalación
```
macOS:  .pkg installer (sin firma MVP) + brew install
Windows: .exe NSIS (sin firma MVP) + winget
Linux:  .deb + curl | bash
Total: ~2.5GB (Chatterbox + runtime + dependencias)
```

---

## 8. Fases de Desarrollo

### ✅ Fase 1: Genesis + Investigación + Equipo (COMPLETADA)
- Visión v2 (3 capas) documentada
- 7 modelos evaluados → Chatterbox + XTTS v2
- 8 expertos con 10 referentes reales cada uno
- 3 reuniones completadas (inicial, revisión, diseño)
- Investigaciones: modelos, accesibilidad AAC, compatibilidad OpenClaw

### ✅ Fase 2: Diseño (COMPLETADA)
- Arquitectura de 3 capas integradas
- 6 mockups de web app (eye tracking compatible)
- Mockup CLI para developers
- Flujo de instalación sin terminal
- Diseño de accesibilidad (WCAG AA + eye tracking + switch)
- 15 decisiones de diseño consensuadas
- Brief v2 (este documento)

### → Fase 3: Desarrollo MVP (SIGUIENTE)
- Setup repositorio GitHub
- Entorno de desarrollo local
- Capa 1: Motor de voz (Chatterbox + pipeline audio)
- API local (FastAPI, localhost:8765)
- Capa 3: Personalidad IA (few-shot + phrase caching)
- Capa 2: Web App (Next.js, 6 pantallas)
- Testing local

### Fase 4: GitHub + Deploy Parcial
- Push código a GitHub
- GitHub Releases con instaladores
- QA final en local
- README para usuarios no técnicos
- Accessibility statement

---

## 9. Decisiones Clave (acumuladas)

### De Fase 1
1. Modelo: Chatterbox TTS Turbo (principal) + XTTS v2 (fallback)
2. Arquitectura: 3 capas (motor + web + personalidad)
3. Plataforma: macOS primero → Linux → Windows
4. Licencia: MIT
5. Público: personas con ELA (primario)

### De Fase 2
6. Chatterbox-only en instalación (~2.5GB). XTTS v2 bajo demanda.
7. Pipeline audio: normalización → noise reduction → VAD → resampling.
8. Phrase caching para frases AAC con personalidad pre-generada.
9. Eye tracking via WebSocket desde FastAPI (no Electron).
10. Mega-target 'Parar' durante grabación (100% ancho × 120px).
11. Dashboard 2 zonas: comunicación + configuración.
12. Cuestionario personalidad: 3 obligatorias + 2 opcionales.
13. Calibración guiada 5 puntos al primer uso eye tracker.
14. Emergency exit universal: esquina sup-derecha 2s = dashboard.
15. Switch access via keyboard emulation + scan mode.
16. Guía de copy/tone empoderador para la app.
17. MVP: .pkg/.exe sin firma + terminal install. Post-MVP: firma.
18. Personalidad: few-shot prompting (no fine-tuning) para MVP.

---

## 10. Criterios de Éxito

### MVP
- [ ] Web app funcional con 6 pantallas en localhost
- [ ] Clonar voz desde grabación o archivo existente
- [ ] Sintetizar texto con voz clonada (<3s en Apple Silicon)
- [ ] Personalidad básica (cuestionario + few-shot)
- [ ] Phrase caching para 50+ frases AAC
- [ ] Accesible por teclado + compatible eye tracking
- [ ] API local funcional (localhost:8765)

### V1.0
- [ ] Instaladores por OS (.pkg, .exe, .deb)
- [ ] Eye tracking completo con Tobii (WebSocket)
- [ ] Switch access con scan mode
- [ ] README accesible para personas no técnicas
- [ ] Integración con Grid 3 / Proloquo2Go documentada

### Métricas
- **MOS:** ≥ 3.5/5.0 en naturalidad
- **Speaker Similarity:** ≥ 0.75 cosine
- **Latencia (solo voz):** <3s (Apple Silicon)
- **Latencia (con personalidad):** <8s (Apple Silicon)
- **Task completion ELA:** >90% (con cualquier input method)

---

## 11. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Performance CPU insuficiente | Media | Alto | Chatterbox-Turbo + MPS + XTTS fallback |
| Eye tracking latencia WebSocket | Baja | Alto | FastAPI async + WebSocket optimizado |
| Personalidad LLM lento en CPU viejo | Media | Medio | Phrase caching + modo "solo voz" |
| Instalador bloqueado por Gatekeeper | Alta | Medio | Instrucciones visuales + terminal alt |
| Sin firma de código MVP | Alta | Bajo | Post-MVP: Apple Developer ID |
| Noise reduction insuficiente (hospital) | Media | Medio | Pipeline audio robusto + VAD |

---

## 12. Documentación del Proyecto

| Documento | Ruta | Contenido |
|-----------|------|----------|
| Visión v2 | `vision/vision.md` | 3 capas, ELA, diferenciadores |
| Arquitectura | `docs/arquitectura-completa.md` | Diagramas, pipeline, API, storage |
| Accesibilidad | `docs/diseno-accesibilidad.md` | WCAG AA, eye tracking, switch, teclado |
| AAC Research | `docs/accesibilidad-aac.md` | Grid 3, Proloquo, Tobii SDK |
| OpenClaw Compat | `docs/compatibilidad-openclaw-voz.md` | Capa 3 personalidad, digital twins |
| Instalación | `docs/flujo-instalacion.md` | .pkg, .exe, bash por OS |
| Mockups Web | `mockups/web-app-mockups.md` | 6 pantallas wireframe ASCII |
| Mockups CLI | `mockups/cli-mockups.md` | Flujo CLI developer |
| Equipo | `equipo/*.md` | 8 expertos, 10 referentes c/u |
| Reuniones | `reuniones/*.md` | 3 actas de reunión |
| Brief | `brief.md` | Este documento |

---

*Brief v2.0 — Proyecto VoiceClone — Vertex Developer — 2026*
*"Preserva tu voz. Para siempre."*