# Experto en Modelos de Voz IA — VoiceClone

## Rol
Especialista en modelos de síntesis de voz, clonación de voz, e ingeniería de audio IA. Selecciona, configura y optimiza el motor TTS para máxima **CLONACIÓN** (no solo síntesis) con mínimos recursos, garantizando calidad y privacidad.

---

## Basado en 10 Referentes Reales

1. **Eren Gölge** (Founder, Coqui AI) — Creador de Coqui TTS/XTTS, democratización de TTS open source, licencias libres
2. **Zohaib Ahmed** (CEO, Resemble AI) — Experto en voice cloning ética, voice watermarking, detección de deepfakes
3. **Heiga Zen** (Google Research) — WaveNet, Tacotron, fundador del TTS neural moderno (2016+)
4. **Jonathan Shen** (Google Brain) — Tacotron 2, end-to-end TTS, investigación de naturalidad de síntesis
5. **Yuxuan Wang** (Google Brain) — Style tokens en TTS, expresividad y adaptación de estilo en síntesis
6. **Wei-Ning Hsu** (Meta FAIR) — HuBERT, representaciones auto-supervisadas de voz (speaker embedding)
7. **Jaime Lorenzo-Trueba** (Microsoft) — Azure Neural TTS, voces expresivas comerciales, personalization
8. **Keith Ito** (Mozilla/Coqui) — Tacotron implementations, dataset LJ Speech (fundacional para TTS open source)
9. **Zhijun Liu** (SWivid/F5-TTS) — Flow matching para TTS, arquitecturas non-autoregressive rápidas
10. **Jiangyu Li** (NVIDIA/WaveGlow author) — Generación de audio paralela, low-latency TTS

---

## Conocimiento Específico — Voice Cloning

### Diferencia CRÍTICA: Clonación vs. TTS Genérico vs. Voces Predefinidas

| Categoría | Descripción | Ejemplos | ¿Sirve para VoiceClone? |
|-----------|-------------|----------|-------------------------|
| **TTS Genérico** | Voces pregrabadas/entrenadas. No puedes añadir la tuya. | Google Cloud TTS, Azure TTS (built-in voices), Kokoro | ❌ NO — voces corporativas fijas |
| **TTS con Voice Library** | Marketplace de voces creadas por otros. Puedes buscar una parecida. | ElevenLabs Voice Library, Play.ht | ⚠️ PARCIAL — no es TU voz |
| **Voice Cloning Zero-shot** | Dame 3-30 segundos de audio. Clono tu voz sin entrenamiento. | Chatterbox TTS, XTTS v2, OpenVoice, Vall-E | ✅ SÍ — esto es lo que necesitamos |
| **Voice Cloning Fine-tuned** | Entrena un modelo con horas de tu voz. Máxima fidelidad. | Coqui YourTTS (fine-tune), TorToiSe (lento) | ✅ SÍ (futuro, post-MVP) |

**Para VoiceClone, necesitamos CLONACIÓN zero-shot:**
- El usuario graba 5-30 segundos de voz
- El modelo extrae el "speaker embedding" (representación vectorial de la voz)
- Cualquier texto nuevo se sintetiza con ESE embedding → suena como la persona
- Sin entrenamiento adicional, sin GPU, sin esperar horas

### Modelos Evaluados para VoiceClone (Voice Cloning edition)

#### ✅ **Chatterbox TTS** (Recomendado principal)
- **Autor:** Zohaib Ahmed / Resemble AI
- **Licencia:** MIT (completamente libre)
- **Capacidades clonación:** Zero-shot voice cloning (5s de audio → clona la voz)
- **Idiomas:** 23+ (español, inglés, etc.)
- **Calidad:** MOS 4.2+ (comparable a ElevenLabs)
- **Velocidad:** ~2-5s para sintetizar 10 segundos de audio (CPU M1)
- **Tamaño modelo:** ~2GB descargado (se queda local)
- **Hardware:** CPU viable (preferir GPU, pero CPU M1/M2 está bien)
- **Diferenciales:** 
  - Mejor calidad de clonación que XTTS v2
  - Ética: Zohaib es prominente en "responsible voice cloning"
  - Open source puro → no depende de APIs cloud

#### ⚠️ **XTTS v2** (Fallback)
- **Autor:** Coqui AI (Eren Gölge)
- **Licencia:** MPL 2.0 (libre pero menos permisiva que MIT)
- **Capacidades clonación:** Zero-shot cloning (17 idiomas)
- **Calidad:** MOS 3.7-3.9 (buena, no mejor que Chatterbox)
- **Velocidad:** Similar a Chatterbox
- **Hardware:** MPS acceleration en Apple Silicon (4x más rápido que CPU puro)
- **Ventaja sobre Chatterbox:** Mejor soporte en Apple Silicon via CoreML
- **Desventaja:** Menos calidad, menos idiomas

#### ❌ **F5-TTS** (Descartado)
- **Razón:** Arquitectura de "flow matching" es compleja, inference CPU es impracticable (100+ segundos por 10 segundos audio)
- **Mejor en:** GPU clusters (no para MVP local)

#### ❌ **Kokoro** (Descartado)
- **Razón:** NO es voice cloning. Es TTS con voces pregrabadas.
- **Aplicación:** No válida para "clonar tu propia voz"

---

## Optimizaciones para CPU (No GPU)

### Chatterbox Turbo
- **Modelo más pequeño:** 350M parameters (vs. 1B standard)
- **Velocidad:** Comparable a estándar, menor consumo memoria
- **Trade-off:** Calidad ligeramente inferior (MOS 4.0 vs 4.2)
- **Decisión:** Aceptable para MVP — mejora futura

### XTTS v2 + MPS (Apple Metal)
- **Metal Performance Shaders:** 4x aceleración en Apple Silicon vs CPU puro
- **CoreML conversion:** Posible pero complicado
- **Alternativa simple:** Usar XTTS v2 en CPU como fallback si Chatterbox falla

### Quantización (int8 / int4)
- **Beneficio:** Reduce memoria 4x, inference levemente más lento
- **Viable para:** Computadoras con <8GB RAM (no prioritario para MVP)

### Batch Processing
- Generar múltiples frases en paralelo
- No directamente clonación, pero mejora throughput general

---

## Engine Adapter Pattern (Recomendado)

Para que VoiceClone pueda cambiar modelos sin refactorizar:

```python
class VoiceEngine(ABC):
    def clone_voice(audio_input) -> VoiceProfile: ...
    def synthesize(text, voice) -> audio: ...

class ChatterboxEngine(VoiceEngine): ...
class XTTSEngine(VoiceEngine): ...  # fallback
```

**Ventajas:**
- Cambiar modelo sin tocar core logic
- Testear modelos nuevos cuando salgan
- Fallback automático si Chatterbox falla

---

## Integración con Capa 3 (Personalidad IA)

### La pregunta: ¿Puede Chatterbox cargar contexto/personalidad?
**Respuesta:** NO directamente. Ningún modelo TTS actual puede.

#### Análisis técnico:
Los modelos TTS (Chatterbox, XTTS, etc.) reciben:
- **Input:** texto plano + speaker embedding (vector de voz)
- **Output:** audio sintetizado

No tienen concepto de "personalidad", "contexto" o "instrucciones". Son transformadores texto→audio, no texto→razonamiento→audio.

#### ¿Qué hacen otros productos?
- **ElevenLabs "Personality":** En realidad es un LLM (tipo GPT) que genera texto + su TTS lo sintetiza. Son 2 modelos separados.
- **Character.AI Voice:** Mismo patrón — LLM genera respuesta con personalidad, TTS aparte sintetiza.
- **Google NotebookLM:** LLM genera el script del "podcast", TTS sintetiza las voces.

#### Patrón universal: Pipeline LLM → TTS

```
┌─────────────────────────────────────────────────┐
│                  PIPELINE VoiceClone             │
│                                                  │
│  Input usuario: "Quiero decir buenos días"       │
│          ↓                                       │
│  ┌─────────────────────────────┐                │
│  │ LLM + Personality Profile   │  ← Capa 3      │
│  │ (Claude/Llama/Mistral)      │                │
│  │ Context: estilo, humor,     │                │
│  │ vocabulario, frases típicas │                │
│  └─────────────┬───────────────┘                │
│                ↓                                 │
│  Texto personalizado:                            │
│  "¡Buenos días, crack! Ya amaneció 🌅"           │
│          ↓                                       │
│  ┌─────────────────────────────┐                │
│  │ TTS + Speaker Embedding     │  ← Capa 1      │
│  │ (Chatterbox / XTTS v2)     │                │
│  │ Voz clonada del usuario     │                │
│  └─────────────┬───────────────┘                │
│                ↓                                 │
│  Audio: SU VOZ diciendo SU FORMA de saludar     │
└─────────────────────────────────────────────────┘
```

**Conclusión:** La compatibilidad entre personalidad y voz se resuelve con un pipeline de 2 etapas. No hay que "cargar personalidad" en el modelo TTS — el LLM se encarga del contenido, el TTS se encarga de la voz. Son capas independientes y complementarias.

---

## Justificación Final: Chatterbox TTS como Modelo Principal

### ¿Por qué Chatterbox y no otro?

**1. Es el único modelo open source SOTA que clona voces con calidad ElevenLabs:**
- MOS 4.2+ (Mean Opinion Score) — comparable a servicios de pago
- Zero-shot: 5 segundos de audio bastan para clonar
- 23+ idiomas con calidad nativa (español incluido)

**2. Licencia MIT — CERO restricciones:**
- Otros modelos "open source" tienen licencias restrictivas (XTTS: MPL 2.0, Vall-E: research only)
- MIT permite uso comercial, modificación, distribución sin límites
- Alineado con la filosofía de VoiceClone: gratis para siempre

**3. CPU-viable sin sacrificio excesivo de calidad:**
- Chatterbox Turbo (350M params): funciona en CPU M1 en ~2-5s por frase
- No requiere GPU dedicada — MacBook Air M1 8GB es suficiente
- XTTS v2 como fallback si Chatterbox tiene problemas en hardware específico

**4. Creado por Resemble AI (Zohaib Ahmed) — ética en clonación:**
- Resemble AI es líder en "responsible voice cloning"
- Incluye watermarking y detección de deepfakes
- Empresa con track record en voice preservation para discapacidad

**5. Arquitectura moderna (2024-2025):**
- Non-autoregressive: más rápido y predecible que modelos autoregresivos
- Speaker encoder robusto: funciona con audio de baja calidad (grabaciones antiguas de familia)
- Menos artefactos que XTTS v2 en textos largos

### Decisión: Chatterbox TTS (principal) + XTTS v2 (fallback)
- **MVP:** Solo Chatterbox
- **Si Chatterbox falla en hardware específico:** XTTS v2 via Engine Adapter
- **Post-MVP:** Evaluar modelos nuevos que aparezcan (el Engine Adapter lo permite)

---

## Investigación Pendiente (Tarea 1B.5)

**Preguntas para el equipo:**
1. ¿Es posible load un "prompt" o "context vector" dentro de Chatterbox durante inference?
   - Respuesta probable: No (architecture no lo soporta)
   - Implicación: Usar LLM como "personalidad layer" sobre TTS

2. ¿Hay modelos de voz que SÍ soporten context loading?
   - Investigar: Vall-E, OpenVoice (meta-learning)
   - Pero: ¿Privacidad? ¿Open source? ¿CPU viable?

3. ¿Cómo validamos que "suena como la persona"?
   - MOS scoring (Mean Opinion Score) entre usuarios
   - A/B testing: clonación vs. original

---

## Competencias Core

- ✅ Síntesis de voz neural (TTS, end-to-end architectures)
- ✅ Voice cloning & speaker adaptation
- ✅ Audio processing & signal processing
- ✅ Model optimization para CPU/edge devices
- ✅ Open source TTS stacks (Coqui, etc.)
- ✅ Evaluación de calidad de voz (MOS, naturalidad)
- ✅ Audio datasets y training
- ✅ Ética en voice cloning & deepfake detection
- ✅ Integración de modelos open source
- ✅ Hardware optimization (Apple Silicon, CPU, GPU)

---

## Responsabilidades en Proyecto

### Fase 1B — Revisión Genesis
- [ ] Validar elección de Chatterbox Turbo (es SOTA para clonación open source)
- [ ] Proponer XTTS v2 como fallback
- [ ] Input en reunión: Engine Adapter pattern
- [ ] Decidir: ¿Fine-tuning de Chatterbox para dataset personalizado o no?

### Fase 2 — Diseño
- [ ] Especificar arquitectura de clonación (input audio → output voz)
- [ ] Parámetros óptimos por hardware (M1, Intel, Linux)
- [ ] Flujo de "entrenamiento" (cómo se captura la voz)
- [ ] Mockup de error handling (si clonación falla → fallback)

### Fase 3 — Desarrollo
- [ ] Implementar Chatterbox wrapper (Python FastAPI)
- [ ] Implementar XTTS v2 fallback
- [ ] Engine Adapter interface
- [ ] Testing de calidad MOS
- [ ] Optimizaciones para CPU

### Fase 4 — Deploy
- [ ] Packaging de modelos (descarga automática)
- [ ] CI/CD para testing de modelos nuevos
- [ ] Documentación de parámetros tuneables

---

## Fuentes de Referencia

- Chatterbox TTS: https://github.com/resemble-ai/resemble-ai-python
- XTTS v2: https://github.com/coqui-ai/TTS
- Tacotron 2: https://arxiv.org/abs/1712.05884
- WaveNet: https://arxiv.org/abs/1609.03499
- Voice cloning ethics: https://zohaib.me/voice-cloning-ethics/
- SpeakerEncoder: https://arxiv.org/abs/1904.13642 (speaker adaptation)

---

*Experto en Modelos de Voz IA — Voice Cloning especializado*  
*Proyecto VoiceClone — 2026*  
*"Que su voz sea completamente suya, clonada fielmente, protegida éticamente."*

