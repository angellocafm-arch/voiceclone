# Reunión de Equipo — Visión v3: Sistema Operativo Accesible por la Vista
## Fecha: 2026-03-20 22:15
## Tipo: Plenaria Urgente — Actualización de visión + incorporación nuevo experto
## Convocada por: Orquestador (instrucciones de Ángel)

---

## Participantes
- Orquestador
- Ingeniero de Comunicación IA
- Experto Voz IA
- Experto UX
- Experto DevOps
- Experto Audio
- Experto Accesibilidad
- Experto Personalidad IA
- **Experto Sistemas Locales / LLM Offline-First** ← NUEVO

---

## Contexto

Ángel ha clarificado la visión completa del producto. Ya NO es solo un clonador de voz con módulo de AAC. Es un **sistema operativo accesible por la vista**, con dos motores:

1. LLM más potente posible según hardware del usuario (controla todo el ordenador)
2. Motor de voz que clona la voz de la persona (el LLM habla con esa voz)

El eye tracking controla los dos. La persona puede comunicarse Y controlar el ordenador (crear carpetas, escribir documentos, abrir el correo) sin teclado ni ratón.

**Onboarding del nuevo experto (por Orquestador):**
El Experto en Sistemas Locales se incorpora para gestionar Ollama, selección de modelos por hardware, y el módulo de control del SO. Su expertise es crítico para el 60% del sistema.

---

## Puntos Tratados

### 1. Impacto en arquitectura (Experto Sistemas Locales presenta)

La nueva visión requiere dos cambios arquitectónicos críticos:

**A) Detección de hardware en la web:**
La landing page necesita detectar RAM/CPU/GPU ANTES de ofrecer descarga. Navigator APIs dan:
- `navigator.deviceMemory` → RAM aproximada (1, 2, 4, 8 GB discretos)
- `navigator.hardwareConcurrency` → núcleos CPU
- `WebGLRenderingContext.getParameter(RENDERER)` → GPU string
Con esto + heurísticas → selección automática del modelo.

**B) Módulo de control del SO:**
El LLM necesita herramientas (tool use / function calling) para actuar en el sistema:
```python
tools = [
    create_folder(path),
    open_file(path),
    launch_app(name),
    browser_navigate(url),
    read_file(path),
    write_file(path, content),
    send_email(to, subject, body)
]
```
Ollama soporta tool use desde versión 0.3+. Compatible con Mistral, Llama 3.1+.

### 2. El LLM habla con la voz del usuario (Experto Voz IA)

Confirmado el pipeline:
```
LLM genera texto (respuesta / confirmación de acción)
       ↓
Pipeline de síntesis (Chatterbox / XTTS)
       ↓
Audio con la voz de la persona
       ↓
Se reproduce automáticamente
```
Latencia total estimada: 2-4 segundos (generación LLM + síntesis)
Para frases cortas de confirmación (<10 palabras): <1.5 segundos

### 3. Módulo de control del SO — debate de seguridad (Experto DevOps + Experto Sistemas Locales)

**Preocupación:** El LLM puede ejecutar comandos del sistema. ¿Qué límites?

**Propuesta consensuada:**
- Lista blanca de acciones permitidas (sin confirmar):
  - Crear carpetas en ~/Desktop, ~/Documents, ~/Downloads
  - Abrir archivos y aplicaciones
  - Leer archivos de texto
  - Navegar web
- Acciones que requieren confirmación vocal antes:
  - Eliminar archivos
  - Enviar emails
  - Instalar software
- Acciones BLOQUEADAS permanentemente:
  - Acceso a ~/clawd, ~/.ssh, claves, passwords
  - Ejecución de scripts arbitrarios
  - Cambios de configuración del sistema

### 4. UX del módulo de control (Experto UX + Experto Accesibilidad)

**Problema detectado:** Si el usuario controla el ordenador por la vista, ¿cómo ve el resultado de las acciones del LLM?

**Solución:**
- Panel lateral siempre visible: últimas 3 acciones ejecutadas
- Cada acción: confirmación vocal + visual ("📁 Carpeta 'Médicos 2026' creada en escritorio")
- Botón de deshacer (eye tracking): mirar "Deshacer" 1 segundo
- Log de acciones del día consultable por voz: "¿Qué hiciste hoy?"

### 5. Eye tracking para módulo de control (Experto Accesibilidad)

Para dar instrucciones al LLM sin teclado, dos modos:
1. **Dictado por voz** (si la persona aún puede hablar): micro siempre activo, push-to-talk por mirada
2. **Teclado virtual por mirada**: teclado en pantalla, dwell time 800ms por tecla
3. **Comandos predefinidos por mirada**: grid de acciones frecuentes (crear carpeta, email, etc.)

El Módulo 2 (control del SO) tiene un grid de acciones de alta frecuencia seleccionables con la vista en <3 segundos.

### 6. Revisión del código existente (Experto Sistemas Locales + Experto DevOps)

El código en `src/` es una base sólida. Evaluación rápida:
- ✅ `src/voice_engine/` — base OK, wrapper Chatterbox/XTTS
- ✅ `src/api/` — FastAPI funcional, hay que ampliar endpoints
- ✅ `src/personality/` — rediseñar para nuevo rol del LLM
- ⚠️ `src/llm/` — esqueleto, no implementado. Implementar con Ollama
- ❌ `src/system/` — no existe. Crear módulo de control del SO
- ❌ `src/web/` — rediseñar para 3 módulos (comunicación, control, productividad)
- ❌ `scripts/install.sh` — ampliar para descargar LLM según hardware

---

## Decisiones (todas unánimes)

| # | Decisión | Razón |
|---|----------|-------|
| 1 | LLM con tool use (Ollama function calling) | Ollama 0.3+ soporta tools, Mistral/Llama3.1 compatibles |
| 2 | Lista blanca de acciones del SO | Seguridad sin sacrificar utilidad |
| 3 | Confirmación vocal ANTES de acciones destructivas | Evitar errores irreversibles |
| 4 | Streaming de respuestas: primera frase → sintetizar | Latencia percibida <1.5s en confirmaciones |
| 5 | Teclado virtual por mirada en Módulo 2 | No todos tienen voz — alternativa siempre disponible |
| 6 | Grid de acciones frecuentes (8 acciones) en Módulo 2 | 80% del tiempo se usan las mismas acciones |
| 7 | Navigator APIs para detección de hardware en web | Sin instalar nada, funciona en Chrome |
| 8 | Fallback: si Ollama falla → solo voz (sin control SO) | Degradación elegante, comunicación siempre disponible |
| 9 | Panel lateral de acciones ejecutadas (siempre visible) | Feedback esencial para usuario sin manos |
| 10 | Botón "Deshacer" accesible por mirada | Seguridad y confianza del usuario |

---

## Devil's Advocate (Experto Audio designado)

| Objeción | Respuesta del equipo |
|----------|---------------------|
| "El LLM 70B tarda 30s en responder en CPU — inaceptable para comunicación" | Para comunicación usamos frases cortas + caché. Solo tareas complejas usan modelo completo. Streaming mitiga la espera. |
| "¿Qué pasa si el LLM borra algo por error?" | Lista blanca + confirmación vocal para destructivos. Log de acciones. Botón deshacer. Papelera siempre, no rm definitivo. |
| "Navigator API no da RAM exacta — puede seleccionar modelo incorrecto" | deviceMemory da valores discretos (1,2,4,8GB). Siempre seleccionamos el modelo conservador (uno por debajo del límite). Mejor lento que sin memoria. |
| "¿Eye tracking WebSocket desde Chrome a localhost?" | Sí, WebSocket localhost no tiene restricciones CORS. Tobii SDK tiene driver que expone WebSocket. Testeado. |

Sin objeciones sin respuesta.

---

## Acciones para el equipo

- [ ] **Experto Sistemas Locales:** Implementar `src/llm/ollama_client.py` con tool use
- [ ] **Experto Sistemas Locales:** Implementar `src/system/` (file_manager, browser_control, app_launcher)
- [ ] **Experto DevOps:** Actualizar `scripts/install.sh` para descarga de LLM según hardware
- [ ] **Experto DevOps:** Implementar `src/landing/hardware.js` (detección de hardware web)
- [ ] **Experto UX + Accesibilidad:** Rediseñar `src/web/` con 3 módulos + grid de acciones
- [ ] **Experto Voz IA:** Implementar streaming pipeline (LLM → TTS → audio)
- [ ] **Experto Personalidad IA:** Rediseñar onboarding como agente conversacional
- [ ] **Orquestador:** Actualizar TRABAJO-ACTIVO.md con tareas concretas

---

## Próximos Pasos

El equipo está alineado. La arquitectura está clara. Arrancar implementación en orden:
1. LLM + Ollama (base de todo)
2. Control del SO (diferenciador clave)
3. Web local con 3 módulos
4. Installer con detección de hardware
5. Landing page
6. Tests E2E

*Reunión archivada: 2026-03-20 22:20*
