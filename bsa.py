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
    """Mosteller formula: BSA = sqrt((H × W) / 3600)."""
    return math.sqrt((height_cm * weight_kg) / 3600.0)


def bsa_dubois(height_cm: float, weight_kg: float) -> float:
    """Du Bois formula: BSA = 0.007184 × H^0.725 × W^0.425."""
    return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)


def bsa_haycock(height_cm: float, weight_kg: float) -> float:
    """Haycock formula: BSA = 0.024265 × H^0.3964 × W^0.5378."""
    return 0.024265 * (height_cm ** 0.3964) * (weight_kg ** 0.5378)


def bsa_gehan_george(height_cm: float, weight_kg: float) -> float:
    """Gehan-George formula: BSA = 0.0235 × H^0.42246 × W^0.51456."""
    return 0.0235 * (height_cm ** 0.42246) * (weight_kg ** 0.51456)


FORMULAS = {
    "Mosteller": bsa_mosteller,
    "DuBois": bsa_dubois,
    "Haycock": bsa_haycock,
    "GehanGeorge": bsa_gehan_george,
}


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
    bsa_mosteller: Optional[float] = None
    bsa_dubois: Optional[float] = None
    bsa_haycock: Optional[float] = None
    bsa_gehan_george: Optional[float] = None
    bsa_mean: Optional[float] = None
    bsa_spread: Optional[float] = None
    bsa_classification: Optional[str] = None
    preferred_formula: str = "Mosteller"
    chemo_dose: Optional[float] = None
    chemo_dose_per_m2: Optional[float] = None
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
        return self.bsa_mosteller


def calculate_patient(
    patient_id: str,
    height_cm: float,
    weight_kg: float,
    dose_per_m2: Optional[float] = None,
    preferred_formula: str = "Mosteller",
) -> BSAResult:
    """Calculate BSA using all formulas for one patient."""
    warnings: list[str] = []

    if height_cm <= 0:
        warnings.append(f"Height {height_cm} must be positive.")
    if weight_kg <= 0:
        warnings.append(f"Weight {weight_kg} must be positive.")

    result = BSAResult(
        patient_id=patient_id, height_cm=height_cm, weight_kg=weight_kg,
        preferred_formula=preferred_formula, warnings=warnings,
    )

    if height_cm <= 0 or weight_kg <= 0:
        return result

    result.bsa_mosteller = round(bsa_mosteller(height_cm, weight_kg), 4)
    result.bsa_dubois = round(bsa_dubois(height_cm, weight_kg), 4)
    result.bsa_haycock = round(bsa_haycock(height_cm, weight_kg), 4)
    result.bsa_gehan_george = round(bsa_gehan_george(height_cm, weight_kg), 4)

    all_bsa = [result.bsa_mosteller, result.bsa_dubois, result.bsa_haycock, result.bsa_gehan_george]
    result.bsa_mean = round(sum(all_bsa) / len(all_bsa), 4)
    result.bsa_spread = round(max(all_bsa) - min(all_bsa), 4)

    primary = result.primary_bsa()
    if primary is not None:
        result.bsa_classification = classify_bsa(primary)

    if dose_per_m2 is not None and primary is not None:
        result.chemo_dose_per_m2 = dose_per_m2
        result.chemo_dose = round(chemotherapy_dose(primary, dose_per_m2), 2)

    return result


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

CSV_INPUT_FIELDS = [
    "patient_id", "height_cm", "weight_kg", "dose_per_m2", "preferred_formula",
]

CSV_OUTPUT_FIELDS = [
    "patient_id", "height_cm", "weight_kg",
    "bsa_mosteller", "bsa_dubois", "bsa_haycock", "bsa_gehan_george",
    "bsa_mean", "bsa_spread", "bsa_classification", "preferred_formula",
    "primary_bsa", "chemo_dose_per_m2", "chemo_dose", "warnings",
]


def process_csv(input_path: str, output_path: str) -> list[BSAResult]:
    """Read patient rows from CSV, compute BSA for each, write results CSV."""
    results: list[BSAResult] = []

    with open(input_path, "r", newline="", encoding="utf-8-sig") as f_in:
        reader = csv.DictReader(f_in)
        missing = set(["patient_id", "height_cm", "weight_kg"]) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {sorted(missing)}")

        for row_num, row in enumerate(reader, start=2):
            patient_id = (row.get("patient_id") or "").strip() or f"row{row_num}"
            row_warnings: list[str] = []

            try:
                height_cm = float(row["height_cm"])
                weight_kg = float(row["weight_kg"])
            except (KeyError, ValueError, TypeError) as exc:
                row_warnings.append(f"Could not parse required fields: {exc}")
                results.append(BSAResult(patient_id=patient_id, height_cm=0, weight_kg=0, warnings=row_warnings))
                continue

            dose_str = (row.get("dose_per_m2") or "").strip()
            dose_per_m2 = float(dose_str) if dose_str else None
            preferred = (row.get("preferred_formula") or "Mosteller").strip()

            result = calculate_patient(
                patient_id=patient_id, height_cm=height_cm, weight_kg=weight_kg,
                dose_per_m2=dose_per_m2, preferred_formula=preferred,
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
                "height_cm": r.height_cm,
                "weight_kg": r.weight_kg,
                "bsa_mosteller": _fmt(r.bsa_mosteller),
                "bsa_dubois": _fmt(r.bsa_dubois),
                "bsa_haycock": _fmt(r.bsa_haycock),
                "bsa_gehan_george": _fmt(r.bsa_gehan_george),
                "bsa_mean": _fmt(r.bsa_mean),
                "bsa_spread": _fmt(r.bsa_spread),
                "bsa_classification": r.bsa_classification or "",
                "preferred_formula": r.preferred_formula,
                "primary_bsa": _fmt(primary),
                "chemo_dose_per_m2": _fmt(r.chemo_dose_per_m2),
                "chemo_dose": _fmt(r.chemo_dose),
                "warnings": " | ".join(r.warnings),
            })

    return results


def _fmt(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.4f}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bsa",
        description="Body Surface Area Calculator (Mosteller, Du Bois, Haycock, Gehan-George).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Calculate BSA for one patient")
    single.add_argument("--id", dest="patient_id", default="patient", help="Patient identifier")
    single.add_argument("--height", type=float, required=True, help="Height in cm")
    single.add_argument("--weight", type=float, required=True, help="Weight in kg")
    single.add_argument("--dose-per-m2", type=float, default=None, help="Chemo dose per m² (e.g., mg/m²)")
    single.add_argument("--formula", default="Mosteller",
                        choices=["Mosteller", "DuBois", "Haycock", "GehanGeorge"],
                        help="Preferred BSA formula (default: Mosteller)")

    batch = subparsers.add_parser("batch", help="Batch CSV processing")
    batch.add_argument("--input", required=True, help="Input CSV path")
    batch.add_argument("--output", required=True, help="Output CSV path")

    return parser


def _print_single_result(result: BSAResult) -> None:
    print(f"Patient: {result.patient_id}")
    print(f"  Height: {result.height_cm:.1f} cm  Weight: {result.weight_kg:.1f} kg")
    print(f"\n  BSA Results:")
    print(f"    Mosteller:     {result.bsa_mosteller:.4f} m²")
    print(f"    Du Bois:       {result.bsa_dubois:.4f} m²")
    print(f"    Haycock:       {result.bsa_haycock:.4f} m²")
    print(f"    Gehan-George:  {result.bsa_gehan_george:.4f} m²")
    print(f"\n    Mean:          {result.bsa_mean:.4f} m²")
    print(f"    Spread:        {result.bsa_spread:.4f} m²")
    print(f"    Classification: {result.bsa_classification}")
    print(f"    Preferred:     {result.preferred_formula} = {result.primary_bsa():.4f} m²")

    if result.chemo_dose is not None:
        print(f"\n  Chemotherapy Dosing:")
        print(f"    Dose per m²:   {result.chemo_dose_per_m2:.2f}")
        print(f"    Total dose:    {result.chemo_dose:.2f}")

    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    - {w}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "single":
        result = calculate_patient(
            patient_id=args.patient_id, height_cm=args.height, weight_kg=args.weight,
            dose_per_m2=args.dose_per_m2, preferred_formula=args.formula,
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
