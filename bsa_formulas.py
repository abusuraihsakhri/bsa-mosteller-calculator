#!/usr/bin/env python3
"""
Body surface area formulas (adult + pediatric) with cross-formula agreement.

Implements the five standard BSA models:
    Mosteller      sqrt(H * W / 3600)
    DuBois         0.007184 * H^0.725 * W^0.425
    Haycock        0.024265 * H^0.3964 * W^0.5378
    Gehan-George   0.0235    * H^0.42246 * W^0.51456
    Boyd           0.0003207 * H^0.3 * Wg^(0.7285 - 0.0188*log10(Wg))

Reports the mean, spread, and flags disagreement >2% (typical institutional
tolerance for dose-affecting BSA discrepancies).
"""

import math
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Anthropometrics:
    height_cm: float
    weight_kg: float

    def __post_init__(self):
        if self.height_cm <= 0 or self.weight_kg <= 0:
            raise ValueError("height and weight must be positive")


def bsa_mosteller(a: Anthropometrics) -> float:
    return math.sqrt(a.height_cm * a.weight_kg / 3600.0)


def bsa_dubois(a: Anthropometrics) -> float:
    return 0.007184 * (a.height_cm ** 0.725) * (a.weight_kg ** 0.425)


def bsa_haycock(a: Anthropometrics) -> float:
    return 0.024265 * (a.height_cm ** 0.3964) * (a.weight_kg ** 0.5378)


def bsa_gehan_george(a: Anthropometrics) -> float:
    return 0.0235 * (a.height_cm ** 0.42246) * (a.weight_kg ** 0.51456)


def bsa_boyd(a: Anthropometrics) -> float:
    wg = a.weight_kg * 1000.0
    exponent = 0.7285 - 0.0188 * math.log10(wg)
    return 0.0003207 * (a.height_cm ** 0.3) * (wg ** exponent)


FORMULAS: Dict[str, object] = {
    "Mosteller": bsa_mosteller,
    "DuBois": bsa_dubois,
    "Haycock": bsa_haycock,
    "GehanGeorge": bsa_gehan_george,
    "Boyd": bsa_boyd,
}


def compute_all_bsa(a: Anthropometrics, tolerance_pct: float = 2.0) -> Dict:
    values = {name: round(fn(a), 4) for name, fn in FORMULAS.items()}
    vals = list(values.values())
    mean = sum(vals) / len(vals)
    spread = max(vals) - min(vals)
    cv = (max(abs(v - mean) for v in vals) / mean) * 100.0
    pediatric = a.age_hint if hasattr(a, "age_hint") else False
    preferred = "Haycock" if (pediatric or a.weight_kg < 30) else "Mosteller"
    return {
        "values_m2": values,
        "mean_m2": round(mean, 4),
        "absolute_spread_m2": round(spread, 4),
        "max_deviation_pct": round(cv, 2),
        "agrees_within_tolerance": cv <= tolerance_pct,
        "preferred_formula": preferred,
    }


if __name__ == "__main__":
    subjects = [
        ("Average adult", Anthropometrics(170, 70)),
        ("Large adult", Anthropometrics(190, 110)),
        ("Small adult", Anthropometrics(152, 45)),
        ("Child ~8y", Anthropometrics(128, 27)),
    ]
    print(f"{'subject':14s} {'Mos':>6s} {'DuB':>6s} {'Hay':>6s} "
          f"{'G-G':>6s} {'Boyd':>6s}  dev%  agree")
    print("-" * 62)
    for name, anthro in subjects:
        r = compute_all_bsa(anthro)
        v = r["values_m2"]
        print(f"{name:14s} {v['Mosteller']:.3f} {v['DuBois']:.3f} "
              f"{v['Haycock']:.3f} {v['GehanGeorge']:.3f} {v['Boyd']:.3f}  "
              f"{r['max_deviation_pct']:>4.1f}  {r['agrees_within_tolerance']}  "
              f"[{r['preferred_formula']}]")
