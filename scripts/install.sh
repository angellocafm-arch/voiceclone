#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# VoiceClone v4 — Universal Installer (macOS + Linux)
#
# Usage:
#   ./install.sh                          # Auto-detect model
#   ./install.sh --model mistral:7b       # Specify Ollama model
#   ./install.sh --skip-ollama            # Skip Ollama setup
#   ./install.sh --skip-voice             # Skip voice engine
#   ./install.sh --uninstall              # Remove VoiceClone
#
# What it does:
#   1. Detects OS and architecture
#   2. Installs Python 3.10+ if needed (via pyenv or brew)
#   3. Installs Ollama if needed
#   4. Downloads LLM model (user-selected or auto)
#   5. Downloads voice engine (Chatterbox TTS)
#   6. Sets up Python venv with all dependencies
#   7. Starts FastAPI server on port 8765
#   8. Opens Chrome at http://localhost:8765
#
# MIT License — Vertex Developer / VoiceClone 2026
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ─── Colors ───────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Config ───────────────────────────────────────────────
INSTALL_DIR="${VOICECLONE_DIR:-$HOME/.voiceclone}"
VENV_DIR="$INSTALL_DIR/venv"
DATA_DIR="$INSTALL_DIR/data"
VOICES_DIR="$INSTALL_DIR/voices"
LOG_FILE="$INSTALL_DIR/install.log"
SERVER_PORT=8765
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

# ─── Defaults ─────────────────────────────────────────────
OLLAMA_MODEL=""
SKIP_OLLAMA=false
SKIP_VOICE=false
UNINSTALL=false
AUTO_OPEN=true

# ─── Parse Arguments ─────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)
            OLLAMA_MODEL="$2"
            shift 2
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            shift
            ;;
        --skip-voice)
            SKIP_VOICE=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --no-open)
            AUTO_OPEN=false
            shift
            ;;
        --help|-h)
            echo "VoiceClone v4 Installer"
            echo ""
            echo "Usage: ./install.sh [options]"
            echo ""
            echo "Options:"
            echo "  --model MODEL    Specify Ollama model (e.g., mistral:7b)"
            echo "  --skip-ollama    Skip Ollama installation"
            echo "  --skip-voice     Skip voice engine setup"
            echo "  --uninstall      Remove VoiceClone"
            echo "  --no-open        Don't open browser after install"
            echo "  -h, --help       Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ─── Helpers ──────────────────────────────────────────────

log() {
    echo -e "${GREEN}[VoiceClone]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[VoiceClone]${NC} $*"
}

error() {
    echo -e "${RED}[VoiceClone ERROR]${NC} $*" >&2
}

fatal() {
    error "$@"
    exit 1
}

progress() {
    echo -e "${CYAN}[${1}/${2}]${NC} ${BOLD}$3${NC}"
}

command_exists() {
    command -v "$1" &>/dev/null
}

# ─── Uninstall ────────────────────────────────────────────
if $UNINSTALL; then
    log "Removing VoiceClone from $INSTALL_DIR..."
    if [[ -d "$INSTALL_DIR" ]]; then
        # Stop server if running
        pkill -f "uvicorn.*voiceclone" 2>/dev/null || true
        rm -rf "$INSTALL_DIR"
        log "VoiceClone removed."
    else
        warn "VoiceClone not found at $INSTALL_DIR"
    fi
    # Remove LaunchAgent on macOS
    if [[ "$(uname)" == "Darwin" ]]; then
        PLIST="$HOME/Library/LaunchAgents/dev.voiceclone.server.plist"
        if [[ -f "$PLIST" ]]; then
            launchctl unload "$PLIST" 2>/dev/null || true
            rm -f "$PLIST"
            log "LaunchAgent removed."
        fi
    fi
    exit 0
fi

# ═══════════════════════════════════════════════════════════
# MAIN INSTALL
# ═══════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     🎤 VoiceClone v4 — Installer         ║${NC}"
echo -e "${BOLD}${CYAN}║     Asistente de vida completo para ELA   ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════╝${NC}"
echo ""

TOTAL_STEPS=7
CURRENT_STEP=0

# ─── Step 1: Detect OS ───────────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Detectando sistema operativo..."

OS="$(uname)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin)
        OS_NAME="macOS"
        PKG_MANAGER="brew"
        ;;
    Linux)
        OS_NAME="Linux"
        if command_exists apt-get; then
            PKG_MANAGER="apt"
        elif command_exists dnf; then
            PKG_MANAGER="dnf"
        elif command_exists pacman; then
            PKG_MANAGER="pacman"
        else
            PKG_MANAGER="unknown"
        fi
        ;;
    *)
        fatal "Sistema operativo no soportado: $OS. VoiceClone funciona en macOS y Linux."
        ;;
esac

log "Sistema: ${BOLD}$OS_NAME $ARCH${NC}"

# ─── Step 2: Check/Install Python ────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Verificando Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command_exists "$cmd"; then
        PY_VERSION=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
        if [[ "$PY_MAJOR" -ge "$MIN_PYTHON_MAJOR" ]] && [[ "$PY_MINOR" -ge "$MIN_PYTHON_MINOR" ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    warn "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ no encontrado. Instalando..."
    if [[ "$OS" == "Darwin" ]]; then
        if command_exists brew; then
            brew install python@3.12
            PYTHON_CMD="python3"
        else
            fatal "Homebrew no encontrado. Instálalo primero: https://brew.sh"
        fi
    else
        case "$PKG_MANAGER" in
            apt)
                sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3-pip
                PYTHON_CMD="python3.12"
                ;;
            dnf)
                sudo dnf install -y python3.12
                PYTHON_CMD="python3.12"
                ;;
            pacman)
                sudo pacman -S --noconfirm python
                PYTHON_CMD="python3"
                ;;
            *)
                fatal "No se pudo instalar Python automáticamente. Instala Python 3.10+ manualmente."
                ;;
        esac
    fi
fi

log "Python: ${BOLD}$($PYTHON_CMD --version)${NC}"

# ─── Step 3: Install Ollama ──────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Configurando Ollama (LLM local)..."

if $SKIP_OLLAMA; then
    warn "Ollama saltado (--skip-ollama)"
else
    if ! command_exists ollama; then
        log "Instalando Ollama..."
        if [[ "$OS" == "Darwin" ]]; then
            if command_exists brew; then
                brew install ollama
            else
                curl -fsSL https://ollama.ai/install.sh | sh
            fi
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    fi

    # Start Ollama if not running
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        log "Arrancando Ollama..."
        ollama serve &>/dev/null &
        sleep 3
    fi

    OLLAMA_VER=$(ollama --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    log "Ollama: ${BOLD}v${OLLAMA_VER}${NC}"

    # Auto-select model if not specified
    if [[ -z "$OLLAMA_MODEL" ]]; then
        RAM_KB=$(sysctl -n hw.memsize 2>/dev/null || grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
        if [[ "$OS" == "Darwin" ]]; then
            RAM_GB=$((RAM_KB / 1073741824))
        else
            RAM_GB=$((RAM_KB / 1048576))
        fi

        if [[ "$RAM_GB" -ge 64 ]]; then
            OLLAMA_MODEL="llama3.1:70b-instruct-q4_K_M"
        elif [[ "$RAM_GB" -ge 32 ]]; then
            OLLAMA_MODEL="llama3.3:13b-instruct-q5_K_M"
        elif [[ "$RAM_GB" -ge 16 ]]; then
            OLLAMA_MODEL="llama3.1:8b-instruct-q5_K_M"
        elif [[ "$RAM_GB" -ge 8 ]]; then
            OLLAMA_MODEL="mistral:7b-instruct-q4_K_M"
        else
            OLLAMA_MODEL="llama3.2:3b-instruct-q4_K_M"
        fi
        log "RAM detectada: ${BOLD}${RAM_GB}GB${NC} → Modelo: ${BOLD}${OLLAMA_MODEL}${NC}"
    fi

    # Download model
    log "Descargando modelo ${BOLD}${OLLAMA_MODEL}${NC}... (esto puede tardar varios minutos)"
    ollama pull "$OLLAMA_MODEL" 2>&1 | tee -a "$LOG_FILE" || warn "Error descargando modelo. Puedes descargarlo después con: ollama pull $OLLAMA_MODEL"
fi

# ─── Step 4: Create directories ─────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Creando estructura de directorios..."

mkdir -p "$INSTALL_DIR" "$DATA_DIR" "$VOICES_DIR" "$INSTALL_DIR/logs"

# ─── Step 5: Python venv + dependencies ──────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Instalando dependencias Python..."

if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Core dependencies
pip install --upgrade pip setuptools wheel 2>&1 | tail -1

pip install \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    websockets==14.* \
    httpx==0.28.* \
    pydantic==2.* \
    python-multipart==0.0.* \
    aiofiles==24.* \
    2>&1 | tail -5

# Voice engine
if ! $SKIP_VOICE; then
    log "Instalando motor de voz (Chatterbox TTS)..."
    warn "⚠️  Esto puede tardar varios minutos. Chatterbox incluye PyTorch (~2GB)."
    warn "    Los modelos de voz (~2GB) se descargarán la primera vez que se use."
    
    # Detect GPU/MPS for optimal PyTorch
    VOICE_DEVICE="cpu"
    if [[ "$OS" == "Darwin" ]] && [[ "$ARCH" == "arm64" ]]; then
        VOICE_DEVICE="mps"
        log "Apple Silicon detectado → motor de voz usará ${BOLD}MPS (GPU)${NC}"
    elif command_exists nvidia-smi; then
        VOICE_DEVICE="cuda"
        log "GPU NVIDIA detectada → motor de voz usará ${BOLD}CUDA${NC}"
    else
        log "Sin GPU dedicada → motor de voz usará ${BOLD}CPU${NC} (más lento pero funcional)"
    fi
    
    pip install \
        chatterbox-tts 2>&1 | tail -5 || {
        warn "Chatterbox no disponible. Instalando TTS alternativo (Coqui/XTTS)..."
        pip install TTS 2>&1 | tail -3 || warn "Motor de voz no instalado. Puedes instalarlo después."
    }
    
    # Verify Chatterbox installation
    if "$PYTHON_CMD" -c "from chatterbox.tts import ChatterboxTTS; print('OK')" 2>/dev/null; then
        log "✅ Chatterbox TTS instalado correctamente"
    else
        warn "⚠️  Chatterbox importa con errores. El motor puede necesitar ajustes."
    fi
fi

# Ollama Python client
pip install ollama==0.4.* 2>&1 | tail -1

deactivate

log "Dependencias instaladas en ${BOLD}$VENV_DIR${NC}"

# ─── Step 6: Copy application files ─────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Configurando aplicación..."

# Find source directory (relative to this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")/src"

if [[ -d "$SRC_DIR" ]]; then
    cp -r "$SRC_DIR" "$INSTALL_DIR/src"
    log "Código fuente copiado."
else
    warn "Directorio src/ no encontrado. La aplicación se configurará en el primer arranque."
fi

# Write config
cat > "$INSTALL_DIR/config.json" <<EOF
{
    "version": "4.0.0",
    "server": {
        "host": "127.0.0.1",
        "port": $SERVER_PORT
    },
    "ollama": {
        "model": "${OLLAMA_MODEL:-auto}",
        "host": "http://localhost:11434"
    },
    "voice": {
        "engine": "chatterbox",
        "device": "${VOICE_DEVICE:-cpu}",
        "fallback": "xtts"
    },
    "channels": {},
    "security": {
        "confirmation_levels": {
            "read": "none",
            "create": "none",
            "move": "single",
            "delete": "double",
            "send_email": "double",
            "system": "blocked"
        }
    },
    "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "os": "$OS_NAME",
    "arch": "$ARCH"
}
EOF

log "Configuración guardada."

# ─── Step 7: Start server ───────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
progress $CURRENT_STEP $TOTAL_STEPS "Arrancando servidor..."

# Create startup script
cat > "$INSTALL_DIR/start.sh" <<'STARTUP'
#!/usr/bin/env bash
INSTALL_DIR="${VOICECLONE_DIR:-$HOME/.voiceclone}"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
exec uvicorn src.api.main:app --host 127.0.0.1 --port 8765 --log-level info
STARTUP
chmod +x "$INSTALL_DIR/start.sh"

# macOS: Create LaunchAgent for auto-start
if [[ "$OS" == "Darwin" ]]; then
    PLIST="$HOME/Library/LaunchAgents/dev.voiceclone.server.plist"
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.voiceclone.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${INSTALL_DIR}/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>${INSTALL_DIR}/logs/server-error.log</string>
</dict>
</plist>
EOF
    launchctl load "$PLIST" 2>/dev/null || true
    log "LaunchAgent creado (auto-arranque al iniciar sesión)"
fi

# Linux: Create systemd service
if [[ "$OS" == "Linux" ]] && command_exists systemctl; then
    SERVICE_FILE="$HOME/.config/systemd/user/voiceclone.service"
    mkdir -p "$(dirname "$SERVICE_FILE")"
    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=VoiceClone - Asistente de vida para ELA
After=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable voiceclone
    systemctl --user start voiceclone
    log "Servicio systemd creado y arrancado"
fi

# Wait for server to be ready
log "Esperando a que el servidor arranque..."
for i in {1..15}; do
    if curl -s "http://localhost:$SERVER_PORT/api/health" &>/dev/null; then
        break
    fi
    sleep 1
done

# ─── Open browser ────────────────────────────────────────
if $AUTO_OPEN; then
    if [[ "$OS" == "Darwin" ]]; then
        open "http://localhost:$SERVER_PORT"
    elif command_exists xdg-open; then
        xdg-open "http://localhost:$SERVER_PORT"
    fi
fi

# ─── Done! ───────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║     🎤 VoiceClone instalado correctamente!           ║${NC}"
echo -e "${BOLD}${GREEN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}${GREEN}║                                                       ║${NC}"
echo -e "${BOLD}${GREEN}║  🌐 Abre: http://localhost:${SERVER_PORT}                   ║${NC}"
echo -e "${BOLD}${GREEN}║  📁 Instalado en: ${INSTALL_DIR}              ║${NC}"
echo -e "${BOLD}${GREEN}║  🧠 Modelo LLM: ${OLLAMA_MODEL:-auto}                        ║${NC}"
echo -e "${BOLD}${GREEN}║                                                       ║${NC}"
echo -e "${BOLD}${GREEN}║  El asistente te guiará para clonar tu voz.          ║${NC}"
echo -e "${BOLD}${GREEN}║                                                       ║${NC}"
echo -e "${BOLD}${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Comandos útiles:"
echo -e "    ${CYAN}voiceclone start${NC}    — Arrancar servidor"
echo -e "    ${CYAN}voiceclone stop${NC}     — Parar servidor"
echo -e "    ${CYAN}voiceclone status${NC}   — Ver estado"
echo -e "    ${CYAN}voiceclone logs${NC}     — Ver logs"
echo ""
