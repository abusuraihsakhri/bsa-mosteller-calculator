#!/usr/bin/env python3
"""
BSA-based chemotherapy dosing engine.

Real oncology pharmacy rules:
  - Dose = BSA x mg/m2, rounded to the nearest 5 mg unless vial rounding applies
  - Protocol re-consent/re-calculation required when BSA changes >10% between cycles
  - Institutional BSA caps (e.g. cap at 2.0 m2) truncate the effective BSA used
  - Carboplatin uses the Calvert formula: Dose(mg) = AUC x (GFR + 25), with GFR
    commonly capped at 125 mL/min; GFR estimated by Cockcroft-Gault
"""

from dataclasses import dataclass
from typing import Optional

from bsa_formulas import Anthropometrics, bsa_mosteller


@dataclass
class CycleRecord:
    cycle_number: int
    bsa_m2: float


def calculate_dose(bsa_m2: float, mg_per_m2: float,
                   round_to_mg: float = 5.0,
                   institutional_bsa_cap: Optional[float] = None) -> dict:
    effective_bsa = min(bsa_m2, institutional_bsa_cap) if institutional_bsa_cap else bsa_m2
    raw = effective_bsa * mg_per_m2
    rounded = round(raw / round_to_mg) * round_to_mg
    capped = institutional_bsa_cap is not None and bsa_m2 > institutional_bsa_cap
    return {
        "nominal_dose_mg": round(raw, 1),
        "administered_dose_mg": rounded,
        "effective_bsa_m2": round(effective_bsa, 3),
        "bsa_capped": capped,
        "rounding_rule": f"nearest {round_to_mg:g} mg",
    }


def check_cycle_to_cycle_change(prev: CycleRecord, curr: CycleRecord,
                                threshold_pct: float = 10.0) -> dict:
    delta_pct = ((curr.bsa_m2 - prev.bsa_m2) / prev.bsa_m2) * 100.0
    requires_review = abs(delta_pct) > threshold_pct
    direction = "increase" if delta_pct > 0 else "decrease"
    return {
        "cycles": [prev.cycle_number, curr.cycle_number],
        "bsa_change_pct": round(delta_pct, 2),
        "direction": direction if abs(delta_pct) > 0.05 else "stable",
        "protocol_action": ("DOSE RECALCULATION REQUIRED (>%.0f%% change)" % threshold_pct
                            if requires_review else "continue protocol dose"),
    }


def cockcroft_gault(age_years: float, weight_kg: float, serum_creatinine_mg_dl: float,
                    female: bool) -> float:
    factor = 0.85 if female else 1.0
    crcl = ((140.0 - age_years) * weight_kg * factor) / \
           (72.0 * serum_creatinine_mg_dl)
    return round(crcl, 1)


def calvert_carboplatin(target_auc: float, gfr_ml_min: float,
                        gfr_cap: float = 125.0) -> dict:
    effective_gfr = min(gfr_ml_min, gfr_cap)
    dose = target_auc * (effective_gfr + 25.0)
    return {
        "target_auc": target_auc,
        "reported_gfr": gfr_ml_min,
        "capped_gfr_used": effective_gfr,
        "carboplatin_dose_mg": round(dose),
        "formula": "Calvert: Dose = AUC x (GFR + 25)",
    }


if __name__ == "__main__":
    anthro = Anthropometrics(168, 78)
    bsa_now = bsa_mosteller(anthro)

    d = calculate_dose(bsa_now, mg_per_m2=75, institutional_bsa_cap=2.0)
    print(f"Cyclophosphamide 75 mg/m2 at BSA {d['effective_bsa_m2']} m2 -> "
          f"{d['administered_dose_mg']} mg (capped={d['bsa_capped']})")

    c1 = CycleRecord(1, 2.30)
    c2 = CycleRecord(2, round(bsa_now, 3))
    chk = check_cycle_to_cycle_change(c1, c2)
    print(f"\nCycle 1->2 BSA {chk['bsa_change_pct']:+.1f}% ({chk['direction']})")
    print(f"action: {chk['protocol_action']}")

    gfr = cockcroft_gault(age_years=64, weight_kg=78, serum_creatinine_mg_dl=1.1,
                          female=False)
    carb = calvert_carboplatin(target_auc=5.0, gfr_ml_min=gfr)
    print(f"\nCockcroft-Gault CrCl = {gfr} mL/min")
    print(f"Calvert AUC 5 -> {carb['carboplatin_dose_mg']} mg carboplatin "
          f"(GFR used {carb['capped_gfr_used']})")

    big = cockcroft_gault(35, 120, 0.7, False)
    print(f"AUC 6 with CrCl {big}: dose = "
          f"{calvert_carboplatin(6.0, big)['carboplatin_dose_mg']} mg "
          f"(GFR capped at 125)")
