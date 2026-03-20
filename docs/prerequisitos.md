# Prerequisitos — VoiceClone v2

**Fecha verificación:** 2026-03-20 22:17 CET

## Resultados

| Prerequisito | Estado | Detalle |
|---|---|---|
| GitHub auth | ✅ OK | Cuenta `angellocafm-arch`, token con scopes: admin:org, repo, workflow, write:packages |
| Proyecto base | ✅ OK | `~/clawd/projects/voiceclone/` existe con estructura completa: src/, docs/, equipo/, reuniones/, mockups/, tests/, vision/ |
| Ollama | ✅ Instalado | v0.18.2 via Homebrew (`/opt/homebrew/bin/ollama`). Necesita `brew services start ollama` para servir modelos. |
| Python | ✅ OK | Python 3.14.3 |

## Código existente detectado

```
src/
├── __init__.py
├── cli.py
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   └── server.py
├── personality/
│   ├── __init__.py
│   ├── engine.py
│   ├── llm.py
│   ├── profile.py
│   └── questionnaire.py
└── voice_engine/
    ├── __init__.py
    ├── audio_utils.py
    ├── base.py
    ├── chatterbox_engine.py
    ├── manager.py
    ├── recorder.py
    └── xtts_engine.py
```

## Acciones tomadas

- GitHub: autenticado con `gh auth login --with-token`
- Ollama: instalado con `brew install ollama` (incluye dependencias mlx, sqlite, mlx-c)
- Para arrancar Ollama: `brew services start ollama` o `OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve`

## Notas

- macOS Apple Silicon (arm64) — target principal
- Python 3.14.3 es versión muy reciente; verificar compatibilidad con torch/torchaudio si se necesitan
- Ollama aún no tiene modelos descargados — se hará en fase de desarrollo
