# Capa 3: Personalidad IA — Documentación Técnica

**Fecha:** 2026-03-20  
**Estado:** ✅ Implementada y testeada (118 tests passing)  
**Versión:** 0.1.0-dev  

---

## Resumen

La Capa 3 de VoiceClone captura y reproduce el estilo de comunicación de una persona. No solo clona la voz (Capa 1), sino CÓMO habla esa persona: su vocabulario, muletillas, tono, humor, y forma de expresarse.

**Pipeline completo:**
```
Texto de entrada → [Capa 3: LLM reescribe en el estilo del usuario] → Texto estilizado → [Capa 1: TTS clona voz] → Audio
```

---

## Arquitectura

### Módulos implementados

```
src/personality/
├── __init__.py           ← Exports públicos
├── engine.py             ← PersonalityEngine (orquestador principal)
├── profile.py            ← PersonalityProfile + PersonalityManager (storage)
├── llm.py                ← LLM backends (Claude, Ollama, Identity/fallback)
└── questionnaire.py      ← Cuestionario de captura + análisis de textos
```

### Clase principal: PersonalityEngine

```python
from personality import PersonalityEngine

engine = PersonalityEngine(llm_backend="auto")
engine.initialize()

# Capturar personalidad
q = engine.start_questionnaire("maria")
q.submit_response("description", "Soy alegre y directa")
q.submit_response("formality", "Casual")
q.submit_response("warmth", "Cálido/a — me gusta conectar")
q.submit_response("energy", "Energético/a — me expreso con ganas")
profile = engine.finalize_questionnaire("maria", q)

# Aplicar personalidad
styled = engine.apply_personality("Necesito ayuda", "maria")
# → "Oye, ¿me echas una mano? Venga, que es rapidito"
```

---

## Componentes

### 1. PersonalityProfile (`profile.py`)

Dataclass que captura todos los rasgos de comunicación:

| Campo | Tipo | Descripción | Valores posibles |
|-------|------|-------------|------------------|
| `description` | str | Auto-descripción libre | Texto libre |
| `formality` | str | Nivel de formalidad | formal, casual |
| `humor_style` | str | Tipo de humor | Texto libre |
| `catchphrases` | list[str] | Muletillas/frases típicas | Lista de frases |
| `topics` | list[str] | Temas frecuentes | Lista de temas |
| `vocabulary_level` | str | Nivel de vocabulario | academic, professional, everyday, colloquial |
| `emoji_usage` | str | Uso de emojis | none, minimal, moderate, heavy |
| `sentence_length` | str | Longitud de frases | short, medium, long |
| `directness` | str | Estilo directo/indirecto | direct, indirect, varies |
| `warmth` | str | Calidez comunicativa | cold, neutral, warm, very_warm |
| `energy` | str | Nivel de energía | low, medium, high |

**Método clave:** `to_system_prompt()` — Genera el system prompt para el LLM a partir del perfil.

**Storage:**
```
~/.voiceclone/personality/{voice_name}/
├── profile.json          ← Datos estructurados (JSON)
├── profile.md            ← Versión legible (Markdown)
└── examples/             ← Textos ejemplo de la persona
    ├── questionnaire_0000.txt
    ├── whatsapp_0001.txt
    └── ...
```

### 2. Questionnaire (`questionnaire.py`)

Cuestionario guiado de 12 preguntas organizadas por categoría:

- **CORE** (4, obligatorias): description, formality, warmth, energy
- **STYLE** (2): sentence_length, directness
- **VOCABULARY** (2): catchphrases, vocabulary_level
- **EMOTIONAL** (2): humor_style, emoji_usage
- **CONTEXT** (2): topics, sample_phrases

**Funcionalidades:**
- Validación de respuestas (elección válida, campos requeridos)
- Tracking de progreso
- Serialización/restauración de estado
- Análisis de textos importados (WhatsApp, emails)
- Detección automática de: formalidad, nivel de emojis, longitud de frases, palabras frecuentes, muletillas potenciales

### 3. LLM Backends (`llm.py`)

Tres backends para la generación de texto personalizado:

| Backend | Privacidad | Calidad | Latencia | Requisitos |
|---------|-----------|---------|----------|------------|
| **ClaudeLLM** | Datos salen al API | Alta | ~1-2s | ANTHROPIC_API_KEY |
| **OllamaLLM** | 100% local | Media-alta | ~2-5s | Ollama + modelo descargado |
| **IdentityLLM** | N/A (passthrough) | N/A | 0ms | Ninguno |

**Auto-detección:** `create_llm(backend="auto")` intenta Claude → Ollama → Identity.

**Operaciones:**
- `rewrite(text, profile)` — Reescribe texto en el estilo de la persona
- `generate_samples(profile, count)` — Genera frases de ejemplo para validación

### 4. PersonalityEngine (`engine.py`)

Orquestador que conecta todo:

```
                    ┌───────────────────┐
                    │  PersonalityEngine │
                    │   (Orchestrator)   │
                    └────────┬──────────┘
                             │
             ┌───────────────┼───────────────┐
             │               │               │
    ┌────────┴──────┐ ┌─────┴──────┐ ┌──────┴────────┐
    │  Questionnaire │ │   Profile   │ │     LLM       │
    │  (capture)     │ │  Manager    │ │  (rewrite)    │
    └────────────────┘ │  (storage)  │ └───────────────┘
                       └─────────────┘
```

---

## API Endpoints

Todos los endpoints de personalidad están en la API FastAPI (`localhost:8765`):

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/personality/questions` | Lista todas las preguntas del cuestionario |
| POST | `/personality/setup` | Crea perfil de personalidad (enviar respuestas) |
| POST | `/personality/validate` | Feedback sobre frases generadas |
| POST | `/personality/speak` | Síntesis con personalidad (LLM + TTS) |
| GET | `/personality/{voice_id}` | Obtener perfil de personalidad |
| DELETE | `/personality/{voice_id}` | Eliminar perfil de personalidad |
| POST | `/personality/analyze` | Analizar textos para extraer patrones |

### Ejemplo de uso completo (curl):

```bash
# 1. Ver preguntas del cuestionario
curl http://localhost:8765/personality/questions | jq

# 2. Configurar personalidad
curl -X POST http://localhost:8765/personality/setup \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "maria",
    "questionnaire": {
      "description": "Soy alegre, me gusta bromear",
      "formality": "Casual",
      "warmth": "Cálido/a — me gusta conectar",
      "energy": "Energético/a — me expreso con ganas",
      "catchphrases": "¿Sabes?, Venga va, Qué fuerte",
      "topics": "familia, cocina, viajes"
    }
  }'

# 3. Validar frases generadas
curl -X POST http://localhost:8765/personality/validate \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "maria",
    "feedback": [
      {"phrase_index": 0, "is_accurate": true},
      {"phrase_index": 1, "is_accurate": false, "comment": "Demasiado formal"}
    ]
  }'

# 4. Síntesis con personalidad
curl -X POST http://localhost:8765/personality/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Necesito que vengas a casa", "voice_id": "maria"}' \
  --output speech.wav

# 5. Analizar textos importados
curl -X POST http://localhost:8765/personality/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "voice_id": "maria",
    "texts": ["Hola tío, ¿qué tal?", "Venga va, perfecto"],
    "source": "whatsapp"
  }'
```

---

## Decisiones Técnicas

### 1. RAG + Context Engineering vs Fine-tuning

**Elegido: RAG + Context Engineering** (Opción 2 del experto)

Razones:
- Menos datos necesarios (cuestionario de 5 min vs horas de textos)
- Funciona con LLMs cloud O locales sin modificar el modelo
- Más fácil de iterar y ajustar
- No requiere GPU para fine-tuning
- Privacidad: con Ollama todo es local

**Post-MVP:** Evaluar fine-tuning con LoRA para power users.

### 2. System Prompt como mecanismo de personalidad

El `PersonalityProfile.to_system_prompt()` genera un system prompt estructurado:
- Describe la personalidad
- Lista muletillas y vocabulario típico
- Incluye ejemplos de frases reales
- Reglas estrictas: solo devolver texto reescrito, sin añadir información

### 3. Graceful Degradation

Si el LLM falla o no está configurado:
- `/personality/speak` funciona → devuelve texto sin modificar + voz clonada
- `/speak` sigue funcionando independientemente
- `IdentityLLM` como fallback silencioso

### 4. Privacidad por diseño

- Con `OllamaLLM`: 0 datos salen del ordenador
- Con `ClaudeLLM`: solo el texto se envía, el perfil se procesa localmente
- Archivos de personalidad en `~/.voiceclone/` con permisos restrictivos
- No hay telemetría ni tracking

---

## Tests

**118 tests totales, todos passing.**

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| `test_personality.py` | 70 | Profile, Manager, Questionnaire, TextAnalysis, LLM, Engine, Pipeline |
| `test_api.py` | 21 | API endpoints (health, voices, speak, clone, personality) |
| `test_voice_engine.py` | 27 | Voice engine base, Chatterbox, XTTS, Manager |

Tests clave:
- `TestFullPipeline::test_complete_flow` — Flujo completo end-to-end
- `TestFullPipeline::test_multiple_voices` — Múltiples personalidades simultáneas
- `TestTextAnalysis::test_analyze_informal_text` — Detección de informalidad
- `TestQuestionnaire::test_build_profile` — Construcción de perfil desde respuestas
- `TestPersonalityEngine::test_full_questionnaire_flow` — Flujo cuestionario completo

---

## Integración con la Web App (Capa 2)

La web app llamará a estos endpoints en el wizard de personalización:

1. **Paso 1:** `GET /personality/questions` → mostrar cuestionario
2. **Paso 2:** Usuario responde → `POST /personality/setup`
3. **Paso 3:** Mostrar sample phrases → `POST /personality/validate`
4. **Paso 4:** Repetir validación 2-3 veces si necesario
5. **Dashboard:** `GET /personality/{voice_id}` para mostrar resumen
6. **Uso diario:** `POST /personality/speak` desde AAC software

---

*Documentación Capa 3 — Proyecto VoiceClone*  
*Vertex Developer — 2026-03-20*
