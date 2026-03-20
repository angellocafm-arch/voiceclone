# VoiceClone — Preserva tu voz. Para siempre.

> Open source voice cloning + personality AI for people with ALS and speech disabilities

---

## 🎯 What is VoiceClone?

VoiceClone is a **three-layer open source platform** that lets anyone preserve and use their voice, with a special focus on people with **ALS, ELA, and similar conditions that take away your voice**.

### The Problem
- **ElevenLabs costs €330/month** — out of reach for most patients
- **There's no tool designed for people losing their voice** — no accessibility, no AAC integration
- **Your voice data shouldn't go to cloud servers** — privacy is critical
- **Existing AAC software uses robotic voices** — not YOUR voice

### The Solution
**3 Integrated Layers:**

| Layer | What it does | Status |
|-------|-------------|--------|
| 🎤 **Voice Cloning Engine** | Clone your voice locally in 2-3 minutes | ✅ MVP Ready |
| 🌐 **Accessible Web App** | Eye tracking + AAC integration (WCAG AA) | ✅ MVP Ready |
| 🧠 **Personality AI** | Your voice speaks like YOU, not a robot | ✅ MVP Ready |

---

## ✨ Key Features

- ✅ **One command install** — Download, install, done (no terminal needed)
- ✅ **Zero-shot voice cloning** — A few minutes of audio = your voice forever
- ✅ **100% local processing** — Nothing leaves your computer. Ever.
- ✅ **Accessible by design** — Eye tracking (Tobii), switch control, keyboard navigation
- ✅ **Personality preservation** — Your voice + your way of speaking + your expressions
- ✅ **AAC integration** — Use with Grid 3, Proloquo2Go, Snap Core First
- ✅ **Multi-engine** — Chatterbox TTS (primary) + XTTS v2 (fallback)
- ✅ **Open source MIT** — Forever free, no paywalls, no subscriptions

---

## 🚀 Quick Start

### Install (macOS)
```bash
curl -fsSL https://voiceclone.dev/install | bash
```

### Install (Windows / Linux)
```bash
# Coming soon — installer builds in progress
```

### After Installation
1. Open VoiceClone (the web app opens automatically)
2. Click **"Clone My Voice"**
3. Record 2-3 minutes reading the guided texts
4. *(Optional)* Answer personality questions — so your voice speaks like YOU
5. Done! Test your cloned voice from the dashboard

### For Developers
```bash
# Clone the repo
git clone https://github.com/angellocafm-arch/voiceclone.git
cd voiceclone

# Install Python dependencies
pip install -e .

# Start the API server
voiceclone server

# Start the web app (separate terminal)
cd src/web && npm install && npm run dev
```

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────┐
│                    WEB APP (Next.js)                 │
│  Landing → Install → Clone → Personality → Dashboard │
│  WCAG AA · Eye tracking · 64px targets              │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP (localhost:8765)
┌───────────────────────┴─────────────────────────────┐
│                  API SERVER (FastAPI)                 │
│  POST /clone · POST /speak · GET /voices · GET /health│
│  POST /personality/setup · POST /personality/speak    │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────┐
│              VOICE ENGINE (Python)                    │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Chatterbox   │→ │ XTTS v2   │  │ Personality  │  │
│  │ TTS (primary)│  │ (fallback) │  │ AI (LLM)    │  │
│  └──────────────┘  └───────────┘  └──────────────┘  │
│  Engine Adapter Pattern — hot-swappable models       │
└──────────────────────────────────────────────────────┘
```

---

## 📋 Stack

| Component | Technology | License | Lines |
|-----------|------------|---------|-------|
| **Voice Engine** | Chatterbox TTS + XTTS v2 | MIT / MPL 2.0 | 2,800+ |
| **API Server** | FastAPI (Python) | MIT | 500+ |
| **Personality AI** | Claude API / Ollama / Identity LLM | MIT | 1,200+ |
| **Web App** | Next.js 16 + Tailwind | MIT | 2,100+ |
| **CLI** | Click + Rich (Python) | MIT | 400+ |
| **Tests** | pytest | MIT | 1,500+ |

**Total: 11,000+ lines of code · 118 tests · 26 documents**

---

## 🎯 For People with ELA/ALS

If you or someone you love is facing voice loss:

1. **Clone your voice BEFORE you lose it** — preservation is time-sensitive
2. **Use with your AAC software** — Grid 3, Proloquo2Go, Snap Core First
3. **Capture your personality too** — not just how you sound, but how you SPEAK
4. **Complete privacy** — your voice data never leaves your computer
5. **Zero cost** — open source, MIT license, forever free

### Accessibility Features
- 🖱️ **Keyboard:** Full navigation with Tab, Enter, Escape
- 👁️ **Eye tracking:** All buttons ≥64px, dwell-click compatible (Tobii)
- 🔘 **Switch access:** 1-2 button navigation for the entire app
- 🔊 **Screen reader:** Full ARIA labels, live regions, progress announcements
- 🌗 **High contrast:** Dark theme optimized for reduced eye strain
- ⚡ **Reduced motion:** Respects `prefers-reduced-motion`

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Vision](vision/vision.md) | Complete product vision — 3 layers, 4 user profiles |
| [Architecture](docs/arquitectura-completa.md) | System design, API contracts, data flows |
| [Accessibility](docs/diseno-accesibilidad.md) | WCAG AA, eye tracking, switch access spec |
| [Installation Flow](docs/flujo-instalacion.md) | How to install without using terminal |
| [Personality AI](docs/capa3-personalidad-ia.md) | How the personality system works |
| [Web App Mockups](mockups/web-app-mockups.md) | All 6 screens with ASCII wireframes |
| [Brief](brief.md) | Complete product brief v2.0 |
| [QA Report](qa-screenshots/QA-REPORT.md) | Full browser testing results |

---

## 🏗️ Project Structure

```
voiceclone/
├── src/
│   ├── voice_engine/        # Capa 1: Voice cloning engine
│   │   ├── base.py          # Abstract base class (VoiceEngine)
│   │   ├── chatterbox_engine.py  # Chatterbox TTS implementation
│   │   ├── xtts_engine.py   # XTTS v2 fallback
│   │   ├── manager.py       # Engine adapter + auto-fallback
│   │   └── audio_utils.py   # Audio validation, conversion, quality
│   ├── personality/          # Capa 3: Personality AI
│   │   ├── profile.py       # PersonalityProfile (17 fields)
│   │   ├── questionnaire.py # 12 guided questions + text analysis
│   │   ├── llm.py           # Claude / Ollama / Identity backends
│   │   └── engine.py        # Orchestrator (text → LLM → styled text → TTS)
│   ├── api/                  # FastAPI server (port 8765)
│   │   └── server.py        # All endpoints + lifespan + CORS
│   ├── web/                  # Next.js 16 web app (Capa 2)
│   │   └── src/
│   │       ├── app/          # App router (page.tsx, layout.tsx)
│   │       ├── components/   # 6 screen components
│   │       └── lib/          # API client, utilities
│   └── cli.py               # Click CLI (clone, speak, voices, server)
├── tests/                    # 118 tests
├── docs/                     # Technical documentation
├── mockups/                  # UI wireframes and specs
├── vision/                   # Product vision docs
├── qa-screenshots/           # Browser testing evidence
└── brief.md                  # Product brief v2.0
```

---

## 🔮 Roadmap

- [x] Phase 1: Genesis + Product Vision
- [x] Phase 2: Team + Design Review + Mockups
- [x] Phase 3: MVP Development (11,000+ lines)
- [ ] Phase 4: GitHub + Releases ← **Current**
- [ ] Phase 5: Community + Contributions
- [ ] Phase 6: AAC Integrations (Grid 3, Tobii SDK)
- [ ] Phase 7: Multi-language support

---

## 📜 License

**MIT License** — Completely open, forever free.

```
Copyright 2026 Vertex Developer (Ángel Fernández)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
```

---

## 💚 Purpose

**160,000+ people worldwide have ALS right now.** Thousands lose their voice every year.

VoiceClone exists because your voice is part of who you are. It's how your children recognize you. It's how you laugh, whisper, and say "I love you."

This tool is free because no one should have to pay €330/month to keep their own voice.

*Tu voz. Para siempre.*

---

**By [Vertex Developer](https://github.com/angellocafm-arch)** · Made with ❤️ for the ALS community
