# VoiceClone — Visión del Proyecto

## Fecha: 2026-03-20
## Autor: Ángel Fernández (Vertex Developer)
## Estado: v2.0 — Visión completa de 3 capas + foco ELA

---

## El Problema (Ampliado)

La clonación de voz con IA es una tecnología madura en 2026, pero tiene **dos problemas enormes**:

### Problema 1: Inaccesibilidad técnica
La clonación de voz es inaccesible para usuarios no técnicos:
- **Servicios cloud** (ElevenLabs, Play.ht) → requieren suscripción, tus datos de voz van a servidores externos, sin privacidad
- **Proyectos open source** (Coqui, Tortoise-TTS, XTTS) → requieren conocimientos de Python, dependencias, GPU, configuración manual
- **No hay integración con el sistema** → clonas la voz... ¿y luego qué? No puedes usarla como "voz del sistema" fácilmente

### Problema 2: Inaccesibilidad social + médica
**Personas con ELA** (Esclerosis Lateral Amiotrófica) y enfermedades similares pierden la voz progresivamente. En 2026:
- **No hay herramientas que preserven la VOZ de la persona ANTES de perderla**
- Los sistemas AAC (Proloquo2Go, Grid 3, Snap Core) usan voces genéricas que suenan robóticas
- Cuando la persona pierde la voz, ya no hay nada que recuperar
- Las soluciones existentes cuestan $$$$ (ElevenLabs a €330/mes, o software propietario caro)
- **Accesibilidad:** AAC + eye tracking (Tobii) + switch access no tienen integración nativa con voz clonada

**Resultado:** Personas con ELA pierden su identidad vocal, familias pierden la oportunidad de preservar la voz de un ser querido.

---

## La Solución — VoiceClone (3 Capas Integradas)

**VoiceClone** es un sistema open source de **3 capas** que permite a cualquier persona preservar, clonar y personalizar su voz. Diseñado especialmente para **ELA y enfermedades que roban la voz**.

### CAPA 1: Motor de Clonación (Local, Open Source)
**"Instala en 1 comando. Tu voz en tu ordenador. Para siempre."**

```bash
curl -fsSL https://voiceclone.dev/install | bash
# Instalador automático para macOS, Linux, Windows
```

- Modelo IA open source que **clona voces reales** (no voces pregrabadas)
- Arquitectura **Engine Adapter** — soporte para múltiples modelos intercambiables (Chatterbox TTS, XTTS v2, etc.)
- **100% local, 100% privado** — nada sale del ordenador. Tus datos de voz son solo tuyos.
- **Sin GPU requerida** — optimizado para CPU (GPU opcional para faster processing)
- **CLI + API local** — integración sencilla con otros programas

### CAPA 2: Web App Accesible (UX para ELA)
**"Diseñada para tus manos. O para tus ojos. O para un solo botón."**

- **Diseño WCAG AA completo** — contraste, tamaños de fuente, navegación por teclado
- **Eye tracking compatible** (Tobii SDK) — control por mirada (dwell time, gaze gestures)
- **Switch access** — usuarios con solo 1-2 pulsadores
- **Voice input** — para usuarios que aún pueden hablar poco
- **AAC integration** — compatible con Grid 3, Proloquo2Go, Snap Core First
  - La voz clonada se registra como "voz personalizada" en el software AAC
  - Un click en AAC → tu voz sintetiza el texto

**Flujo para personas con ELA:**
1. Abre la web app (antes de perder la voz, o con grabaciones antiguas si ya la perdió)
2. Graba tu voz (2-3 minutos o sube grabaciones viejas)
3. El sistema clona tu voz
4. Conecta con tu sistema AAC (Tobii, Grid 3, etc.)
5. **Tu voz sigue siendo tu voz** — incluso cuando tu cuerpo dice que no

### CAPA 3: Personalidad IA (Diferenciador Único)
**"No solo suena como tú. Se expresa como tú."**

Aprovecha arquitectura OpenClaw para capturar la **ESENCIA de la persona**:
- Vocabulario característico y frases típicas
- Forma de expresarse, ironía, humor
- Manías verbales, patrones de comunicación
- Contexto y referencias personales

**Arquitectura:**
1. LLM (Claude/local) genera texto PERSONALIZADO basado en el perfil de la persona
2. Ese texto se sintetiza con la voz clonada
3. Resultado: **no solo suena como tú, SE EXPRESA como tú**

**Aplicaciones:**
- Mensajes de voz personalizados (amigos, familia)
- AAC que responde "como tú lo harías"
- Recording legado: "Mi voz, mi personalidad, para siempre"

---

## Usuarios Objetivo

### Usuario primario: Personas con ELA
- Quieren **preservar su voz ANTES de perderla**
- Necesitan accesibilidad: eye tracking, AAC, switch access
- Les importa **que suene como ellos** — no quieren voces robóticas genéricas
- Situación económica variable — necesitan gratis/barato, no ElevenLabs

### Usuario secundario: Familias con miembros con ELA
- Quieren preservar la voz de un ser querido con grabaciones antiguas
- Necesitan herramientas sencillas, intuitivas
- Apoyo emocional: "Su voz sigue con nosotros"

### Usuario terciario: Personas con otras discapacidades
- Parálisis cerebral, distrofia muscular, ALS-like conditions
- Cualquiera que use AAC y quiera una voz personalizada

### Usuario cuaternario: Desarrolladores
- Quieren integrar voz clonada en su app
- Buscan API local simple, privacidad, open source

### Usuario quinario: Creadores de contenido
- Generación de audio con su voz sin subir datos a la nube
- Automatización, podcast, stories personalizados

---

## Diferenciador vs Plataformas de Pago

| Aspecto | ElevenLabs | Google Cloud TTS | VoiceClone |
|---------|------------|------------------|------------|
| Privacidad | ❌ Cloud | ❌ Cloud | ✅ 100% Local |
| Facilidad | ✅ Web | ✅ Web | ✅ Un comando |
| Costo | ❌ €5-330/mes | ❌ Pay-per-use | ✅ Gratis (MIT) |
| Accesibilidad AAC | ❌ No | ❌ No | ✅ Integrado |
| Eye tracking | ❌ No | ❌ No | ✅ Tobii + WCAG |
| Personalidad IA | ⚠️ Limited | ❌ No | ✅ OpenClaw-style |
| Open Source | ❌ No | ❌ No | ✅ Sí (MIT) |
| Sin GPU | ✅ Cloud | ✅ Cloud | ✅ CPU optimizado |
| Para ELA | ❌ No | ❌ No | ✅ Diseñado para |

---

## Scope Inicial (MVP — Fase 3-4)

### Capa 1 — Motor de Clonación (Prioridad ALTA)
- ✅ Script de instalación automática (macOS primero, Linux, Windows)
- ✅ Grabación guiada de voz (CLI interactivo + Web app)
- ✅ Clonación de voz con Chatterbox TTS (SOTA open source)
- ✅ Fallback XTTS v2 (CPU)
- ✅ Generación TTS con la voz clonada (CLI + API)
- ✅ API local HTTP (FastAPI) para integración
- ✅ Engine Adapter pattern (intercambiar modelos)

### Capa 2 — Web App (Prioridad ALTA)
- ✅ Landing emotivo para ELA ("Preserva tu voz")
- ✅ Grabación guiada de voz (UI accesible, WCAG AA)
- ✅ Descarga automática e instalación del motor (sin terminal)
- ✅ Integración Tobii SDK (eye tracking básico)
- ✅ Integración AAC — registrar como "voz del sistema"
- ✅ 6 pantallas: Landing, Descarga, Clonación, Personalidad, Integración, Dashboard
- ✅ Switch access para usuarios con discapacidad motriz

### Capa 3 — Personalidad IA (Prioridad MEDIA — MVP básico)
- ✅ Captura de perfil de personalidad (cuestionario simple)
- ✅ Integración LLM básica (Claude API o local)
- ⚠️ No en MVP: fine-tuning avanzado, digital twins completos

### No incluido en MVP:
- GUI editor avanzada (solo web app básica)
- Multi-idioma automático
- Streaming en tiempo real
- Marketplace de voces
- Plugins para OBS/Discord

---

## Scope Futuro (post-MVP — Fases posteriores)

- **Multi-idioma** — clonar una voz en español y usarla en inglés
- **Real-time** — síntesis en tiempo real (streaming)
- **Plugins** — integración con OBS, Discord, Zoom
- **App móvil** — grabación desde iOS/Android
- **Modelos custom** — entrenar modelos pequeños para edge devices
- **Digital twins avanzados** — personalidad + contexto profundo

---

## Criterios de Éxito del MVP

### Técnicos
1. **Tiempo de instalación:** < 5 minutos (incluyendo descarga de modelo)
2. **Tiempo de clonación:** < 10 minutos (grabación + procesamiento)
3. **Calidad de voz:** MOS > 3.5 (comparable a servicios cloud mid-tier)
4. **Hardware mínimo:** MacBook Air M1 8GB / PC con 8GB RAM (sin GPU dedicada)
5. **Plataformas:** macOS (ARM + Intel), Linux (x86_64), Windows
6. **Dependencias visibles para el usuario:** CERO (todo se instala automáticamente)

### De Accesibilidad
7. **WCAG AA compliance** — contrastes, tamaños, navegación teclado ✅
8. **Eye tracking funcional** — Tobii integration 80%+ accuracy
9. **AAC integration** — registro en Grid 3, Proloquo2Go ✅
10. **Switch access** — navegación con 1-2 botones ✅

### De Impacto Social
11. **Para personas con ELA** — testeado con usuarios reales (accesibilidad + emocional)
12. **Privacidad garantizada** — cero datos en cloud, cero telemetría
13. **Gratis y open source** — MIT License, no paywalls futuros

---

## Stack Tecnológico (Decidido tras investigación)

### Backend — Motor de Clonación (Python)
- **Lenguaje:** Python 3.10+ (ecosistema ML robusto)
- **Modelo principal:** Chatterbox Turbo (MIT, 23 idiomas, SOTA, CPU-friendly)
- **Fallback:** XTTS v2 (fallback si Chatterbox no funciona)
- **Engine Adapter:** Patrón para intercambiar modelos
- **Audio:** sounddevice + librosa para grabación + procesamiento
- **API local:** FastAPI (rápida, moderna, perfecta para local)
- **Puerto por defecto:** 8765

### Frontend — Web App (Next.js)
- **Framework:** Next.js 14+ (Vercel, cuenta openparty2026)
- **Accesibilidad:** WCAG AA, Radix UI components
- **Eye tracking:** Tobii SDK integration (JS client)
- **Package:** standalone web installer (descarga + instala motor automáticamente)
- **Hospedaje:** Vercel (free tier para MVP)

### Instalación + Packaging
- **macOS:** .pkg installer (native)
- **Linux:** .deb package (Debian-based)
- **Windows:** .exe installer (NSIS)
- **Alternativa universal:** pip + script bash (curl | bash)
- **Tool:** PyInstaller para binarios standalone

### Integración Sistema
- **macOS:** NSSSpeechSynthesizer wrapper, `say` command replacement
- **AAC:** Grid 3 SDK, Proloquo2Go API (si disponibles)
- **Eye tracking:** Tobii Core SDK
- **Switch access:** WCAG compliant keyboard navigation

### DevOps + Distribución
- **Repo:** GitHub (angellocafm-arch/voiceclone — MIT License)
- **CI/CD:** GitHub Actions (build + test en macOS, Linux, Windows)
- **Releases:** GitHub Releases con instaladores pre-built
- **Web app:** Vercel deployment (CI/CD automático)

---

## Licencia

**MIT License** — completamente libre para uso personal y comercial. Nada de paywalls futuros.

```
Copyright 2026 Vertex Developer

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software to use, modify, and distribute freely.
```

---

## Visión Final — En Una Frase

> **Que cualquier persona, incluyendo quien está perdiendo la voz, pueda preservar y usar su voz en su ordenador. Sin pagar. Sin la nube. Sin tecnicismos. Con su personalidad intacta.**

### Propósito Social

En 2026, **más de 160,000 personas en el mundo tienen ELA activa**. Cada año, miles pierden la capacidad de hablar. VoiceClone es un regalo para ellos y sus familias: la oportunidad de que su voz nunca se pierda.

Es también un gesto: **que la tecnología IA no solo optimice, sino humanice**. Que preserve lo más valioso: la voz que identifica a una persona.

---

*Proyecto Vertex Developer — 2026*  
*"Tu voz. Para siempre."*
