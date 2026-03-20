# Investigación: Integración AAC + Eye Tracking + Voice Cloning

**Fecha:** 2026-03-20  
**Investigador:** Tanke (Orquestador VoiceClone)  
**Fuente:** Web search + análisis técnico

---

## Pregunta Central

¿Cómo se integra una voz clonada en sistemas AAC existentes (Grid 3, Proloquo2Go)? ¿Hay APIs disponibles? ¿Cómo usa un usuario con ELA su voz clonada en su sistema AAC actual?

---

## Hallazgos

### 1. Grid 3 (Smartbox) — AAC Software Líder

**Estado 2026:**
- Grid 3 es el estándar en AAC profesional
- Soporta múltiples voces sintetizadas
- **Integración con ElevenLabs:** Grid 3 permite usar voces clonadas de ElevenLabs via API key

**Flujo con ElevenLabs:**
```
1. Usuario crea voz clonada en ElevenLabs
2. Copia API key de ElevenLabs
3. En Grid 3 → Configuración → Voces → Añade ElevenLabs API key
4. Selecciona su voz clonada de la lista
5. Todos los botones/texto sintetizan con esa voz
```

**Implicación para VoiceClone:**
- ✅ Grid 3 acepta voces de APIs externas
- Preguntas: ¿Aceptaría una API local de VoiceClone?
- ¿Necesitaría que siga el formato/protocol de ElevenLabs?

**Próximos pasos:**
- Contactar Smartbox (Grid 3 dev team)
- Solicitar documentación de API voice integration
- Validar si podemos registrar nuestra API local

---

### 2. Proloquo2Go (AssistiveWare) — AAC Mobile

**Estado 2026:**
- AAC app popular en iPad/iPhone
- Usa **Acapela Neural Voices** (TTS cloud)
- **Apple Personal Voice support:** Clave para VoiceClone

**Apple Personal Voice:**
- Feature de Apple (iOS 17+, macOS Sonoma+)
- Usuario graba ~15 minutos de voz
- Apple genera modelo TTS personal
- Cualquier app que use síntesis de Apple → usa Personal Voice

**Integración Proloquo2Go + Personal Voice:**
```
1. Usuario en iPhone → Settings → Accessibility → Personal Voice
2. Graba 15 minutos de lectura guiada
3. Apple genera Personal Voice
4. Abre Proloquo2Go
5. Selecciona Personal Voice como output
6. Todos los botones sintetizan con su voz
```

**Limitaciones:**
- Solo iOS 17+ / macOS Sonoma+ (no cobertura completa)
- Requiere hardware Apple
- No es "voz clonada" de cero, es "entreno oficial de Apple"

**Ventaja para VoiceClone:**
- ✅ Demuestra que integración con AAC es viable
- ✅ Proloquo2Go es flexible con outputs de voz
- ⚠️ Pero: Personal Voice es Apple-only

---

### 3. OpenAAC Initiative — APIs Públicas

**Qué es:**
- Comunidad de desarrollo AAC (Slack community, openAAC.org)
- Abogar por APIs públicas en software AAC
- Facilitar que developers integren servicios

**Estado 2026:**
- Grid 3, Proloquo2Go aún NO tienen APIs públicas totalmente abiertas
- Pero: Existe demanda y movimiento hacia APIs
- Algunos desarrolladores de AAC lanzan APIs (ej: JABtalk)

**Implicación para VoiceClone:**
- ✅ Hay un movimiento en la dirección correcta
- ⚠️ Pero: No podemos asumir que Grid 3 / Proloquo abrirán APIs rápido
- Alternativa: Crear nuestra propia integración local

---

## Arquitectura de Integración Propuesta

### Opción A: Integración Directa AAC (Post-MVP)

```
VoiceClone API (local)
    ↓
Grid 3 / Proloquo voice plugin
    ↓
Usuario ve "VoiceClone" en lista de voces
    ↓
Selecciona → usa voz clonada
```

**Viabilidad:**
- Requiere que Grid 3 / Proloquo tengan APIs documentadas
- O: Implementar soporte manual (sin API oficial)
- Timeline: Post-MVP, cuando APIs sean claras

### Opción B: Apple Personal Voice-like (MVP Viable)

```
1. Usuario clona voz con VoiceClone (Capa 1)
2. VoiceClone registra voz como "Personal Voice" local
3. Sistema operativo (macOS) ve la voz como opción
4. Proloquo2Go / cualquier app AAC → usa esa voz
```

**Viabilidad:**
- Requiere integración con TTS del SO (macOS NSSSpeechSynthesizer)
- Viable en MVP para macOS
- Linux: distro-dependent, más complejo
- Windows: sin equivalente directo

**Implementación MVP:**
```python
# Pseudocode macOS
from AppKit import NSSpeechSynthesizer

# Registrar voz clonada como "voz del sistema"
voice_path = "~/.voiceclone/my_voice.model"
register_system_voice(voice_path, name="Mi Voz")

# Ahora cualquier app que use NSSSpeechSynthesizer puede usar "Mi Voz"
```

### Opción C: Standalone + Integración Manual (MVP + Post-MVP)

```
MVP:
- VoiceClone standalone (clona voz, sintetiza texto)
- Usuario puede exportar audio
- Integra manualmente en Grid 3 / Proloquo (copy-paste voz)

Post-MVP:
- APIs formales con Grid 3 / Proloquo
- Integración automática
```

---

## Tobii Eye Tracking Integration

### Hardware
- **Tobii Pro Eye Tracker 5L:** €495, rango de seguimiento 18-90cm
- **Tobii Eye Tracking Core:** Integrado en algunos PCs de gaming
- **Tobii REH:** Rehabilitación, más caro, especializado

### Software Integration
- **Tobii Core SDK:** C++/Python, disponible para macOS/Windows/Linux
- **JavaScript SDK:** Limited, no recomendado para control crítico
- **Tobii Client API:** HTTP local, permite solicitudes de calibración/datos

### Recomendación para VoiceClone MVP

**Electron app con Tobii nativo:**
```cpp
// Usar Tobii Core SDK en C++ backend
// Electron frontend comunica via IPC con backend
// Gaze data → controla UI en tiempo real

Frontend (Electron):
  - Botones sensibles a mirada
  - Dwell time indicators
  - Voice cloning/synthesis UI

Backend (C++/Python + Tobii SDK):
  - Procesa gaze data en tiempo real
  - Detecta dwell events
  - Comunica con frontend via WebSocket
```

**Flujo para usuario con ELA:**
```
1. Usuario mira botón "Grabar voz"
2. Sistema detecta dwell (1-2 segundos)
3. Inicia grabación
4. Usuario mira botón "Parar"
5. Dwell → Para grabación
6. Voz clonada lista
```

---

## Plan de Integración (Fases)

### MVP (Fase 3)
- ✅ VoiceClone standalone con Tobii eye tracking
- ✅ Exportar voz clonada a archivo (.wav, .model)
- ✅ Integración manual con macOS TTS (si viable)
- ⚠️ Grid 3 / Proloquo: investigación, sin implementación aún

### Post-MVP (Fase 5+)
- Contactar Smartbox / AssistiveWare por APIs
- Implementar Grid 3 integration plugin
- Implementar Proloquo2Go integration

### Comercial (Futuro)
- Marketplace de voces para AAC users
- Soporte a cambios de voz según contexto/emoción

---

## Contactos para Próximo Paso

**Smartbox (Grid 3):**
- Developer support: developer@smartboxat.com (estimado)
- Documentación: https://www.smartboxat.com/

**AssistiveWare (Proloquo2Go):**
- Developer: https://support.assistiveware.com/
- Community: Slack de AAC

**OpenAAC:**
- Community: https://openAAC.org
- Slack: openAAC community

---

## Decisión para MVP

✅ **Arquitectura: Standalone + Tobii integrado**
- Electron app con Tobii Core SDK
- Eye tracking para control de UI
- Exportar voz clonada (.wav + modelo)
- Integración manual con AAC software (copy-paste)

✅ **Timeline:**
- Fase 2: Diseño Tobii UI + flujos
- Fase 3: Implementación Tobii + exportación
- Fase 4: Testing con usuarios ELA

✅ **Post-MVP:**
- Investigación formal con Grid 3 / Proloquo APIs
- Implementación automática si APIs disponibles

---

*Investigación completada por Tanke, 2026-03-20*
