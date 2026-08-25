# Body Surface Area (BSA) Calculator

Calculates body surface area using four published formulas, with chemotherapy dose calculation support.

## Formulas Implemented

| Formula | Equation |
|:---|:---|
| **Mosteller** | `BSA = sqrt((height_cm × weight_kg) / 3600)` |
| **Du Bois** | `BSA = 0.007184 × height_cm^0.725 × weight_kg^0.425` |
| **Haycock** | `BSA = 0.024265 × height_cm^0.3964 × weight_kg^0.5378` |
| **Gehan-George** | `BSA = 0.0235 × height_cm^0.42246 × weight_kg^0.51456` |

### Normal Adult BSA Range
- **1.6 – 2.0 m²** (typical adult)

### Chemotherapy Dosing
- `Total Dose = BSA (m²) × dose_per_m²`

## Usage

```bash
# Single patient
python bsa.py single --height 170 --weight 70

# With chemotherapy dosing
python bsa.py single --height 170 --weight 70 --dose-per-m2 100

# Preferred formula
python bsa.py single --height 170 --weight 70 --formula DuBois

# Batch CSV processing
python bsa.py batch --input patients.csv --output results.csv
```

## CSV Input Format

Required: `patient_id`, `height_cm`, `weight_kg`
Optional: `dose_per_m2`, `preferred_formula` (Mosteller/DuBois/Haycock/GehanGeorge)

## Requirements

Python 3.9+ (stdlib only)

## Disclaimer

For educational and clinical decision support only. BSA-based dosing is one factor in chemotherapy dosing decisions — always consult oncology protocols and pharmacist review.
