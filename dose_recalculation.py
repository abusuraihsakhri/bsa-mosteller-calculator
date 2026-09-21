#!/usr/bin/env python3
"""Protocol-agnostic helpers for BSA arithmetic.

This module deliberately does not encode drug-specific doses, mandatory BSA
caps, rounding rules, or treatment thresholds. Those decisions must come from a
verified regimen, prescribing information, trial protocol, or institutional
policy.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CycleRecord:
    cycle_number: int
    bsa_m2: float


def _positive(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


def _nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return value


def calculate_dose(
    bsa_m2: float,
    mg_per_m2: float,
    round_to_mg: Optional[float] = None,
    institutional_bsa_cap: Optional[float] = None,
) -> dict:
    """Apply caller-supplied BSA, dose density, optional cap, and rounding."""
    bsa = _positive("bsa_m2", bsa_m2)
    dose_density = _nonnegative("mg_per_m2", mg_per_m2)

    cap = None
    if institutional_bsa_cap is not None:
        cap = _positive("institutional_bsa_cap", institutional_bsa_cap)

    effective_bsa = min(bsa, cap) if cap is not None else bsa
    raw = effective_bsa * dose_density

    if round_to_mg is None:
        administered = raw
        rounding_rule = "none"
    else:
        increment = _positive("round_to_mg", round_to_mg)
        administered = round(raw / increment) * increment
        rounding_rule = f"nearest {increment:g} mg"

    return {
        "nominal_dose_mg": round(raw, 4),
        "administered_dose_mg": round(administered, 4),
        "effective_bsa_m2": round(effective_bsa, 4),
        "bsa_capped": cap is not None and bsa > cap,
        "rounding_rule": rounding_rule,
    }


def check_cycle_to_cycle_change(
    prev: CycleRecord,
    curr: CycleRecord,
    threshold_pct: Optional[float] = None,
) -> dict:
    """Report BSA change; optionally compare with a caller-supplied threshold."""
    previous = _positive("prev.bsa_m2", prev.bsa_m2)
    current = _positive("curr.bsa_m2", curr.bsa_m2)
    delta_pct = ((current - previous) / previous) * 100.0

    result = {
        "cycles": [prev.cycle_number, curr.cycle_number],
        "bsa_change_pct": round(delta_pct, 2),
        "direction": "increase" if delta_pct > 0.05 else "decrease" if delta_pct < -0.05 else "stable",
        "threshold_pct": None,
        "threshold_exceeded": None,
    }
    if threshold_pct is not None:
        threshold = _nonnegative("threshold_pct", threshold_pct)
        result["threshold_pct"] = threshold
        result["threshold_exceeded"] = abs(delta_pct) > threshold
    return result


def cockcroft_gault(age_years: float, weight_kg: float, serum_creatinine_mg_dl: float,
                    female: bool) -> float:
    """Return Cockcroft-Gault creatinine clearance using supplied inputs.

    The caller is responsible for selecting the appropriate weight convention
    and confirming whether Cockcroft-Gault is appropriate for the intended use.
    """
    age = _nonnegative("age_years", age_years)
    if age >= 140:
        raise ValueError("age_years must be less than 140 for this equation")
    weight = _positive("weight_kg", weight_kg)
    creatinine = _positive("serum_creatinine_mg_dl", serum_creatinine_mg_dl)
    factor = 0.85 if female else 1.0
    return round(((140.0 - age) * weight * factor) / (72.0 * creatinine), 1)


def calvert_carboplatin(target_auc: float, gfr_ml_min: float,
                        gfr_cap: Optional[float] = None) -> dict:
    """Evaluate the Calvert arithmetic with a caller-supplied GFR value.

    No GFR estimation method or cap is chosen automatically. If gfr_cap is
    supplied, it is treated as protocol input rather than a default standard.
    """
    auc = _positive("target_auc", target_auc)
    gfr = _nonnegative("gfr_ml_min", gfr_ml_min)
    cap = _positive("gfr_cap", gfr_cap) if gfr_cap is not None else None
    effective_gfr = min(gfr, cap) if cap is not None else gfr
    dose = auc * (effective_gfr + 25.0)
    return {
        "target_auc": auc,
        "reported_gfr": gfr,
        "gfr_cap": cap,
        "gfr_used": effective_gfr,
        "carboplatin_dose_mg": round(dose, 2),
        "formula": "Calvert: dose = AUC × (GFR + 25)",
    }
