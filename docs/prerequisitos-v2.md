# Prerequisitos VoiceClone v4 — Verificación 2026-03-20 22:47

## Estado de Herramientas

| Herramienta | Estado | Versión | Notas |
|-------------|--------|---------|-------|
| GitHub CLI | ✅ OK | gh (logged in) | Cuenta: angellocafm-arch, token con scopes: admin:org, repo, workflow |
| Python | ✅ OK | 3.14.3 | Suficiente para FastAPI, torch, etc. |
| Ollama | ⚠️ Instalado, no corriendo | 0.18.2 | `ollama serve` necesario antes de usar |
| Node.js | ✅ OK | v24.13.0 | Para Next.js / frontend |
| ffmpeg | ✅ OK | (disponible) | Para conversión de audio |

## Estructura del Proyecto

```
~/clawd/projects/voiceclone/src/
├── __init__.py
├── api/              # FastAPI endpoints
├── cli.py            # CLI principal
├── personality/      # Personalidad del asistente
├── voice_engine/     # Motor de voz (Chatterbox/XTTS)
└── web/              # Frontend web
```

## Directorios Adicionales Existentes

- `docs/` — Documentación
- `equipo/` — Expertos virtuales
- `mockups/` — Diseños previos
- `reuniones/` — Actas de reuniones
- `scripts/` — Scripts de instalación
- `tests/` — Tests
- `vision/` — Documentos de visión
- `qa-screenshots/` — Capturas de QA

## Pendientes para Fase 0

- [x] Arrancar Ollama antes de tests con LLM: `ollama serve`
- [ ] Verificar que Chatterbox/XTTS están instalados en el venv

## Plataforma Objetivo

- **Principal:** macOS Apple Silicon (M1/M2/M3/M4)
- **Secundaria:** Linux x86_64
- **Futura:** Windows (post-MVP)
