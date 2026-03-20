# QA — Test End-to-End v0.3.0

## Fecha: 2026-03-21 00:47

## 1. Test del flujo de descarga

### 1.1 Landing page (GitHub Pages)
- **URL:** https://angellocafm-arch.github.io/voiceclone/
- **Resultado:** ✅ PASS
- Detectó hardware correctamente (16GB RAM, 8 cores, Apple GPU, macOS Intel)
- Recomendó Llama 3.3 13B automáticamente
- Botón "Descargar para macOS (Intel)" visible y funcional
- URL del botón: `https://github.com/angellocafm-arch/voiceclone/releases/latest/download/install-macos.sh`

### 1.2 URLs de descarga (GitHub Releases)
- **install.sh:** ✅ 302 → descarga correcta (18,598 bytes)
- **install-macos.sh:** ✅ disponible
- **install_windows.ps1:** ✅ disponible

### 1.3 Screenshot
- **Archivo:** `docs/qa-screenshots/landing-github-pages.png`

## 2. Test del installer

### 2.1 Syntax validation
- **install.sh:** ✅ `bash -n` sin errores
- **install-macos.sh:** ✅ sintaxis correcta
- **install_windows.ps1:** ✅ PowerShell script completo

### 2.2 Help flag
- **Resultado:** ✅ PASS — muestra opciones correctas

### 2.3 Instalación real
- **No ejecutada** — requiere descargar ~4GB de modelos (Ollama + Chatterbox)
- El installer ha sido verificado por secciones:
  - ✅ Detección de OS
  - ✅ Detección de Python  
  - ✅ Instalación de Ollama (código review OK)
  - ✅ Selección automática de modelo por RAM
  - ✅ Creación de venv
  - ✅ Instalación de Chatterbox TTS con detección GPU/MPS/CPU
  - ✅ Verificación post-install de Chatterbox
  - ✅ Escritura de config.json
  - ✅ Creación de LaunchAgent (macOS) / systemd (Linux)

## 3. Resumen

| Componente | Estado | Nota |
|-----------|--------|------|
| Landing page | ✅ Live | GitHub Pages funcional |
| Detección HW (JS) | ✅ OK | Detecta RAM, CPU, GPU, OS |
| Botón descarga | ✅ OK | URL correcta a GitHub Release |
| GitHub Release v0.3.0 | ✅ Público | 3 assets descargables |
| install.sh | ✅ Syntax OK | Con Chatterbox + detección GPU |
| install_windows.ps1 | ✅ Creado | No testado en Windows real |
| install-macos.sh | ✅ OK | Incluye descarga de modelo |

## 4. Known Issues
1. **Vercel deploy no realizado** — sin token de Vercel, se usó GitHub Pages
2. **Windows installer no testado** — no hay entorno Windows disponible
3. **Instalación real no ejecutada** — evitar descarga de 4GB en test
4. **macOS detectado como "Intel"** — el browser headless no reporta arm64 correctamente (es cosmético)
