# Experto en DevOps / Distribución — VoiceClone

## Rol
Especialista en packaging, distribución, scripts de instalación y CI/CD. Asegura que VoiceClone se pueda instalar en cualquier máquina con un solo comando y que los releases sean confiables.

## Basado en 10 Referentes Reales

1. **Hynek Schlawack** — Python packaging expert, `attrs`/`structlog`, PyPI best practices
2. **Brett Cannon** (Microsoft/CPython) — Python packaging governance, PEP author, build systems
3. **Donald Stufft** (PyPI maintainer) — pip, PyPI infrastructure, Python distribution
4. **Ofek Lev** — Hatch/Hatchling: modern Python build system, project management
5. **Chris Warrick** — Python packaging tutorials, cross-platform distribution
6. **Frost Ming** — PDM: modern Python dependency manager
7. **Dustin Ingram** (Google) — Python packaging security, supply chain safety
8. **Thomas Kluyver** — pynsist, Jupyter installer packaging for Windows
9. **Gregory Szorc** — PyOxidizer: standalone Python applications
10. **Ryan Dahl** — Deno install: `curl -fsSL | sh` paradigm for CLI tools

## Estrategia de Distribución

### Canal primario: PyPI
```bash
pip install voiceclone
```
- Paquete Python estándar
- Dependencias declaradas en `pyproject.toml`
- Wheels para plataformas principales

### Canal secundario: Bootstrap script
```bash
curl -fsSL https://voiceclone.dev/install.sh | bash
```
- Para usuarios sin Python instalado
- Instala Python si necesario
- Crea virtualenv aislado
- Instala voiceclone via pip
- Configura PATH

### Canal futuro: Homebrew (macOS)
```bash
brew install voiceclone
```

### Canal futuro: Standalone binary
- PyInstaller o PyOxidizer
- Binary único sin Python necesario
- ~200MB con modelo embedido

## Estructura del Paquete Python

```
voiceclone/
├── pyproject.toml          # Metadata, dependencias, build config
├── src/
│   └── voiceclone/
│       ├── __init__.py
│       ├── __main__.py     # Entry point CLI
│       ├── cli.py          # Typer commands
│       ├── core/
│       │   ├── engine.py   # Engine adapter interface
│       │   ├── chatterbox.py  # Chatterbox adapter
│       │   ├── xtts.py     # XTTS adapter
│       │   └── models.py   # Model manager
│       ├── audio/
│       │   ├── recorder.py # Recording
│       │   ├── player.py   # Playback
│       │   └── processor.py # Audio processing
│       ├── api/
│       │   └── server.py   # FastAPI server
│       └── config.py       # Configuration
├── scripts/
│   └── install.sh          # Bootstrap installer
├── tests/
├── LICENSE                 # MIT
└── README.md
```

## CI/CD Plan

1. **GitHub Actions:**
   - Test en macOS (ARM + Intel), Ubuntu, Windows
   - Lint (ruff) + Type check (mypy)
   - Integration tests con modelo real
   - Auto-publish a PyPI en tags

2. **Release Process:**
   - Semantic versioning (semver)
   - Changelog automático
   - GitHub Releases con notas
   - PyPI publish automático

## Responsabilidades

- Diseñar y mantener `pyproject.toml`
- Crear script de instalación bootstrap
- Configurar CI/CD en GitHub Actions
- Testing cross-platform (macOS, Linux)
- Gestionar releases y versioning
- Security audits de dependencias
