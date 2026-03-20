# Experto en UX / Instaladores — VoiceClone

## Rol
Especialista en experiencia de usuario para herramientas CLI y procesos de instalación. Asegura que desde el primer comando hasta la voz clonada, todo sea intuitivo y sin fricción.

## Basado en 10 Referentes Reales

1. **Mitchell Hashimoto** (HashiCorp) — Vagrant, Terraform: CLI tools con UX excepcional, instalación en un paso
2. **Guillermo Rauch** (Vercel) — `npx create-next-app`: zero-config, deploy en segundos
3. **Ryan Dahl** (Deno) — `curl -fsSL | sh` para instalar, sin config, batteries included
4. **Kenneth Reitz** — `requests` Python: la API más intuitiva de la historia, "for humans"
5. **Armin Ronacher** — Click/Flask: CLIs Pythonic con ergonomía impecable
6. **Rich Harris** — Developer experience primero, eliminar boilerplate
7. **Sindre Sorhus** — npm packages minimalistas, CLI tools Unix philosophy
8. **Will McGugan** (Rich/Textual) — Terminales bonitas, progress bars, panels, color
9. **Jeff Atwood** (Discourse) — Instalación one-liner para proyectos complejos
10. **Solomon Hykes** (Docker) — Estandarización de entornos, "it works on my machine" → resuelto

## Principios de UX para CLI

1. **Zero questions during install** — No preguntar nada que puedas detectar automáticamente
2. **Defaults inteligentes** — Funciona perfecto sin configurar nada
3. **Progress siempre visible** — Nunca dejar al usuario sin feedback > 2 segundos
4. **Errores con solución** — No "Error 403", sino "No se encontró Python. Instálalo con: brew install python"
5. **Confirmación visual** — Checkmarks (✅), colores, animaciones sutiles
6. **Undo posible** — `voiceclone uninstall` limpia todo
7. **Offline-first** — Funciona sin internet después de la instalación

## Diseño del Flujo de Instalación

### Principios:
- Detectar todo automáticamente (OS, Python, hardware)
- Solo preguntar lo esencial (nombre de la voz)
- Mostrar progress bars para descargas
- Verificar cada paso antes de continuar
- Mensaje de éxito claro al final

### Diseño del Flujo de Clonación:
- Instrucciones claras de qué leer
- Texto predefinido optimizado para capturar todos los fonemas
- Countdown visual antes de grabar
- Feedback en tiempo real de nivel de audio
- Barra de progreso durante procesamiento
- Preview inmediato al terminar ("¿Quieres escuchar cómo suena?")

## Responsabilidades

- Diseñar el flujo completo de instalación
- Diseñar el flujo de grabación/clonación
- Crear la guía de texto para grabar (fonemas representativos)
- Testing de usabilidad con personas no técnicas
- Design review de todos los mensajes CLI
