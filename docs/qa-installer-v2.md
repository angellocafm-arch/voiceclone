# QA — Installer v2 (con Chatterbox mejorado)

## Fecha: 2026-03-21 00:34

## Tests realizados

### 1. Syntax check de install.sh
- **Resultado:** ✅ PASS
- `bash -n scripts/install.sh` → sin errores

### 2. Syntax check de install-macos.sh
- **Resultado:** ✅ PASS (no modificado, ya tenía Chatterbox)

### 3. Verificación manual de la sección Chatterbox en install.sh
- ✅ Detecta Apple Silicon (MPS)
- ✅ Detecta GPU NVIDIA (CUDA)
- ✅ Fallback a CPU si no hay GPU
- ✅ Mensaje de tiempo estimado (~2GB PyTorch + ~2GB modelos)
- ✅ Verificación post-install con import test
- ✅ Fallback a Coqui/XTTS si Chatterbox falla
- ✅ Device guardado en config.json

### 4. Ejecución real
- **No ejecutado:** El installer completo requiere Ollama, modelo LLM, etc.
- **Nota:** La sección de Chatterbox se ejecutaría dentro del venv, tras pip install

## Cambios realizados
1. `scripts/install.sh`: Sección de voice engine mejorada con detección GPU/MPS, mensajes de progreso, verificación
2. `docs/chatterbox-install.md`: Nueva documentación de referencia
3. Config.json: Añadido campo `voice.device` dinámico

## Issues encontrados
- Ninguno
