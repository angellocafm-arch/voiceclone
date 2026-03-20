# Reunión de Equipo Ampliada — Revisión de Visión (3 Capas)

## Fecha: 2026-03-20, 17:10
## Tipo: Plenaria — Revisión de Visión + Onboarding Nuevos Expertos
## Convocada por: Orquestador

---

## Participantes

| Experto | Rol | Status |
|---------|-----|--------|
| **Orquestador** | Tech Lead / Director Técnico | Existente |
| **Comunicador IA** | Ingeniero de Comunicación con IA | Existente |
| **Experto Voz IA** | Modelos de síntesis + clonación | Existente |
| **Experto UX** | Experiencia de usuario + instaladores | Existente |
| **Experto DevOps** | Packaging + distribución + CI/CD | Existente |
| **Experto Audio** | Procesamiento de audio + señal | Existente |
| **Experto Accesibilidad** | WCAG + Eye tracking + AAC + AT | 🆕 NUEVO |
| **Experto Personalidad IA** | LLM personality + context + digital twins | 🆕 NUEVO |

---

## Contexto

La visión del proyecto ha evolucionado significativamente desde la reunión inicial. Lo que empezó como un motor de clonación de voz local ahora es un sistema de **3 capas** diseñado específicamente para **personas con ELA y discapacidades similares**. Se requiere:

1. Onboarding de 2 nuevos expertos (Accesibilidad + Personalidad IA)
2. Validación de la viabilidad técnica de cada capa
3. Alinear al equipo completo con la nueva visión

---

## Parte 1: Onboarding — Briefing de Nuevos Expertos

### Orquestador:
> "Bienvenidos al equipo. VoiceClone empezó como un motor de clonación de voz local y ha evolucionado a algo mucho más grande. Resumo rápido:
>
> **Capa 1 — Motor:** Chatterbox TTS, open source, corre local en CPU. Ya investigado y decidido.  
> **Capa 2 — Web App:** Next.js, accesible, para que personas con ELA puedan usar la herramienta sin terminal.  
> **Capa 3 — Personalidad:** Un LLM que captura cómo habla la persona y genera texto personalizado antes de que el TTS lo sintetice.
>
> Los usuarios principales son personas con ELA que van a perder (o ya perdieron) la voz. La accesibilidad no es un nice-to-have, es el core. Y la personalidad es nuestro diferenciador: no solo suena como tú, se expresa como tú."

### Experto Accesibilidad (nuevo):
> "Entendido. Tengo varias preguntas inmediatas:
> 1. ¿La web app será la interfaz principal para usuarios con ELA, o hay un modo CLI también?
> 2. ¿Qué dispositivos de eye tracking estamos targeting? ¿Solo Tobii o hay otros?
> 3. ¿Estamos diseñando para ELA temprana (aún tienen algo de movilidad) o ELA avanzada (solo ojos)?
> 4. ¿Hay usuarios reales con ELA que podamos consultar para testing?"

### Orquestador:
> "La web app es la interfaz principal para usuarios finales. CLI para developers. Eye tracking: Tobii como primario, pero diseñamos con switch access genérico para cualquier hardware. Diseñamos para AMBOS estados de ELA — temprana y avanzada. Testing con usuarios reales es post-MVP, pero el diseño debe anticiparlo."

### Experto Personalidad IA (nuevo):
> "Mi primera preocupación es la cantidad de datos que necesitamos. Para una persona con ELA avanzada que ya no puede hablar, ¿qué datos tenemos disponibles? ¿Solo grabaciones antiguas? ¿WhatsApp messages? ¿Cuánto es 'suficiente' para capturar personalidad?"

### Comunicador IA:
> "Buena pregunta. La realidad es que para muchos usuarios, los datos serán escasos. WhatsApp messages, algún video familiar, notas de voz. No vamos a tener 10,000 ejemplos de texto. El sistema debe funcionar con **pocos datos** — few-shot, no fine-tuning."

---

## Parte 2: Debate — ¿Es la Capa 3 (Personalidad) viable técnicamente?

### Experto Personalidad IA:
> "Mi recomendación para MVP es clara: **RAG + Context Engineering**, no fine-tuning.
>
> Razones:
> 1. Los usuarios tendrán pocos datos (10-50 textos, no miles)
> 2. Fine-tuning requiere GPU y horas de entrenamiento — contradice 'CPU-friendly'
> 3. Con un cuestionario bien diseñado (5-10 min) + 10-50 ejemplos de texto, podemos construir un 'Personality Profile' que un LLM inyecta como contexto
> 4. El feedback loop ('¿suena como yo?') permite iterar sin re-entrenar
>
> Pipeline: input → LLM con Personality Profile en contexto → texto personalizado → Chatterbox → audio"

### Experto Voz IA:
> "Confirmo que Chatterbox NO puede cargar contexto de personalidad. Es text-in, audio-out. El pipeline de 2 etapas es el único camino viable. Esto es exactamente lo que hacen ElevenLabs y Character.AI internamente."

### Experto UX:
> "Pregunta importante: ¿el usuario final ve este pipeline? ¿O es invisible?"

### Experto Personalidad IA:
> "Invisible al 99%. El usuario escribe (o selecciona via AAC) lo que quiere decir. El sistema internamente pasa por el LLM para ajustar el estilo, y luego sintetiza. Para el usuario, simplemente 'dice las cosas como él las diría'."

### Experto Audio:
> "¿Qué latencia añade la capa de LLM? Si el usuario está en una conversación AAC real, necesita respuestas en <2 segundos."

### Experto Personalidad IA:
> "Con Claude API: ~1-2 segundos para un texto corto. Con un LLM local tipo Mistral 7B: ~3-5 segundos en CPU M1. Para AAC en tiempo real, podríamos usar la voz clonada sin personalidad (latencia baja) y ofrecer personalidad como opción 'enhanced' cuando la latencia es aceptable."

### Orquestador:
> "Decisión: para MVP, la personalidad es OPCIONAL. La voz clonada funciona sin ella. La Capa 3 se activa cuando el usuario quiere y el hardware lo permite. No bloqueamos la experiencia base."

---

## Parte 3: Debate — Accesibilidad para Eye Tracking

### Experto Accesibilidad:
> "He revisado la visión y tengo inputs clave:
>
> **Eye tracking en web:**
> - Tobii tiene un SDK JavaScript (Tobii Pro SDK) para web — pero tiene limitaciones
> - La mayoría de usuarios de eye tracking en AAC usan **Tobii Dynavox** que tiene su propio software (Grid 3, Communicator 5)
> - Nuestra web app no necesita 'ser' el eye tracker — necesita ser **compatible con el software de eye tracking que ya usan**
>
> **Recomendación clave:**
> En vez de integrar Tobii SDK directamente en nuestra web, deberíamos:
> 1. Hacer la web **100% keyboard-navigable** (WCAG AA baseline)
> 2. Usar **dwell-click** compatible (el software de eye tracking ya convierte mirada en clicks)
> 3. Diseñar con **targets grandes** (mínimo 48x48px, ideal 64x64px para gaze)
> 4. Reducir la cantidad de targets por pantalla (máximo 6-8 opciones visibles)
> 5. Navegación lineal (no grids complejas)
>
> Esto es más robusto que integrar Tobii SDK directamente. Funciona con Tobii, con switches, con cualquier dispositivo de AT."

### Experto UX:
> "Eso cambia el diseño de los mockups significativamente. Targets grandes, pocos elementos por pantalla, navegación secuencial. Parecido a un wizard más que a un dashboard."

### Experto Accesibilidad:
> "Exacto. Pensad en cada pantalla como: **máximo 3-4 acciones principales**, cada una con un botón enorme, alto contraste, texto grande. Un usuario con eye tracking debería poder completar todo el flujo mirando botones secuencialmente."

### Orquestador:
> "Acepto. El diseño será wizard-style con targets grandes. Cada pantalla = 1 decisión principal. El dashboard final puede ser más complejo porque el usuario ya terminó el flujo crítico."

---

## Parte 4: Debate — Integración AAC y Voz como Output

### Experto Accesibilidad:
> "Otro punto fundamental: ¿cómo llega la voz clonada al sistema AAC del usuario?
>
> Los sistemas AAC (Grid 3, Proloquo2Go, Snap Core First) usan voces del sistema operativo:
> - **macOS:** Las voces aparecen en System Settings → Accessibility → Spoken Content
> - **Windows:** Voces SAPI5 o OneCore
> - **iOS/iPadOS:** AVSpeechSynthesizer
>
> Para que VoiceClone sea útil en AAC, necesitamos una de dos cosas:
> 
> **Opción A:** Registrar la voz clonada como voz del sistema operativo (técnicamente complejo, distinto por OS)
> 
> **Opción B:** Crear un 'servidor TTS local' que el software AAC pueda usar como fuente de voz (API HTTP local)
>
> Recomiendo **Opción B** para MVP. Es un endpoint HTTP en localhost:8765 que el software AAC puede llamar. Grid 3 soporta voces externas via API."

### Experto DevOps:
> "La Opción B encaja perfectamente con nuestra arquitectura. FastAPI en puerto 8765 ya está planificada. Solo necesitamos documentar el endpoint para que las apps AAC lo puedan usar."

### Experto Voz IA:
> "Confirmo. El endpoint `POST /speak` con body `{text, voice_id}` que devuelve audio WAV es suficiente. Grid 3 puede configurarse para llamar endpoints HTTP para síntesis."

### Orquestador:
> "Decisión: MVP usa API HTTP local (Opción B). La integración como voz del sistema operativo (Opción A) queda para post-MVP. Documentamos cómo conectar Grid 3 y Proloquo2Go con nuestro endpoint."

---

## Parte 5: Debate — Integración OpenClaw-style Context con Motor de Voz

### Comunicador IA:
> "La pregunta de Ángel era: ¿se puede usar arquitectura OpenClaw para la Capa 3?
>
> OpenClaw maneja:
> - Memory files (MEMORY.md, memory/*.md)
> - Context injection (SOUL.md, USER.md)
> - Personality via system prompt
>
> Para VoiceClone, podríamos adaptar este patrón:
> - Un 'PERSONALITY.md' por usuario (equivalente a SOUL.md)
> - Un directorio de memory con ejemplos de su forma de hablar
> - Un system prompt que inyecta todo como contexto al LLM"

### Experto Personalidad IA:
> "Me gusta. Es simple, auditable (el usuario puede leer y editar su 'personality file'), y funciona con cualquier LLM. El formato sería:
>
> ```
> personality/
> ├── profile.md         ← Cuestionario respondido
> ├── examples/          ← Textos ejemplo
> │   ├── greetings.txt
> │   ├── casual.txt
> │   └── formal.txt
> └── voice/             ← Audio de referencia
>     └── reference.wav
> ```
>
> El LLM recibe `profile.md` + ejemplos relevantes (RAG) como contexto, genera texto, y Chatterbox sintetiza con la voz de `reference.wav`."

### Orquestador:
> "Decisión: adoptamos el patrón OpenClaw-style con archivos legibles. Formato markdown para el perfil de personalidad. El usuario puede editar manualmente si quiere."

---

## Parte 6: Devil's Advocate

### Designado: Experto DevOps

### Objeción 1: "La Capa 3 añade complejidad innecesaria al MVP"
> "¿Realmente necesitamos personalidad en el MVP? La voz clonada ya es un diferenciador enorme. Añadir un LLM layer significa más dependencias (Claude API o LLM local), más latencia, más cosas que pueden fallar. Para un usuario con ELA que solo necesita que su voz suene como él, la Capa 1 + Capa 2 bastan."

**Respuesta del equipo:**
> - *Orquestador:* "Punto válido. La Capa 3 es OPCIONAL en MVP. Si el usuario no la activa, el flujo es directo: texto → TTS → audio. Cero latencia extra."
> - *Experto Personalidad IA:* "De acuerdo con que sea opcional. Pero el cuestionario de personalidad debería estar en el MVP como 'feature avanzada'. Es un diferenciador contra ElevenLabs que justifica el proyecto."
> - **Decisión:** Capa 3 presente en MVP pero como feature opcional, claramente separada del flujo base.

### Objeción 2: "El eye tracking real puede ser mucho más complejo de lo que asumimos"
> "Diseñar para eye tracking 'en teoría' es muy diferente a que funcione con usuarios reales de Tobii. ¿Hemos probado algo? ¿Sabemos si los targets de 48px funcionan con la precisión real de gaze en un usuario con ELA que tiene temblores oculares?"

**Respuesta del equipo:**
> - *Experto Accesibilidad:* "Correcto, no podemos validar sin testing real. Pero el diseño que propongo (targets grandes, pocos elementos, navegación lineal) es el estándar AAC probado en Grid 3 y otros software que llevan años funcionando. No reinventamos la rueda — seguimos los patterns que ya funcionan."
> - *Orquestador:* "Anotado. Pre-release, necesitamos testing con al menos 1 usuario real de eye tracking. Queda como requisito de Fase 3."
> - **Decisión:** Diseñamos siguiendo patterns probados de AAC, pero testing real es obligatorio antes de release público.

### Objeción 3: "¿Qué pasa con la privacidad del LLM en Capa 3?"
> "Si usamos Claude API para la personalidad, los datos del usuario (su perfil, sus textos) van a Anthropic. Esto contradice '100% local, 100% privado'. Un usuario con ELA que comparte sus WhatsApp messages para capturar personalidad... esos datos son extremadamente sensibles."

**Respuesta del equipo:**
> - *Experto Personalidad IA:* "Excelente punto. Para MVP, ofrecemos 2 modos: (1) LLM local (Mistral 7B / Llama 3) — 100% privado pero necesita 8GB+ RAM, y (2) Claude API — mejor calidad pero datos salen. El usuario elige explícitamente. Default: local."
> - *Comunicador IA:* "Además, los datos se procesan pero no se almacenan. Anthropic no retiene datos de API calls en su policy. Pero la opción local debe ser la default."
> - **Decisión:** Default es LLM local (100% privado). Claude API es opcional y requiere consentimiento explícito con warning claro sobre privacidad.

---

## Decisiones Tomadas

| # | Decisión | Razón | Responsable |
|---|----------|-------|-------------|
| 1 | Capa 3 (Personalidad) es OPCIONAL en MVP | Reduce complejidad, no bloquea experiencia base | Orquestador |
| 2 | Pipeline LLM → TTS (no TTS con contexto) | Ningún TTS soporta contexto nativo. Pipeline probado por ElevenLabs/Character.AI | Experto Voz IA |
| 3 | RAG + Context Engineering para personalidad (no fine-tuning) | Pocos datos disponibles, CPU-friendly, iterativo | Exp. Personalidad IA |
| 4 | Web app compatible con eye tracking via targets grandes, no SDK directo | Más robusto, funciona con cualquier AT, estándar AAC | Exp. Accesibilidad |
| 5 | API HTTP local (puerto 8765) para integración AAC | Compatible con Grid 3, simple, no requiere drivers del sistema | Exp. DevOps |
| 6 | Patrón OpenClaw-style para personality files (markdown) | Legible, editable, auditable, familiar para el equipo | Comunicador IA |
| 7 | Default: LLM local (privacidad). Claude API opcional con consentimiento | Privacidad es core promise. Cloud solo con warning explícito | Exp. Personalidad IA |
| 8 | Testing real con usuario de eye tracking es requisito pre-release | No podemos validar accesibilidad solo en teoría | Orquestador |

---

## Acciones Pendientes

- [ ] Mockups con targets grandes + navegación wizard (Exp. UX + Exp. Accesibilidad) — Fase 2
- [ ] Documentar endpoint API para AAC integration (Exp. DevOps + Exp. Voz IA) — Fase 2
- [ ] Diseñar formato Personality Profile (Exp. Personalidad IA) — Fase 2
- [ ] Investigar LLM local viable para Capa 3 en CPU (Exp. Personalidad IA) — Tarea 1B.5
- [ ] Investigar APIs de AAC software (Grid 3, Proloquo2Go) (Exp. Accesibilidad) — Tarea 1B.6
- [ ] Buscar asociación ELA para testing beta (Orquestador) — post-Fase 3

---

## Devil's Advocate Summary

**Experto designado:** Experto DevOps

| Objeción | Respuesta del equipo | Acción requerida |
|----------|---------------------|-----------------|
| Capa 3 añade complejidad innecesaria al MVP | Será feature opcional, no bloquea flujo base | Separar claramente Capa 3 como "advanced feature" |
| Eye tracking puede no funcionar como asumimos | Diseñamos con patterns AAC probados (Grid 3 style) | Testing real obligatorio pre-release |
| LLM cloud en Capa 3 contradice "100% privado" | Default LLM local, Cloud opcional con consentimiento explícito | UI de consentimiento en Personality setup |

---

## Próximos Pasos

1. **Tarea 1B.5:** Investigar compatibilidad OpenClaw + modelos de voz (web search)
2. **Tarea 1B.6:** Investigar integración eye tracking + AAC (web search)
3. **Fase 2:** Diseño de arquitectura completa + mockups con decisiones de esta reunión
4. Reunión de diseño (Fase 2) incluirá revisión de mockups con todos los expertos

---

## Autocrítica de la Reunión

- ✅ **Bien:** Onboarding de nuevos expertos fue eficiente. Los 2 nuevos aportaron insights clave desde la primera intervención.
- ✅ **Bien:** Devil's Advocate levantó la bandera de privacidad (Objeción 3) que es crítica para el target de usuarios.
- ⚠️ **Mejorable:** No definimos métricas concretas de éxito para Capa 3 — ¿cómo medimos si la personalidad "suena" como la persona?
- 💡 **Aprendizaje:** El enfoque de "compatible con eye tracking via AT estándar" en vez de "integrar SDK de eye tracking directamente" es más pragmático y robusto. El software AAC ya resuelve el problema de input — nosotros solo necesitamos ser compatibles.

---

*Acta generada automáticamente por el sistema de reuniones Vertex Developer*  
*Proyecto VoiceClone — Reunión de Revisión de Visión — 2026-03-20*
