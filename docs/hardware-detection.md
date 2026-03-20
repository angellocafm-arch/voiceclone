# Detección de Hardware via JavaScript en Chrome

## Fecha: 2026-03-20
## Propósito: Documentar cómo detectar capacidades del visitante para recomendar modelo LLM

---

## APIs Disponibles en el Navegador

### 1. RAM — `navigator.deviceMemory`
- **Soporte:** Chrome 63+, Edge 79+, Opera 50+ (NO Firefox, NO Safari)
- **Valores:** 0.25, 0.5, 1, 2, 4, 8 (máximo reportado por privacidad)
- **Limitación CRÍTICA:** Chrome limita a 8GB máximo por fingerprinting protection
- **Workaround:** Si deviceMemory = 8, asumir ≥8GB (podría ser 16, 32, 64)

### 2. CPU Cores — `navigator.hardwareConcurrency`
- **Soporte:** Todos los navegadores modernos
- **Valores:** Número real de logical cores (incluye hyperthreading)
- **Ejemplo:** M1 = 8, M2 Pro = 12, Intel i7 = 8-16
- **Utilidad:** Indicador indirecto de la gama del procesador

### 3. GPU — WebGL Renderer
```javascript
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
```
- **Soporte:** Chrome, Firefox, Edge (puede estar oculto en modo privado)
- **Valores ejemplo:**
  - "Apple M1" / "Apple M2 Pro" / "Apple M3 Max"
  - "NVIDIA GeForce RTX 4090"
  - "Intel Iris Plus Graphics"
- **Utilidad:** Determinar si hay GPU dedicada para modelos grandes

### 4. Plataforma — `navigator.platform` + `navigator.userAgent`
- Detectar macOS / Windows / Linux
- Detectar arquitectura (arm64 para Apple Silicon)

---

## Tabla de Recomendación de Modelos

| RAM (estimada) | CPU Cores | GPU | Modelo Recomendado | Tamaño |
|----------------|-----------|-----|-------------------|--------|
| ≤4 GB | Any | Any | Llama 3.2 3B Q4 | ~2 GB |
| 8 GB | ≤4 | Integrada | Llama 3.2 3B Q8 | ~3.5 GB |
| 8 GB | ≥6 | Integrada | Mistral 7B Q4 | ~4 GB |
| 16 GB | ≥6 | Integrada | Llama 3.1 8B Q5 | ~6 GB |
| 16 GB | ≥8 | Apple Silicon | Llama 3.1 8B Q8 | ~9 GB |
| 32 GB | ≥8 | Apple Silicon / dGPU | Llama 3.3 13B Q5 | ~10 GB |
| ≥64 GB | ≥12 | GPU ≥16GB VRAM | Llama 3.1 70B Q4 | ~40 GB |

### Lógica de Decisión
```
SI deviceMemory <= 4 → 3B
SI deviceMemory == 8 AND cores <= 4 → 3B (Q8)
SI deviceMemory == 8 AND cores >= 6 → 7B (Q4)
SI deviceMemory == 8 AND cores >= 8 AND gpu contiene "Apple M" → 8B (Q5)
SI cores >= 8 AND gpu contiene ("RTX" OR "Apple M2" OR "Apple M3") → 13B
SI cores >= 12 AND gpu contiene ("RTX 40" OR "Apple M2 Max/Ultra" OR "Apple M3") → 70B (con advertencia de descarga larga)
```

### Nota sobre deviceMemory = 8 (el tope de Chrome)
Como Chrome reporta máximo 8, usamos heurísticas adicionales:
- **cores ≥ 12** → probablemente ≥32 GB (workstation/pro)
- **GPU "Apple M2 Pro/Max/Ultra"** → seguro ≥32 GB
- **GPU "RTX 3090/4090"** → seguro ≥32 GB
- En estos casos, recomendar 13B-32B con opción manual para 70B

---

## Estrategia de Fallback

Si no se puede detectar hardware (modo privado, bloqueador):
1. Mostrar selector manual: "¿Cuánta RAM tiene tu ordenador?"
2. Opciones: 4 GB / 8 GB / 16 GB / 32 GB / 64 GB+
3. Recomendar modelo basándose en la selección

---

## Detección de SO para Descarga

```javascript
function detectOS() {
    const platform = navigator.platform.toLowerCase();
    const userAgent = navigator.userAgent.toLowerCase();

    if (platform.includes('mac') || userAgent.includes('macintosh')) {
        return userAgent.includes('arm64') || 
               (platform === 'macintel' && navigator.maxTouchPoints > 0)
            ? 'macos-arm64'   // Apple Silicon
            : 'macos-x64';   // Intel Mac
    }
    if (platform.includes('linux')) return 'linux-x64';
    if (platform.includes('win')) return 'windows-x64';
    return 'unknown';
}
```

---

## Fuentes
- MDN Web Docs: navigator.deviceMemory, hardwareConcurrency
- Chrome Platform Status: Hardware APIs
- WebGL debug renderer info extension spec
