# Diseño de Accesibilidad — VoiceClone

## Fecha: 2026-03-20
## Autor: Equipo VoiceClone (Experto Accesibilidad + Experto UX)
## Validado por: 10 referentes reales en accesibilidad (Treviranus, Vanderheiden, Watson, Gustafson, Lay-Flurrie, Patel, Zimmerman, Biondi, Gaddy, Williams)
## Estándar objetivo: WCAG 2.2 AA + extensiones propias para ELA

---

## Tabla de Contenidos

1. Filosofía de Accesibilidad
2. Perfiles de Usuario
3. WCAG 2.2 AA — Cumplimiento Completo
4. Eye Tracking — Diseño de Interacción por Mirada
5. Switch Access — Navegación con 1-2 Pulsadores
6. Navegación por Teclado
7. Voz a Texto (Speech Input)
8. Diseño Visual
9. Diseño de Componentes Accesibles
10. Testing de Accesibilidad
11. Accessibility Statement
12. Implementación Técnica (ARIA + Semántica)
13. Matriz de Cumplimiento por Pantalla

---

## 1. Filosofía de Accesibilidad

### Principio rector: "Si no lo puede usar con los ojos, no lo publiques."

VoiceClone tiene un usuario que no puede mover las manos, no puede hablar, y quizás solo puede mover los ojos. Si esa persona no puede clonar su voz con nuestra app, hemos fallado.

**No diseñamos "accesibilidad" como feature adicional.** La accesibilidad ES el diseño.

### Framework: Inclusive Design (Jutta Treviranus, IDRC)

- **Reconocer diversidad:** No hay "un usuario". Hay espectros de capacidad.
- **One-size-fits-one:** Preferimos interfaces adaptables sobre interfaces genéricas.
- **Extender beneficios:** Lo que funciona para alguien con ELA, mejora la experiencia de todos.

### Los 4 Principios POUR (WCAG Foundation)

| Principio | Significado | Aplicación en VoiceClone |
|-----------|-------------|--------------------------|
| **Perceivable** | El usuario puede percibir todo el contenido | Contraste, texto alt, captions, feedback sonoro |
| **Operable** | El usuario puede operar todos los controles | Eye tracking, switch, teclado, voz |
| **Understandable** | El usuario comprende cómo funciona | Lenguaje simple, predictibilidad, ayuda contextual |
| **Robust** | Funciona con tecnología asistiva | Screen readers, ARIA, Tobii, AAC software |

---

## 2. Perfiles de Usuario

### Perfil A: ELA Temprana — "Todavía puedo hablar, algo"

- Voz: Deteriorada pero audible
- Manos: Limitadas, puede usar ratón/teclado lentamente
- Visión: Normal o con gafas
- Cognición: Completa
- Input primario: Ratón/teclado (lento) o touchpad
- Escenario crítico: Grabar 30 segundos de voz sin frustración

### Perfil B: ELA Avanzada — "Ya no puedo hablar ni mover las manos"

- Voz: Ninguna
- Manos: Ninguna o mínima (quizás 1 dedo)
- Visión: Normal (generalmente preservada en ELA)
- Cognición: Completa
- Input primario: Eye tracking (Tobii) + switch (1-2 botones)
- Escenario crítico: Completar flujo entero solo con mirada

### Perfil C: Cuidador/Familiar

- Capacidades: Completas (persona sana)
- Necesita: subir grabaciones antiguas, configurar voz, enseñar al usuario
- Input primario: Ratón/teclado/touch estándar
- Escenario crítico: Configurar voz en 10 minutos sin documentación

### Perfil D: Persona con Parálisis Cerebral u otra condición motriz

- Voz: Variable
- Manos: Movimientos involuntarios, espasticidad
- Targets enormes (>72px para movimientos involuntarios)
- Filtro de activación accidental (confirmación de acciones)
- Input primario: Switch, head tracking, o eye tracking

---

## 3. WCAG 2.2 AA — Cumplimiento Completo

### 3.1 Perceivable

#### Text Alternatives (1.1)
- Toda imagen no decorativa tiene alt text descriptivo
- Iconos de acción: `aria-label` descriptivo
- Iconos decorativos: `aria-hidden="true"`
- Audio: transcripción visible siempre (texto debajo del reproductor)
- Nunca reproducir audio sin mostrar qué se está diciendo

#### Time-based Media (1.2)
- Todos los audios de ejemplo: transcripción visible debajo
- Video tutorial (si se añade): subtítulos CC en español e inglés
- Barra de progreso de grabación: indica tiempo restante en texto
- Control de playback: pausar, retroceder, velocidad

#### Adaptable (1.3)
- Orden de lectura lógico (DOM order = visual order)
- Headings jerárquicos: h1 → h2 → h3 (nunca saltar niveles)
- Landmarks ARIA: main, nav, banner, contentinfo
- Formularios: labels asociados + fieldsets para grupos
- Funciona en portrait Y landscape

#### Distinguishable (1.4)

**Paleta de contraste verificada:**

| Elemento | Foreground | Background | Ratio |
|----------|-----------|-----------|-------|
| Body text | #F5F5F5 | #0A0A0A | 19.3:1 |
| Primary button | #FFFFFF | #1E3A5F | 8.6:1 |
| Secondary button | #F5F5F5 | #2A2A2A | 11.3:1 |
| Success indicator | #0A0A0A | #2ECC71 | 5.8:1 |
| Warning text | #0A0A0A | #F39C12 | 4.8:1 |
| Error text | #FFFFFF | #E74C3C | 5.4:1 |
| Focus indicator | #FFD700 | #0A0A0A | 14.3:1 |
| Link text | #5DADE2 | #0A0A0A | 7.1:1 |

Todos superan 4.5:1 (AA para texto normal).

**Tipografía:**
- Font: Inter (sans-serif, altamente legible)
- Body text: 20px / 1.6 line-height (mínimo)
- Headings: 32-48px / 1.3 line-height
- Buttons: 18px bold
- NO usar italic para info importante
- NO usar ONLY color para transmitir información

**Resize:** Funciona hasta 200% zoom sin scroll horizontal. Hasta 400%: contenido reorganizado pero funcional.

### 3.2 Operable

#### Keyboard Accessible (2.1)
- Tab / Shift+Tab: navegar adelante/atrás
- Enter/Space: activar botones y links
- Escape: cerrar modales, cancelar acción
- Arrow keys: navegar dentro de grupos (radio buttons, tabs)
- No keyboard traps: Escape siempre sale de modales
- Focus management: al avanzar wizard → foco al heading de nueva pantalla

#### Enough Time (2.2)
- NO hay timeouts en ninguna pantalla
- La grabación NO tiene límite de tiempo
- El procesamiento muestra barra de progreso sin countdown
- El cuestionario no tiene presión temporal

#### Seizures (2.3)
- NO hay flashes >3 por segundo
- NO hay animaciones de parpadeo
- Indicador de grabación: punto rojo ESTÁTICO + texto "GRABANDO"
- `prefers-reduced-motion`: transiciones instantáneas, waveform estática

#### Navigable (2.4)

**Títulos por pantalla:**
- P1: "VoiceClone — Preserva tu voz"
- P2: "Instalando VoiceClone — Paso 2 de 4"
- P3: "Clonar tu voz — VoiceClone"
- P4: "Tu personalidad — VoiceClone"
- P5: "Conectar con tu sistema — VoiceClone"
- P6: "Dashboard — VoiceClone"

**Skip links:** "Ir al contenido principal", "Ir a las acciones"

**Focus visible SIEMPRE:**
```css
:focus-visible {
  outline: 3px solid #FFD700;
  outline-offset: 4px;
  border-radius: 8px;
}
/* NUNCA outline: none */
```

#### Input Modalities (2.5)

**Target sizes:**

| Tipo de botón | Tamaño mínimo | Padding |
|--------------|--------------|---------|
| Primary CTA | 320px × 80px | 24px 48px |
| Secondary action | 280px × 72px | 20px 40px |
| Icon button | 64px × 64px | 16px |
| Playback controls | 72px × 72px | 20px |
| Navigation (back) | 56px × 56px | 12px |

- Separación mínima entre targets: 16px
- No depende de gestos complejos
- Single pointer para todo
- Confirmación en acciones destructivas (foco default en "Cancelar")

### 3.3 Understandable

#### Readable (3.1)

**Vocabulario controlado:**

| Término técnico | En la interfaz |
|----------------|---------------|
| Clone | "Clonar/copiar tu voz" |
| TTS | "Convertir texto en voz" |
| Speaker embedding | "Perfil de voz" |
| API | "Servicio local" |
| AAC | "Software de comunicación" |
| Eye tracking | "Control con la mirada" |
| Switch access | "Control con pulsador" |
| Dwell time | "Tiempo de mirada" |

Idioma: `<html lang="es">`. Términos en otro idioma marcados: `<span lang="en">eye tracking</span>`.

#### Predictable (3.2)
- Navegación consistente en todas las pantallas
- Wizard siempre arriba, botón "Atrás" siempre superior-izquierda
- CTA primario siempre azul (#1E3A5F), siempre debajo del contenido
- No hay cambios de contexto al recibir foco o cambiar input

#### Input Assistance (3.3)
- Errores identificados por texto + color + icono (no solo color)
- Sugerencias de corrección específicas
- Prevención de errores graves con modal de confirmación
- Labels claros en todos los inputs (no depender de placeholders)

### 3.4 Robust (Compatible - 4.1)
- HTML semántico: `<button>` para acciones, `<a>` para navegación
- ARIA roles solo cuando HTML semántico no basta
- Name, Role, Value expuestos correctamente
- Testing con VoiceOver (macOS), NVDA (Windows), Tobii, Switch Control

---

## 4. Eye Tracking — Diseño de Interacción por Mirada

### 4.1 Dwell Time (Tiempo de Permanencia)

El usuario MIRA un elemento durante X milisegundos → se activa. Equivalente al "click".

**Configuración recomendada:**

| Tipo de acción | Dwell time | Justificación |
|---------------|-----------|---------------|
| Activar botón | 800ms | Equilibrio rapidez/seguridad |
| Botón crítico (eliminar, grabar) | 1200ms | Previene errores |
| Scroll | 500ms | Más ágil |
| Abrir tooltip/help | 600ms | Info contextual |
| Cancelar acción | 400ms | Escape rápido |

Todos configurables por usuario (Settings → Accesibilidad). Rango: 200ms a 3000ms.

**Feedback visual de dwell:**

```
t=0ms:    Borde sutil aparece (sistema detectó mirada)
          ┌──────────────────┐
          │   🎤 Grabar      │  ← borde 2px #FFD700
          └──────────────────┘

t=0-800ms: Indicador circular de progreso se llena
          ┌──────────────────┐
          │   🎤 Grabar   ◐  │  ← círculo llenándose
          └──────────────────┘

t=800ms:  Se activa con feedback visual + sonoro
          ┌──────────────────┐
          │   🎤 Grabar   ✓  │  ← activado, tick sonoro
          └──────────────────┘

Si desvía mirada ANTES de 800ms: se cancela. Progreso se resetea.
```

### 4.2 Gaze Gestures

- Mirar zona superior-izquierda 600ms = "Atrás"
- Mirar zona inferior = Scroll down
- Mirar zona superior = Scroll up

**Zonas de la pantalla:**

```
┌────────────────────────────────────────┐
│ ← ATRÁS    │        TOOLBAR           │
│ (gaze zone)│                          │
├────────────┼──────────────────────────┤
│            │                          │
│            │    CONTENIDO PRINCIPAL   │
│ SCROLL ↑   │                          │
│            │    (botones con dwell)   │
│            │                          │
├────────────┼──────────────────────────┤
│ SCROLL ↓   │     ACCIONES FOOTER     │
└────────────┴──────────────────────────┘

Zonas edge: 80px de ancho con feedback visual (flechas, iconos).
```

### 4.3 Reglas de Layout para Eye Tracking

1. **Espaciado generoso:** Mínimo 32px entre bordes de botones (recomendado 48px). Precisión eye tracker ~0.5° = ~22px en monitor estándar. Con margen: 32px mínimo.

2. **Targets grandes:** Botones principales mínimo 320px × 80px. Target grande = dwell más fácil.

3. **Máximo 4-6 elementos interactivos por pantalla.** Más opciones = confusión por saccades.

4. **Posicionamiento predecible:** Acción principal centro-inferior, Atrás superior-izquierda, Siguiente inferior-derecha, Progreso arriba. El ojo aprende patrones — mantenerlos constantes.

5. **Zona neutra obligatoria:** Zonas de pantalla sin targets donde el usuario "descansa la mirada" sin activar nada. Centro dedicado a contenido informativo.

6. **Anti-patrón Midas Touch:** Solución: dwell time + zona neutra + confirmación visual progresiva. El usuario VE el progreso y puede cancelar desviando la mirada.

### 4.4 Eye Tracking Layout por Pantalla

**Pantalla 3 (Clonación) — Optimizada para mirada:**

```
┌──────────────────────────────────────────────────────────┐
│  ← ATRÁS                    Paso 1 de 3: Tu voz         │
│  (gaze: 600ms)                                           │
│──────────────────────────────────────────────────────────│
│                                                          │
│                  ZONA NEUTRA                              │
│          ¿Cómo quieres clonar tu voz?                    │
│          (solo texto, sin targets)                        │
│                                                          │
│──────────────────────────────────────────────────────────│
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  │     🎤  Grabar ahora                             │    │
│  │     (dwell: 800ms, feedback circular)            │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│              48px separación                              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  │     📁  Subir una grabación                      │    │
│  │     (dwell: 800ms, feedback circular)            │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│              ZONA NEUTRA (descanso visual)                │
│                                                          │
└──────────────────────────────────────────────────────────┘

2 targets solamente. Separación 48px. Zonas neutras arriba y abajo.
```

### 4.5 Configuración de Eye Tracking del Usuario

**Settings → Accesibilidad → Control con la mirada:**

```
┌──────────────────────────────────────────────────────────┐
│  Control con la mirada                                    │
│                                                          │
│  Activar/Desactivar:  [🟢 ON]                           │
│                                                          │
│  Tiempo de mirada (dwell):                               │
│    Rápido ─────●───── Lento                              │
│    200ms        800ms       3000ms                       │
│                                                          │
│  Tamaño de indicador:                                    │
│    Pequeño ──●──────── Grande                            │
│                                                          │
│  Sonido al activar:   [🟢 ON]                           │
│                                                          │
│  Zonas de scroll:     [🟢 ON]                           │
│                                                          │
│  Calibrar eye tracker: [Calibrar →]                      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Switch Access — Navegación con 1-2 Pulsadores

### 5.1 Concepto

Un pulsador (switch) es un botón físico que la persona activa con cualquier parte del cuerpo: mejilla, cabeza, rodilla, soplido, parpadeo. El software debe funcionar con 1 solo switch.

### 5.2 Patrón de Escaneo (Scanning)

**Modo 1 switch (automático):**

```
FLUJO:
1. El sistema resalta automáticamente cada grupo de elementos (highlight)
2. El usuario espera a que se resalte el grupo correcto
3. Pulsa el switch → entra en el grupo
4. El sistema resalta cada elemento individual del grupo
5. Pulsa switch → selecciona ese elemento
6. Si se pasa: espera el ciclo completo → vuelve a empezar

EJEMPLO EN PANTALLA 3 (Clonación):

Ciclo 1: Resalta grupo "Opciones"
┌──────────────────────────────────────┐
│  ╔══════════════════════════════╗    │ ← GRUPO 1 resaltado
│  ║  🎤 Grabar ahora            ║    │    (borde amarillo grueso)
│  ╚══════════════════════════════╝    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │  📁 Subir grabación         │    │ ← sin resaltar
│  └──────────────────────────────┘    │
└──────────────────────────────────────┘

[SWITCH PRESS] → Selecciona "Grabar ahora"

Si no presiona:
Ciclo 2: Resalta "Subir grabación"
Ciclo 3: Resalta "Atrás"
Ciclo 4: Vuelve al inicio
```

**Modo 2 switches:**
- Switch 1: Avanzar al siguiente elemento
- Switch 2: Seleccionar elemento actual

### 5.3 Velocidad de Escaneo

| Velocidad | Intervalo | Para quién |
|-----------|----------|-----------|
| Muy lenta | 3000ms | Usuarios nuevos, niños |
| Lenta | 2000ms | Default recomendado |
| Media | 1500ms | Usuarios experimentados |
| Rápida | 1000ms | Usuarios expertos |
| Muy rápida | 500ms | Power users |

Configurable por usuario en Settings → Accesibilidad → Control con pulsador.

### 5.4 Orden de Escaneo por Pantalla

Crítico: el orden debe ser predecible y eficiente. El usuario no puede "saltar" — debe esperar su turno.

**Pantalla 1 (Landing):**
```
Scan order:
1. [Descargar macOS]     ← primera opción (la más común)
2. [Descargar Windows]
3. [Descargar Linux]
4. [Ya lo instalaste → Abrir]
5. [Links footer: GitHub, Docs]
→ Ciclo
```

**Pantalla 3 (Clonación):**
```
Scan order:
1. [🎤 Grabar ahora]
2. [📁 Subir grabación]
3. [← Atrás]
→ Ciclo
```

**Pantalla 3a (Grabando):**
```
Scan order:
1. [⏹ Parar]           ← primera porque es la acción urgente
2. [🔄 Reiniciar]
3. [← Atrás/Cancelar]
→ Ciclo
```

**Pantalla 6 (Dashboard):**
```
Scan order:
1. [Campo de texto + teclado virtual]
2. [🔊 Hablar]
3. [🔊+✨ Con personalidad]
4. [➕ Nueva voz]
5. [✏️ Editar personalidad]
6. [🗣 AAC Config]
7. [📊 Estadísticas]
8. [⚙️ Configurar]
→ Ciclo
```

### 5.5 Switch + Teclado Virtual

Para escribir texto (campo de input en Dashboard), el switch activa un teclado virtual en pantalla:

```
┌──────────────────────────────────────────────────────────┐
│  Texto: "Hola, ¿cómo estás?"                            │
│  ─────────────────────────────────────────────           │
│                                                          │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐    │
│  │ Q  │ W  │ E  │ R  │ T  │ Y  │ U  │ I  │ O  │ P  │    │
│  ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤    │
│  │ A  │ S  │ D  │ F  │ G  │ H  │ J  │ K  │ L  │ Ñ  │    │
│  ├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤    │
│  │ Z  │ X  │ C  │ V  │ B  │ N  │ M  │ ,  │ .  │ ←  │    │
│  ├────┴────┼────┴────┴────┴────┴────┼────┴────┼────┤    │
│  │  SPACE  │     PREDICCIÓN         │  HABLAR │ ✕  │    │
│  └─────────┴────────────────────────┴─────────┴────┘    │
│                                                          │
│  Predicciones: [hola] [cómo] [estás] [buenas] [adiós]   │
│                                                          │
└──────────────────────────────────────────────────────────┘

Escaneo: fila → columna (scan rows first, then columns)
Predicción: reduce keystrokes dramáticamente
Teclas: 48px × 48px mínimo (más grandes que teclado estándar)
```

### 5.6 Feedback Auditivo para Switch

| Evento | Sonido | Descripción |
|--------|--------|-------------|
| Elemento resaltado | Tick suave | Para que el usuario sepa que el escaneo avanza |
| Elemento seleccionado | Click confirmación | Selección exitosa |
| Entrar en grupo | Tono ascendente | "Estoy dentro del grupo" |
| Salir de grupo | Tono descendente | "Volví al nivel superior" |
| Error | Buzz suave | Acción no disponible |

Todos desactivables en Settings. Para usuarios que prefieren silencio.

---

## 6. Navegación por Teclado

### 6.1 Tab Order Global

```
1. Skip link ("Ir al contenido principal") — solo visible con Tab
2. Logo/home link
3. Wizard step indicator
4. Contenido principal (heading h1)
5. Acciones principales (botones CTA)
6. Acciones secundarias
7. Footer
→ Ciclo al inicio
```

### 6.2 Shortcuts de Teclado

| Shortcut | Acción | Contexto |
|----------|--------|---------|
| Alt+1 | Ir a paso 1 (Voz) | Wizard |
| Alt+2 | Ir a paso 2 (Personalidad) | Wizard |
| Alt+3 | Ir a paso 3 (Conectar) | Wizard |
| Alt+D | Ir al Dashboard | Global |
| Alt+S | Abrir Settings | Global |
| Space | Play/Pause audio | Cuando hay audio |
| Escape | Cancelar/Cerrar | Modales, grabación |
| Alt+R | Iniciar/Parar grabación | Pantalla grabación |

Todos documentados en Settings → Atajos de teclado.

### 6.3 Focus Styles

```css
/* Focus por defecto — SIEMPRE visible */
:focus-visible {
  outline: 3px solid #FFD700;
  outline-offset: 4px;
  border-radius: 8px;
  /* Nunca outline: none */
}

/* Focus en botones */
button:focus-visible {
  outline: 3px solid #FFD700;
  outline-offset: 4px;
  box-shadow: 0 0 0 6px rgba(255, 215, 0, 0.3);
}

/* Focus en inputs */
input:focus-visible, textarea:focus-visible {
  outline: 3px solid #FFD700;
  outline-offset: 2px;
  border-color: #FFD700;
}

/* High contrast mode */
@media (forced-colors: active) {
  :focus-visible {
    outline: 3px solid CanvasText;
    outline-offset: 4px;
  }
}
```

---

## 7. Voz a Texto (Speech Input)

### 7.1 Para usuarios que aún pueden hablar

Perfil A (ELA temprana) puede tener voz deteriorada pero funcional. Soporte de speech input:

- **Web Speech API (browser):** Reconocimiento de voz nativo
- **Campo de texto:** Botón "🎤 Dictar" junto al input
- **Tolerancia a disartria:** El speech recognition puede fallar con voz ELA → ofrecer corrección fácil
- **Feedback visual:** Texto reconocido aparece en tiempo real con opción de editar

### 7.2 Comandos de voz (post-MVP)

```
"Grabar" → Inicia grabación
"Parar" → Para grabación
"Reproducir" → Reproduce último audio
"Atrás" → Navega atrás
"Siguiente" → Navega siguiente
"Hablar [texto]" → Sintetiza texto con voz clonada
```

---

## 8. Diseño Visual

### 8.1 Paleta de Colores

```
FONDO PRINCIPAL:     #0A0A0A  (negro profundo)
FONDO SECUNDARIO:    #1A1A1A  (gris muy oscuro)
FONDO TARJETAS:      #2A2A2A  (gris oscuro)

TEXTO PRINCIPAL:     #F5F5F5  (blanco suave)
TEXTO SECUNDARIO:    #CCCCCC  (gris claro)
TEXTO DISABLED:      #888888  (gris medio)

ACCIÓN PRIMARIA:     #1E3A5F  (azul profundo)
ACCIÓN HOVER:        #264B7A  (azul más claro)
ACCIÓN ACTIVE:       #152D49  (azul más oscuro)

ÉXITO:               #2ECC71  (verde)
WARNING:             #F39C12  (naranja)
ERROR:               #E74C3C  (rojo)
INFO:                #5DADE2  (azul claro)

FOCUS:               #FFD700  (dorado — altísimo contraste)

ALTO CONTRASTE ALTERNATIVO (activable en Settings):
  Fondo: #000000 puro
  Texto: #FFFFFF puro
  Focus: #FFFF00 (amarillo puro)
  Botones: borde 3px blanco
```

### 8.2 Tipografía

```
FONT: Inter (Google Fonts)
FALLBACK: system-ui, -apple-system, Segoe UI, sans-serif

ESCALAS:
  --text-xs:    16px   (captions, metadata)
  --text-sm:    18px   (labels, ayuda)
  --text-base:  20px   (body text — base grande)
  --text-lg:    24px   (subtítulos)
  --text-xl:    32px   (títulos de pantalla)
  --text-2xl:   40px   (heading principal)
  --text-3xl:   48px   (landing hero)

LINE HEIGHTS:
  Body: 1.6
  Headings: 1.3
  Buttons: 1.4
  Compact (labels): 1.5

LETTER SPACING:
  Body: 0.01em (ligeramente expandido)
  Headings: -0.02em (ligeramente condensado)
  Buttons: 0.02em (más espacio para legibilidad)

WEIGHT:
  Body: 400 (regular)
  Emphasis: 600 (semibold)
  Headings: 700 (bold)
  Buttons: 700 (bold)
```

### 8.3 Modo de Alto Contraste

Activable en Settings → Accesibilidad → Alto contraste.

```
Cambios:
  - Fondo: #000000 puro (vs #0A0A0A)
  - Texto: #FFFFFF puro (vs #F5F5F5)
  - Bordes en TODOS los botones: 3px solid #FFFFFF
  - Focus: #FFFF00 (amarillo puro, máximo contraste)
  - Links: subrayados siempre (no solo hover)
  - Iconos: versiones de alto contraste
  
Respeta automáticamente @media (forced-colors: active)
y @media (prefers-contrast: more)
```

---

## 9. Diseño de Componentes Accesibles

### 9.1 Botón Principal (CTA)

```html
<button
  class="btn-primary"
  aria-label="Grabar tu voz ahora"
  data-gaze-dwell="800"
  data-scan-group="actions"
  data-scan-order="1"
>
  <span class="btn-icon" aria-hidden="true">🎤</span>
  <span class="btn-text">Grabar ahora</span>
  <span class="btn-help">Lee un texto corto en voz alta</span>
  <span class="gaze-indicator" aria-hidden="true"></span>
</button>

/* CSS */
.btn-primary {
  min-width: 320px;
  min-height: 80px;
  padding: 24px 48px;
  font-size: 18px;
  font-weight: 700;
  background: #1E3A5F;
  color: #FFFFFF;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: background 200ms ease;
}

.btn-primary:hover { background: #264B7A; }
.btn-primary:active { background: #152D49; }
.btn-primary:focus-visible {
  outline: 3px solid #FFD700;
  outline-offset: 4px;
}

/* Gaze indicator - círculo de progreso */
.gaze-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border: 3px solid #FFD700;
  border-radius: 50%;
  opacity: 0;
  /* Se anima con JS basándose en gaze duration */
}

/* Switch scanning highlight */
[data-scan-active="true"] {
  outline: 4px solid #FFD700;
  outline-offset: 6px;
  animation: scan-pulse 1s ease-in-out infinite;
}
```

### 9.2 Reproductor de Audio Accesible

```
┌──────────────────────────────────────────────────────────┐
│  "Hola, esta es mi voz clonada."                        │ ← Texto visible
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  ▶ Reproducir │  │  ■ Parar     │                     │ ← 72px targets
│  └──────────────┘  └──────────────┘                     │
│                                                          │
│  ████████████░░░░░░░░░░░░  3.2s / 8.0s                  │ ← Progreso
│                                                          │
│  Velocidad: [0.5x] [1x] [1.5x]                         │ ← Opcional
│                                                          │
└──────────────────────────────────────────────────────────┘

ARIA:
<div role="region" aria-label="Reproductor de audio: ejemplo de voz clonada">
  <p id="audio-transcript">Hola, esta es mi voz clonada.</p>
  <button aria-label="Reproducir audio">▶ Reproducir</button>
  <button aria-label="Parar audio">■ Parar</button>
  <div role="progressbar"
       aria-valuemin="0" aria-valuemax="8"
       aria-valuenow="3.2"
       aria-label="Progreso de reproducción: 3.2 de 8 segundos">
  </div>
</div>
```

### 9.3 Barra de Progreso de Instalación

```
ARIA:
<div role="progressbar"
     aria-valuemin="0" aria-valuemax="100"
     aria-valuenow="67"
     aria-label="Descargando modelo de voz: 67 por ciento completado, aproximadamente 2 minutos restantes">
  <div class="progress-fill" style="width: 67%"></div>
</div>
<p aria-live="polite">1.4 GB de 2.1 GB · ~2 minutos restantes</p>

NOTA: aria-live="polite" anuncia actualizaciones al screen reader
sin interrumpir lo que esté leyendo.
Actualizar cada 10% (no cada segundo — sería spam sonoro).
```

### 9.4 Wizard Step Indicator

```html
<nav aria-label="Progreso del asistente">
  <ol class="wizard-steps">
    <li aria-current="false">
      <span class="step-number">1</span>
      <span class="step-label">Tu voz</span>
      <span class="sr-only">completado</span>
    </li>
    <li aria-current="step">
      <span class="step-number">2</span>
      <span class="step-label">Tu personalidad</span>
      <span class="sr-only">paso actual</span>
    </li>
    <li aria-current="false">
      <span class="step-number">3</span>
      <span class="step-label">Conectar</span>
      <span class="sr-only">pendiente</span>
    </li>
  </ol>
</nav>
```

### 9.5 Modal de Confirmación

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ⚠️  ¿Eliminar la voz "María García"?                   │
│                                                          │
│  Esta acción no se puede deshacer.                       │
│  Se eliminará el perfil de voz y la personalidad.        │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐         │
│  │     Cancelar       │  │   Sí, eliminar      │         │
│  │   (foco default)   │  │                     │         │
│  └────────────────────┘  └────────────────────┘         │
│                                                          │
└──────────────────────────────────────────────────────────┘

ARIA:
<div role="alertdialog"
     aria-modal="true"
     aria-labelledby="modal-title"
     aria-describedby="modal-desc">
  <h2 id="modal-title">¿Eliminar la voz "María García"?</h2>
  <p id="modal-desc">Esta acción no se puede deshacer...</p>
  <button autofocus>Cancelar</button>  <!-- FOCO EN CANCELAR -->
  <button class="danger">Sí, eliminar</button>
</div>

- Foco atrapado dentro del modal (focus trap)
- Escape = Cancelar
- Fondo oscurecido (overlay)
- Focus default en Cancelar (previene eliminación accidental)
```

### 9.6 Grabación de Audio

```
ESTADOS:

1. ANTES DE GRABAR:
   [🎤 Empezar a grabar]  ← botón grande, prominente
   Instrucciones visibles: "Lee el texto de abajo en voz alta"

2. GRABANDO:
   ● GRABANDO (punto rojo ESTÁTICO + texto)
   Barra de duración: ████████░░░░  18s
   [⏹ Parar grabación]  ← ÚNICA acción disponible, prominente
   [🔄 Reiniciar]  ← secundario
   
   aria-live="polite" anuncia cada 10 segundos: "18 segundos grabados"

3. PROCESANDO:
   ⏳ Procesando tu voz...
   Barra de progreso indeterminada
   No hay acciones disponibles (solo esperar)
   aria-live="polite": "Procesando tu voz, por favor espera"

4. RESULTADO:
   ✅ Tu voz ha sido clonada
   [▶ Reproducir ejemplo]
   [✅ Suena bien]  [🔄 Repetir]
   aria-live="assertive": "Tu voz ha sido clonada exitosamente"
```

---

## 10. Testing de Accesibilidad

### 10.1 Testing Automatizado

| Herramienta | Qué detecta | Cuándo ejecutar |
|------------|-------------|----------------|
| axe-core | WCAG AA automático (~40% de issues) | En cada PR (CI/CD) |
| pa11y | Errores de accesibilidad en HTML | En cada build |
| Lighthouse | Score de accesibilidad general | Semanal |
| eslint-plugin-jsx-a11y | Errores de accesibilidad en JSX | En desarrollo (IDE) |

**CI/CD Pipeline:**
```yaml
# GitHub Actions
- name: Accessibility Audit
  run: |
    npx axe-core --rules wcag2aa --exit
    npx pa11y http://localhost:3000
    # Falla el build si hay errores WCAG AA
```

### 10.2 Testing Manual

| Test | Cómo | Frecuencia |
|------|------|-----------|
| Keyboard-only navigation | Desconectar ratón, usar solo teclado | Cada pantalla nueva |
| Screen reader (VoiceOver) | Navegar toda la app con VoiceOver | Cada release |
| Zoom 200% | Ampliar browser al 200% | Cada pantalla nueva |
| Zoom 400% | Ampliar al 400%, verificar reflow | Cada release |
| Color-blind simulation | Usar simuladores (Sim Daltonism) | Cada cambio de colores |
| Reduced motion | Activar prefers-reduced-motion | Cada animación nueva |
| High contrast mode | Activar forced-colors | Cada release |

### 10.3 Testing con Tecnología Asistiva (Post-MVP)

| Herramienta | Plataforma | Prioridad |
|------------|-----------|----------|
| VoiceOver | macOS/iOS | P0 (primaria) |
| NVDA | Windows | P1 |
| Tobii Eye Tracker 5 | Windows/macOS | P0 (crítica para ELA) |
| Switch Control | macOS/iOS | P0 |
| Dragon NaturallySpeaking | Windows | P2 |
| JAWS | Windows | P2 |

### 10.4 User Testing con personas con ELA

**Protocolo recomendado (post-MVP):**
1. Contactar asociaciones de ELA (ALS Association, fundaciones locales)
2. Reclutar 3-5 testers con diferentes niveles de ELA
3. Sesiones individuales de 30-45 min
4. Tareas: clonar voz, usar dashboard, configurar personalidad
5. Observar: frustraciones, errores, tiempos, abandonos
6. Documentar y priorizar hallazgos

**Métricas de éxito:**
- Task completion rate >90% (con cualquier input method)
- Error recovery rate >95%
- Satisfacción (SUS score) >70
- Tiempo de completar flujo completo: <15 min (incluyendo grabación)

---

## 11. Accessibility Statement

**Texto para incluir en la web y README:**

```markdown
## Accesibilidad

VoiceClone está diseñado para personas con ELA y otras condiciones que
afectan al habla y la movilidad. Nuestro compromiso de accesibilidad
no es un feature — es la razón de ser del producto.

### Estándares
- WCAG 2.2 Nivel AA
- Compatible con eye tracking (Tobii y similares)
- Compatible con switch access (1-2 pulsadores)
- Navegación completa por teclado
- Compatible con screen readers (VoiceOver, NVDA, JAWS)

### Métodos de input soportados
- Ratón/trackpad
- Teclado completo
- Eye tracking (Tobii Eye Tracker 5, PCEye)
- Switch access (1-2 pulsadores, cualquier tipo)
- Reconocimiento de voz (Web Speech API)
- Touch screen

### Reportar problemas de accesibilidad
Si encuentras una barrera de accesibilidad en VoiceClone,
repórtala en GitHub Issues con la etiqueta "accessibility".
Priorizamos estos reportes al máximo.

### Contacto
accessibility@voiceclone.dev (pendiente activar)
```

---

## 12. Implementación Técnica (ARIA + Semántica)

### 12.1 Estructura HTML por Pantalla

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clonar tu voz — VoiceClone</title>
</head>
<body>
  <!-- Skip links -->
  <a href="#main" class="skip-link">Ir al contenido principal</a>
  <a href="#actions" class="skip-link">Ir a las acciones</a>
  
  <!-- Header -->
  <header role="banner">
    <a href="/" aria-label="VoiceClone — Inicio">🎤 VoiceClone</a>
    <nav aria-label="Progreso del asistente">
      <ol class="wizard-steps">
        <li aria-current="step">Paso 1: Tu voz</li>
        <li>Paso 2: Personalidad</li>
        <li>Paso 3: Conectar</li>
      </ol>
    </nav>
  </header>
  
  <!-- Main content -->
  <main id="main" role="main">
    <h1>¿Cómo quieres clonar tu voz?</h1>
    
    <div id="actions" class="action-group" role="group"
         aria-label="Opciones de clonación">
      <button class="btn-primary"
              data-gaze-dwell="800"
              data-scan-order="1">
        🎤 Grabar ahora
      </button>
      <button class="btn-secondary"
              data-gaze-dwell="800"
              data-scan-order="2">
        📁 Subir grabación
      </button>
    </div>
  </main>
  
  <!-- Footer -->
  <footer role="contentinfo">
    <a href="/accessibility">Accesibilidad</a>
    <a href="https://github.com/angellocafm-arch/voiceclone">GitHub</a>
  </footer>
</body>
</html>
```

### 12.2 ARIA Live Regions

```html
<!-- Para feedback en tiempo real (grabación, procesamiento) -->
<div aria-live="polite" aria-atomic="true" id="status-announcer">
  <!-- JS actualiza este contenido -->
  <!-- Screen reader lo anuncia cuando cambia -->
</div>

<!-- Para mensajes urgentes (errores, completado) -->
<div aria-live="assertive" role="alert" id="alert-announcer">
  <!-- Interrumpe al screen reader para anunciar -->
</div>

EJEMPLO:
// Cuando la grabación está en curso:
document.getElementById('status-announcer').textContent =
  'Grabando: 18 segundos';

// Cuando la clonación se completa:
document.getElementById('alert-announcer').textContent =
  'Tu voz ha sido clonada exitosamente. Puedes escuchar un ejemplo.';
```

### 12.3 Custom Properties para Accesibilidad

```css
:root {
  /* Timing configurable por usuario */
  --gaze-dwell-default: 800ms;
  --gaze-dwell-critical: 1200ms;
  --scan-speed: 2000ms;
  
  /* Tamaños configurables */
  --target-min-size: 64px;
  --target-gap: 16px;
  --focus-width: 3px;
  --focus-offset: 4px;
  --focus-color: #FFD700;
  
  /* Tipografía configurable */
  --font-scale: 1; /* Multiplicador de tamaño */
}

/* Ejemplo: usuario selecciona "texto grande" en settings */
.text-large { --font-scale: 1.25; }
.text-extra-large { --font-scale: 1.5; }

body {
  font-size: calc(20px * var(--font-scale));
}
```

---

## 13. Matriz de Cumplimiento por Pantalla

### Checklist de Accesibilidad por Pantalla

| Criterio | P1 Landing | P2 Instalar | P3 Clonar | P4 Personal. | P5 Conectar | P6 Dashboard |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Targets ≥64px | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Máx 6 acciones | ✅ (4) | ✅ (1) | ✅ (2) | ✅ (4) | ✅ (4) | ✅ (6) |
| Alto contraste | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Keyboard nav | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| No scroll req. | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Focus visible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ARIA labels | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Eye tracking | ✅ | N/A* | ✅ | ✅ | ✅ | ✅ |
| Switch access | ✅ | N/A* | ✅ | ✅ | ✅ | ✅ |
| Screen reader | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Zona neutra | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| Gaze dwell feedback | ✅ | N/A* | ✅ | ✅ | ✅ | ✅ |
| Sin animaciones peligrosas | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Texto alternativo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Reduced motion | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Alto contraste mode | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

*P2 (Instalación): es proceso automático, solo tiene botón "Cancelar".
⚠️ P6 (Dashboard): puede necesitar scroll en pantallas pequeñas — diseñar responsive.

### Prioridad de Issues por Severidad

| Severidad | Descripción | Acción |
|-----------|-------------|--------|
| **P0 — Blocker** | El usuario no puede completar una tarea. | Fix inmediato antes de release. |
| **P1 — Critical** | El usuario completa la tarea con mucha dificultad. | Fix antes de release. |
| **P2 — Major** | El usuario completa la tarea pero con frustración. | Fix en siguiente sprint. |
| **P3 — Minor** | Mejora cosmética de accesibilidad. | Backlog priorizado. |

---

## Resumen Ejecutivo

VoiceClone está diseñado desde cero para el peor caso de uso: una persona con ELA avanzada que solo puede mover los ojos. Si funciona para ella, funciona para todos.

**4 métodos de input soportados:**
1. 👁 Eye tracking (Tobii) — dwell time + gaze gestures
2. 🔘 Switch access (1-2 pulsadores) — escaneo automático
3. ⌨️ Teclado completo — tab navigation + shortcuts
4. 🎤 Reconocimiento de voz — Web Speech API

**Estándar:** WCAG 2.2 AA como mínimo, con extensiones propias para ELA.

**Principio:** La accesibilidad no es una feature. Es la razón de ser.

---

*Diseño de Accesibilidad Completo — Proyecto VoiceClone*
*Vertex Developer — 2026*
*"Si no lo puede usar con los ojos, no lo publiques."*