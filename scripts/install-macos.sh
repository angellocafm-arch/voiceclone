#!/usr/bin/env bash
# VoiceClone — macOS Installer
# One command: curl -fsSL https://voiceclone.dev/install | bash
#
# What it does:
# 1. Checks system requirements (macOS 12+, Python 3.10+)
# 2. Installs Python dependencies in a venv
# 3. Downloads Chatterbox TTS model (~2.5GB)
# 4. Sets up the local API server as a LaunchAgent
# 5. Opens the web interface
#
# MIT License — Vertex Developer 2026

set -euo pipefail

# ═══════════════════════════════════════════════════
# Colors
# ═══════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ═══════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════
INSTALL_DIR="$HOME/.voiceclone"
VENV_DIR="$INSTALL_DIR/venv"
MODELS_DIR="$INSTALL_DIR/models"
VOICES_DIR="$INSTALL_DIR/voices"
REPO_URL="https://github.com/angellocafm-arch/voiceclone"
MIN_PYTHON_VERSION="3.10"
MIN_MACOS_VERSION="12"

# ═══════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════
log() { echo -e "${BLUE}[VoiceClone]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# ═══════════════════════════════════════════════════
# Banner
# ═══════════════════════════════════════════════════
echo ""
echo -e "${BOLD}🎤 VoiceClone — Preserva tu voz. Para siempre.${NC}"
echo -e "   Open source voice cloning for people with ALS"
echo -e "   ${BLUE}https://github.com/angellocafm-arch/voiceclone${NC}"
echo ""

# ═══════════════════════════════════════════════════
# Step 1: System checks
# ═══════════════════════════════════════════════════
log "Verificando sistema..."

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
if [ "$MACOS_VERSION" -lt "$MIN_MACOS_VERSION" ]; then
    error "Requiere macOS 12 (Monterey) o superior. Tienes macOS $MACOS_VERSION."
fi
success "macOS $MACOS_VERSION detectado"

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    success "Apple Silicon (M1/M2/M3) detectado — rendimiento óptimo"
elif [ "$ARCH" = "x86_64" ]; then
    success "Intel detectado — compatible"
else
    error "Arquitectura no soportada: $ARCH"
fi

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
    warn "Python 3.10+ no encontrado."
    log "Instalando Python via Homebrew..."
    if ! command -v brew &>/dev/null; then
        log "Instalando Homebrew primero..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python@3.12
    PYTHON_CMD="python3.12"
fi
success "Python encontrado: $($PYTHON_CMD --version)"

# Check disk space (need ~5GB)
DISK_FREE=$(df -g "$HOME" | tail -1 | awk '{print $4}')
if [ "$DISK_FREE" -lt 5 ]; then
    error "Necesitas al menos 5GB libres. Tienes ${DISK_FREE}GB."
fi
success "Espacio en disco: ${DISK_FREE}GB disponibles"

# ═══════════════════════════════════════════════════
# Step 2: Create install directory
# ═══════════════════════════════════════════════════
log "Creando directorio de instalación..."
mkdir -p "$INSTALL_DIR" "$MODELS_DIR" "$VOICES_DIR"
success "Directorio: $INSTALL_DIR"

# ═══════════════════════════════════════════════════
# Step 3: Clone or update repository
# ═══════════════════════════════════════════════════
if [ -d "$INSTALL_DIR/repo" ]; then
    log "Actualizando VoiceClone..."
    cd "$INSTALL_DIR/repo"
    git pull --ff-only 2>/dev/null || true
else
    log "Descargando VoiceClone..."
    git clone --depth 1 "$REPO_URL.git" "$INSTALL_DIR/repo"
fi
success "Código descargado"

# ═══════════════════════════════════════════════════
# Step 4: Python virtual environment
# ═══════════════════════════════════════════════════
log "Configurando entorno Python..."
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

log "Instalando dependencias (esto puede tardar 1-2 minutos)..."
pip install --quiet --upgrade pip
cd "$INSTALL_DIR/repo"
pip install --quiet -e ".[dev]" 2>/dev/null || pip install --quiet -e .
success "Dependencias instaladas"

# ═══════════════════════════════════════════════════
# Step 5: Download model
# ═══════════════════════════════════════════════════
log "Verificando modelo de voz..."
# The model downloads automatically on first use via HuggingFace
# We just pre-warm the download here
"$VENV_DIR/bin/python" -c "
try:
    from chatterbox.tts import ChatterboxTTS
    print('Modelo Chatterbox disponible — descargando pesos (~2.5GB)...')
    # This triggers the HuggingFace download
    model = ChatterboxTTS.from_pretrained(device='cpu')
    print('✅ Modelo descargado correctamente')
except ImportError:
    print('⚠️ Chatterbox se descargará en el primer uso')
except Exception as e:
    print(f'⚠️ Se descargará al primer uso: {e}')
" 2>/dev/null || warn "El modelo se descargará en el primer uso (normal)"

# ═══════════════════════════════════════════════════
# Step 6: Create LaunchAgent (auto-start API server)
# ═══════════════════════════════════════════════════
log "Configurando servicio..."
PLIST_PATH="$HOME/Library/LaunchAgents/dev.voiceclone.server.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.voiceclone.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/python</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>src.api.server:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8765</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR/repo</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/logs/server-error.log</string>
</dict>
</plist>
EOF

mkdir -p "$INSTALL_DIR/logs"

# Start the service
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
success "Servicio configurado (se inicia automáticamente)"

# ═══════════════════════════════════════════════════
# Step 7: Create CLI shortcut
# ═══════════════════════════════════════════════════
log "Creando acceso directo..."
WRAPPER="$INSTALL_DIR/bin/voiceclone"
mkdir -p "$INSTALL_DIR/bin"
cat > "$WRAPPER" << EOF
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
cd "$INSTALL_DIR/repo"
python -m src.cli "\$@"
EOF
chmod +x "$WRAPPER"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR/bin"; then
    SHELL_RC="$HOME/.zshrc"
    [ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc"
    echo "export PATH=\"$INSTALL_DIR/bin:\$PATH\"" >> "$SHELL_RC"
    export PATH="$INSTALL_DIR/bin:$PATH"
fi
success "Comando 'voiceclone' disponible"

# ═══════════════════════════════════════════════════
# Step 8: Wait for server and open web
# ═══════════════════════════════════════════════════
log "Esperando a que el servidor arranque..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8765/health >/dev/null 2>&1; then
        success "Servidor listo en http://localhost:8765"
        break
    fi
    sleep 1
done

# Open the web app
log "Abriendo VoiceClone..."
if [ -d "$INSTALL_DIR/repo/src/web" ]; then
    cd "$INSTALL_DIR/repo/src/web"
    if [ ! -d "node_modules" ]; then
        npm install --silent 2>/dev/null || true
    fi
    # Start web app in background
    npx next dev --port 3456 &>/dev/null &
    sleep 3
    open "http://localhost:3456"
else
    open "http://localhost:8765/docs"
fi

# ═══════════════════════════════════════════════════
# Done!
# ═══════════════════════════════════════════════════
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  🎤 VoiceClone instalado correctamente!       ${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Web App:${NC}     http://localhost:3456"
echo -e "  ${BOLD}API:${NC}         http://localhost:8765"
echo -e "  ${BOLD}CLI:${NC}         voiceclone --help"
echo -e "  ${BOLD}Directorio:${NC}  $INSTALL_DIR"
echo ""
echo -e "  ${YELLOW}Siguiente paso:${NC} Clona tu voz desde la web app"
echo ""
echo -e "  ${BLUE}Tu voz es tuya. Para siempre.${NC} 💚"
echo ""
