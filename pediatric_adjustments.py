#!/usr/bin/env python3
"""
Pediatric BSA Adjustments for BSA Mosteller Calculator.
Pediatric-specific BSA calculations, dose capping, and growth-based dosing.
"""

from typing import Dict, Any, Optional


def calculate_bsa_pediatric(weight_kg: float, height_cm: float, age_years: float,
                             drug_name: Optional[str] = None) -> Dict[str, Any]:
    """Calculate BSA with pediatric-specific adjustments."""
    mosteller = (weight_kg * height_cm / 3600.0) ** 0.5
    fujimoto = 0.007184 * (weight_kg ** 0.425) * (height_cm ** 0.725)
    haycock = 0.024265 * (weight_kg ** 0.5378) * (height_cm ** 0.3964)

    if age_years < 0.25:
        neonatal_adjustment = "Neonatal dosing protocol recommended. Consult neonatology."
    elif age_years < 2:
        neonatal_adjustment = "Infant dosing. Use weight-based rather than BSA-based where possible."
    elif age_years < 12:
        neonatal_adjustment = "Pediatric BSA. Dose capping may apply."
    else:
        neonatal_adjustment = "Adolescent. Adult BSA formulas applicable."

    dose_caps = {}
    if drug_name and age_years < 18:
        adult_max = {"methotrexate": 1000, "carboplatin": 750, "doxorubicin": 120}
        if drug_name in adult_max:
            pediatric_cap = adult_max[drug_name] * (age_years / 18.0)
            dose_caps[drug_name] = round(pediatric_cap, 0)

    return {
        "bsa_mosteller": round(mosteller, 2),
        "bsa_fujimoto": round(fujimoto, 2),
        "bsa_haycock": round(haycock, 2),
        "bsa_consensus": round((mosteller + fujimoto + haycock) / 3.0, 2),
        "age_category": neonatal_adjustment,
        "dose_caps": dose_caps,
        "age_years": age_years,
    }


class BsaPediatricAgent:
    """Sub-agent for pediatric BSA adjustments."""

    def __init__(self):
        self.agent_name = "BsaPediatricAgent"

    def evaluate(self, weight_kg: float, height_cm: float, age_years: float,
                 drug_name: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate pediatric BSA."""
        result = calculate_bsa_pediatric(weight_kg, height_cm, age_years, drug_name)
        alerts = []

        if age_years < 0.25:
            alerts.append({
                "type": "NEONATAL_DOSING", "severity": "WARNING",
                "message": "Neonatal patient. BSA-based dosing may be unreliable.",
                "recommendation": "Use weight-based dosing. Consult neonatal pharmacy."
            })

        if result["bsa_mosteller"] > 2.0 and age_years < 12:
            alerts.append({
                "type": "LARGE_CHILD", "severity": "ADVISORY",
                "message": f"BSA {result['bsa_mosteller']:.2f} m2 unusually high for age {age_years:.0f}.",
                "recommendation": "Verify height/weight measurements. Consider obesity assessment."
            })

        return {"pediatric_result": result, "alerts": alerts}
