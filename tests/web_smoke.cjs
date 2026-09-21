const assert = require('node:assert/strict');
const app = require('../assets/app.js');

const standard = app.calculateRecord({
  heightCm: 170,
  weightKg: 70,
  formula: 'Mosteller',
  dosePerM2: 100,
  gfr: 90,
});

assert.ok(Math.abs(standard.selectedBsa - Math.sqrt((170 * 70) / 3600)) < 1e-12);
assert.ok(Math.abs(standard.calculatedDose - standard.selectedBsa * 100) < 1e-12);
assert.ok(Math.abs(standard.indexedGfr - 90 * 1.73 / standard.selectedBsa) < 1e-12);
assert.equal(Object.keys(standard.values).length, 5);

assert.throws(() => app.calculateRecord({ heightCm: 0, weightKg: 70 }), /Height must be a positive number/);
assert.throws(() => app.calculateRecord({ heightCm: 170, weightKg: 70, dosePerM2: -1 }), /Dose per m²/);

console.log('Browser calculator smoke tests passed.');
