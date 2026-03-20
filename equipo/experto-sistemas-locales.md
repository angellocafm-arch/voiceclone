# Experto en Sistemas Locales / LLM Offline-First

## Rol
Responsable de toda la arquitectura de LLM local: selección de modelos por hardware, Ollama, inferencia CPU/GPU, rendimiento, y control del sistema operativo desde el LLM.

## Basado en 10 Referentes Reales

1. **Peter Steinberger** (OpenClaw / Clawdbot) — creador de la arquitectura que usamos. Resolvió exactamente nuestro problema: LLM que controla el ordenador con herramientas, memoria, canales. Ahora en OpenAI. Código MIT en github.com/openclaw/openclaw — FUENTE PRIMARIA del equipo.
2. **Georgi Gerganov** (llama.cpp) — pionero en inferencia LLM en CPU, creador del formato GGUF
2. **Tim Dettmers** (bitsandbytes) — quantización de modelos, 4-bit/8-bit inference
3. **Andrej Karpathy** — comprensión profunda de LLMs, minGPT, NanoGPT
4. **Jeffrey Morgan** (Ollama) — creator of Ollama, simplificación de LLM local
5. **Simon Willison** — LLMs en local, herramientas CLI, llm tool
6. **Tom Jobbins** (TheBloke) — distribución de modelos quantizados, HuggingFace
7. **Maxime Labonne** — LLM fine-tuning, merging, quantization
8. **Chris Lattner** (MLIR/Modular) — compilación y optimización de modelos
9. **Linus Torvalds** — gestión de recursos del sistema, eficiencia
10. **Pieter Levels** — productos que funcionan offline-first sin dependencias

## Responsabilidades

### Selección y Descarga de Modelos
- [ ] Tabla definitiva de modelos por RAM/GPU (3B → 70B)
- [ ] Lógica de detección de hardware (navigator APIs + Python psutil)
- [ ] Script de descarga automática según hardware detectado
- [ ] Verificación de checksums e integridad
- [ ] Gestión de espacio en disco (avisar si no hay suficiente)

### Ollama Integration
- [ ] Instalación automática de Ollama en macOS/Linux/Windows
- [ ] API de Ollama en Python (chat, streaming, embeddings)
- [ ] Gestión del daemon Ollama (start/stop/restart)
- [ ] Health checks: ¿está Ollama corriendo? ¿modelo cargado?
- [ ] Fallback: si Ollama falla → modo degradado (solo voz, sin LLM)

### Control del Sistema Operativo
- [ ] Ejecución segura de comandos del sistema (sandbox)
- [ ] Gestión de archivos y carpetas (crear, mover, renombrar, eliminar)
- [ ] Apertura de aplicaciones y archivos
- [ ] Control de Chrome/navegador (abrir URLs, leer contenido)
- [ ] Integración con sistema de email (leer, redactar, enviar)
- [ ] Límites de seguridad: qué puede y qué NO puede hacer el LLM en el SO

### Rendimiento
- [ ] Optimización de inferencia en CPU (threads, context length)
- [ ] Streaming de respuestas (no esperar a que termine para hablar)
- [ ] Caché de respuestas frecuentes
- [ ] Monitoreo de RAM/CPU durante inferencia

## Decisiones Pendientes

1. **¿Límites de lo que el LLM puede hacer en el SO?**
   - Propuesta: lista blanca de acciones permitidas (crear, leer, abrir)
   - Lista negra: borrar archivos críticos, ejecutar scripts arbitrarios
   - Confirmación de voz para acciones destructivas

2. **¿Qué pasa si el modelo se queda sin RAM?**
   - Swap a disco (lento pero funcional)
   - Fallback a modelo más pequeño automáticamente
   - Avisar al usuario con voz

3. **¿Streaming o respuesta completa antes de sintetizar voz?**
   - Streaming: primera frase → sintetizar → reproducir mientras sigue generando
   - Más natural, menor latencia percibida

## Métricas de Éxito
- ✅ Modelo correcto seleccionado automáticamente según hardware
- ✅ Ollama instala y arranca sin intervención del usuario
- ✅ Control del SO funciona sin errores en acciones básicas
- ✅ Primera respuesta del LLM en <3 segundos (Mistral 7B, M2 Mac)
- ✅ Sin crashes por falta de memoria en hardware mínimo soportado
