# Investigación de Modelos de Voz Open Source (Estado del Arte 2025-2026)

## Fecha: 2026-03-20
## Investigador: Tanke (Vertex Developer)

---

## Resumen Ejecutivo

Se investigaron los **principales modelos open source de clonación de voz** disponibles a marzo 2026. El objetivo es identificar el mejor modelo para VoiceClone: que funcione en CPU (sin GPU dedicada), con calidad alta, fácil instalación, y licencia permisiva.

**Recomendación preliminar:** **Chatterbox TTS** (Resemble AI) como modelo principal, con **XTTS v2** como alternativa sólida.

---

## Modelos Investigados

### 1. Chatterbox TTS (Resemble AI) ⭐ RECOMENDADO

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | Resemble AI |
| **Licencia** | MIT (100% open source) |
| **Parámetros** | ~350M (Chatterbox-Turbo) |
| **Idiomas** | 23+ idiomas nativos |
| **Clonación** | Zero-shot desde 5 segundos de audio |
| **Calidad** | Superior a ElevenLabs en blind tests independientes |
| **Latencia** | Sub-200ms (GPU), funcional en CPU |
| **GitHub** | github.com/resemble-ai/chatterbox |
| **Instalación** | `pip install chatterbox-tts` |

**Fortalezas:**
- Mejor calidad de todos los modelos open source evaluados
- Control granular de emociones y acentos
- Watermark ético integrado (PerTh neural watermark)
- Instalación trivial via pip
- Variante Turbo optimizada para hardware modesto
- Comunidad activa, trending en Hugging Face

**Debilidades:**
- CPU inference significativamente más lento que GPU
- Requiere Python 3.10+ (3.11 recomendado)
- ~5GB de espacio para modelos

**Hardware mínimo CPU:**
- RAM: 8GB (recomendado)
- Disco: ~10GB con dependencias
- macOS 12.0+ para Apple Silicon
- Python 3.10+

---

### 2. XTTS v2 (Coqui TTS) ⭐ ALTERNATIVA SÓLIDA

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | Coqui AI (cerró dic 2024) → Comunidad + Idiap Research Institute |
| **Licencia** | MPL 2.0 (open source, algunas restricciones) |
| **Idiomas** | 17 idiomas |
| **Clonación** | Zero-shot desde 6 segundos de audio |
| **Calidad** | Muy alta, "Voice Cloning King" de open source |
| **Latencia** | <150ms streaming (GPU), ~tiempo real en CPU |
| **GitHub** | github.com/coqui-ai/TTS (fork Idiap) |
| **Instalación** | `pip install TTS` |

**Fortalezas:**
- Proyecto maduro y probado en producción
- Cross-language voice cloning (clonas en español, genera en inglés)
- Rendimiento CPU aceptable: ~10s de audio en ~10-11s en CPU
- MPS acceleration en Apple Silicon (4x más rápido que CPU puro)
- Comunidad grande, mucha documentación
- El más descargado en Hugging Face

**Debilidades:**
- Empresa Coqui cerró en 2024 (ahora solo comunidad)
- Licencia MPL 2.0 (menos permisiva que MIT, pero OK para open source)
- Algunos usuarios reportan calidad inferior a Chatterbox en 2025

**Hardware mínimo CPU:**
- RAM: 4GB (8GB recomendado)
- CPU: 4+ cores
- macOS: funciona en Apple Silicon con MPS
- ~1000 palabras en ~2 minutos (CPU puro)

---

### 3. F5-TTS (Microsoft-derived)

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | SWivid (basado en E2-TTS de Microsoft) |
| **Licencia** | CC-BY-NC-4.0 (⚠️ no comercial) |
| **Clonación** | Zero-shot desde 3-10 segundos |
| **Calidad** | "Most realistic open source" según evaluaciones |
| **CPU** | ❌ MUY LENTO — 8 palabras = 7:40 minutos |
| **GitHub** | github.com/SWivid/F5-TTS |

**Fortalezas:**
- Calidad excepcional (posiblemente la mejor naturalidad)
- Arquitectura non-autoregressive innovadora
- Funciona en navegador (offline)
- Modo podcast multi-speaker

**Debilidades:**
- **DESCARTADO para VoiceClone:** CPU inference inutilizable (7+ minutos para una frase)
- Licencia no comercial
- Solo inglés y chino
- Requiere GPU para uso práctico

---

### 4. OpenVoice v2 (MyShell)

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | MyShell AI |
| **Licencia** | MIT |
| **Idiomas** | 6 idiomas (EN, ES, FR, ZH, JA, KO) |
| **Clonación** | Zero-shot, separada del TTS base |
| **CPU** | ✅ Funcional — requisitos bajos |
| **GitHub** | github.com/myshell-ai/OpenVoice |

**Fortalezas:**
- Requisitos de hardware muy bajos (4GB RAM, dual-core 2GHz)
- Licencia MIT
- Arquitectura modular: voice cloning separado de TTS base
- Funciona en CPU

**Debilidades:**
- Calidad inferior a Chatterbox y XTTS en 2025
- Solo 6 idiomas
- Menos expresividad emocional
- Comunidad más pequeña

---

### 5. Kokoro

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | Hexgrad |
| **Licencia** | Apache 2.0 |
| **Parámetros** | 82M (ultra ligero) |
| **CPU** | ✅ Excelente — "ultra-fast, CPU-friendly" |

**⚠️ DESCARTADO:** No tiene clonación de voz nativa. Solo voces predefinidas. Excelente TTS pero no sirve para el caso de uso de VoiceClone.

---

### 6. StyleTTS2

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | Columbia University |
| **Licencia** | MIT |
| **Clonación** | Sí, con fine-tuning |
| **CPU** | ⚠️ Lento, requiere 16 cores para fine-tuning |

**Debilidades:**
- Fine-tuning (no zero-shot) para clonación → complejidad para usuario final
- Requiere dataset más grande
- CPU: funcional para inference, pero lento

---

### 7. CosyVoice2 (Alibaba)

| Aspecto | Detalle |
|---------|---------|
| **Desarrollador** | Alibaba/FunAudioLLM |
| **Licencia** | Apache 2.0 |
| **Idiomas** | 9 idiomas + 18 dialectos chinos |
| **Clonación** | Zero-shot |
| **CPU** | ❌ 10-50x más lento, requiere 16GB+ RAM |

**Fortalezas:**
- Streaming ultra-low latency (con GPU)
- Multilingüe excepcional
- Control emocional y dialectal fino

**Debilidades:**
- CPU inference impracticable (10-50x más lento)
- Orientado a GPU
- Setup complejo

---

## Tabla Comparativa Final

| Modelo | Calidad | CPU Performance | Licencia | Instalación | Idiomas | Clonación Zero-Shot | Comunidad | Score |
|--------|---------|----------------|----------|-------------|---------|-------------------|-----------|-------|
| **Chatterbox** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | MIT ✅ | `pip install` ✅ | 23+ | 5s ✅ | ⭐⭐⭐⭐ | **9/10** |
| **XTTS v2** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | MPL 2.0 | `pip install` ✅ | 17 | 6s ✅ | ⭐⭐⭐⭐⭐ | **8.5/10** |
| **OpenVoice v2** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | MIT ✅ | Manual ⚠️ | 6 | ✅ | ⭐⭐⭐ | **7/10** |
| **F5-TTS** | ⭐⭐⭐⭐⭐ | ⭐ | CC-NC ❌ | Manual ⚠️ | 2 | ✅ | ⭐⭐⭐ | **5/10** |
| **CosyVoice2** | ⭐⭐⭐⭐ | ⭐ | Apache ✅ | Complejo ❌ | 9+ | ✅ | ⭐⭐⭐ | **5/10** |
| **Kokoro** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Apache ✅ | `pip install` ✅ | Multi | ❌ NO CLONA | ⭐⭐⭐ | N/A |
| **StyleTTS2** | ⭐⭐⭐⭐ | ⭐⭐ | MIT ✅ | Manual ⚠️ | EN | Fine-tune ⚠️ | ⭐⭐⭐ | **5.5/10** |

---

## Recomendación

### Modelo principal: **Chatterbox TTS (Resemble AI)**

**Por qué:**
1. **Mejor calidad** — supera a ElevenLabs en blind tests
2. **MIT License** — máxima libertad
3. **Zero-shot 5s** — mínimo audio necesario
4. **pip install** — instalación trivial
5. **23+ idiomas** — cobertura excepcional
6. **Ethical watermarking** — responsabilidad incluida
7. **Chatterbox-Turbo** — variante optimizada para hardware modesto

### Modelo alternativo: **XTTS v2**

**Por qué como backup:**
1. Mejor rendimiento CPU (casi real-time con MPS en Apple Silicon)
2. Proyecto maduro con más documentación
3. Cross-language cloning único
4. Comunidad más grande

### Estrategia propuesta:
- **Default:** Chatterbox TTS como motor principal
- **Fallback:** XTTS v2 como alternativa si Chatterbox no funciona en hardware del usuario
- **Futuro:** Arquitectura modular que permita cambiar modelos

---

## Fuentes

- Resemble AI (resemble.ai/chatterbox)
- Coqui TTS GitHub (github.com/coqui-ai/TTS)
- F5-TTS (github.com/SWivid/F5-TTS)
- OpenVoice (github.com/myshell-ai/OpenVoice)
- Hugging Face Model Hub
- Reddit r/LocalLLM, r/MachineLearning
- DigitalOcean tutorials
- Hyperstack.cloud comparative analysis
- Multiple independent benchmark reports (2025)
