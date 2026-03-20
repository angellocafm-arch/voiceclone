/**
 * Tests for hardware detection module.
 * Run with: node tests/test_hardware.js
 *
 * @module test_hardware
 */

const {
  selectModel,
  estimateActualRAM,
  isAppleSiliconGPU,
  isHighEndGPU,
  isMidRangeGPU,
  MODEL_CATALOG,
} = require('../src/landing/hardware.js');

let passed = 0;
let failed = 0;

/**
 * Simple test assertion helper.
 * @param {string} name - Test name
 * @param {boolean} condition - Assertion
 */
function assert(name, condition) {
  if (condition) {
    passed++;
    console.log(`  ✅ ${name}`);
  } else {
    failed++;
    console.error(`  ❌ ${name}`);
  }
}

// --- GPU Detection Tests ---
console.log('\n🖥️  GPU Detection:');

assert('Apple M1 is Apple Silicon', isAppleSiliconGPU('Apple M1'));
assert('Apple M2 Pro is Apple Silicon', isAppleSiliconGPU('Apple M2 Pro'));
assert('Apple M3 Max is Apple Silicon', isAppleSiliconGPU('Apple M3 Max'));
assert(
  'NVIDIA RTX 4090 is NOT Apple Silicon',
  !isAppleSiliconGPU('NVIDIA GeForce RTX 4090'),
);
assert('null is not Apple Silicon', !isAppleSiliconGPU(null));

assert('RTX 4090 is high-end', isHighEndGPU('NVIDIA GeForce RTX 4090'));
assert('RTX 3090 is high-end', isHighEndGPU('NVIDIA GeForce RTX 3090'));
assert(
  'Apple M3 Max is high-end',
  isHighEndGPU('Apple M3 Max'),
);
assert(
  'Apple M2 Ultra is high-end',
  isHighEndGPU('Apple M2 Ultra'),
);
assert('Intel Iris is NOT high-end', !isHighEndGPU('Intel Iris Plus Graphics'));
assert('null is not high-end', !isHighEndGPU(null));

assert('Apple M1 is mid-range', isMidRangeGPU('Apple M1'));
assert('RTX 3060 is mid-range', isMidRangeGPU('NVIDIA GeForce RTX 3060'));
assert(
  'Intel HD 630 is NOT mid-range',
  !isMidRangeGPU('Intel HD Graphics 630'),
);

// --- RAM Estimation Tests ---
console.log('\n💾  RAM Estimation:');

assert('4GB reported → 4GB', estimateActualRAM(4, 4, null) === 4);
assert('2GB reported → 2GB', estimateActualRAM(2, 2, null) === 2);
assert('8GB + 4 cores → 8GB (trust report)', estimateActualRAM(8, 4, null) === 8);
assert(
  '8GB + 8 cores → 16GB (heuristic)',
  estimateActualRAM(8, 8, null) === 16,
);
assert(
  '8GB + 12 cores → 32GB (heuristic)',
  estimateActualRAM(8, 12, null) === 32,
);
assert(
  '8GB + 16 cores → 64GB (heuristic)',
  estimateActualRAM(8, 16, null) === 64,
);
assert(
  '8GB + RTX 4090 → 64GB (heuristic)',
  estimateActualRAM(8, 8, 'NVIDIA GeForce RTX 4090') === 64,
);
assert(
  '8GB + 10 cores + Apple M → 32GB',
  estimateActualRAM(8, 10, 'Apple M2 Pro') === 32,
);
assert(
  'null RAM + 8 cores → 16GB',
  estimateActualRAM(null, 8, null) === 16,
);
assert(
  'null RAM + null cores → 4GB (safe default)',
  estimateActualRAM(null, null, null) === 4,
);

// --- Model Selection Tests ---
console.log('\n🧠  Model Selection:');

const model4gb = selectModel(4, 4, null);
assert(`4GB RAM → basic tier (${model4gb.tier})`, model4gb.tier === 'basic');
assert(`4GB RAM → 3B model (${model4gb.displayName})`, model4gb.displayName.includes('3B'));

const model8gb = selectModel(8, 6, null);
assert(
  `8GB/6cores → standard tier (${model8gb.tier})`,
  model8gb.tier === 'standard',
);

const model16gb = selectModel(16, 8, 'Apple M2');
assert(
  `16GB Apple M2 → advanced tier (${model16gb.tier})`,
  model16gb.tier === 'advanced',
);

const model32gb = selectModel(32, 12, 'Apple M2 Pro');
assert(
  `32GB Apple M2 Pro → advanced tier (${model32gb.tier})`,
  model32gb.tier === 'advanced',
);

const model64gb = selectModel(64, 16, 'Apple M3 Max');
assert(
  `64GB Apple M3 Max → ultra tier (${model64gb.tier})`,
  model64gb.tier === 'ultra',
);

// Edge cases
const modelMin = selectModel(2, 2, null);
assert(
  `2GB RAM → basic tier (${modelMin.tier})`,
  modelMin.tier === 'basic',
);

const modelNoGPU = selectModel(16, 8, 'Intel HD Graphics 630');
assert(
  `16GB + Intel HD → not ultra (${modelNoGPU.tier})`,
  modelNoGPU.tier !== 'ultra',
);

// --- MODEL_CATALOG Tests ---
console.log('\n📋  Model Catalog:');

assert('Catalog has 5 models', MODEL_CATALOG.length === 5);
assert(
  'Models are ordered by minRAM',
  MODEL_CATALOG.every(
    (m, i) => i === 0 || m.minRAM >= MODEL_CATALOG[i - 1].minRAM,
  ),
);
assert(
  'All models have required fields',
  MODEL_CATALOG.every(
    (m) =>
      m.model && m.displayName && m.sizeGB && m.ramRequired && m.tier && m.description,
  ),
);

// --- Summary ---
console.log(`\n${'='.repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);
console.log('='.repeat(50));

if (failed > 0) {
  process.exit(1);
}
