# Reunión de Equipo — VoiceClone v4: Canales de Mensajería

**Fecha:** 2026-03-20, 22:56 CET  
**Convocada por:** Orquestador  
**Asistentes:** 9 expertos + Orquestador  
**Contexto:** Visión v4 validada por Ángel incluye canales de mensajería (Telegram, WhatsApp, Signal) basados en arquitectura OpenClaw (MIT)

---

## Agenda

1. Revisión de la visión v4 (canales de mensajería)
2. Debate: ¿Reutilizar código OpenClaw directamente o reimplementar?
3. Debate: Seguridad cuando Telegram controla el SO
4. Decisiones técnicas y asignaciones

---

## 1. Revisión de Visión v4

**Orquestador:** La visión v4 añade un cuarto módulo: canales de mensajería. El sistema debe funcionar como gateway local, igual que OpenClaw, pero 100% local y con síntesis de voz integrada. El caso clave: un familiar escribe por Telegram → el mensaje suena en la habitación del paciente con su propia voz clonada.

**Comunicador IA:** Esto es un game-changer para el proyecto. Convierte VoiceClone de una herramienta local a un puente entre el paciente y su mundo. La voz clonada hablando mensajes de Telegram es emocionalmente devastador (en el buen sentido).

---

## 2. Debate: ¿Reutilizar o Reimplementar?

**Experto Sistemas Locales:** He estudiado la arquitectura de OpenClaw. Es TypeScript/Node.js con grammY para Telegram y Baileys para WhatsApp. Nuestro stack es Python. Propongo reimplementar la interfaz de canales en Python, pero manteniendo exactamente la misma arquitectura de plugins.

**Experto DevOps:** Coincido. Reutilizar directamente significaría añadir Node.js como dependencia además de Python. Eso complica el installer. Un usuario con ELA no debería necesitar dos runtimes.

**Experto Audio:** Además, necesitamos el pipeline de voz integrado en el canal. En OpenClaw el output es texto → HTML. Nosotros necesitamos texto → voz → reproducir audio. Es un pipeline fundamentalmente diferente en la última milla.

**Devil's Advocate (Experto UX):** Pero ojo, reimplementar Baileys en Python no es trivial. WhatsApp Web es un protocolo reverse-engineered que cambia constantemente. ¿Tenemos la capacidad de mantener un bridge de WhatsApp en Python a largo plazo?

**Experto Sistemas Locales:** Buen punto. Para WhatsApp propongo usar whatsapp-web.js via un microservicio bridge Node.js mínimo, o directamente python-whatsapp-bot si la API Business está disponible. Para Telegram, python-telegram-bot es maduro y estable — no necesitamos reinventar nada.

**Experto Accesibilidad:** Desde accesibilidad: lo importante es que el canal sea transparente. El paciente no debería saber ni importarle si es Telegram o WhatsApp. Ve un mensaje, lo selecciona con la mirada, responde. El canal es un detalle de implementación.

### DECISIÓN: Reimplementar en Python con arquitectura de plugins inspirada en OpenClaw
- **A favor:** 8/9
- **En contra:** 0/9
- **Abstención:** 1/9 (DevOps — "ambas opciones son válidas")

**Justificación:**
1. Elimina dependencia de Node.js en el installer
2. Pipeline de voz integrado nativamente
3. python-telegram-bot y la API de Telegram son estables
4. WhatsApp se aborda en fase posterior (bridge o API Business)
5. La arquitectura de plugins (interfaz ABC) es agnóstica al lenguaje

---

## 3. Debate: Seguridad — Telegram Controlando el SO

**Devil's Advocate (Experto UX):** Esto es el elefante en la sala. Si un familiar manda "borra todo" por Telegram y el LLM lo ejecuta, tenemos un desastre. ¿Cómo gestionamos esto?

**Orquestador:** Excelente. Este es probablemente el punto más crítico del diseño. Abro debate.

**Experto Personalidad IA:** Propongo una separación clara:
- **Mensajes de canal entrantes → NUNCA ejecutan acciones del SO directamente**
- El LLM procesa el mensaje y lo anuncia con voz, pero no actúa
- Solo el paciente (via eye tracking local) puede dar instrucciones al SO

**Experto Sistemas Locales:** Eso es demasiado restrictivo. El caso de uso incluye que un cuidador remoto pueda enviar "Abre el PDF del informe médico" por Telegram y que el sistema lo haga. Propongo niveles:

```
NIVEL 1 — Sin confirmación (canal remoto):
  - Leer mensajes en voz alta
  - Mostrar notificación en pantalla

NIVEL 2 — Confirmación vocal/mirada del paciente:
  - Abrir archivos o URLs que alguien envía
  - Ejecutar acciones sugeridas por el canal

NIVEL 3 — NUNCA desde canal remoto:
  - Eliminar archivos
  - Enviar emails en nombre del paciente
  - Cualquier acción destructiva o irreversible

NIVEL 4 — BLOQUEADO siempre:
  - Comandos de sistema (sudo, formatear, etc.)
```

**Experto Voz IA:** Añado: la confirmación vocal es problemática para pacientes con ELA avanzada que ya no pueden hablar. La confirmación debe ser por mirada (dwell en botón "Confirmar" ≥2 segundos) o por patrón de parpadeo configurable.

**Experto Accesibilidad:** Totalmente de acuerdo. El sistema de confirmación debe ser:
1. **Primario:** Dwell de mirada en botón de confirmación (2 segundos)
2. **Secundario:** Parpadeo deliberado (3 parpadeos rápidos)
3. **Terciario:** Voz (si disponible)
4. **Último recurso:** Timeout sin acción = denegar

**Devil's Advocate:** ¿Y si el eye tracker falla? ¿Y si el paciente tiene un espasmo y "confirma" accidentalmente?

**Experto Accesibilidad:** Buena pregunta. Para acciones destructivas (Nivel 3), la confirmación debe ser un patrón complejo: mirar esquina superior izquierda + volver al botón. Es imposible de hacer por accidente.

### DECISIÓN: Modelo de seguridad en 4 niveles con confirmación multimodal
- **A favor:** 9/9 (unánime)

**Implementación acordada:**
1. Mensajes de canal NUNCA ejecutan acciones destructivas
2. Acciones benignas desde canal requieren confirmación local del paciente
3. Confirmación por dwell (2s) como método primario
4. Patrón anti-accidente para acciones destructivas
5. Todo configurable por el paciente/cuidador desde la interfaz

---

## 4. Decisiones Técnicas Adicionales

### Prioridad de Canales
**Decisión:** Telegram primero (bot API estable + gratuita), WhatsApp después (requiere bridge o API Business con coste).

**Justificación (Experto DevOps):**
- Telegram Bot API: gratuita, bien documentada, python-telegram-bot es excelente
- WhatsApp: requiere Business API ($) o bridge reverse-engineered (frágil)
- Signal: signal-cli existe, pero es menos prioritario
- iMessage: solo macOS, via AppleScript (viable)

### Arquitectura de Channel Manager
```python
class ChannelManager:
    channels: Dict[str, ChannelPlugin]      # Canales activos
    message_queue: asyncio.Queue            # Cola de mensajes entrantes
    voice_engine: VoiceEngine               # Motor de voz para anunciar
    security_policy: SecurityPolicy         # Niveles de confirmación

    async def on_message(msg: IncomingMessage):
        # 1. Verificar origen autorizado
        # 2. Encolar para procesamiento
        # 3. Anunciar con voz si está habilitado
        # 4. Si contiene instrucción → solicitar confirmación local

    async def send(channel: str, to: str, msg: OutgoingMessage):
        # 1. Sintetizar voz si se solicita
        # 2. Enviar por el canal correspondiente
```

### Almacenamiento de Configuración de Canales
```python
# ~/.voiceclone/channels.json
{
    "telegram": {
        "enabled": true,
        "bot_token": "123:abc",
        "announce_messages": true,  # Leer mensajes en voz alta
        "allowed_senders": ["*"],   # Quién puede enviar instrucciones
        "auto_reply": false         # No responder automáticamente
    }
}
```

---

## 5. Asignaciones

| Experto | Tarea | Prioridad |
|---------|-------|-----------|
| Sistemas Locales | Implementar ChannelPlugin ABC + TelegramChannel | P0 |
| Audio + Voz | Integrar pipeline voz en canal (msg → speak) | P0 |
| Personalidad IA | Diseñar prompts para anuncio de mensajes | P1 |
| Accesibilidad | Diseñar confirmación multimodal (dwell, parpadeo) | P1 |
| UX | Diseñar UI del módulo Canales (lista, config) | P1 |
| DevOps | Pipeline de testing para canales (mock bot) | P2 |

---

## Resumen de Decisiones

1. ✅ **Reimplementar en Python** (no reutilizar código Node.js de OpenClaw)
2. ✅ **Arquitectura de plugins** con interfaz ABC (ChannelPlugin)
3. ✅ **Seguridad en 4 niveles** — canales remotos NUNCA ejecutan acciones destructivas sin confirmación local
4. ✅ **Confirmación multimodal** — dwell (primario), parpadeo (secundario), voz (terciario)
5. ✅ **Telegram primero** — Bot API estable y gratuita
6. ✅ **Configuración en JSON local** — ~/.voiceclone/channels.json
7. ✅ **Pipeline: mensaje → voz → reproducir** — integrado, no separado

---

*Próxima reunión: post-implementación de Módulo 4 para revisión de seguridad.*
