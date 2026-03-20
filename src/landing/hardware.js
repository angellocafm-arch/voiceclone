/**
 * VoiceClone — Hardware Detection Module
 *
 * Detects user hardware capabilities via browser APIs and recommends
 * the optimal LLM model for their system.
 *
 * APIs used:
 * - navigator.deviceMemory (Chrome/Edge only, capped at 8GB)
 * - navigator.hardwareConcurrency (all modern browsers)
 * - WebGL debug renderer info (GPU detection)
 * - navigator.platform / userAgent (OS detection)
 *
 * @module hardware
 * @version 1.0.0
 * @license MIT
 */

/**
 * @typedef {Object} HardwareInfo
 * @property {number|null} ramGB - Detected RAM in GB (null if unavailable, max 8 from API)
 * @property {number|null} cpuCores - Logical CPU core count
 * @property {string|null} gpuVendor - GPU vendor string
 * @property {string|null} gpuRenderer - GPU renderer string
 * @property {string} os - Detected OS: 'macos-arm64' | 'macos-x64' | 'linux-x64' | 'windows-x64' | 'unknown'
 * @property {boolean} hasGPU - Whether a discrete or capable GPU was detected
 * @property {boolean} isAppleSilicon - Whether running on Apple Silicon
 */

/**
 * @typedef {Object} ModelRecommendation
 * @property {string} model - Ollama model tag (e.g., 'llama3.2:3b-q4_K_M')
 * @property {string} displayName - Human-readable model name
 * @property {string} sizeGB - Approximate download size
 * @property {string} ramRequired - Minimum RAM needed
 * @property {string} tier - Performance tier: 'basic' | 'standard' | 'advanced' | 'pro' | 'ultra'
 * @property {string} description - User-facing description
 */

/**
 * Detects GPU information using WebGL debug renderer info.
 * @returns {{ vendor: string|null, renderer: string|null }}
 */
function detectGPU() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return { vendor: null, renderer: null };

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    if (!debugInfo) return { vendor: null, renderer: null };

    return {
      vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || null,
      renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || null,
    };
  } catch {
    return { vendor: null, renderer: null };
  }
}

/**
 * Detects the operating system and architecture.
 * @returns {string} OS identifier
 */
function detectOS() {
  const platform = (navigator.platform || '').toLowerCase();
  const userAgent = (navigator.userAgent || '').toLowerCase();

  if (platform.includes('mac') || userAgent.includes('macintosh')) {
    // Apple Silicon detection: arm64 in UA or iPad-like touchpoints on "Intel" platform
    const isARM =
      userAgent.includes('arm64') ||
      (platform === 'macintel' && navigator.maxTouchPoints > 0);
    return isARM ? 'macos-arm64' : 'macos-x64';
  }
  if (platform.includes('linux')) return 'linux-x64';
  if (platform.includes('win')) return 'windows-x64';
  return 'unknown';
}

/**
 * Checks if the GPU string indicates Apple Silicon.
 * @param {string|null} renderer - GPU renderer string
 * @returns {boolean}
 */
function isAppleSiliconGPU(renderer) {
  if (!renderer) return false;
  const r = renderer.toLowerCase();
  return r.includes('apple m') || r.includes('apple gpu');
}

/**
 * Checks if the GPU is a high-end discrete GPU.
 * @param {string|null} renderer - GPU renderer string
 * @returns {boolean}
 */
function isHighEndGPU(renderer) {
  if (!renderer) return false;
  const r = renderer.toLowerCase();
  return (
    r.includes('rtx 40') ||
    r.includes('rtx 30') ||
    r.includes('apple m2 max') ||
    r.includes('apple m2 ultra') ||
    r.includes('apple m3 max') ||
    r.includes('apple m3 ultra') ||
    r.includes('apple m4 max') ||
    r.includes('apple m4 ultra')
  );
}

/**
 * Checks if the GPU is a mid-range capable GPU (Apple Silicon Pro or RTX).
 * @param {string|null} renderer - GPU renderer string
 * @returns {boolean}
 */
function isMidRangeGPU(renderer) {
  if (!renderer) return false;
  const r = renderer.toLowerCase();
  return (
    r.includes('apple m') || // Any Apple Silicon is decent
    r.includes('rtx') ||
    r.includes('radeon rx 6') ||
    r.includes('radeon rx 7')
  );
}

/**
 * Estimates actual RAM when browser API is capped.
 * Uses CPU cores + GPU as heuristic.
 * @param {number|null} reportedRAM - navigator.deviceMemory value
 * @param {number|null} cores - CPU core count
 * @param {string|null} gpuRenderer - GPU renderer
 * @returns {number} Estimated RAM in GB
 */
function estimateActualRAM(reportedRAM, cores, gpuRenderer) {
  // If API unavailable, use conservative estimate from cores
  if (reportedRAM === null) {
    if (cores === null) return 4;
    if (cores >= 12) return 32;
    if (cores >= 8) return 16;
    if (cores >= 4) return 8;
    return 4;
  }

  // If below cap, trust the value
  if (reportedRAM < 8) return reportedRAM;

  // At cap (8GB) — use heuristics to estimate higher
  if (isHighEndGPU(gpuRenderer)) return 64;
  if (cores >= 16) return 64;
  if (cores >= 12) return 32;
  if (
    cores >= 10 &&
    gpuRenderer &&
    gpuRenderer.toLowerCase().includes('apple m')
  ) {
    return 32;
  }
  if (cores >= 8) return 16;

  // Default: trust the 8GB report
  return 8;
}

/**
 * Collects all hardware information from the browser.
 * @returns {HardwareInfo}
 */
function detectHardware() {
  const gpu = detectGPU();
  const ramReported = navigator.deviceMemory || null;
  const cores = navigator.hardwareConcurrency || null;
  const os = detectOS();
  const estimatedRAM = estimateActualRAM(ramReported, cores, gpu.renderer);

  return {
    ramGB: estimatedRAM,
    ramReported: ramReported,
    cpuCores: cores,
    gpuVendor: gpu.vendor,
    gpuRenderer: gpu.renderer,
    os: os,
    hasGPU: isMidRangeGPU(gpu.renderer),
    isAppleSilicon: isAppleSiliconGPU(gpu.renderer) || os === 'macos-arm64',
  };
}

/** @type {ModelRecommendation[]} */
const MODEL_CATALOG = [
  {
    model: 'llama3.2:3b-instruct-q4_K_M',
    displayName: 'Llama 3.2 3B',
    sizeGB: '2',
    ramRequired: '4',
    tier: 'basic',
    description:
      'Modelo ligero. Funciona en ordenadores con poca memoria. Respuestas rápidas, capacidad básica.',
    minRAM: 4,
    maxRAM: 6,
  },
  {
    model: 'mistral:7b-instruct-q4_K_M',
    displayName: 'Mistral 7B',
    sizeGB: '4',
    ramRequired: '8',
    tier: 'standard',
    description:
      'Buen equilibrio entre velocidad y calidad. Recomendado para la mayoría de ordenadores.',
    minRAM: 7,
    maxRAM: 12,
  },
  {
    model: 'llama3.1:8b-instruct-q5_K_M',
    displayName: 'Llama 3.1 8B',
    sizeGB: '6',
    ramRequired: '8',
    tier: 'standard',
    description:
      'Mayor capacidad de comprensión y tool use. Ideal para control del ordenador.',
    minRAM: 8,
    maxRAM: 14,
  },
  {
    model: 'llama3.3:13b-instruct-q5_K_M',
    displayName: 'Llama 3.3 13B',
    sizeGB: '10',
    ramRequired: '16',
    tier: 'advanced',
    description:
      'Excelente comprensión y generación. Perfecto para conversaciones naturales.',
    minRAM: 15,
    maxRAM: 48,
  },
  {
    model: 'llama3.1:70b-instruct-q4_K_M',
    displayName: 'Llama 3.1 70B',
    sizeGB: '40',
    ramRequired: '64',
    tier: 'ultra',
    description:
      'El modelo más potente. Calidad excepcional pero requiere hardware potente. Descarga ~40 GB.',
    minRAM: 49,
    maxRAM: Infinity,
  },
];

/**
 * Selects the best model for the detected hardware.
 * @param {number} ramGB - Estimated RAM in GB
 * @param {number|null} cpuCores - CPU core count
 * @param {string|null} gpuRenderer - GPU renderer string
 * @returns {ModelRecommendation}
 */
function selectModel(ramGB, cpuCores, gpuRenderer) {
  // Find the best model that fits the estimated RAM
  let selected = MODEL_CATALOG[0]; // Default: smallest

  for (const model of MODEL_CATALOG) {
    if (ramGB >= model.minRAM) {
      selected = model;
    }
  }

  // Boost: Apple Silicon or dedicated GPU can handle quantization better
  if (isAppleSiliconGPU(gpuRenderer) || isHighEndGPU(gpuRenderer)) {
    const nextTier = MODEL_CATALOG.find(
      (m) => m.minRAM > selected.minRAM && ramGB >= m.minRAM * 0.8,
    );
    if (nextTier) {
      selected = nextTier;
    }
  }

  return {
    model: selected.model,
    displayName: selected.displayName,
    sizeGB: selected.sizeGB,
    ramRequired: selected.ramRequired,
    tier: selected.tier,
    description: selected.description,
  };
}

/**
 * Main detection + recommendation function.
 * Call this on page load.
 * @returns {{ hardware: HardwareInfo, recommendation: ModelRecommendation }}
 */
function detectAndRecommend() {
  const hardware = detectHardware();
  const recommendation = selectModel(
    hardware.ramGB,
    hardware.cpuCores,
    hardware.gpuRenderer,
  );

  return { hardware, recommendation };
}

/**
 * Returns the download URL for the installer based on OS.
 * @param {string} os - OS identifier from detectOS()
 * @returns {{ url: string, filename: string, label: string }}
 */
function getInstallerDownload(os) {
  const base = 'https://github.com/angellocafm-arch/voiceclone/releases/latest/download';

  switch (os) {
    case 'macos-arm64':
      return {
        url: `${base}/voiceclone-macos-arm64.pkg`,
        filename: 'voiceclone-macos-arm64.pkg',
        label: 'Descargar para macOS (Apple Silicon)',
      };
    case 'macos-x64':
      return {
        url: `${base}/voiceclone-macos-x64.pkg`,
        filename: 'voiceclone-macos-x64.pkg',
        label: 'Descargar para macOS (Intel)',
      };
    case 'linux-x64':
      return {
        url: `${base}/voiceclone-linux-x64.sh`,
        filename: 'voiceclone-linux-x64.sh',
        label: 'Descargar para Linux',
      };
    case 'windows-x64':
      return {
        url: `${base}/voiceclone-windows-x64.exe`,
        filename: 'voiceclone-windows-x64.exe',
        label: 'Descargar para Windows',
      };
    default:
      return {
        url: `${base}/voiceclone-linux-x64.sh`,
        filename: 'voiceclone-linux-x64.sh',
        label: 'Descargar (selecciona tu sistema)',
      };
  }
}

// Export for module use and tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    detectGPU,
    detectOS,
    detectHardware,
    selectModel,
    detectAndRecommend,
    getInstallerDownload,
    estimateActualRAM,
    isAppleSiliconGPU,
    isHighEndGPU,
    isMidRangeGPU,
    MODEL_CATALOG,
  };
}
