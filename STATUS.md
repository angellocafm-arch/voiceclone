# VoiceClone — Estado del Proyecto
## Última actualización: 2026-03-21 00:50
## Sesión autónoma: Tanke (cierre MVP v0.3.0)

---

## ¿Qué es el proyecto?

**Asistente de vida completo para personas con ELA y dificultades motoras.**

- Habla con la voz clonada de la persona (100% local)
- Controla todo el ordenador por la vista (eye tracking)
- Se comunica por Telegram/WhatsApp desde el móvil
- LLM adaptativo según hardware del usuario (3B → 70B)
- Sin nube, sin base de datos, sin suscripción, sin internet después de instalar
- Open source MIT en GitHub

---

## 🎉 MVP v0.3.0 — COMPLETADO

### Lo que se hizo en esta sesión (2026-03-21):

1. ✅ **Chatterbox TTS integrado en el installer** — detección GPU/MPS/CPU, verificación post-install
2. ✅ **Installer Windows creado** — `install_windows.ps1` completo con winget, Ollama, Chatterbox
3. ✅ **GitHub Release v0.3.0** — https://github.com/angellocafm-arch/voiceclone/releases/tag/v0.3.0
   - 3 installers descargables: `install.sh`, `install-macos.sh`, `install_windows.ps1`
4. ✅ **Landing page live** — https://angellocafm-arch.github.io/voiceclone/
   - Detección automática de hardware (RAM, CPU, GPU, OS)
   - Recomendación de modelo según hardware
   - Botón de descarga funcional que apunta al release
5. ✅ **Test end-to-end** — Landing funcional, botón OK, syntax verificado, URLs descargables

---

## URLs

| Recurso | URL |
|---------|-----|
| **Landing page** | https://angellocafm-arch.github.io/voiceclone/ |
| **GitHub repo** | https://github.com/angellocafm-arch/voiceclone |
| **Release v0.3.0** | https://github.com/angellocafm-arch/voiceclone/releases/tag/v0.3.0 |
| **Instalar (macOS/Linux)** | `curl -fsSL https://github.com/angellocafm-arch/voiceclone/releases/latest/download/install.sh \| bash` |

---

## Estado del código (v0.3.0)

### ✅ COMPLETADO
- `src/voice_engine/` — Chatterbox + XTTS v2 wrapper
- `src/llm/` — Ollama client, onboarding agent, phrase predictor
- `src/system/` — Control del SO con 4 niveles de seguridad
- `src/channels/` — Telegram + WhatsApp
- `src/rag/` — RAG local con FAISS
- `src/api/main.py` — FastAPI 20+ endpoints + WebSocket eye tracking
- `src/web/` — Next.js 4 módulos con eye tracking
- `src/landing/` — Landing con detección de hardware
- `scripts/install.sh` — Installer universal macOS + Linux
- `scripts/install-macos.sh` — Installer macOS optimizado
- `scripts/install_windows.ps1` — Installer Windows
- `docs/` — Documentación de QA, arquitectura, Chatterbox
- GitHub Release v0.3.0 con 3 installers
- GitHub Pages landing funcional

### ⚠️ PENDIENTE
1. **Test en máquina limpia** — instalar desde cero en un Mac/Linux/Windows sin dependencias
2. **Vercel deploy** — cuando Ángel configure token (ahora en GitHub Pages)
3. **Frontend web completo** — interfaz Next.js funcional end-to-end
4. **Integración AAC real** — Grid 3, Proloquo2Go

### 📋 FASE 2 (futura)
- Integración directa con Grid 3 (contactar Smartbox para API)
- Integración con Proloquo2Go (AssistiveWare)
- GUI de escritorio (Electron)
- Comunidad open-source

---

## Repositorio GitHub

- **URL:** https://github.com/angellocafm-arch/voiceclone
- **Cuenta:** angellocafm-arch
- **Licencia:** MIT
- **Versión:** v0.3.0 (tag: v0.3.0-mvp)

---
*Documentado por Tanke — Vertex Developer*
