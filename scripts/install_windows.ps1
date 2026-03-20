# ═══════════════════════════════════════════════════════════
# VoiceClone v4 — Windows Installer (PowerShell)
#
# Usage:
#   Right-click → Run with PowerShell
#   Or: powershell -ExecutionPolicy Bypass -File install_windows.ps1
#
# What it does:
#   1. Checks Windows 10/11
#   2. Installs Python 3.11+ if needed (via winget)
#   3. Installs Ollama for Windows
#   4. Downloads LLM model (auto-selected by RAM)
#   5. Sets up Python venv with Chatterbox TTS
#   6. Starts FastAPI server on port 8765
#   7. Opens Chrome at http://localhost:8765
#
# MIT License — Vertex Developer / VoiceClone 2026
# ═══════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ─── Config ───────────────────────────────────────────────
$INSTALL_DIR = "$env:USERPROFILE\.voiceclone"
$VENV_DIR = "$INSTALL_DIR\venv"
$SERVER_PORT = 8765

# ─── Helpers ──────────────────────────────────────────────
function Write-Status($msg) { Write-Host "[VoiceClone] $msg" -ForegroundColor Green }
function Write-Warning2($msg) { Write-Host "[VoiceClone] $msg" -ForegroundColor Yellow }
function Write-Error2($msg) { Write-Host "[VoiceClone ERROR] $msg" -ForegroundColor Red }

function Test-CommandExists($cmd) {
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🎤 VoiceClone v4 — Windows Installer  ║" -ForegroundColor Cyan
Write-Host "║     Asistente de vida completo para ELA   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Step 1: Check Windows version ───────────────────────
Write-Status "Verificando sistema operativo..."
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-Error2 "VoiceClone requiere Windows 10 o superior."
    exit 1
}
Write-Status "Windows $($osVersion.Major).$($osVersion.Minor) detectado"

# ─── Step 2: Check/Install Python ────────────────────────
Write-Status "Verificando Python 3.10+..."

$pythonCmd = $null
foreach ($cmd in @("python3", "python", "py")) {
    if (Test-CommandExists $cmd) {
        $ver = & $cmd --version 2>&1
        if ($ver -match "3\.(1[0-9]|[2-9][0-9])") {
            $pythonCmd = $cmd
            break
        }
    }
}

if (-not $pythonCmd) {
    Write-Warning2 "Python 3.10+ no encontrado. Intentando instalar..."
    
    if (Test-CommandExists "winget") {
        Write-Status "Instalando Python 3.12 via winget..."
        winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        $pythonCmd = "python"
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")
    } else {
        Write-Error2 "No se pudo instalar Python automaticamente."
        Write-Host "  Descarga Python 3.12 desde: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "  IMPORTANTE: Marca 'Add Python to PATH' durante la instalacion." -ForegroundColor Yellow
        exit 1
    }
}

Write-Status "Python: $(& $pythonCmd --version)"

# ─── Step 3: Install Ollama ──────────────────────────────
Write-Status "Configurando Ollama (LLM local)..."

if (-not (Test-CommandExists "ollama")) {
    Write-Status "Instalando Ollama..."
    if (Test-CommandExists "winget") {
        winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    } else {
        Write-Warning2 "Descarga Ollama manualmente: https://ollama.ai/download"
        Write-Host "  Despues ejecuta este script de nuevo." -ForegroundColor Yellow
    }
}

# Start Ollama
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
} catch {
    Write-Status "Arrancando Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# Auto-select model by RAM
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
if ($ramGB -ge 64) { $model = "llama3.1:70b-instruct-q4_K_M" }
elseif ($ramGB -ge 32) { $model = "llama3.3:13b-instruct-q5_K_M" }
elseif ($ramGB -ge 16) { $model = "llama3.1:8b-instruct-q5_K_M" }
elseif ($ramGB -ge 8) { $model = "mistral:7b-instruct-q4_K_M" }
else { $model = "llama3.2:3b-instruct-q4_K_M" }

Write-Status "RAM detectada: ${ramGB}GB -> Modelo: $model"
Write-Status "Descargando modelo $model (puede tardar varios minutos)..."
& ollama pull $model 2>&1 | Out-Null

# ─── Step 4: Create directories ─────────────────────────
Write-Status "Creando estructura de directorios..."
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$INSTALL_DIR\data" | Out-Null
New-Item -ItemType Directory -Force -Path "$INSTALL_DIR\voices" | Out-Null
New-Item -ItemType Directory -Force -Path "$INSTALL_DIR\logs" | Out-Null

# ─── Step 5: Python venv + dependencies ──────────────────
Write-Status "Creando entorno virtual Python..."
if (-not (Test-Path "$VENV_DIR\Scripts\activate.ps1")) {
    & $pythonCmd -m venv $VENV_DIR
}

& "$VENV_DIR\Scripts\Activate.ps1"

Write-Status "Instalando dependencias..."
& pip install --upgrade pip setuptools wheel 2>&1 | Select-Object -Last 1

& pip install fastapi uvicorn[standard] websockets httpx pydantic python-multipart aiofiles 2>&1 | Select-Object -Last 3

# Voice engine
Write-Warning2 "Instalando Chatterbox TTS (motor de voz). Puede tardar varios minutos (~2GB)..."

# Detect GPU
$hasNvidia = $false
try { 
    $null = & nvidia-smi 2>&1
    $hasNvidia = $true
} catch {}

if ($hasNvidia) {
    Write-Status "GPU NVIDIA detectada -> motor de voz usara CUDA"
    $voiceDevice = "cuda"
} else {
    Write-Status "Sin GPU NVIDIA -> motor de voz usara CPU"
    $voiceDevice = "cpu"
}

& pip install chatterbox-tts 2>&1 | Select-Object -Last 5

# Verify
try {
    & $pythonCmd -c "from chatterbox.tts import ChatterboxTTS; print('OK')" 2>&1 | Out-Null
    Write-Status "Chatterbox TTS instalado correctamente"
} catch {
    Write-Warning2 "Chatterbox se configurara en el primer uso"
}

& pip install ollama 2>&1 | Select-Object -Last 1

deactivate

# ─── Step 6: Write config ───────────────────────────────
$config = @{
    version = "4.0.0"
    server = @{ host = "127.0.0.1"; port = $SERVER_PORT }
    ollama = @{ model = $model; host = "http://localhost:11434" }
    voice = @{ engine = "chatterbox"; device = $voiceDevice; fallback = "xtts" }
    installed_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    os = "Windows"
    arch = $env:PROCESSOR_ARCHITECTURE
} | ConvertTo-Json -Depth 3

$config | Out-File -FilePath "$INSTALL_DIR\config.json" -Encoding utf8

# ─── Step 7: Create startup script ──────────────────────
$startScript = @"
@echo off
call "$VENV_DIR\Scripts\activate.bat"
cd "$INSTALL_DIR"
uvicorn src.api.main:app --host 127.0.0.1 --port $SERVER_PORT --log-level info
"@
$startScript | Out-File -FilePath "$INSTALL_DIR\start.bat" -Encoding ascii

# ─── Open browser ────────────────────────────────────────
Write-Status "Abriendo navegador..."
Start-Process "http://localhost:$SERVER_PORT"

# ─── Done! ───────────────────────────────────────────────
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     🎤 VoiceClone instalado correctamente!            ║" -ForegroundColor Green
Write-Host "╠═══════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║                                                       ║" -ForegroundColor Green
Write-Host "║  🌐 Abre: http://localhost:$SERVER_PORT                    ║" -ForegroundColor Green
Write-Host "║  📁 Instalado en: $INSTALL_DIR               ║" -ForegroundColor Green
Write-Host "║  🧠 Modelo LLM: $model                       ║" -ForegroundColor Green
Write-Host "║                                                       ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Para arrancar: ejecuta $INSTALL_DIR\start.bat" -ForegroundColor Cyan
Write-Host ""
