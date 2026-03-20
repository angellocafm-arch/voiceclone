# Reunión de Equipo — Evolución Capa 3: LLM como Orquestador de Comunicación

## Fecha: 2026-03-20, 21:45
## Tipo: Plenaria — Rediseño Capa 3
## Convocada por: Ángel (vía Orquestador)
## Estado: ARCHIVADA — pendiente de implementación

---

## Contexto que trajo Ángel

La persona con ELA **no genera texto desde cero**. Lo que hace es:
- Mirar la pantalla con eye tracking
- Seleccionar frases hechas, palabras, o construir frases desde un teclado de símbolos (AAC)
- El sistema habla por ella con su voz clonada

El LLM **no es para que la persona escriba más fácil**. Es para:

1. **Orquestar la clonación** — que el setup no sea un formulario cerrado con parámetros fijos, sino que la familia pueda personalizar el sistema pasándole documentación, conversaciones, posts de redes sociales
2. **Predicción de frases** — antes de que el texto crudo llegue al motor de voz, el LLM puede sugerir cómo completar la frase o predecir lo que la persona va a decir (basándose en historial + personalidad)
3. **Control de síntesis** — el LLM puede añadir anotaciones invisibles al usuario que le digan al motor de voz cómo reproducir el audio: más rápido, más lento, tono serio, tono alegre, pausa aquí

Ejemplo concreto:
```
Persona mira "gracias" en tablero AAC
       ↓
LLM recibe: "gracias"
LLM tiene contexto: están en una situación emotiva (familia reunida)
LLM anota: [emoción: cálida, velocidad: lenta, pausa antes]
       ↓
Motor de voz recibe: "gracias [pausa=0.5s] [emoción=warm]"
       ↓
Audio suena exactamente como lo diría esa persona
```

---

## Lo que cambia en la arquitectura

### Antes (estado actual en GitHub)
```
Texto del usuario → LLM (básico, casi no modifica) → Motor de voz → Audio
```

### Después (nueva arquitectura Capa 3)
```
Selección AAC / eye tracking → texto crudo
       ↓
LLM con:
  - Perfil de personalidad (documentos, textos, redes sociales)
  - Contexto de la conversación actual
  - Predictor de frases (basado en historial)
  - Generador de anotaciones de síntesis
       ↓
Texto anotado (enriquecido, NO visible al usuario)
       ↓
Motor de voz (interpreta anotaciones → velocidad, emoción, pausas)
       ↓
Audio que suena como esa persona lo diría EN ESE MOMENTO
```

---

## Decisiones de la reunión

### DECISIÓN 1: LLM local obligatorio
- **Modelo:** Ollama con Mistral 7B o Llama 3.1 8B
- **Por qué local:** La persona usa el ordenador para comunicarse. No puede depender de internet. Si hay corte → silencio. Inaceptable.
- **Fallback:** Si Ollama no está disponible → texto crudo directamente al motor de voz (degradación elegante)

### DECISIÓN 2: Sistema de personalización por documentos (RAG ligero)
- La familia puede subir: conversaciones de WhatsApp, emails, posts de redes, diarios, cualquier texto
- El LLM indexa esos documentos en una base vectorial local (Chroma o FAISS)
- Cuando la persona habla, el LLM busca patrones similares en esos documentos
- Resultado: el sistema aprende a hablar como esa persona sin que nadie programe nada

### DECISIÓN 3: Protocolo de anotaciones de síntesis
Definir un lenguaje mínimo de anotaciones que el LLM puede insertar:
```
[speed=slow]     → habla más despacio
[speed=fast]     → habla más rápido  
[emotion=warm]   → tono cálido
[emotion=serious] → tono serio
[pause=0.3s]     → pausa de 0.3 segundos
[emphasis]texto[/emphasis] → énfasis en esa palabra
```
El motor de voz aprende a interpretar estas anotaciones. El usuario nunca las ve.

### DECISIÓN 4: Predicción de frases proactiva
- Mientras la persona "escribe" con el eye tracking, el LLM en segundo plano predice las 3-5 frases más probables
- Se muestran en pantalla como opciones seleccionables con la mirada
- Reduce el tiempo para decir algo de 30 segundos a 3-5 segundos

### DECISIÓN 5: Contexto de conversación
- El sistema guarda las últimas N frases de la conversación activa
- El LLM usa ese contexto para que las respuestas sean coherentes
- Ejemplo: si acaban de hablar de un tema, las predicciones son relevantes a ese tema

---

## Impacto en el código existente

### personality/backends/ → REDISEÑAR
- Añadir: `ollama_rag_backend.py` — LLM local con RAG sobre documentos de la persona
- Añadir: `annotation_generator.py` — genera anotaciones de síntesis
- Añadir: `phrase_predictor.py` — predicción de frases basada en historial

### voice_engine/ → AMPLIAR
- Añadir soporte de anotaciones SSML-like en Chatterbox y XTTS
- `synthesize_with_annotations(text_with_annotations)` 

### web/components/ → AMPLIAR
- `PersonalityScreen` → añadir upload de documentos (WhatsApp, emails, etc.)
- `DashboardScreen` → añadir panel de predicciones en tiempo real
- Nuevo componente: `ConversationMode` — modo de uso real (eye tracking activo)

### Nuevo módulo: rag/
- `document_ingester.py` — parsea WhatsApp exports, emails, PDFs, TXT
- `vector_store.py` — FAISS local, embeddings con sentence-transformers
- `context_retriever.py` — recupera fragmentos relevantes en tiempo real

---

## Trabajo pendiente de implementar

- [ ] Diseñar protocolo de anotaciones de síntesis completo
- [ ] Implementar RAG local con FAISS + sentence-transformers
- [ ] Implementar document_ingester (WhatsApp, email, TXT, PDF)
- [ ] Implementar phrase_predictor con historial de conversación
- [ ] Ampliar motor de voz para interpretar anotaciones
- [ ] Rediseñar PersonalityScreen para upload de documentos
- [ ] Implementar ConversationMode (pantalla de uso real)
- [ ] Integrar con eye tracking WebSocket (frases predichas visibles)

---

## Nota del Orquestador

Esta es la parte que convierte VoiceClone de "una herramienta de clonación de voz" en "la voz digital de una persona". Es el diferenciador real. Ninguna plataforma existente (ElevenLabs, Resemble AI, etc.) hace esto de forma open source y local.

El trabajo de Fase 3 existente sigue siendo válido como base. Esta evolución se construye encima, no reemplaza.

---

**Próximo paso:** Ángel revisa y da OK → el equipo implementa estas mejoras en una Fase 3B.

*Archivada el 2026-03-20 21:45*
