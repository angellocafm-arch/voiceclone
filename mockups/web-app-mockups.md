# Mockups Web App — VoiceClone (6 Pantallas)

## Fecha: 2026-03-20
## Autor: Equipo VoiceClone (Experto UX + Experto Accesibilidad)
## Diseño: Wizard-style, WCAG AA, targets 64px+, eye tracking compatible

---

## Principios de Diseño Aplicados

- **Wizard-style:** Cada pantalla = 1 decisión principal
- **Targets:** Mínimo 64x64px con 16px separación
- **Máximo 4-6 acciones por pantalla** (eye tracking friendly)
- **Alto contraste:** Fondo oscuro (#0A0A0A) + texto claro (#F5F5F5)
- **Tipografía grande:** Títulos 32px+, cuerpo 20px+, botones 18px+
- **Focus visible:** Borde 3px #FFD700 (dorado) en foco
- **Sin scroll requerido** (todo visible en viewport)
- **Sin animaciones que distraigan** (pueden confundir eye tracker)
- **Color scheme:** Azul profundo (#1E3A5F) para acciones, verde (#2ECC71) para éxito, naranja (#F39C12) para warning

---

## Pantalla 1: Landing — "Preserva tu voz"

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║                                                                ║
║           ─────────────────────────────────                    ║
║                                                                ║
║                  Preserva tu voz.                              ║
║                  Para siempre.                                 ║
║                                                                ║
║           ─────────────────────────────────                    ║
║                                                                ║
║     Tu voz es tuya. Clónala en tu ordenador.                  ║
║     100% gratis. 100% privado. 100% local.                    ║
║                                                                ║
║     Diseñado para personas con ELA y                           ║
║     enfermedades que afectan al habla.                        ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │         ▶  Descargar para macOS                    │       ║
║  │            (Apple Silicon + Intel)                  │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │         ▶  Descargar para Windows                  │       ║
║  │            (Windows 10+)                           │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │         ▶  Descargar para Linux                    │       ║
║  │            (Ubuntu, Debian, Fedora)                │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║     Ya lo instalaste?  [ Abrir VoiceClone → ]                 ║
║                                                                ║
║  ───────────────────────────────────────────────               ║
║  Open Source (MIT) · GitHub · Documentación                    ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes
- **Emoción:** Tono cálido pero no triste. Empoderante, no victimista.
- **CTA principal:** Descargar (los 3 OS visibles, autodetecta cuál destacar)
- **Accesibilidad:** 3 botones enormes, cada uno es un target para eye tracking
- **Texto mínimo:** Solo lo esencial. Sin FAQs, sin testimonios (eso va en otra página)
- **"Ya lo instalaste?":** Link para usuarios que vuelven
- **Footer discreto:** Open source, GitHub, docs

---

## Pantalla 2: Descarga + Instalación (Progress)

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║                                                                ║
║              Instalando VoiceClone...                          ║
║                                                                ║
║                                                                ║
║     Paso 2 de 4: Descargando modelo de voz                    ║
║                                                                ║
║     ┌──────────────────────────────────────────┐              ║
║     │█████████████████████░░░░░░░░░░░░░░░░░░░░│  67%          ║
║     └──────────────────────────────────────────┘              ║
║                                                                ║
║     1.4 GB de 2.1 GB · ~2 minutos restantes                  ║
║                                                                ║
║                                                                ║
║     ✅ Paso 1: Entorno Python instalado                       ║
║     ⏳ Paso 2: Descargando modelo Chatterbox TTS              ║
║     ○  Paso 3: Configurando servicio local                    ║
║     ○  Paso 4: Verificación final                             ║
║                                                                ║
║                                                                ║
║     ─────────────────────────────────────────                  ║
║     Todo se instala en tu ordenador.                           ║
║     Nada se envía a internet.                                  ║
║     Tu voz será solo tuya.                                     ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │              ✕  Cancelar instalación                │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes
- **Sin interacción requerida:** El usuario solo espera
- **Progress claro:** Barra grande + porcentaje + tiempo estimado
- **Pasos numerados:** El usuario sabe dónde está y cuánto falta
- **Mensaje de privacidad:** Refuerza que nada sale del ordenador (tranquiliza)
- **Cancelar:** Único botón, discreto (abajo), por si el usuario cambia de opinión
- **Eye tracking:** No requiere interacción. Solo lectura pasiva + cancel si necesario

---

## Pantalla 3: Clonación de Voz — Graba o Sube

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Paso 1 de 3: Tu voz                               ║
║                                                                ║
║                                                                ║
║     ¿Cómo quieres clonar tu voz?                              ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     🎤  Grabar ahora                               │       ║
║  │                                                    │       ║
║  │     Lee un texto corto en voz alta                 │       ║
║  │     (30 segundos es suficiente)                    │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║                         ── o ──                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     📁  Subir una grabación                        │       ║
║  │                                                    │       ║
║  │     Nota de voz, video, podcast...                 │       ║
║  │     Cualquier audio con tu voz vale                │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║                                                                ║
║     💡 Tip: Si ya perdiste la voz, pide a tu familia          ║
║        que busque notas de voz o videos antiguos.             ║
║                                                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Sub-pantalla 3a: Grabando (si elige "Grabar ahora")

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Grabando tu voz                                   ║
║                                                                ║
║                                                                ║
║     Lee este texto en voz alta, con tu voz normal:            ║
║                                                                ║
║     ┌──────────────────────────────────────────────┐          ║
║     │                                              │          ║
║     │  "El sol de la mañana ilumina las calles     │          ║
║     │   de la ciudad. Los pájaros cantan mientras   │          ║
║     │   la gente pasea tranquilamente por el        │          ║
║     │   parque. Me gusta este momento del día,      │          ║
║     │   cuando todo está en calma y puedo pensar    │          ║
║     │   con claridad."                              │          ║
║     │                                              │          ║
║     └──────────────────────────────────────────────┘          ║
║                                                                ║
║                                                                ║
║                    ●  GRABANDO                                 ║
║                    ████████░░░░  18s / 30s                     ║
║                                                                ║
║                                                                ║
║  ┌─────────────────────┐    ┌──────────────────────┐          ║
║  │    ⏹  Parar         │    │    🔄  Reiniciar      │          ║
║  └─────────────────────┘    └──────────────────────┘          ║
║                                                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Sub-pantalla 3b: Procesando + Resultado

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Tu voz ha sido clonada ✅                         ║
║                                                                ║
║                                                                ║
║     Escucha cómo suena tu voz clonada:                        ║
║                                                                ║
║     ┌──────────────────────────────────────────────┐          ║
║     │                                              │          ║
║     │  "Hola, esta es mi voz clonada. ¿Suena       │          ║
║     │   como yo? Espero que sí."                   │          ║
║     │                                              │          ║
║     │        🔊 ▶  Reproducir                      │          ║
║     │                                              │          ║
║     └──────────────────────────────────────────────┘          ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │         ✅  Suena bien, continuar                  │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │         🔄  No suena bien, repetir                 │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes — Pantalla 3
- **2 opciones claras:** Grabar o subir. Sin confusión.
- **Tip emocional:** "Si ya perdiste la voz" — reconoce la situación con sensibilidad
- **Texto de lectura:** Diseñado para cubrir fonemas del español. Tono neutral.
- **Validación obligatoria:** El usuario DEBE escuchar y aprobar la clonación
- **Botones grandes:** "Suena bien" / "Repetir" — 2 opciones, sin ambigüedad
- **Eye tracking:** Máximo 2-3 targets por sub-pantalla

---

## Pantalla 4: Captura de Personalidad — "Cuéntanos cómo eres"

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Paso 2 de 3: Tu personalidad                      ║
║              (opcional — puedes saltarte esto)                  ║
║                                                                ║
║                                                                ║
║     Tu voz ya está clonada. ¿Quieres que también              ║
║     se exprese como tú?                                        ║
║                                                                ║
║     Esto es opcional. Si lo activas, cuando escribas           ║
║     algo, el sistema lo dirá "a tu manera".                    ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     ✨  Sí, personalizar mi voz                    │       ║
║  │                                                    │       ║
║  │     Responde unas preguntas (5 minutos)           │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     ⏭  Saltar por ahora                           │       ║
║  │                                                    │       ║
║  │     Puedes activarlo después                       │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Sub-pantalla 4a: Cuestionario (si elige "Personalizar")

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Pregunta 1 de 5                                   ║
║                                                                ║
║                                                                ║
║     ¿Cómo te describes a ti mismo/a?                          ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     😊  Alegre y bromista                          │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     😌  Tranquilo/a y cercano/a                    │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     🎯  Directo/a y práctico/a                     │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     ✍️  Quiero escribir mi propia descripción      │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Sub-pantalla 4b: Validación de Personalidad

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              ¿Esto suena como tú?                              ║
║                                                                ║
║                                                                ║
║     Hemos generado estas frases con tu estilo.                 ║
║     ¿Te reconoces?                                            ║
║                                                                ║
║     ┌──────────────────────────────────────────────┐          ║
║     │                                              │          ║
║     │  1. "¡Venga, que nos vamos!"                 │ 🔊 ▶    ║
║     │  2. "Oye, ¿sabes qué? Me ha encantado"      │ 🔊 ▶    ║
║     │  3. "No me líes, que es fácil"               │ 🔊 ▶    ║
║     │  4. "Bueno, a ver, déjame pensar..."         │ 🔊 ▶    ║
║     │  5. "¡Qué bueno eso, eh!"                   │ 🔊 ▶    ║
║     │                                              │          ║
║     └──────────────────────────────────────────────┘          ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │         ✅  Sí, así soy yo                         │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │         🔄  No del todo, ajustar                   │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes — Pantalla 4
- **Claramente opcional:** "Puedes saltarte esto" en grande
- **Cuestionario simple:** Opciones predefinidas (no campos de texto obligatorios)
- **Opción libre:** "Escribir mi propia descripción" para power users
- **Validación con audio:** Las frases se pueden escuchar con la voz clonada
- **Feedback loop:** Si "No del todo" → ajusta y regenera
- **Eye tracking:** 3-4 opciones por pregunta, targets de 64px+

---

## Pantalla 5: Integración — Conecta con tu sistema

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                     🎤 VoiceClone                              ║
║              ───────────────────────                           ║
║              Paso 3 de 3: Conectar                             ║
║                                                                ║
║                                                                ║
║     Tu voz está lista. ¿Dónde quieres usarla?                ║
║                                                                ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     💻  Usar aquí en VoiceClone                    │       ║
║  │                                                    │       ║
║  │     Escribe texto → se reproduce con tu voz       │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     🗣  Conectar con software AAC                  │       ║
║  │                                                    │       ║
║  │     Grid 3 · Snap Core · Proloquo2Go             │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     ⌨️  Usar desde terminal (CLI)                  │       ║
║  │                                                    │       ║
║  │     Para desarrolladores                           │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
║  ┌────────────────────────────────────────────────────┐       ║
║  │                                                    │       ║
║  │     ⏭  Ir al Dashboard                            │       ║
║  │                                                    │       ║
║  └────────────────────────────────────────────────────┘       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes — Pantalla 5
- **3 caminos claros:** Usar aquí, AAC software, o CLI
- **"Usar aquí"** es la opción más sencilla — va directo al dashboard
- **AAC:** Abre guía paso a paso para cada software
- **CLI:** Para developers, abre instrucciones de terminal
- **Skip:** "Ir al Dashboard" para quien no necesita integración ahora
- **Eye tracking:** 4 opciones, cada una con descripción corta

---

## Pantalla 6: Dashboard — "Tu voz está lista"

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  🎤 VoiceClone                              ⚙️ Configurar    ║
║  ───────────────────────────────────────────────────────       ║
║                                                                ║
║                                                                ║
║     ✅  Tu voz está lista                                     ║
║                                                                ║
║     ┌──────────────────────────────────────────────┐          ║
║     │  Voz: "María García"                         │          ║
║     │  Motor: Chatterbox TTS                       │          ║
║     │  Personalidad: ✅ Activada                   │          ║
║     │  API: localhost:8765 🟢 Activa               │          ║
║     └──────────────────────────────────────────────┘          ║
║                                                                ║
║                                                                ║
║     Escribe algo y escúchalo con tu voz:                      ║
║                                                                ║
║     ┌──────────────────────────────────────────────┐          ║
║     │                                              │          ║
║     │  Escribe aquí...                             │          ║
║     │                                              │          ║
║     └──────────────────────────────────────────────┘          ║
║                                                                ║
║     ┌───────────────┐  ┌───────────────┐                      ║
║     │  🔊 Hablar    │  │  🔊 + ✨      │                      ║
║     │  (solo voz)   │  │  (con person.)│                      ║
║     └───────────────┘  └───────────────┘                      ║
║                                                                ║
║                                                                ║
║  ───────────────────────────────────────────────               ║
║                                                                ║
║  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      ║
║  │ ➕ Nueva │  │ ✏️ Editar│  │ 🗣 AAC  │  │ 📊 Uso  │      ║
║  │   voz    │  │  persona.│  │  Config  │  │  Stats   │      ║
║  └──────────┘  └──────────┘  └──────────┘  └──────────┘      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### UX Notes — Pantalla 6
- **Estado claro:** Voz, motor, personalidad, API — todo visible
- **Acción principal:** Campo de texto + botón "Hablar" — uso inmediato
- **2 modos de hablar:** Solo voz (rápido) o con personalidad (más lento pero personalizado)
- **Acciones secundarias:** 4 botones en grid inferior
  - Nueva voz: clonar otra
  - Editar personalidad: ajustar cuestionario
  - AAC Config: conectar con software AAC
  - Uso/Stats: métricas de uso
- **Eye tracking:** Campo de texto puede necesitar teclado virtual AAC
- **API status:** Indicador verde = servicio corriendo

---

## Accesibilidad — Checklist por Pantalla

| Criterio | P1 | P2 | P3 | P4 | P5 | P6 |
|----------|----|----|----|----|----|----|
| Targets ≥ 64px | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Máx. 6 acciones | ✅ (3) | ✅ (1) | ✅ (2) | ✅ (4) | ✅ (4) | ✅ (6) |
| Alto contraste | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Keyboard nav | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| No scroll req. | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Focus visible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ARIA labels | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sin animaciones distractoras | ✅ | ⚠️* | ✅ | ✅ | ✅ | ✅ |

*P2: La barra de progreso se anima suavemente — aceptable porque no requiere interacción.
*P6: El dashboard puede necesitar scroll en pantallas pequeñas → diseñar responsive.

---

## Navegación General (Wizard Flow)

```
Landing (P1) → Instalación (P2) → Clonación (P3) → Personalidad (P4) → Integración (P5) → Dashboard (P6)
                                                     ↑ opcional ↑
                                                     (puede saltarse)
```

- **Back button:** Siempre disponible (esquina superior izquierda, target 48px+)
- **Progress indicator:** "Paso X de 3" visible en todas las pantallas del wizard
- **Skip:** Disponible en pasos opcionales (personalidad)
- **Return:** Desde Dashboard, el usuario puede volver a cualquier sección

---

## Responsive Design (Breakpoints)

| Dispositivo | Layout | Notas |
|-------------|--------|-------|
| Desktop (>1024px) | Centrado, max-width 800px | Óptimo para eye tracking |
| Tablet (768-1024px) | Full width, padding 32px | iPad + Tobii PCEye |
| Mobile (<768px) | Stack vertical, padding 16px | No prioritario para ELA |

---

*Mockups Web App — 6 Pantallas*  
*Proyecto VoiceClone — 2026*  
*Diseñados para ser usados con los ojos, un botón, o un teclado.*
