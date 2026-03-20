# Chatterbox TTS — Guía de Instalación

## Paquete oficial
- **PyPI:** `pip install chatterbox-tts`
- **GitHub:** https://github.com/resemble-ai/chatterbox
- **Autor:** Resemble AI

## Modelos disponibles
| Modelo | Params | Idiomas | Uso ideal |
|--------|--------|---------|-----------|
| Chatterbox-Turbo | 350M | Inglés | Voice agents, producción, baja latencia |
| Chatterbox-Multilingual | 500M | 23+ | Apps globales, localización |
| Chatterbox (original) | 500M | Inglés | TTS zero-shot con controles creativos |

## Requisitos
- **Python:** 3.11 recomendado (3.10+ funciona)
- **PyTorch:** Se instala como dependencia automática
- **GPU:** Opcional. Soporta CUDA (NVIDIA), MPS (Apple Silicon), CPU
- **VRAM:** Turbo requiere ~2GB, standard ~3-4GB
- **Disco:** ~2-4GB para modelos (descarga automática de HuggingFace)

## Instalación por plataforma

### macOS Apple Silicon (MPS)
```bash
pip install chatterbox-tts
# PyTorch con soporte MPS se instala automáticamente
# Usar device="mps" en código
```

### Linux con GPU NVIDIA
```bash
pip install chatterbox-tts
# PyTorch CUDA se instala automáticamente si NVIDIA drivers están presentes
# Usar device="cuda"
```

### CPU (cualquier plataforma)
```bash
pip install chatterbox-tts
# Funciona en CPU pero es más lento (~5-10x)
# Usar device="cpu"
```

## Verificación
```python
python3 -c "from chatterbox.tts import ChatterboxTTS; print('Chatterbox TTS OK')"
```

## Descarga de modelos
Los modelos se descargan automáticamente la primera vez que se llama `from_pretrained()`.
Se guardan en `~/.cache/huggingface/hub/`.

## Notas
- El modelo Turbo (350M) es el más eficiente para producción
- Requiere un audio de referencia de ~10s para voice cloning
- Soporta tags paralingüísticos: [laugh], [cough], [chuckle]
- Investigado: 2026-03-21
