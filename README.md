# Body Surface Area Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/bsa-mosteller-calculator/)

A browser and Python calculator for body surface area (BSA) using five established formulas: Mosteller, Du Bois & Du Bois, Haycock, Gehan–George, and Boyd.

## Features

- Responsive browser calculator with a light default theme and optional dark mode.
- Python CLI for single-record and CSV batch calculations.
- Formula comparison across five BSA equations.
- Optional arithmetic for a caller-supplied dose-per-m² value.
- Optional conversion of an absolute GFR/clearance value to a value indexed to 1.73 m².
- Validation for non-positive, non-finite, and invalid inputs.
- Automated Python and browser-side tests.

The application does **not** select a treatment regimen, infer a drug dose, impose a BSA cap, choose renal/hepatic dose adjustments, or replace a clinical protocol. Any dose, cap, adjustment factor, or threshold supplied to the software must come from an independently verified source.

## Browser use

Open `index.html` directly or serve the repository locally:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

The browser version performs all calculations locally. It has no external runtime dependency and does not upload entered measurements or results.

## Python CLI

Single record:

```bash
python cli.py single --height 178 --weight 82.5 --formula Mosteller
```

With optional arithmetic:

```bash
python cli.py single --height 178 --weight 82.5 --dose-per-m2 100 --gfr 78
```

Batch CSV processing:

```bash
python cli.py batch -i sample.csv -o results.csv
```

Required CSV fields are height and weight. Common variants such as `height_cm`, `height`, `weight_kg`, and `weight` are recognized. Optional columns include record identifier, age, sex, dose per m², absolute GFR/clearance, and preferred formula.

## Formulas

| Formula | Equation |
| --- | --- |
| Mosteller | `sqrt(height_cm × weight_kg / 3600)` |
| Du Bois & Du Bois | `0.007184 × height_cm^0.725 × weight_kg^0.425` |
| Haycock | `0.024265 × height_cm^0.3964 × weight_kg^0.5378` |
| Gehan–George | `0.0235 × height_cm^0.42246 × weight_kg^0.51456` |
| Boyd | `0.0003207 × height_cm^0.3 × weight_g^(0.7285 − 0.0188 × log10(weight_g))` |

The primary formula is user-selected. Formula choice should follow the applicable study method, protocol, or institutional standard.

## Testing

```bash
python -m pip install pytest
python -m pytest -q
node --check assets/app.js
node tests/web_smoke.cjs
```

The repository has no Python runtime dependency outside the standard library. The browser application is plain HTML, CSS, and JavaScript.

## Clinical-use boundaries

The software keeps equation evaluation separate from protocol-specific dosing decisions. In particular, the helper modules do not contain built-in drug doses, automatic pediatric dose caps, arbitrary organ-function dose multipliers, or a default carboplatin GFR cap.

References for the core BSA context:

- Mosteller RD. Simplified calculation of body-surface area. *N Engl J Med.* 1987;317(17):1098. PMID: 3657876.
- Griggs JJ, et al. Appropriate Systemic Therapy Dosing for Obese Adult Patients With Cancer: ASCO Guideline Update. *J Clin Oncol.* 2021;39(18):2037-2048. doi:10.1200/JCO.21.00471.

## Browser compatibility

The site uses standard browser APIs and is intended for current versions of Chrome, Edge, Firefox, and Safari. JavaScript is required.

## License

MIT. See [LICENSE](LICENSE).
