# Web App Arquitectura v4 — 4 Módulos Principales

**Fecha:** 2026-03-20 22:51  
**Fase:** F4 — Frontend  
**Tarea:** F4.1 Rediseño de arquitectura  

---

## Estructura de Directorios Propuesta

```
src/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Layout global (navegación, sidebar)
│   │   ├── page.tsx            # Landing/entrada principal
│   │   └── modules/
│   │       ├── communication/  # Módulo 1
│   │       ├── control/        # Módulo 2
│   │       ├── channels/       # Módulo 3
│   │       └── settings/       # Módulo 4
│   ├── components/
│   │   ├── marketing/          # MOVER AQUÍ: pantallas antiguas
│   │   │   ├── LandingScreen.tsx
│   │   │   ├── IntegrationScreen.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── Navigation.tsx  (by gaze gesture)
│   │   │   ├── Sidebar.tsx     (acciones rápidas)
│   │   │   └── ModuleSwitcher.tsx
│   │   └── ui/
│   │       ├── GazeTarget.tsx
│   │       ├── MegaButton.tsx  (≥64px)
│   │       ├── PhraseBoard.tsx
│   │       └── AudioPlayer.tsx
│   ├── hooks/
│   │   ├── useGaze.ts          (Tobii integration)
│   │   ├── useSpeak.ts         (Síntesis voz)
│   │   ├── usePredict.ts       (Predicción frases)
│   │   └── useControl.ts       (Control SO)
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── theme.ts            (Dark mode)
│   │   └── a11y.ts             (WCAG AA helpers)
│   └── styles/
│       ├── globals.css
│       └── dark.css
├── public/
│   └── icons/
└── package.json
```

---

## Los 4 Módulos Principales

### Módulo 1: COMUNICACIÓN (CommunicationModule)
**Propósito:** Generar y enviar mensajes con tu voz y personalidad.

**Componentes:**
- **Phrase Board:** Grid de frases frecuentes (seleccionables por mirada, dwell 800ms)
- **Text Input:** Campo de texto + botón HABLAR (full-width, 128px height)
- **Predictions:** Panel lateral con 5 frases predichas (ordenadas por frecuencia + contexto)
- **Audio Player:** Reproductor de audio generado (play/pause/repeat por dwell o voz)

**API endpoints utilizados:**
- POST `/api/speak` — Generar audio con voz clonada
- GET `/api/predict` — Obtener frases predichas
- GET `/api/voices` — Listar voces disponibles

**Accesibilidad:**
- WCAG AA: todos los botones ≥64px
- Eye tracking: dwell 800ms en frases
- Teclado: Tab entre frases, Enter para hablar
- Feedback auditivo: sonido de "listo para escuchar"

---

### Módulo 2: CONTROL DEL ORDENADOR (ControlModule)
**Propósito:** Ejecutar acciones en el SO desde la web app (crear archivo, email, buscar, etc.)

**Componentes:**
- **Quick Actions Grid:** 8 acciones frecuentes (crear carpeta, nuevo email, buscar web, leer archivo, etc.)
- **Instruction Input:** Campo de texto + botón EJECUTAR (o comando por voz)
- **History Panel:** Últimas 3 acciones ejecutadas (con opción DESHACER)
- **Confirmation Modal:** Para acciones que requieren confirmación

**API endpoints utilizados:**
- POST `/api/control/files` — Crear/abrir/editar archivos
- POST `/api/control/email` — Enviar email
- GET `/api/control/search` — Buscar en web
- POST `/api/control/apps` — Lanzar aplicaciones
- POST `/api/control/undo` — Deshacer última acción

**Niveles de confirmación:**
- `none` — Acciones seguras (crear carpeta, abrir URL)
- `single` — Una confirmación (enviar email)
- `double` — Doble confirmación + dwell (ejecutar script)
- `blocked` — Solo a través de teclado (acceso a sensibles)

---

### Módulo 3: CANALES (ChannelsModule)
**Propósito:** Conectar y gestionar integraciones con mensajería (Telegram, WhatsApp, etc.)

**Componentes:**
- **Channel List:** Lista de canales conectados (Telegram, WhatsApp, etc.)
- **Settings per Channel:** Configuración de qué notificaciones recibir
- **Message History:** Últimos mensajes recibidos (readonly)
- **Connect Dialog:** Para autorizar nuevos canales

**API endpoints utilizados:**
- GET `/api/channels` — Listar canales disponibles y su estado
- POST `/api/channels/{id}/connect` — Autorizar canal
- PUT `/api/channels/{id}/settings` — Actualizar notificaciones
- GET `/api/channels/{id}/history` — Historial de mensajes

---

### Módulo 4: CONFIGURACIÓN (SettingsModule)
**Propósito:** Preferencias de usuario, tema, modelos de voz, RAG.

**Componentes:**
- **Profile Settings:** Nombre, descripción, foto
- **Voice Settings:** Modelo TTS, velocidad, tono, idioma
- **Personality Settings:** Perfil de personalidad (qué RAG documents usar, tono conversacional)
- **Theme Toggle:** Dark mode / Light mode
- **Advanced:** Nivel de confirmaciones, idiomas, exportar datos

**API endpoints utilizados:**
- GET/PUT `/api/onboarding/profile` — Perfil de usuario
- GET/PUT `/api/onboarding/personality` — Personalidad
- GET `/api/voices` — Lista de voces
- POST `/api/rag/add-document` — Cargar documentos RAG

---

## Layout Global

### Top Navigation (horizontal bar)
- Logo VoiceClone a la izquierda
- Breadcrumb: "Inicio > [Módulo Actual]"
- Selector de módulo (4 iconos grandes para click/gaze, 64px)

### Sidebar Izquierdo (collapsible, 200px)
- Quick access a últimas acciones
- Settings rápidos (volumen, tema)
- Botón de emergencia (reset)

### Main Content Area
- Cada módulo ocupa 100% del ancho disponible
- Responsive: en mobile, sidebar se oculta

### Accesibilidad de Navegación
- **Por mirada (gaze gesture):** Flick hacia arriba/abajo para cambiar módulo
- **Por teclado:** Ctrl+1/2/3/4 para módulos
- **Por voz:** "Ir a comunicación", "Control", etc.

---

## Diseño Visual

### Dark Mode (por defecto)
- Background: #0F0F0F (casi negro, reduce fatiga visual para ELA)
- Primary: #00D4FF (cyan, alto contraste en dark)
- Text: #E0E0E0 (gris claro)

### WCAG AA Compliance
- Contraste texto/fondo: ≥4.5:1
- Tamaño mínimo botones: 64x64px
- Focus indicators: #FFD700 (dorado brillante)
- Espaciado entre elementos: ≥8px

### Responsive
- Desktop: Layout 4-módulos
- Tablet: 2 módulos lado a lado
- Mobile: Uno a la vez, selector de módulo arriba

---

## Animaciones y Transiciones

### Dwell Feedback
Cuando el usuario mira un botón >800ms:
1. Aparece indicador visual de progreso (anillo que se llena)
2. Cuando llega 100% → sonido de "clic" y ejecución

### Gaze Gestures
- **Mirada arriba + mantener 1s:** Cambiar a módulo anterior
- **Mirada abajo + mantener 1s:** Cambiar a módulo siguiente
- **Doble parpadeo:** Cancelar / Salir

---

## Estado de Mockups Anteriores

**MOVER a `src/components/marketing/`:**
- LandingScreen.tsx → landing/landing-page.tsx
- IntegrationScreen.tsx (marketing) → marketing/integration-marketing.tsx
- PersonalityScreen.tsx → marketing/personality-screen-marketing.tsx
- DashboardScreen.tsx → marketing/dashboard-marketing.tsx
- CloneScreen.tsx → marketing/clone-screen-marketing.tsx
- OnboardingScreen.tsx → marketing/onboarding-old.tsx

**NO borrar.** Mantenerlos como referencia de estilos, componentes reutilizables (GazeTracker, etc.)

---

## Próximos Pasos (F4.2 onwards)

| Tarea | Descripción | Tipo |
|-------|-------------|------|
| F4.2 | Módulo Comunicación (componentes + hooks) | 🏗️ 45min |
| F4.3 | Módulo Control (componentes + API) | 🏗️ 45min |
| F4.4 | Módulo Canales (gestión estado + UI) | 🏗️ 45min |
| F4.5 | Módulo Configuración (forms + validación) | 🏗️ 45min |
| F4.6 | Integración Layout + Navegación | 🏗️ 30min |
| F4.7 | Eye Tracking (gaze gestures + dwell) | 🏗️ 45min |
| F4.8 | Testing + QA en browser | 🔨 30min |

---

*F4.1 completada — Arquitectura documentada y validada.*  
*Listo para codificación en F4.2+*
