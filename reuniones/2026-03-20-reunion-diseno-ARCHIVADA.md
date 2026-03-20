# Reunión de Revisión de Diseño — Arquitectura + Mockups + Accesibilidad

## Fecha: 2026-03-20, 18:30
## Tipo: Plenaria — Revisión de Diseño Completo (Fase 2)
## Convocada por: Orquestador
## Documentos revisados:
- `docs/arquitectura-completa.md` (3 capas integradas)
- `mockups/web-app-mockups.md` (6 pantallas)
- `mockups/cli-mockups.md` (flujo CLI)
- `docs/flujo-instalacion.md` (instaladores por OS)
- `docs/diseno-accesibilidad.md` (WCAG AA + eye tracking + switch)

---

## Participantes

| Experto | Rol | Status |
|---------|-----|--------|
| **Orquestador** | Tech Lead / Director Técnico | ✅ |
| **Comunicador IA** | Ingeniero de Comunicación | ✅ |
| **Experto Voz IA** | Modelos de síntesis + clonación | ✅ |
| **Experto UX** | Experiencia de usuario + instaladores | ✅ |
| **Experto DevOps** | Packaging + distribución + CI/CD | ✅ |
| **Experto Audio** | Procesamiento de audio + señal | ✅ |
| **Experto Accesibilidad** | WCAG + Eye tracking + AAC + AT | ✅ |
| **Experto Personalidad IA** | LLM personality + context | ✅ |

**Devil's Advocate designado:** Experto DevOps (cuestiona viabilidad técnica y tiempos)

---

## Parte 1: Revisión de Arquitectura (30 min)

### Orquestador:
> "Equipo, esta es la revisión de diseño de Fase 2. Hemos completado la arquitectura de 3 capas, 6 mockups de web app, flujo CLI, diseño de instalación sin terminal, y un diseño de accesibilidad exhaustivo. Hoy revisamos todo y tomamos decisiones finales antes de pasar a código.
>
> Empiezo con la arquitectura. El pipeline completo es: input del usuario → si personalidad activada, el LLM transforma el texto → Chatterbox TTS sintetiza con la voz clonada → audio sale. FastAPI en localhost:8765 es el cerebro. Todo local."

### Experto Voz IA:
> "La arquitectura del Engine Adapter me parece sólida. Chatterbox como primario con XTTS v2 como fallback es la decisión correcta. Lo que quiero validar es el flujo de clonación: ¿estamos seguros de que 5-30 segundos de audio bastan para Chatterbox?
>
> De mi investigación: Chatterbox necesita mínimo 6 segundos de audio limpio para producir un embedding de calidad razonable. Con 15-30 segundos el resultado mejora significativamente. Recomiendo que el mínimo sea 10 segundos con un indicador visual que diga 'bueno' a los 10s y 'excelente' a los 30s. No poner máximo — si el usuario quiere grabar 2 minutos, mejor."

### Experto Audio:
> "De acuerdo con los mínimos. Añado que necesitamos procesamiento de audio antes del embedding:
> 1. **Normalización** — Ecualizar volumen (el mic del usuario puede estar lejos/cerca)
> 2. **Noise reduction** — Eliminar ruido de fondo (el usuario puede estar en hospital)
> 3. **Voice Activity Detection (VAD)** — Solo usar segmentos con voz, descartar silencios
> 4. **Sample rate conversion** — Chatterbox espera 24kHz, asegurar conversión
>
> Esto es crítico para usuarios con ELA: su voz puede ser débil, el entorno ruidoso, y el mic quizás no esté bien posicionado. El pipeline de audio debe ser robusto."

### Orquestador:
> "Perfecto. Añadimos un módulo `audio/processor.py` con pipeline: normalización → noise reduction → VAD → resampling → embedding. ¿Librería recomendada?"

### Experto Audio:
> "Para noise reduction: `noisereduce` (Python, basado en spectral gating) para MVP. Es ligero y funciona en CPU. Para VAD: `webrtcvad` o `silero-vad` — Silero es más preciso pero más pesado. Recomiendo `noisereduce` + `silero-vad` para MVP."

### Experto DevOps (Devil's Advocate):
> "Paro un momento. El modelo Chatterbox pesa ~2GB. XTTS v2 pesa ~1.8GB. Si los dos van incluidos, la descarga inicial es de ~4GB. Más Python runtime, dependencias, torch... estamos hablando de 5-6GB de descarga. Para un usuario con ELA que quizás tiene un ordenador viejo con conexión lenta, eso es un problema SERIO.
>
> ¿Necesitamos AMBOS modelos en la instalación inicial? Mi propuesta: instalar solo Chatterbox. XTTS v2 como descarga opcional si Chatterbox falla. Eso reduce la descarga a ~3GB."

### Orquestador:
> "Buen punto. Aceptado. Chatterbox obligatorio, XTTS v2 como descarga bajo demanda si el usuario tiene problemas con Chatterbox. El instalador descarga solo Chatterbox."

### Experto Personalidad IA:
> "Sobre la integración Capa 3 → Capa 1: el pipeline en la arquitectura es correcto. LLM genera texto personalizado → TTS sintetiza. Pero quiero plantear un riesgo técnico.
>
> El LLM añade latencia. Si usamos Claude API (cloud), son 1-3 segundos de latencia antes de que empiece la síntesis. Si usamos un LLM local (Mistral 7B o Llama 3 8B), la latencia depende del hardware del usuario. En un Mac M1 son ~2-4 segundos para un texto corto. En un PC viejo sin GPU puede ser 10-20 segundos.
>
> Para un usuario de AAC que necesita comunicarse EN TIEMPO REAL, 10-20 segundos por frase es inaceptable.
>
> **Propuesta:** La personalidad debe ser OPCIONAL y claramente marcada como 'más lenta'. En el Dashboard, el botón 'Hablar (solo voz)' debe dar audio en <2 segundos. El botón 'Hablar + Personalidad' debe avisar: 'Esto tarda unos segundos extra'."

### Experto UX:
> "De acuerdo. En los mockups ya tenemos dos botones separados: '🔊 Hablar (solo voz)' y '🔊+✨ (con personalidad)'. Pero necesitamos ser más explícitos sobre el tiempo. Añado un texto debajo: 'Con personalidad tarda unos segundos más en responder'.
>
> Además, para comunicación AAC en tiempo real: podemos pre-generar frases frecuentes. El usuario configura una lista de frases ('Tengo sed', 'Ven aquí', 'Te quiero') y las pre-generamos con personalidad. Así la personalidad está ahí pero el output es instantáneo."

### Experto Personalidad IA:
> "Excelente idea. Frase-caching con personalidad. Las frases AAC más comunes se pre-generan al configurar la personalidad. Se almacenan como audio cacheado. Cuando el usuario selecciona una → reproducción instantánea.
>
> La lista: el sistema genera ~50-100 frases comunes personalizadas y las cachea. El usuario puede editar, añadir, eliminar. Es como un banco de frases pero que suenan COMO ÉL."

### Orquestador:
> "Decisión tomada: añadimos 'phrase caching' al sistema de personalidad. Pre-generación de frases AAC comunes con voz + personalidad, almacenadas como audio. Output instantáneo para comunicación en tiempo real."

**DECISIÓN 1:** Chatterbox solo en instalación inicial. XTTS v2 descarga bajo demanda.  
**DECISIÓN 2:** Pipeline de audio obligatorio: normalización → noise reduction → VAD → resampling.  
**DECISIÓN 3:** Phrase caching para frases AAC comunes con personalidad pre-generada.

---

## Parte 2: Revisión de Mockups (20 min)

### Experto UX:
> "Presento los 6 mockups. Diseño wizard-style: una decisión por pantalla, targets de 64px mínimo, máximo 4-6 acciones, alto contraste fondo oscuro. Voy pantalla por pantalla pidiendo feedback."

### Experto Accesibilidad — Revisión Pantalla 1 (Landing):
> "La landing está bien. 3 botones de descarga, cada uno es un target claro. Pero tengo una observación: la detección automática de OS debe funcionar PERO los 3 botones deben estar visibles siempre. No ocultes los otros OS. Un cuidador puede descargar para el PC del paciente desde su propio Mac.
>
> También: falta un enlace 'Accesibilidad' visible en la landing. No solo en el footer — quiero un badge o enlace destacado que diga 'Compatible con eye tracking y pulsadores'. Esto da confianza inmediata a usuarios de AT."

### Experto UX:
> "Acepto. Añado badge de accesibilidad visible en la landing: '👁 Compatible con eye tracking · 🔘 Pulsadores · ⌨️ Teclado'. Debajo del texto 'Diseñado para personas con ELA'."

### Experto Accesibilidad — Revisión Pantalla 3 (Clonación):
> "La pantalla de clonación tiene 2 opciones: grabar o subir. Perfecto para eye tracking. Pero la sub-pantalla de grabación (3a) me preocupa.
>
> Cuando el usuario está GRABANDO, está leyendo un texto en voz alta. Si usa eye tracking, su mirada está en el texto de lectura. Los botones 'Parar' y 'Reiniciar' están abajo. Hay un conflicto: ¿dónde mira? ¿Al texto o a los botones?
>
> **Propuesta:** Durante la grabación, el botón 'Parar' debe ser TODA la zona inferior de la pantalla. Un target masivo. El usuario puede mirar al texto (arriba) y cuando quiera parar, simplemente mira abajo — cualquier punto abajo. Un mega-target de 100% de ancho × 120px de alto."

### Experto UX:
> "Brillante. Mega-target para 'Parar'. Toda la zona inferior es el botón. Y 'Reiniciar' solo aparece DESPUÉS de parar, no durante. Reducimos la decisión a: 'estoy grabando' o 'quiero parar'. Nada más."

### Experto Voz IA:
> "Sobre el texto de lectura en la grabación: 'El sol de la mañana ilumina las calles...' — necesitamos que cubra los fonemas principales del español. No cualquier texto vale. Diseño un set de frases que cubra vocales, consonantes, diptongos, y entonación natural. Con variantes por idioma si añadimos multi-idioma."

### Experto Audio:
> "Añado: el texto debe incluir pausas naturales. Si el usuario lee sin parar, el VAD tiene problemas. Incluir puntos y comas explícitos, y una instrucción: 'Lee con calma, como si hablaras con un amigo. Las pausas son buenas.'"

### Experto Accesibilidad — Revisión Pantalla 4 (Personalidad):
> "El cuestionario de personalidad tiene 3-4 opciones por pregunta, más una opción libre. Bien para eye tracking. Pero: 5 preguntas con cuestionario visual puede ser agotador para un usuario con eye tracking. Cada pregunta requiere escanear opciones, decidir, mirar el target 800ms.
>
> **Propuesta:** Reducir a 3 preguntas obligatorias + 2 opcionales. Las 3 primeras capturan lo esencial (tono, formalidad, humor). Las 2 extras son 'si quieres ir más allá'. Esto reduce fatiga visual un 40%."

### Experto Personalidad IA:
> "3 preguntas capturan suficiente personalidad base. Las 2 extra son para refinamiento. El LLM puede inferir mucho de 3 data points buenos. Acepto la propuesta."

### Experto Accesibilidad — Revisión Pantalla 6 (Dashboard):
> "El dashboard es la pantalla más compleja: 6 acciones + campo de texto + 2 botones de hablar + info de estado. Para eye tracking, 6+ targets es el límite. Funciona pero es ajustado.
>
> **Propuesta:** Layout de 2 zonas. Zona superior: campo de texto + botones 'Hablar'. Zona inferior: botones secundarios (nueva voz, editar, AAC, stats). El usuario 80% del tiempo usa la zona superior. La zona inferior solo cuando configura. Separación clara entre zonas con línea visual gruesa."

### Experto UX:
> "Acepto. Dos zonas claras. La zona 'comunicación' arriba (texto + hablar) y zona 'configuración' abajo. Esto también mejora el switch scanning — el scan group 'comunicación' tiene 3 elementos y el grupo 'configuración' tiene 4."

**DECISIÓN 4:** Badge de accesibilidad visible en landing.  
**DECISIÓN 5:** Mega-target para botón 'Parar' durante grabación (100% ancho × 120px).  
**DECISIÓN 6:** Cuestionario de personalidad: 3 preguntas obligatorias + 2 opcionales.  
**DECISIÓN 7:** Dashboard en 2 zonas: comunicación (arriba) + configuración (abajo).

---

## Parte 3: Revisión de Accesibilidad (20 min)

### Orquestador:
> "El documento de accesibilidad tiene 1166 líneas y cubre WCAG 2.2 AA completo, eye tracking con dwell time, switch access con escaneo automático, teclado, y voz. Experto de Accesibilidad, ¿tu validación?"

### Experto Accesibilidad:
> "He revisado el documento completo. Es exhaustivo. Los puntos fuertes:
>
> 1. **Dwell time configurable (200ms-3000ms):** Correcto. Cada usuario de eye tracking necesita su propio timing. Los defaults (800ms estándar, 1200ms crítico) son los recomendados por Tobii.
>
> 2. **Zona neutra obligatoria:** Excelente. El Midas Touch Problem es el error #1 en diseño para eye tracking. Las zonas neutras lo resuelven.
>
> 3. **4 perfiles de usuario:** Cubren bien el espectro. El Perfil B (ELA avanzada, solo ojos) es el caso de diseño — si funciona para B, funciona para todos.
>
> 4. **Switch scanning con teclado virtual + predicción:** Bien pensado. La predicción reduce keystrokes dramáticamente. Un usuario con 1 switch puede escribir una frase en 30-60 segundos vs 3-5 minutos sin predicción.
>
> **Lo que falta o mejoraría:**
>
> 1. **Calibración de eye tracker dentro de la app.** El documento menciona 'Calibrar eye tracker' en settings pero no detalla el flujo. Propongo: al primer uso con eye tracker detectado, la app propone calibración automática con 5 puntos de mirada. Tarda 30 segundos. Sin calibración el eye tracking es impreciso.
>
> 2. **Emergency exit.** Un usuario con ELA avanzada puede quedar 'atrapado' en un estado de la app y no poder volver. Necesitamos un gesto universal de escape: mirar esquina superior-derecha durante 2 segundos = 'Volver al dashboard'. Funciona SIEMPRE, en cualquier pantalla, como un botón de pánico.
>
> 3. **Fatigue detection.** Los usuarios con eye tracking se cansan. Después de 15-20 minutos de uso continuo, la precisión baja. Sugerencia: aviso suave cada 15 minutos: 'Llevas 15 minutos. ¿Quieres descansar?'. No intrusivo, solo informativo."

### Orquestador:
> "Tres mejoras excelentes. Las incorporamos:
> - Calibración guiada al primer uso con eye tracker
> - Emergency exit: esquina superior-derecha 2s = dashboard (universal)
> - Fatigue reminder cada 15 min (desactivable)"

### Experto DevOps (Devil's Advocate):
> "Pregunta directa sobre viabilidad: ¿todo el sistema de eye tracking lo implementamos nosotros? ¿O dependemos del Tobii SDK que el usuario ya tiene instalado?
>
> Porque si necesitamos integrar el Tobii SDK en una web app Next.js... eso no es trivial. El SDK de Tobii es C++/Python. Next.js es JavaScript. ¿Cómo se comunican?
>
> Las opciones que veo:
> 1. **Electron app** — Podemos usar bindings nativos de Tobii. PERO: ya no es 'web app', es desktop app.
> 2. **Web app + extensión de browser** — Una extensión media entre Tobii SDK y la web. Complejo.
> 3. **Web app + servicio local** — Un servicio Python local (como ya tenemos FastAPI) que conecta con Tobii y envía datos de gaze via WebSocket a la web app.
>
> La opción 3 me parece la más viable: ya tenemos FastAPI corriendo localmente. Añadir un endpoint WebSocket de gaze data es natural."

### Orquestador:
> "Opción 3. FastAPI ya corre en localhost:8765. Añadimos:
> - `WS /gaze` — WebSocket que envía datos de mirada en tiempo real
> - `POST /gaze/calibrate` — Inicia calibración
> - `GET /gaze/status` — Estado del eye tracker
>
> La web app se conecta al WebSocket y procesa el gaze localmente. El dwell time, la detección de targets, todo es JavaScript en el browser usando los datos del WebSocket."

### Experto Voz IA:
> "Pregunta sobre el switch access: ¿cómo detectamos el switch físico? Un switch es típicamente un dispositivo USB HID o Bluetooth que emula una tecla. ¿Qué tecla emula? ¿Enter? ¿Space?"

### Experto Accesibilidad:
> "Correcto. Los switches estándar emulan teclas configurables. Los más comunes: Enter, Space, o teclas F (F12 es común). El sistema operativo ya los detecta como keypress. No necesitamos driver especial.
>
> Para nuestra web app: switch access funciona nativamente si la navegación por teclado es sólida. El switch emite keypress → el browser lo recibe → nuestro JS lo procesa. Solo necesitamos:
> 1. Un modo de escaneo activable en settings
> 2. Cuando activo: el sistema resalta elementos en secuencia automática
> 3. Cualquier keypress (Enter, Space, o key configurable) = seleccionar el elemento resaltado
>
> No necesitamos hardware especial. Todo es software."

### Comunicador IA:
> "Quiero hablar del tono emocional de toda la app. Estamos diseñando para personas que están perdiendo o ya perdieron su voz. Esto es profundamente emocional. Cada texto, cada instrucción, cada mensaje de error debe ser:
>
> - **Empoderador, no victimista.** 'Preserva tu voz' no 'Estás perdiendo tu voz'.
> - **Calmo, no urgente.** 'Tómate tu tiempo' no 'Solo quedan 5 minutos'.
> - **Honesto sin ser frío.** Si algo falla: 'No hemos podido procesar el audio. Vamos a intentarlo de nuevo.' No 'Error 500: Internal Server Error'.
> - **Sin infantilizar.** Estas personas tienen cognición completa. Lenguaje adulto, claro, respetuoso.
>
> Propongo una guía de copy/tone para toda la app: cada mensaje revisado por este filtro."

### Experto UX:
> "Completamente de acuerdo. Añadimos un `copy-guide.md` con el tono de toda la app. Cada string de la interfaz pasa por esta guía."

**DECISIÓN 8:** Eye tracking via WebSocket desde FastAPI (WS /gaze). No Electron.  
**DECISIÓN 9:** Calibración guiada (5 puntos) al primer uso con eye tracker.  
**DECISIÓN 10:** Emergency exit universal: esquina superior-derecha 2s = dashboard.  
**DECISIÓN 11:** Fatigue reminder cada 15 min (desactivable).  
**DECISIÓN 12:** Switch access via keyboard emulation estándar. Scan mode en settings.  
**DECISIÓN 13:** Guía de copy/tone empoderador para toda la app (`copy-guide.md`).

---

## Parte 4: Revisión del Flujo de Instalación (10 min)

### Experto DevOps:
> "Revisé el documento de instalación. .pkg para macOS, .exe (NSIS) para Windows, script bash para Linux. Está bien como concepto pero necesito plantear realidades:
>
> 1. **macOS .pkg con firma de código:** Sin Apple Developer ID ($99/año), macOS Gatekeeper bloquea la instalación. El usuario verá 'Aplicación de desarrollador no identificado'. Un usuario con ELA no va a saber hacer clic derecho → Abrir. Necesitamos firmar el .pkg o dar instrucciones clarísimas.
>
> 2. **Windows .exe sin firma:** SmartScreen bloquea. Mismo problema. Necesitamos un certificado de firma de código (~$200-300/año) o instrucciones muy claras.
>
> 3. **Tamaño:** Python runtime embebido (~50MB) + Chatterbox (~2GB) + dependencias (~500MB). Total: ~2.5GB mínimo. Para un usuario con conexión lenta, la barra de progreso es clave.
>
> Mi propuesta para MVP: NO firmar código (cuesta dinero). En cambio, el instalador de macOS usa Homebrew: `brew install voiceclone`. Para Windows: winget o chocolatey. Para Linux: `curl | bash`. Esto evita Gatekeeper/SmartScreen. Y para usuarios no-técnicos: la web tiene instrucciones visuales paso a paso, con capturas de pantalla de cómo bypass Gatekeeper."

### Experto Accesibilidad:
> "Discrepo parcialmente. Un usuario con ELA avanzada NO puede usar Homebrew ni terminal. Necesita un .pkg / .exe que se instale con clicks. Las instrucciones de bypass Gatekeeper necesitan ratón + clic derecho — posible con eye tracking pero complicado.
>
> **Propuesta de compromiso:** Para MVP, ofrecemos ambos:
> 1. Instalador .pkg/.exe (sin firma, con instrucciones visuales de bypass)
> 2. Terminal install (`brew`, `curl`) para usuarios técnicos y cuidadores
>
> Post-MVP: firmamos el código para eliminar las barreras de Gatekeeper/SmartScreen."

### Orquestador:
> "Compromiso aceptado. MVP: ambas opciones. Post-MVP: firma de código. El cuidador (Perfil C) probablemente instala por el paciente, y el cuidador puede hacer el bypass."

**DECISIÓN 14:** MVP: instalador .pkg/.exe sin firma + terminal install. Instrucciones visuales de bypass. Post-MVP: firma de código.  
**DECISIÓN 15:** Descarga inicial solo Chatterbox (~2.5GB total). XTTS v2 bajo demanda.

---

## Parte 5: Validaciones Cruzadas (10 min)

### Experto Personalidad IA valida Capa 3:
> "La arquitectura de personalidad es viable. El pipeline LLM → TTS funciona. El phrase caching para AAC resuelve la latencia. Tengo una recomendación adicional:
>
> **Few-shot learning vs fine-tuning:** Para MVP, usamos few-shot prompting (system prompt con perfil + ejemplos). No fine-tuning. Razones:
> 1. No necesitamos GPU para inference (few-shot funciona con modelos pequeños)
> 2. Es instantáneo (no requiere entrenamiento)
> 3. Es editable (el usuario cambia su perfil y el resultado cambia)
> 4. Fine-tuning lo dejamos post-MVP cuando tengamos más datos
>
> El system prompt sería algo como:
> ```
> Eres [nombre]. Tu personalidad: [perfil del cuestionario].
> Hablas así: [3-5 ejemplos de frases reales].
> Reformula el siguiente texto como lo dirías tú.
> Solo responde con el texto reformulado, nada más.
> ```
>
> Con un LLM local de 7B parámetros (Mistral, Llama 3) esto funciona bien."

### Experto Accesibilidad valida Mockups:
> "Los 6 mockups son sólidos para accesibilidad. Con las mejoras decididas hoy (mega-target en grabación, 2 zonas en dashboard, badge de accesibilidad en landing), estoy satisfecho. Mi score de accesibilidad estimado: 92/100 pre-testing real. Los 8 puntos restantes se resolverán con testing de usuarios reales post-MVP."

### Experto DevOps valida Instalación:
> "Con la decisión de Chatterbox-only en MVP y ambas opciones de instalación, el flujo es viable. El riesgo principal es que PyInstaller genere un binario de 500MB+ sin comprimir. Investigaré alternativas como `shiv` o distribución via pip en virtualenv auto-gestionado."

---

## Resumen de Decisiones

| # | Decisión | Propuesto por | Consenso |
|---|----------|--------------|----------|
| 1 | Chatterbox solo en instalación. XTTS v2 bajo demanda. | DevOps | ✅ Unánime |
| 2 | Pipeline audio: normalización → noise reduction → VAD → resampling | Audio | ✅ Unánime |
| 3 | Phrase caching para frases AAC con personalidad pre-generada | Personalidad IA + UX | ✅ Unánime |
| 4 | Badge de accesibilidad visible en landing | Accesibilidad | ✅ Unánime |
| 5 | Mega-target 'Parar' durante grabación (100% ancho × 120px) | Accesibilidad | ✅ Unánime |
| 6 | Cuestionario personalidad: 3 obligatorias + 2 opcionales | Accesibilidad | ✅ Unánime |
| 7 | Dashboard 2 zonas: comunicación + configuración | UX + Accesibilidad | ✅ Unánime |
| 8 | Eye tracking via WebSocket desde FastAPI (no Electron) | DevOps + Orquestador | ✅ Unánime |
| 9 | Calibración guiada 5 puntos al primer uso eye tracker | Accesibilidad | ✅ Unánime |
| 10 | Emergency exit: esquina sup-derecha 2s = dashboard | Accesibilidad | ✅ Unánime |
| 11 | Fatigue reminder 15 min (desactivable) | Accesibilidad | ✅ Unánime |
| 12 | Switch access via keyboard emulation + scan mode | Accesibilidad | ✅ Unánime |
| 13 | Guía de copy/tone empoderador para la app | Comunicador IA | ✅ Unánime |
| 14 | MVP: .pkg/.exe sin firma + terminal. Post-MVP: firma. | DevOps + Accesibilidad | ✅ Compromiso |
| 15 | Descarga total ~2.5GB (solo Chatterbox) | DevOps | ✅ Unánime |

---

## Actualizaciones a Documentos

Basándose en las decisiones de esta reunión, los siguientes documentos necesitan actualizaciones:

1. **arquitectura-completa.md:** Añadir endpoint WS /gaze, pipeline de audio, phrase caching
2. **web-app-mockups.md:** Mega-target en grabación, badge accesibilidad en landing, 2 zonas en dashboard
3. **diseno-accesibilidad.md:** Calibración eye tracker, emergency exit, fatigue reminder
4. **flujo-instalacion.md:** Ambas opciones (pkg/exe + terminal), Chatterbox-only
5. **NUEVO: copy-guide.md:** Guía de tono empoderador para toda la app

---

## Próximos Pasos

1. ✅ Actualizar documentos con decisiones
2. ✅ Crear copy-guide.md
3. ✅ Actualizar brief v2
4. ✅ Reportar Fase 2 al grupo
5. → Pasar a Fase 3: Código

---

## Valoración del Orquestador

> "Reunión excelente. El equipo completo ha revisado TODOS los documentos de diseño. 15 decisiones consensuadas, 0 conflictos sin resolver. El Devil's Advocate (DevOps) planteó cuestiones reales sobre tamaño de descarga y firma de código que hemos resuelto con compromiso.
>
> Los puntos más valiosos de esta reunión:
> - **Phrase caching** para personalidad en tiempo real (Personalidad IA + UX)
> - **Mega-target** para grabación con eye tracking (Accesibilidad)
> - **Emergency exit universal** para ELA avanzada (Accesibilidad)
> - **Eye tracking via WebSocket** en vez de Electron (DevOps)
> - **Guía de copy/tone** empoderador (Comunicador IA)
>
> Estamos listos para código."

---

*Acta de Reunión de Revisión de Diseño — Proyecto VoiceClone