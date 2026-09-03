#!/usr/bin/env python3
"""
Body Surface Area (BSA) Calculator
====================================

Implements multiple BSA formulas:
  - Mosteller:    BSA = sqrt((height_cm × weight_kg) / 3600)
  - Du Bois:      BSA = 0.007184 × height_cm^0.725 × weight_kg^0.425
  - Haycock:      BSA = 0.024265 × height_cm^0.3964 × weight_kg^0.5378
  - Gehan-George: BSA = 0.0235 × height_cm^0.42246 × weight_kg^0.51456

Includes chemotherapy dose calculation: dose = BSA × dose_per_m²

Stdlib only. Usage: python bsa.py --help
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# BSA Formulas
# ---------------------------------------------------------------------------


def bsa_mosteller(height_cm: float, weight_kg: float) -> float:
    """Mosteller formula (1987): BSA = sqrt((H * W) / 3600)."""
    return math.sqrt((height_cm * weight_kg) / 3600.0)


def bsa_dubois(height_cm: float, weight_kg: float) -> float:
    """Du Bois & Du Bois formula (1916): BSA = 0.007184 * H^0.725 * W^0.425."""
    return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)


def bsa_haycock(height_cm: float, weight_kg: float) -> float:
    """Haycock formula (1978): BSA = 0.024265 * H^0.3964 * W^0.5378."""
    return 0.024265 * (height_cm ** 0.3964) * (weight_kg ** 0.5378)


def bsa_gehan_george(height_cm: float, weight_kg: float) -> float:
    """Gehan & George formula (1970): BSA = 0.0235 * H^0.42246 * W^0.51456."""
    return 0.0235 * (height_cm ** 0.42246) * (weight_kg ** 0.51456)


def bsa_boyd(height_cm: float, weight_kg: float) -> float:
    """Boyd formula (1935): BSA = 0.0003207 * H^0.3 * (W_grams)^(0.7285 - 0.0188 * log10(W_grams))."""
    weight_grams = weight_kg * 1000.0
    exponent = 0.7285 - 0.0188 * math.log10(weight_grams)
    return 0.0003207 * (height_cm ** 0.3) * (weight_grams ** exponent)


FORMULAS = {
    "Mosteller": bsa_mosteller,
    "DuBois": bsa_dubois,
    "Haycock": bsa_haycock,
    "GehanGeorge": bsa_gehan_george,
    "Boyd": bsa_boyd,
}


def normalize_gfr_to_bsa(raw_gfr_ml_min: float, bsa_m2: float) -> float:
    """Normalize measured/calculated GFR to standard body surface area (1.73 m²).

    Formula: Normalized GFR (mL/min/1.73 m²) = Raw GFR (mL/min) * (1.73 / BSA)
    """
    if bsa_m2 <= 0:
        raise ValueError("BSA must be positive to normalize GFR.")
    return raw_gfr_ml_min * (1.73 / bsa_m2)


def denormalize_gfr_from_bsa(normalized_gfr: float, bsa_m2: float) -> float:
    """Convert normalized GFR (mL/min/1.73 m²) to absolute patient GFR (mL/min).

    Formula: Raw GFR (mL/min) = Normalized GFR * (BSA / 1.73)
    """
    return normalized_gfr * (bsa_m2 / 1.73)


# ---------------------------------------------------------------------------
# BSA classification
# ---------------------------------------------------------------------------

NORMAL_BSA_RANGE = (1.6, 2.0)  # m², typical adult


def classify_bsa(bsa_m2: float) -> str:
    """Classify BSA relative to normal adult range."""
    if bsa_m2 < NORMAL_BSA_RANGE[0]:
        return "Below normal range"
    elif bsa_m2 > NORMAL_BSA_RANGE[1]:
        return "Above normal range"
    else:
        return "Within normal range"


# ---------------------------------------------------------------------------
# Chemotherapy dosing
# ---------------------------------------------------------------------------


def chemotherapy_dose(bsa_m2: float, dose_per_m2: float) -> float:
    """Calculate chemotherapy dose: dose = BSA × dose_per_m².

    Args:
        bsa_m2: Body surface area in m²
        dose_per_m2: Drug dose per m² (e.g., mg/m²)

    Returns:
        Total dose in same units as dose_per_m2
    """
    return bsa_m2 * dose_per_m2


# ---------------------------------------------------------------------------
# Patient result
# ---------------------------------------------------------------------------


@dataclass
class BSAResult:
    patient_id: str
    height_cm: float
    weight_kg: float
    age: Optional[float] = None
    sex: Optional[str] = None
    bsa_mosteller: Optional[float] = None
    bsa_dubois: Optional[float] = None
    bsa_haycock: Optional[float] = None
    bsa_gehan_george: Optional[float] = None
    bsa_boyd: Optional[float] = None
    bsa_mean: Optional[float] = None
    bsa_spread: Optional[float] = None
    bsa_classification: Optional[str] = None
    preferred_formula: str = "Mosteller"
    chemo_dose: Optional[float] = None
    chemo_dose_per_m2: Optional[float] = None
    gfr_raw_ml_min: Optional[float] = None
    gfr_indexed_1_73m2: Optional[float] = None
    warnings: list[str] = field(default_factory=list)

    def primary_bsa(self) -> Optional[float]:
        """Return the BSA from the preferred formula."""
        name = self.preferred_formula
        if name == "Mosteller":
            return self.bsa_mosteller
        elif name == "DuBois":
            return self.bsa_dubois
        elif name == "Haycock":
            return self.bsa_haycock
        elif name == "GehanGeorge":
            return self.bsa_gehan_george
        elif name == "Boyd":
            return self.bsa_boyd
        return self.bsa_mosteller


def calculate_patient(
    patient_id: str,
    height_cm: float,
    weight_kg: float,
    age: Optional[float] = None,
    sex: Optional[str] = None,
    dose_per_m2: Optional[float] = None,
    gfr_raw_ml_min: Optional[float] = None,
    preferred_formula: str = "Mosteller",
) -> BSAResult:
    """Calculate BSA using all standard formulas for one patient."""
    warnings: list[str] = []

    if height_cm <= 0:
        warnings.append(f"Height {height_cm} must be positive.")
    if weight_kg <= 0:
        warnings.append(f"Weight {weight_kg} must be positive.")

    result = BSAResult(
        patient_id=patient_id,
        height_cm=height_cm,
        weight_kg=weight_kg,
        age=age,
        sex=sex,
        preferred_formula=preferred_formula,
        warnings=warnings,
    )

    if height_cm <= 0 or weight_kg <= 0:
        return result

    result.bsa_mosteller = round(bsa_mosteller(height_cm, weight_kg), 4)
    result.bsa_dubois = round(bsa_dubois(height_cm, weight_kg), 4)
    result.bsa_haycock = round(bsa_haycock(height_cm, weight_kg), 4)
    result.bsa_gehan_george = round(bsa_gehan_george(height_cm, weight_kg), 4)
    result.bsa_boyd = round(bsa_boyd(height_cm, weight_kg), 4)

    all_bsa = [
        result.bsa_mosteller,
        result.bsa_dubois,
        result.bsa_haycock,
        result.bsa_gehan_george,
        result.bsa_boyd,
    ]
    result.bsa_mean = round(sum(all_bsa) / len(all_bsa), 4)
    result.bsa_spread = round(max(all_bsa) - min(all_bsa), 4)

    primary = result.primary_bsa()
    if primary is not None:
        result.bsa_classification = classify_bsa(primary)

    if dose_per_m2 is not None and primary is not None:
        result.chemo_dose_per_m2 = dose_per_m2
        result.chemo_dose = round(chemotherapy_dose(primary, dose_per_m2), 2)

    if gfr_raw_ml_min is not None and primary is not None and primary > 0:
        result.gfr_raw_ml_min = gfr_raw_ml_min
        result.gfr_indexed_1_73m2 = round(normalize_gfr_to_bsa(gfr_raw_ml_min, primary), 2)

    return result


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

CSV_INPUT_FIELDS = [
    "patient_id", "height_cm", "weight_kg", "dose_per_m2", "preferred_formula",
]

CSV_OUTPUT_FIELDS = [
    "patient_id",
    "age",
    "sex",
    "height_cm",
    "weight_kg",
    "bsa_mosteller",
    "bsa_dubois",
    "bsa_haycock",
    "bsa_gehan_george",
    "bsa_boyd",
    "bsa_mean",
    "bsa_spread",
    "bsa_classification",
    "preferred_formula",
    "primary_bsa",
    "chemo_dose_per_m2",
    "chemo_dose",
    "gfr_raw_ml_min",
    "gfr_indexed_1_73m2",
    "warnings",
]


def _match_column(fieldnames: list[str], candidates: list[str]) -> Optional[str]:
    """Find a column in fieldnames matching any candidate (case-insensitive, normalized)."""
    norm_map = {f.strip().lower().replace(" ", "_").replace("-", "_"): f for f in fieldnames}
    for c in candidates:
        key = c.lower().replace(" ", "_").replace("-", "_")
        if key in norm_map:
            return norm_map[key]
    return None


def process_csv(input_path: str, output_path: str) -> list[BSAResult]:
    """Read patient rows from CSV, compute BSA across formulas, write results CSV."""
    results: list[BSAResult] = []

    with open(input_path, "r", newline="", encoding="utf-8-sig") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []

        col_id = _match_column(fieldnames, ["patient_id", "patientid", "id", "mrn", "patient"])
        col_height = _match_column(fieldnames, ["height_cm", "height", "ht_cm", "ht"])
        col_weight = _match_column(fieldnames, ["weight_kg", "weight", "wt_kg", "wt"])
        col_age = _match_column(fieldnames, ["age", "age_years", "age_yrs"])
        col_sex = _match_column(fieldnames, ["sex", "gender"])
        col_dose = _match_column(fieldnames, ["dose_per_m2", "chemo_dose_per_m2", "dose_mg_m2", "chemotherapy_dose_per_m2"])
        col_gfr = _match_column(fieldnames, ["gfr_raw_ml_min", "gfr", "crcl", "raw_gfr", "gfr_ml_min"])
        col_pref = _match_column(fieldnames, ["preferred_formula", "formula"])

        if not col_height or not col_weight:
            raise ValueError(f"Input CSV is missing required height/weight columns. Found: {fieldnames}")

        for row_num, row in enumerate(reader, start=2):
            patient_id = (row.get(col_id) if col_id else "").strip() if col_id and row.get(col_id) else f"row{row_num}"
            row_warnings: list[str] = []

            try:
                height_cm = float(row[col_height])
                weight_kg = float(row[col_weight])
            except (KeyError, ValueError, TypeError) as exc:
                row_warnings.append(f"Could not parse required height/weight fields: {exc}")
                results.append(BSAResult(patient_id=patient_id, height_cm=0, weight_kg=0, warnings=row_warnings))
                continue

            age_val = None
            if col_age and row.get(col_age):
                try:
                    age_val = float(row[col_age].strip())
                except ValueError:
                    pass

            sex_val = row.get(col_sex, "").strip() if col_sex and row.get(col_sex) else None

            dose_per_m2 = None
            if col_dose and row.get(col_dose):
                d_str = row[col_dose].strip()
                if d_str:
                    try:
                        dose_per_m2 = float(d_str)
                    except ValueError:
                        row_warnings.append(f"Invalid dose_per_m2 value: {d_str}")

            gfr_raw = None
            if col_gfr and row.get(col_gfr):
                g_str = row[col_gfr].strip()
                if g_str:
                    try:
                        gfr_raw = float(g_str)
                    except ValueError:
                        row_warnings.append(f"Invalid GFR value: {g_str}")

            preferred = "Mosteller"
            if col_pref and row.get(col_pref):
                p_str = row[col_pref].strip()
                if p_str:
                    preferred = p_str

            result = calculate_patient(
                patient_id=patient_id,
                height_cm=height_cm,
                weight_kg=weight_kg,
                age=age_val,
                sex=sex_val,
                dose_per_m2=dose_per_m2,
                gfr_raw_ml_min=gfr_raw,
                preferred_formula=preferred,
            )
            result.warnings = row_warnings + result.warnings
            results.append(result)

    with open(output_path, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=CSV_OUTPUT_FIELDS)
        writer.writeheader()
        for r in results:
            primary = r.primary_bsa()
            writer.writerow({
                "patient_id": r.patient_id,
                "age": _fmt(r.age, decimals=1) if r.age is not None else "",
                "sex": r.sex or "",
                "height_cm": r.height_cm,
                "weight_kg": r.weight_kg,
                "bsa_mosteller": _fmt(r.bsa_mosteller),
                "bsa_dubois": _fmt(r.bsa_dubois),
                "bsa_haycock": _fmt(r.bsa_haycock),
                "bsa_gehan_george": _fmt(r.bsa_gehan_george),
                "bsa_boyd": _fmt(r.bsa_boyd),
                "bsa_mean": _fmt(r.bsa_mean),
                "bsa_spread": _fmt(r.bsa_spread),
                "bsa_classification": r.bsa_classification or "",
                "preferred_formula": r.preferred_formula,
                "primary_bsa": _fmt(primary),
                "chemo_dose_per_m2": _fmt(r.chemo_dose_per_m2, decimals=2),
                "chemo_dose": _fmt(r.chemo_dose, decimals=2),
                "gfr_raw_ml_min": _fmt(r.gfr_raw_ml_min, decimals=2),
                "gfr_indexed_1_73m2": _fmt(r.gfr_indexed_1_73m2, decimals=2),
                "warnings": " | ".join(r.warnings),
            })

    return results


def _fmt(value: Optional[float], decimals: int = 4) -> str:
    return "" if value is None else f"{value:.{decimals}f}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bsa",
        description="Body Surface Area Calculator (Mosteller, Du Bois, Haycock, Gehan-George, Boyd).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Calculate BSA for one patient")
    single.add_argument("--id", dest="patient_id", default="patient", help="Patient identifier")
    single.add_argument("--height", type=float, required=True, help="Height in cm")
    single.add_argument("--weight", type=float, required=True, help="Weight in kg")
    single.add_argument("--age", type=float, default=None, help="Patient age in years")
    single.add_argument("--sex", default=None, help="Patient biological sex")
    single.add_argument("--dose-per-m2", type=float, default=None, help="Chemo dose per m² (e.g., mg/m²)")
    single.add_argument("--gfr", type=float, default=None, help="Raw GFR in mL/min for 1.73m² normalization")
    single.add_argument("--formula", default="Mosteller",
                        choices=["Mosteller", "DuBois", "Haycock", "GehanGeorge", "Boyd"],
                        help="Preferred BSA formula (default: Mosteller)")

    batch = subparsers.add_parser("batch", help="Batch CSV processing")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", required=True, help="Output CSV path")

    return parser


def _print_single_result(result: BSAResult) -> None:
    print(f"Patient: {result.patient_id}")
    demographics = []
    if result.age is not None:
        demographics.append(f"Age: {result.age:.0f}y")
    if result.sex is not None:
        demographics.append(f"Sex: {result.sex}")
    demographics.append(f"Height: {result.height_cm:.1f} cm")
    demographics.append(f"Weight: {result.weight_kg:.1f} kg")
    print(f"  {' | '.join(demographics)}")

    print(f"\n  BSA Results:")
    print(f"    Mosteller (1987):   {result.bsa_mosteller:.4f} m²")
    print(f"    Du Bois (1916):     {result.bsa_dubois:.4f} m²")
    print(f"    Haycock (1978):     {result.bsa_haycock:.4f} m²")
    print(f"    Gehan-George (1970): {result.bsa_gehan_george:.4f} m²")
    if result.bsa_boyd is not None:
        print(f"    Boyd (1935):        {result.bsa_boyd:.4f} m²")
    print(f"\n    Mean:          {result.bsa_mean:.4f} m²")
    print(f"    Spread:        {result.bsa_spread:.4f} m²")
    print(f"    Classification: {result.bsa_classification}")
    print(f"    Preferred:     {result.preferred_formula} = {result.primary_bsa():.4f} m²")

    if result.chemo_dose is not None:
        print(f"\n  Chemotherapy Dosing:")
        print(f"    Dose per m²:   {result.chemo_dose_per_m2:.2f}")
        print(f"    Total dose:    {result.chemo_dose:.2f}")

    if result.gfr_indexed_1_73m2 is not None:
        print(f"\n  Renal Function / GFR Normalization:")
        print(f"    Raw GFR:       {result.gfr_raw_ml_min:.2f} mL/min")
        print(f"    Indexed GFR:   {result.gfr_indexed_1_73m2:.2f} mL/min/1.73 m²")

    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    - {w}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_patient(
            patient_id=args.patient_id,
            height_cm=args.height,
            weight_kg=args.weight,
            age=args.age,
            sex=args.sex,
            dose_per_m2=args.dose_per_m2,
            gfr_raw_ml_min=args.gfr,
            preferred_formula=args.formula,
        )
        _print_single_result(result)
        return 0

    if args.command == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} patients -> {args.output}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
