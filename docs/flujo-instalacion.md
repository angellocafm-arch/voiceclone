# Flujo de Instalación Sin Terminal — VoiceClone

## Fecha: 2026-03-20
## Autor: Equipo VoiceClone (Experto DevOps + Experto UX)

---

## Principio Fundamental

> Un usuario con ELA no puede abrir Terminal, escribir comandos, ni resolver errores de dependencias. La instalación debe ser: **click → esperar → listo**.

---

## Flujo por Sistema Operativo

### macOS — .pkg Installer

#### Experiencia del Usuario
```
1. Abre voiceclone.dev en Safari
2. Click "Descargar para macOS"
3. Descarga: VoiceClone-1.0.0-arm64.pkg (50MB)
   (auto-detecta ARM vs Intel)
4. Doble click en el .pkg
5. macOS Installer se abre:
   - "Introducción" → Click "Continuar"
   - "Licencia MIT" → Click "Continuar"
   - "Instalación" → Click "Instalar"
   - Introduce contraseña del sistema (o Touch ID)
6. Progress bar: "Instalando..." (30 segundos)
7. Progress bar: "Descargando modelo de voz..." (3-5 min, 2.1GB)
8. "Instalación completada ✅"
   → Abre automáticamente http://localhost:8765 en Safari
9. VoiceClone web app lista para usar
```

#### Bajo el Capó (.pkg contents)
```
VoiceClone.pkg
├── preinstall.sh
│   └── Verifica macOS version >= 13 (Ventura)
│
├── payload/
│   ├── /opt/voiceclone/
│   │   ├── python/              ← Python 3.12 standalone (no requiere brew)
│   │   │   └── python3.12       (bundled, 45MB)
│   │   ├── venv/                ← Virtualenv con todas las dependencias
│   │   │   └── lib/python3.12/site-packages/
│   │   │       ├── voiceclone/
│   │   │       ├── fastapi/
│   │   │       ├── torch/
│   │   │       └── chatterbox/
│   │   ├── bin/
│   │   │   └── voiceclone       ← CLI binary (symlinked to /usr/local/bin/)
│   │   └── uninstall.sh         ← Script de desinstalación limpio
│   │
│   └── /Library/LaunchAgents/
│       └── dev.voiceclone.server.plist  ← Auto-start del servidor API
│
├── postinstall.sh
│   ├── Descarga modelo Chatterbox (2.1GB) a ~/.voiceclone/models/
│   ├── Crea directorio ~/.voiceclone/
│   ├── Inicia servicio (launchctl load)
│   ├── Espera a que localhost:8765 responda
│   └── Abre Safari en http://localhost:8765
│
└── Distribution.xml
    └── Metadata: título, version, min-os-version, etc.
```

#### Build Process
```bash
# 1. Crear payload
pkgbuild --root ./payload \
         --identifier dev.voiceclone \
         --version 1.0.0 \
         --scripts ./scripts \
         --install-location / \
         VoiceClone-component.pkg

# 2. Crear product archive (installer UI)
productbuild --distribution Distribution.xml \
             --package-path . \
             --resources ./resources \
             VoiceClone-1.0.0.pkg

# 3. Sign (requiere Apple Developer certificate — post-MVP)
productsign --sign "Developer ID Installer: Vertex Developer" \
            VoiceClone-1.0.0.pkg \
            VoiceClone-1.0.0-signed.pkg

# 4. Notarize (requiere Apple Developer account — post-MVP)
xcrun notarytool submit VoiceClone-1.0.0-signed.pkg \
      --apple-id ... --team-id ... --password ...
```

#### MVP Simplificación
- **Sin signing/notarization** (requiere Apple Developer $99/año)
- Los usuarios necesitarán: System Settings → Privacy → "Allow anyway"
- Documentar este paso claramente con screenshots
- Post-MVP: firmar y notarizar para instalación sin warning

---

### Windows — .exe Installer (NSIS)

#### Experiencia del Usuario
```
1. Abre voiceclone.dev
2. Click "Descargar para Windows"
3. Descarga: VoiceClone-Setup-1.0.0.exe (60MB)
4. Doble click → Windows SmartScreen warning
   → Click "Más información" → "Ejecutar de todos modos"
5. Installer wizard:
   - "Bienvenido" → Click "Siguiente"
   - "Ubicación" → Default C:\VoiceClone → "Siguiente"
   - "Instalar" → Click "Instalar"
6. Progress bar: "Instalando..." (30 segundos)
7. Progress bar: "Descargando modelo de voz..." (3-5 min)
8. "Instalación completada ✅"
   → Checkbox "Abrir VoiceClone" (marcado por defecto)
   → Click "Finalizar"
9. Se abre http://localhost:8765 en navegador por defecto
```

#### NSIS Script (estructura)
```nsi
!include "MUI2.nsh"

Name "VoiceClone"
OutFile "VoiceClone-Setup-1.0.0.exe"
InstallDir "$PROGRAMFILES\VoiceClone"

Section "Install"
  ; 1. Copiar Python embebido
  SetOutPath "$INSTDIR\python"
  File /r "python-3.12-embed-win64\*.*"
  
  ; 2. Copiar voiceclone package
  SetOutPath "$INSTDIR\voiceclone"
  File /r "dist\voiceclone\*.*"
  
  ; 3. Crear directorio de datos
  CreateDirectory "$APPDATA\voiceclone"
  
  ; 4. Descargar modelo (background, con progress)
  NSISdl::download "https://models.voiceclone.dev/chatterbox-v1.bin" \
                    "$APPDATA\voiceclone\models\chatterbox-v1.bin"
  
  ; 5. Crear acceso directo
  CreateShortcut "$DESKTOP\VoiceClone.lnk" \
                 "$INSTDIR\voiceclone.exe"
  
  ; 6. Registrar servicio o tarea programada
  ; (opción: Windows Service o Task Scheduler)
  
  ; 7. Registrar desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\VoiceClone.lnk"
  ; NO eliminar datos del usuario ($APPDATA\voiceclone)
  ; a menos que el usuario lo pida explícitamente
SectionEnd
```

#### MVP Simplificación
- **Sin firma digital** (requiere certificado de code signing ~$200-400/año)
- SmartScreen warning es inevitable sin firma
- Documentar "Más información" → "Ejecutar de todos modos" con screenshots
- Post-MVP: firmar con certificado EV (elimina warning completamente)

---

### Linux — .deb Package + Script Bash

#### Opción 1: Script bash (universal)
```bash
$ curl -fsSL https://voiceclone.dev/install.sh | bash
```

**El script hace:**
```bash
#!/bin/bash
set -e

echo "🎤 VoiceClone — Instalación"
echo "────────────────────────────"

# 1. Detectar distro
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
elif [ -f /etc/fedora-release ]; then
    DISTRO="fedora"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
fi

# 2. Instalar Python si necesario
if ! command -v python3.12 &> /dev/null; then
    echo "Instalando Python 3.12..."
    case $DISTRO in
        debian) sudo apt-get install -y python3.12 python3.12-venv ;;
        fedora) sudo dnf install -y python3.12 ;;
        arch)   sudo pacman -S python ;;
    esac
fi

# 3. Crear directorio y virtualenv
mkdir -p ~/.voiceclone
python3.12 -m venv ~/.voiceclone/venv

# 4. Instalar voiceclone
~/.voiceclone/venv/bin/pip install voiceclone

# 5. Symlink CLI
sudo ln -sf ~/.voiceclone/venv/bin/voiceclone /usr/local/bin/voiceclone

# 6. Descargar modelo
echo "Descargando modelo Chatterbox TTS (2.1 GB)..."
voiceclone download-model chatterbox

# 7. Crear systemd service
sudo tee /etc/systemd/system/voiceclone.service > /dev/null <<EOF
[Unit]
Description=VoiceClone API Server
After=network.target

[Service]
ExecStart=/usr/local/bin/voiceclone server
User=$USER
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable voiceclone
sudo systemctl start voiceclone

echo ""
echo "✅ VoiceClone instalado correctamente"
echo "API: http://localhost:8765"
echo "CLI: voiceclone --help"
```

#### Opción 2: .deb package (Debian/Ubuntu)
```
voiceclone_1.0.0_amd64.deb
├── DEBIAN/
│   ├── control
│   ├── preinst
│   ├── postinst      ← Descarga modelo, crea servicio
│   ├── prerm
│   └── postrm
└── opt/voiceclone/
    ├── python/
    ├── venv/
    └── bin/voiceclone
```

---

## Desinstalación

### macOS
```bash
# Desde terminal:
/opt/voiceclone/uninstall.sh

# O desde web app: Settings → Desinstalar
# El script:
# 1. Para el servicio (launchctl unload)
# 2. Elimina /opt/voiceclone/
# 3. Pregunta: ¿eliminar voces y datos? (default: no)
# 4. Si sí: elimina ~/.voiceclone/
```

### Windows
```
Panel de Control → Programas → VoiceClone → Desinstalar
# O desde web app: Settings → Desinstalar
# El desinstalador:
# 1. Para el servicio
# 2. Elimina C:\VoiceClone\
# 3. NO elimina datos ($APPDATA\voiceclone) a menos que se pida
```

### Linux
```bash
# Script:
voiceclone uninstall

# O manualmente:
sudo systemctl stop voiceclone
sudo systemctl disable voiceclone
sudo rm /etc/systemd/system/voiceclone.service
sudo rm /usr/local/bin/voiceclone
rm -rf ~/.voiceclone/  # solo si quiere eliminar datos
```

---

## Actualización

```bash
# Desde CLI:
voiceclone update

# Desde web app: Settings → "Actualizar disponible" → Click

# El proceso:
# 1. Descarga nueva versión del package
# 2. Para el servicio
# 3. Reemplaza binarios
# 4. Reinicia servicio
# 5. No toca datos del usuario (~/.voiceclone/voices/)
```

---

## Manejo de Errores de Instalación

| Error | Causa | Mensaje al usuario | Solución automática |
|-------|-------|-------------------|---------------------|
| Sin espacio | Disco <4GB libre | "Necesitas 4GB libres" | Sugerir limpiar |
| Sin internet | No hay conexión | "Se necesita internet para descargar el modelo" | Retry automático |
| macOS antiguo | <13 Ventura | "Necesitas macOS 13 o superior" | Link a actualizar |
| Python falta (Linux) | Sin Python 3.12 | "Instalando Python..." | Auto-install |
| Puerto ocupado | 8765 en uso | "Puerto 8765 ocupado. Usando 8766" | Auto-fallback |
| Permiso denegado | Sin sudo (Linux) | "Necesitas permisos de admin" | Pedir sudo |
| Modelo corrupto | Descarga interrumpida | "Descarga incompleta. Reintentando..." | Auto-retry |

---

## Resumen de Tamaños

| Componente | Tamaño | Notas |
|------------|--------|-------|
| Installer (.pkg/.exe) | ~50-60MB | Python embebido + voiceclone code |
| Modelo Chatterbox | ~2.1GB | Se descarga post-install |
| Modelo XTTS v2 (fallback) | ~1.8GB | Opcional, se descarga si se necesita |
| Directorio datos (~/.voiceclone/) | ~10-50MB | Voces + personalidad + config |
| **Total inicial** | **~2.2GB** | Installer + modelo principal |

---

*Flujo de Instalación — Proyecto VoiceClone*  
*Vertex Developer — 2026*  
*"Click. Esperar. Hablar."*
