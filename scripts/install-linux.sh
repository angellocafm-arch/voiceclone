#!/usr/bin/env bash
# VoiceClone — Linux Installer
# One command: curl -fsSL https://voiceclone.dev/install-linux | bash
#
# Supports: Ubuntu 20.04+, Debian 11+, Fedora 36+
#
# MIT License — Vertex Developer 2026

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# Config
INSTALL_DIR="$HOME/.voiceclone"
VENV_DIR="$INSTALL_DIR/venv"
MODELS_DIR="$INSTALL_DIR/models"
VOICES_DIR="$INSTALL_DIR/voices"
REPO_URL="https://github.com/angellocafm-arch/voiceclone"

# Helpers
log() { echo -e "${BLUE}[VoiceClone]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# Banner
echo ""
echo -e "${BOLD}🎤 VoiceClone — Preserva tu voz. Para siempre.${NC}"
echo -e "   Open source voice cloning for people with ALS"
echo ""

# ═══════════════════════════════════════════════════
# Step 1: System checks
# ═══════════════════════════════════════════════════
log "Verificando sistema..."

# Detect package manager
PKG_MGR=""
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
else
    error "No se detectó apt, dnf, ni pacman. Distribución no soportada."
fi
success "Gestor de paquetes: $PKG_MGR"

# Check Python
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    log "Instalando Python 3.12..."
    case "$PKG_MGR" in
        apt) sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3-pip ;;
        dnf) sudo dnf install -y python3.12 ;;
        pacman) sudo pacman -S --noconfirm python ;;
    esac
    PYTHON_CMD="python3.12"
fi
success "Python: $($PYTHON_CMD --version)"

# Install system deps
log "Instalando dependencias del sistema..."
case "$PKG_MGR" in
    apt) sudo apt-get install -y git ffmpeg libsndfile1 nodejs npm 2>/dev/null || true ;;
    dnf) sudo dnf install -y git ffmpeg libsndfile nodejs npm 2>/dev/null || true ;;
    pacman) sudo pacman -S --noconfirm git ffmpeg libsndfile nodejs npm 2>/dev/null || true ;;
esac

# Check disk space
DISK_FREE=$(df -BG "$HOME" | tail -1 | awk '{gsub("G",""); print $4}')
if [ "$DISK_FREE" -lt 5 ]; then
    error "Necesitas al menos 5GB libres. Tienes ${DISK_FREE}GB."
fi
success "Espacio en disco: ${DISK_FREE}GB disponibles"

# ═══════════════════════════════════════════════════
# Step 2-4: Same as macOS (clone, venv, deps)
# ═══════════════════════════════════════════════════
log "Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR" "$MODELS_DIR" "$VOICES_DIR"

if [ -d "$INSTALL_DIR/repo" ]; then
    log "Actualizando..."
    cd "$INSTALL_DIR/repo" && git pull --ff-only 2>/dev/null || true
else
    log "Descargando VoiceClone..."
    git clone --depth 1 "$REPO_URL.git" "$INSTALL_DIR/repo"
fi
success "Código descargado"

log "Configurando entorno Python..."
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
cd "$INSTALL_DIR/repo"
pip install --quiet -e ".[dev]" 2>/dev/null || pip install --quiet -e .
success "Dependencias instaladas"

# ═══════════════════════════════════════════════════
# Step 5: systemd service
# ═══════════════════════════════════════════════════
log "Configurando servicio..."
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR" "$INSTALL_DIR/logs"

cat > "$SERVICE_DIR/voiceclone.service" << EOF
[Unit]
Description=VoiceClone API Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR/repo
ExecStart=$VENV_DIR/bin/python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=5
StandardOutput=append:$INSTALL_DIR/logs/server.log
StandardError=append:$INSTALL_DIR/logs/server-error.log

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable voiceclone 2>/dev/null || true
systemctl --user start voiceclone 2>/dev/null || true
success "Servicio systemd configurado"

# ═══════════════════════════════════════════════════
# Step 6: CLI wrapper
# ═══════════════════════════════════════════════════
WRAPPER="$INSTALL_DIR/bin/voiceclone"
mkdir -p "$INSTALL_DIR/bin"
cat > "$WRAPPER" << EOF
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR/repo"
python -m src.cli "\$@"
EOF
chmod +x "$WRAPPER"

if ! echo "$PATH" | grep -q "$INSTALL_DIR/bin"; then
    SHELL_RC="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
    echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> "$SHELL_RC"
    export PATH="$INSTALL_DIR/bin:$PATH"
fi
success "Comando 'voiceclone' disponible"

# ═══════════════════════════════════════════════════
# Done!
# ═══════════════════════════════════════════════════
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  🎤 VoiceClone instalado correctamente!       ${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}API:${NC}         http://localhost:8765"
echo -e "  ${BOLD}CLI:${NC}         voiceclone --help"
echo -e "  ${BOLD}Directorio:${NC}  $INSTALL_DIR"
echo -e "  ${BOLD}Servicio:${NC}    systemctl --user status voiceclone"
echo ""
echo -e "  Para la web app:"
echo -e "    cd $INSTALL_DIR/repo/src/web && npm install && npm run dev"
echo ""
echo -e "  ${BLUE}Tu voz es tuya. Para siempre.${NC} 💚"
echo ""
