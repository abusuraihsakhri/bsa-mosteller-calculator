#!/usr/bin/env python3
"""
BSA Pharmacokinetic Adjustments for BSA Mosteller Calculator.
Adjusts drug dosing based on BSA, renal function, and hepatic status.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DrugProfile:
    """PK profile for a drug requiring BSA-based dosing."""
    name: str
    base_dose_mg_per_m2: float
    renal_adjustment: bool
    hepatic_adjustment: bool
    max_dose_mg: float
    narrow_therapeutic: bool


PK_DRUGS = {
    "methotrexate": DrugProfile("Methotrexate", 40.0, True, False, 1000.0, True),
    "5fluorouracil": DrugProfile("5-Fluorouracil", 500.0, False, True, 4000.0, True),
    "carboplatin": DrugProfile("Carboplatin", 300.0, True, False, 750.0, True),
    "docetaxel": DrugProfile("Docetaxel", 75.0, False, True, 150.0, True),
    "bleomycin": DrugProfile("Bleomycin", 10.0, True, False, 30.0, True),
    "cyclophosphamide": DrugProfile("Cyclophosphamide", 600.0, False, False, 2000.0, False),
    "doxorubicin": DrugProfile("Doxorubicin", 60.0, False, True, 120.0, True),
    "paclitaxel": DrugProfile("Paclitaxel", 175.0, False, False, 350.0, False),
}


def calculate_bsa_pharmacokinetic_adjustment(drug_name: str, bsa: float,
                                              crcl: float = 120.0,
                                              alt: float = 40.0) -> Dict[str, Any]:
    """Calculate BSA-based drug dose with PK adjustments."""
    drug = PK_DRUGS.get(drug_name)
    if not drug:
        return {"error": f"Unknown drug: {drug_name}. Available: {list(PK_DRUGS.keys())}"}

    base_dose = drug.base_dose_mg_per_m2 * bsa
    adjustment_factors = []
    total_factor = 1.0

    if drug.renal_adjustment and crcl < 60:
        rf = max(0.25, crcl / 120.0)
        total_factor *= rf
        adjustment_factors.append(f"Renal (CrCl {crcl:.0f}): x{rf:.2f}")

    if drug.hepatic_adjustment and alt > 120:
        hf = max(0.5, 1.0 - ((alt - 120) / 200))
        total_factor *= hf
        adjustment_factors.append(f"Hepatic (ALT {alt:.0f}): x{hf:.2f}")

    adjusted_dose = min(base_dose * total_factor, drug.max_dose_mg)

    monitoring = ["CBC before each cycle"]
    if drug.renal_adjustment:
        monitoring.append("BUN/Cr before each cycle")
    if drug.hepatic_adjustment:
        monitoring.append("LFTs weekly")
    if drug.narrow_therapeutic:
        monitoring.append("Drug level monitoring if available")

    return {
        "drug": drug.name,
        "bsa_m2": round(bsa, 2),
        "base_dose_mg": round(base_dose, 1),
        "adjustment_factors": adjustment_factors,
        "total_factor": round(total_factor, 3),
        "adjusted_dose_mg": round(adjusted_dose, 1),
        "max_dose_mg": drug.max_dose_mg,
        "monitoring": monitoring,
    }


class BsaPharmacokineticAgent:
    """Sub-agent for BSA pharmacokinetic adjustments."""

    def __init__(self):
        self.agent_name = "BsaPharmacokineticAgent"

    def evaluate(self, drug_name: str, bsa: float, crcl: float = 120.0,
                 alt: float = 40.0) -> Dict[str, Any]:
        """Evaluate BSA-based drug dosing."""
        result = calculate_bsa_pharmacokinetic_adjustment(drug_name, bsa, crcl, alt)
        alerts = []

        if "error" in result:
            alerts.append({
                "type": "INVALID_DRUG", "severity": "ERROR",
                "message": result["error"],
                "recommendation": "Select from available drugs."
            })
        elif result["total_factor"] < 0.5:
            alerts.append({
                "type": "MAJOR_DOSE_REDUCTION", "severity": "WARNING",
                "message": f"Dose reduced to {result['total_factor']*100:.0f}% due to organ impairment.",
                "recommendation": "Consider alternative agent. Close monitoring required."
            })
        elif result["adjusted_dose_mg"] >= result["max_dose_mg"]:
            alerts.append({
                "type": "DOSE_CAP", "severity": "INFO",
                "message": f"Dose capped at maximum ({result['max_dose_mg']}mg).",
                "recommendation": "Cap applied per protocol."
            })

        return {"pk_result": result, "alerts": alerts}
