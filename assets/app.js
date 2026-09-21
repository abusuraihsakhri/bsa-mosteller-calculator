(function (root) {
  'use strict';

  const FORMULAS = {
    Mosteller: (heightCm, weightKg) => Math.sqrt((heightCm * weightKg) / 3600),
    DuBois: (heightCm, weightKg) => 0.007184 * Math.pow(heightCm, 0.725) * Math.pow(weightKg, 0.425),
    Haycock: (heightCm, weightKg) => 0.024265 * Math.pow(heightCm, 0.3964) * Math.pow(weightKg, 0.5378),
    GehanGeorge: (heightCm, weightKg) => 0.0235 * Math.pow(heightCm, 0.42246) * Math.pow(weightKg, 0.51456),
    Boyd: (heightCm, weightKg) => {
      const weightGrams = weightKg * 1000;
      const exponent = 0.7285 - 0.0188 * Math.log10(weightGrams);
      return 0.0003207 * Math.pow(heightCm, 0.3) * Math.pow(weightGrams, exponent);
    },
  };

  const DISPLAY_NAMES = {
    Mosteller: 'Mosteller',
    DuBois: 'Du Bois',
    Haycock: 'Haycock',
    GehanGeorge: 'Gehan–George',
    Boyd: 'Boyd',
  };

  function positiveNumber(value, label) {
    const number = Number(value);
    if (!Number.isFinite(number) || number <= 0) {
      throw new Error(`${label} must be a positive number.`);
    }
    return number;
  }

  function optionalNonnegative(value, label) {
    if (value === '' || value === null || value === undefined) return null;
    const number = Number(value);
    if (!Number.isFinite(number) || number < 0) {
      throw new Error(`${label} must be zero or greater.`);
    }
    return number;
  }

  function calculateBsa(heightCm, weightKg) {
    const height = positiveNumber(heightCm, 'Height');
    const weight = positiveNumber(weightKg, 'Weight');
    const values = {};
    for (const [name, fn] of Object.entries(FORMULAS)) {
      values[name] = fn(height, weight);
    }
    return values;
  }

  function calculateRecord({ heightCm, weightKg, formula = 'Mosteller', dosePerM2 = null, gfr = null }) {
    if (!Object.prototype.hasOwnProperty.call(FORMULAS, formula)) {
      throw new Error('Select a valid BSA formula.');
    }

    const values = calculateBsa(heightCm, weightKg);
    const selected = values[formula];
    const all = Object.values(values);
    const mean = all.reduce((sum, value) => sum + value, 0) / all.length;
    const spread = Math.max(...all) - Math.min(...all);
    const dose = optionalNonnegative(dosePerM2, 'Dose per m²');
    const absoluteGfr = optionalNonnegative(gfr, 'GFR / clearance');

    return {
      values,
      selectedFormula: formula,
      selectedBsa: selected,
      mean,
      spread,
      dosePerM2: dose,
      calculatedDose: dose === null ? null : selected * dose,
      gfr: absoluteGfr,
      indexedGfr: absoluteGfr === null ? null : absoluteGfr * (1.73 / selected),
    };
  }

  function format(value, digits = 4) {
    return Number(value).toFixed(digits);
  }

  function initBrowser() {
    const form = document.getElementById('calculator-form');
    if (!form) return;

    const heightInput = document.getElementById('height');
    const weightInput = document.getElementById('weight');
    const formulaInput = document.getElementById('formula');
    const doseInput = document.getElementById('dose');
    const gfrInput = document.getElementById('gfr');
    const primaryValue = document.getElementById('primary-value');
    const primaryFormula = document.getElementById('primary-formula');
    const meanValue = document.getElementById('mean-value');
    const spreadValue = document.getElementById('spread-value');
    const doseValue = document.getElementById('dose-value');
    const gfrValue = document.getElementById('gfr-value');
    const errorBox = document.getElementById('error-message');
    const comparisonBody = document.getElementById('comparison-body');
    const resetButton = document.getElementById('reset-button');
    const themeButton = document.getElementById('theme-toggle');

    function setError(message = '') {
      errorBox.textContent = message;
      errorBox.hidden = !message;
    }

    function render(result) {
      primaryValue.textContent = `${format(result.selectedBsa)} m²`;
      primaryFormula.textContent = DISPLAY_NAMES[result.selectedFormula];
      meanValue.textContent = `${format(result.mean)} m²`;
      spreadValue.textContent = `${format(result.spread)} m²`;
      doseValue.textContent = result.calculatedDose === null ? '—' : format(result.calculatedDose, 2);
      gfrValue.textContent = result.indexedGfr === null ? '—' : `${format(result.indexedGfr, 2)} mL/min/1.73 m²`;

      comparisonBody.replaceChildren();
      for (const [name, value] of Object.entries(result.values)) {
        const row = document.createElement('tr');
        if (name === result.selectedFormula) row.className = 'selected-row';
        const formulaCell = document.createElement('th');
        formulaCell.scope = 'row';
        formulaCell.textContent = DISPLAY_NAMES[name];
        const valueCell = document.createElement('td');
        valueCell.textContent = `${format(value)} m²`;
        row.append(formulaCell, valueCell);
        comparisonBody.append(row);
      }
    }

    function runCalculation() {
      try {
        const result = calculateRecord({
          heightCm: heightInput.value,
          weightKg: weightInput.value,
          formula: formulaInput.value,
          dosePerM2: doseInput.value,
          gfr: gfrInput.value,
        });
        setError();
        render(result);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Unable to calculate with these inputs.');
      }
    }

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      runCalculation();
    });

    resetButton.addEventListener('click', () => {
      form.reset();
      heightInput.value = '170';
      weightInput.value = '70';
      formulaInput.value = 'Mosteller';
      setError();
      runCalculation();
      heightInput.focus();
    });

    const savedTheme = localStorage.getItem('bsa-theme');
    if (savedTheme === 'dark') document.documentElement.dataset.theme = 'dark';

    function syncThemeLabel() {
      const dark = document.documentElement.dataset.theme === 'dark';
      themeButton.setAttribute('aria-pressed', String(dark));
      themeButton.textContent = dark ? 'Light' : 'Dark';
    }

    themeButton.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      localStorage.setItem('bsa-theme', next);
      syncThemeLabel();
    });

    syncThemeLabel();
    runCalculation();
  }

  const api = { FORMULAS, DISPLAY_NAMES, calculateBsa, calculateRecord };
  root.BSAApp = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initBrowser);
    else initBrowser();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
