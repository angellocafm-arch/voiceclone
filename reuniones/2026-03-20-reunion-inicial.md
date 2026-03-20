# Reunión Inicial — Equipo VoiceClone
## Fecha: 2026-03-20 16:30
## Asistentes: Equipo completo (6 expertos)
## Moderador: Orquestador
## Devil's Advocate designado: Experto DevOps

---

## 1. Apertura — Orquestador

**Orquestador:** Bienvenidos al kickoff de VoiceClone. Objetivo del proyecto: que cualquier persona sin conocimientos técnicos pueda clonar su voz con un solo comando. 100% local, 100% open source, 100% privado. Tenemos la investigación de modelos y arquitectura completada. Hoy debatimos y tomamos decisiones finales sobre tres puntos clave:

1. **¿Qué modelo de TTS usamos?**
2. **¿Arquitectura monolítica o modular?**
3. **¿Docker o instalación nativa?**

Cada experto presenta su posición. DevOps será Devil's Advocate hoy. Empezamos.

---

## 2. Debate 1: Selección de Modelo TTS

### Experto Voz IA — Posición

**Recomendación: Chatterbox TTS como motor principal, XTTS v2 como fallback.**

Argumentos:
- Chatterbox gana en calidad pura. En blind tests independientes supera a ElevenLabs. Eso es decir mucho para un modelo open source.
- Licencia MIT — cero fricciones legales. XTTS usa MPL 2.0, que es open source pero tiene restricciones de copyleft en archivos modificados.
- Zero-shot desde 5 segundos de audio. El usuario graba 30s por seguridad, pero técnicamente con 5s ya funciona.
- Chatterbox-Turbo tiene 350M params — funcional en CPU con tiempos aceptables.
- 23+ idiomas nativos vs 17 de XTTS. Para un proyecto que aspira a ser global, esto importa.

El riesgo real es performance en CPU. Chatterbox en CPU puro es más lento que XTTS. Pero con la variante Turbo y la tendencia a que Apple Silicon mejore su MPS support, esto se mitiga.

### Experto Audio — Posición

Concuerdo con Chatterbox como principal. Desde la perspectiva de calidad de audio, los artefactos en la salida de Chatterbox son mínimos comparados con XTTS. Menos glitches, menos repeticiones, mejor preservación del timbre original.

**Pero** quiero añadir: el formato de entrada importa. Chatterbox acepta WAV 22050Hz mono igual que XTTS, pero su preprocesamiento interno es más robusto. Maneja mejor audio con ruido ambiental ligero, lo cual es crítico para nuestro caso de uso — usuarios grabando desde un micrófono de laptop en su casa, no en un estudio.

### Experto UX — Posición

Desde UX, me importa una cosa: **¿cuánto tarda?** Si el usuario graba su voz y tiene que esperar 5 minutos en CPU para generar una frase, la experiencia es mala.

Datos de la investigación:
- Chatterbox CPU: funcional pero sub-200ms solo en GPU. En CPU estamos hablando de 5-15s por frase corta.
- XTTS v2 CPU: ~10s de audio en ~10-11s. Casi real-time.
- XTTS v2 con MPS (Apple Silicon): 4x más rápido que CPU puro.

**Mi pregunta al equipo:** ¿Podemos hacer que Chatterbox use MPS en Apple Silicon? Si no, XTTS gana en experiencia de usuario para la mayoría de nuestro target inicial (macOS primero).

### Experto Voz IA — Respuesta

Chatterbox soporta MPS de Apple Silicon. No es tan optimizado como XTTS para MPS todavía, pero funciona. El equipo de Resemble AI está activamente mejorando esto. Para marzo 2026, el soporte MPS de Chatterbox es funcional con 2-3x mejora sobre CPU puro.

### Experto DevOps (Devil's Advocate) — Desafío

Voy a cuestionar la elección de Chatterbox:

1. **Resemble AI es una empresa comercial.** Su modelo de negocio es vender servicios de voz IA. ¿Qué pasa si deciden cambiar la licencia? Tenemos precedentes (Elastic, Redis, HashiCorp). XTTS, aunque Coqui cerró, ahora es genuinamente comunitario en Idiap Research Institute.

2. **El ecosistema de XTTS es más maduro.** Más tutoriales, más forks, más soporte comunitario. Si un usuario tiene un problema, encontrará más respuestas para XTTS en StackOverflow/Reddit.

3. **Tamaño de modelos.** Chatterbox necesita ~5GB. XTTS ~2GB. Para un "un solo comando" donde la descarga es parte de la experiencia, 5GB vs 2GB es diferencia real — especialmente en conexiones lentas.

### Orquestador — Mediación

Puntos válidos de DevOps. Vamos a resolverlos:

1. **Riesgo de licencia:** MIT es MIT. Incluso si Resemble cambia la licencia de versiones futuras, la versión actual con MIT queda libre para siempre. Podemos forkear. Riesgo mitigado por diseño.

2. **Ecosistema:** Cierto, pero nuestra arquitectura modular con Engine Adapter permite cambiar de motor sin reescribir nada. Si XTTS resulta mejor soportado, el switch es trivial.

3. **Tamaño:** Punto válido. ¿Experto Voz IA, Chatterbox-Turbo cuánto pesa?

### Experto Voz IA — Respuesta

Chatterbox-Turbo es significativamente más ligero que el modelo completo. Estamos hablando de ~1.5-2GB para Turbo. Comparable a XTTS.

### Comunicador IA — Posición

Desde comunicación, mi prioridad es poder decir "la mejor calidad de voz clonada, open source y gratis." Chatterbox nos da ese claim. XTTS es "muy bueno", Chatterbox es "el mejor." Esa diferencia importa para el README, para el tweet, para la adopción.

### Orquestador — Decisión

**DECISIÓN: Chatterbox TTS (variante Turbo) como motor principal. XTTS v2 como fallback automático.**

Razones:
- Mejor calidad (argumento diferenciador del proyecto)
- MIT license (máxima libertad)
- Turbo comparable en tamaño a XTTS
- Arquitectura modular mitiga riesgo de lock-in
- Fallback a XTTS si hardware del usuario no soporta Chatterbox bien

**Auto-detección en runtime:** Si el hardware del usuario funciona bien con Chatterbox → usar Chatterbox. Si no → fallback automático a XTTS con aviso al usuario.

✅ **Aprobado por unanimidad**

---

## 3. Debate 2: Arquitectura Monolítica vs Modular

### Orquestador — Planteamiento

La investigación de arquitectura propone un diseño modular con Engine Adapter pattern. ¿Estamos de acuerdo o alguien ve ventajas en monolítico?

### Experto DevOps — Posición

**Modular, sin duda.** Pero con matiz: modular internamente, monolítico para el usuario. El usuario instala UN paquete (`pip install voiceclone`), pero internamente los componentes son intercambiables.

Esto es exactamente lo que hace Docker (monolítico para el usuario, altamente modular dentro). No quiero que el usuario tenga que instalar `voiceclone-core`, `voiceclone-chatterbox`, `voiceclone-audio` por separado. Un paquete, múltiples módulos internos.

### Experto UX — Posición

100% de acuerdo con DevOps. El usuario ve:
```
pip install voiceclone
voiceclone clone
voiceclone say "Hola"
```

Tres comandos. Tres interacciones. Cero configuración de módulos.

Internamente, me da igual si son 50 módulos. Pero la superficie de usuario es UN ejecutable con sub-comandos.

### Experto Audio — Posición

Desde audio, modular es obligatorio. El pipeline de audio (grabación → procesamiento → normalización → modelo → post-procesamiento → playback) tiene pasos independientes que DEBEN poder actualizarse por separado. Si encontramos un mejor algoritmo de noise reduction, cambio un módulo sin tocar nada más.

### Experto Voz IA — Posición

El Engine Adapter pattern propuesto es correcto. Una interfaz `TTSEngine` con métodos `synthesize(text, voice) → audio` y `clone(audio) → voice`. Chatterbox y XTTS implementan esa interfaz. Si mañana sale un modelo mejor, creamos un nuevo adapter y listo.

### DevOps (Devil's Advocate) — Desafío

Mi preocupación con modular: **over-engineering prematuro.** Estamos en MVP. ¿Realmente necesitamos un Engine Adapter pattern con interfaz abstracta para v1.0? ¿O podemos hacer que Chatterbox sea el motor directo y abstraer después?

Contraargumento a mí mismo: el coste de hacer el adapter ahora es mínimo (una clase abstracta con 2 métodos). El coste de refactorizar después si no lo hacemos es alto. **Lo hago como advocate, pero la respuesta correcta es hacer el adapter ahora.**

### Orquestador — Decisión

**DECISIÓN: Arquitectura modular interna, monolítica para el usuario.**

Especificaciones:
- UN paquete pip: `voiceclone`
- Engine Adapter pattern con interfaz `TTSEngine`
- Componentes internos independientes: CLI, Core, Audio, API
- El usuario nunca ve la modularidad — solo comandos simples
- Coste de abstracción inicial: mínimo (1 clase abstracta, 2 adapters)

✅ **Aprobado por unanimidad**

---

## 4. Debate 3: Docker vs Instalación Nativa

### Experto DevOps — Posición

**Instalación nativa (pip + bootstrap script).** Docker NO tiene sentido para VoiceClone. Razones técnicas concretas:

1. **Micrófono:** Acceder al micrófono desde Docker requiere `--device /dev/snd` en Linux, y en macOS es directamente imposible sin hacks (PulseAudio forwarding). Para un usuario no técnico, esto es un blocker.

2. **Audio output:** Reproducir audio desde Docker requiere configuración de audio passthrough. En macOS, no hay forma limpia de hacer esto.

3. **Tamaño:** Imagen Docker con PyTorch + modelo = 8-10GB mínimo. Con instalación nativa estamos en 3-4GB.

4. **DX:** `docker run -it --device /dev/snd -v ~/.voiceclone:/root/.voiceclone voiceclone clone` vs `voiceclone clone`. No hace falta explicar cuál es mejor.

### Experto UX — Posición

Docker es un non-starter para nuestro usuario objetivo. "Persona no técnica" y "Docker" son mutuamente excluyentes. Nuestro usuario no sabe qué es un contenedor. Quiere abrir la Terminal, pegar un comando, y que funcione.

El bootstrap script (`curl -fsSL | bash`) es el estándar para esto. Homebrew, nvm, Rust, Deno — todos se instalan así. Los usuarios ya confían en este patrón.

### Experto Audio — Posición

Desde audio: Docker introduce latencia en audio I/O. Incluso si solucionamos el acceso al micrófono, la latencia añadida por la capa de virtualización degrada la experiencia. Para grabación en tiempo real, necesitamos acceso directo al hardware de audio.

### DevOps (Devil's Advocate) — Desafío a sí mismo

¿Docker como opción OPCIONAL para developers que quieran contribuir o para CI/CD? Sí. Tener un `Dockerfile` para reproducibilidad de entorno de desarrollo es buena práctica. Pero NO es el canal de distribución para usuarios finales.

### Comunicador IA — Posición

Mi métrica: ¿puedo explicar la instalación en un tweet?

Docker: "Instala Docker Desktop (1GB), configura audio passthrough, ejecuta docker run con 5 flags..." → NO.

Nativo: "Pega esto en tu Terminal y ya: `curl -fsSL https://voiceclone.dev/install.sh | bash`" → SÍ. ✅

### Orquestador — Decisión

**DECISIÓN: Instalación nativa como canal principal. Docker solo para desarrollo/CI.**

- **Usuarios finales:** `curl | bash` o `pip install voiceclone`
- **Desarrolladores:** `docker-compose up` para entorno de desarrollo reproducible
- **CI/CD:** Docker en GitHub Actions para testing cross-platform

Razones:
- Acceso a micrófono y audio del sistema son requisitos del producto
- Docker añade complejidad inaceptable para el usuario objetivo
- Tamaño de imagen prohibitivo
- El patrón `curl | bash` está probado y aceptado

✅ **Aprobado por unanimidad**

---

## 5. Decisiones Adicionales

### 5.1 Stack Tecnológico — Confirmado

| Componente | Tecnología | Status |
|------------|-----------|--------|
| Lenguaje | Python 3.10+ | ✅ Confirmado |
| CLI | Typer + Rich | ✅ Confirmado |
| API Server | FastAPI + uvicorn | ✅ Confirmado |
| TTS Principal | Chatterbox TTS (Turbo) | ✅ Confirmado |
| TTS Fallback | XTTS v2 | ✅ Confirmado |
| Audio | sounddevice + scipy | ✅ Confirmado |
| Distribución | PyPI + bootstrap script | ✅ Confirmado |
| Tests | pytest | ✅ Confirmado |
| CI/CD | GitHub Actions | ✅ Confirmado |
| Licencia | MIT | ✅ Confirmado |

### 5.2 Plataformas — Orden de prioridad

1. **macOS (Apple Silicon)** — Primera plataforma (Ángel usa Mac)
2. **macOS (Intel)** — Segundo
3. **Linux (Ubuntu/Debian)** — Tercero
4. **Windows (WSL)** — Futuro

### 5.3 Nombre de los comandos CLI — Propuesta del Comunicador

```bash
voiceclone setup     # Instalación inicial + descarga modelo
voiceclone clone     # Grabar voz + clonar
voiceclone say       # Generar audio con voz clonada
voiceclone serve     # API local para integración
voiceclone voices    # Listar voces disponibles
voiceclone export    # Exportar voz para compartir
voiceclone doctor    # Diagnóstico de problemas
voiceclone uninstall # Desinstalar limpiamente
```

**Añadido `doctor`** — Comunicador: "Cuando algo no funciona, el usuario necesita UN comando que le diga qué está mal y cómo arreglarlo. `voiceclone doctor` inspecciona Python, dependencias, modelos, micrófono, audio y reporta con ✅/❌."

✅ **Aprobado**

### 5.4 Directorio de datos — Experto DevOps

```
~/.voiceclone/
├── models/           # Modelos descargados (~2GB)
├── voices/           # Voces clonadas del usuario
│   └── mi-voz/
│       ├── reference.wav
│       ├── config.json
│       └── cache/
├── config.toml       # Configuración global
└── logs/             # Logs de diagnóstico
```

✅ **Aprobado**

---

## 6. Action Items Post-Reunión

| # | Acción | Responsable | Deadline |
|---|--------|-------------|----------|
| 1 | Escribir brief técnico con decisiones de esta reunión | Orquestador | Fase 1 |
| 2 | Diseñar flujo de usuario detallado (wireframes CLI) | UX | Fase 2 |
| 3 | Definir interfaz TTSEngine exacta | Voz IA | Fase 2 |
| 4 | Diseñar pipeline de audio completo | Audio | Fase 2 |
| 5 | Crear pyproject.toml base | DevOps | Fase 2 |
| 6 | Definir texto de grabación optimizado (fonemas) | Audio + Comunicador | Fase 2 |
| 7 | Escribir mensajes CLI (setup, clone, errors) | Comunicador | Fase 2 |

---

## 7. Resumen de Decisiones

| # | Decisión | Resultado | Votos |
|---|----------|-----------|-------|
| 1 | Modelo TTS principal | **Chatterbox TTS (Turbo)** | Unanimidad |
| 2 | Modelo TTS fallback | **XTTS v2** | Unanimidad |
| 3 | Arquitectura | **Modular interna, monolítica para usuario** | Unanimidad |
| 4 | Distribución | **Instalación nativa (pip + curl script)** | Unanimidad |
| 5 | Plataforma inicial | **macOS Apple Silicon** | Unanimidad |
| 6 | Licencia | **MIT** | Unanimidad |

---

## 8. Notas del Devil's Advocate (DevOps)

Mis desafíos fueron respondidos satisfactoriamente:
- **Riesgo de licencia Chatterbox:** Mitigado por MIT irrevocable + arquitectura modular
- **Ecosistema XTTS más maduro:** Aceptado, pero calidad > madurez para nuestro caso
- **Over-engineering modular:** El coste de abstracción es mínimo, el beneficio es alto
- **Docker como alternativa:** Rechazado correctamente por razones técnicas sólidas (audio I/O)

No queda ninguna objeción sin resolver. Apruebo todas las decisiones.

---

*Reunión finalizada: 2026-03-20 17:15*
*Siguiente paso: Brief técnico (Tarea 1.7)*
*Próxima reunión: Al iniciar Fase 2*
