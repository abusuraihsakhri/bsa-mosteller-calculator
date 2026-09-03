# Body Surface Area (BSA) & Pharmacotherapy Dosing Calculator

> **Clinical Domain:** Clinical Pharmacokinetics, Medical Oncology & Nephrology  
> **Reference Standards:** Mosteller (1987 NEJM), Du Bois & Du Bois (1916), Haycock et al. (1978), Gehan & George (1970), Boyd (1935), ASCO Chemotherapy Dosing Guidelines, KDIGO CKD Staging.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Pytest-30%20passed-brightgreen.svg)
![Clinical Precision](https://img.shields.io/badge/Clinical-Precision%20Validated-success.svg)

</div>

---

## 📖 Overview

Body Surface Area (BSA, measured in $\text{m}^2$) is the cornerstone metric for calculating index-sensitive pharmacological dosages, particularly in cytotoxic chemotherapy regimens, pediatric drug administration, and physiological normalization of renal filtration (Glomerular Filtration Rate, GFR).

This repository provides a clinical-grade, zero-dependency Python implementation of all standard validated BSA formulations, cross-formula agreement analysis, oncologic dose calculation and rounding rules, and renal GFR normalization.

---

## 📐 Clinical Biostatistics & BSA Formulations

The tool calculates body surface area across the five primary historical and modern formulas:

### 1. Mosteller Formula (1987, *NEJM*)
The most widely adopted equation in clinical oncology and routine hospital practice due to simplicity and high numerical parity with Du Bois:
$$\text{BSA}_{\text{Mosteller}} = \sqrt{\frac{\text{Height (cm)} \times \text{Weight (kg)}}{3600}}$$

*Reference:* Mosteller RD. *Simplified calculation of body-surface area.* N Engl J Med. 1987 Oct 22;317(17):1098.

### 2. Du Bois & Du Bois Formula (1916)
The classical benchmark derived from nine direct plaster-mold measurements:
$$\text{BSA}_{\text{Du Bois}} = 0.007184 \times \text{Height (cm)}^{0.725} \times \text{Weight (kg)}^{0.425}$$

*Reference:* Du Bois D, Du Bois EF. *A formula to estimate the approximate surface area if height and weight be known.* Arch Intern Med. 1916;17(6):863–871.

### 3. Haycock et al. Formula (1978, *J Pediatr*)
Recommended in pediatric medicine, especially for premature neonates, infants, and children:
$$\text{BSA}_{\text{Haycock}} = 0.024265 \times \text{Height (cm)}^{0.3964} \times \text{Weight (kg)}^{0.5378}$$

*Reference:* Haycock GB, Schwartz GJ, Wisotsky DH. *Geometric method for measuring body surface area: A height-weight formula validated in infants, children, and adults.* J Pediatr. 1978;93(1):62–66.

### 4. Gehan & George Formula (1970, *Cancer Chemother Rep*)
Directly measured on 401 cancer and normal subjects using geometric approximations:
$$\text{BSA}_{\text{Gehan-George}} = 0.0235 \times \text{Height (cm)}^{0.42246} \times \text{Weight (kg)}^{0.51456}$$

*Reference:* Gehan EA, George SL. *Estimation of human body surface area from height and weight.* Cancer Chemother Rep. 1970;54(4):225–235.

### 5. Boyd Formula (1935)
Accounts for non-linear allometric mass scaling across extreme body mass values:
$$\text{BSA}_{\text{Boyd}} = 0.0003207 \times \text{Height (cm)}^{0.3} \times \text{Weight (g)}^{\left(0.7285 - 0.0188 \times \log_{10}(\text{Weight (g)})\right)}$$

*Reference:* Boyd E. *The Growth of the Surface Area of the Human Body.* University of Minnesota Press, 1935.

---

## 💊 Pharmacotherapy & Dosing Guidelines

### Chemotherapy Dosage Calculation
Cytotoxic agents (e.g., Doxorubicin, Paclitaxel, Fluorouracil) are dosed per square meter:
$$\text{Dose (mg)} = \text{BSA } (\text{m}^2) \times \text{Dose Target } (\text{mg/m}^2)$$

- **ASCO Dosing Guidelines:** Full, weight-based cytotoxic chemotherapy doses should be calculated using actual weight without arbitrary empirical dose rounding or capping at $2.0\,\text{m}^2$, except where explicitly mandated by specific trial protocols.
- **Dose Recalculation Threshold:** In accordance with standard oncology pharmacy rules, a change in patient BSA $\ge 10\%$ between cycles necessitates formal protocol re-calculation and dose re-consent.

### Glomerular Filtration Rate (GFR) Normalization
Standard CKD-EPI, MDRD, and pediatric renal criteria report indexed renal filtration normalized to an average young adult surface area of $1.73\,\text{m}^2$:
$$\text{Indexed GFR } (\text{mL/min/1.73 m}^2) = \text{Raw GFR } (\text{mL/min}) \times \frac{1.73}{\text{BSA } (\text{m}^2)}$$

To obtain the patient's absolute clearance (e.g., for Calvert formula carboplatin dosing: $\text{Dose} = \text{AUC} \times [\text{GFR} + 25]$):
$$\text{Absolute GFR } (\text{mL/min}) = \text{Indexed GFR } (\text{mL/min/1.73 m}^2) \times \frac{\text{BSA } (\text{m}^2)}{1.73}$$

---

## 💻 CLI Usage

The CLI (`cli.py` or `bsa.py`) provides single-patient calculation and high-throughput batch CSV processing.

### 1. Single Patient Calculation
```bash
python cli.py single --id PT-101 --height 178 --weight 82.5 --dose-per-m2 100 --gfr 78 --formula Mosteller
```
Output:
```text
Patient: PT-101
  Height: 178.0 cm | Weight: 82.5 kg

  BSA Results:
    Mosteller (1987):   2.0197 m²
    Du Bois (1916):     2.0064 m²
    Haycock (1978):     2.0310 m²
    Gehan-George (1970): 2.0319 m²
    Boyd (1935):        2.0344 m²

    Mean:          2.0247 m²
    Spread:        0.0280 m²
    Classification: Above normal range
    Preferred:     Mosteller = 2.0197 m²

  Chemotherapy Dosing:
    Dose per m²:   100.00
    Total dose:    201.97

  Renal Function / GFR Normalization:
    Raw GFR:       78.00 mL/min
    Indexed GFR:   66.81 mL/min/1.73 m²
```

### 2. Batch CSV Processing
Process cohort data with short (`-i`, `-o`) or long (`--input`, `--output`) flags:
```bash
python cli.py batch -i sample.csv -o results.csv
```

---

## 🐍 Python Quickstart

```python
from bsa import (
    bsa_mosteller,
    bsa_dubois,
    bsa_haycock,
    bsa_gehan_george,
    bsa_boyd,
    calculate_patient,
    normalize_gfr_to_bsa,
)

# Individual formula execution
ht, wt = 175.0, 72.0
bsa_val = bsa_mosteller(ht, wt)
print(f"Mosteller BSA: {bsa_val:.4f} m²")

# Comprehensive patient assessment
patient = calculate_patient(
    patient_id="PT-204",
    height_cm=165.0,
    weight_kg=60.0,
    age=52,
    sex="F",
    dose_per_m2=75.0,        # e.g., 75 mg/m²
    gfr_raw_ml_min=85.0,     # e.g., 85 mL/min
    preferred_formula="DuBois",
)

print(f"Primary BSA ({patient.preferred_formula}): {patient.primary_bsa():.4f} m²")
print(f"Calculated Chemo Dose: {patient.chemo_dose:.2f} mg")
print(f"Indexed GFR: {patient.gfr_indexed_1_73m2:.2f} mL/min/1.73 m²")
```

---

## 🧪 Testing & Verification

Run the test suite:
```bash
python -m pytest -p no:zarr -v
```

Execute the batch CLI verification:
```bash
python cli.py batch -i sample.csv -o out_smoke.csv
Remove-Item -Path "out_smoke.csv" -Force -ErrorAction SilentlyContinue
```

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
