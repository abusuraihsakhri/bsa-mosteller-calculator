#!/usr/bin/env python3
"""Generic protocol-supplied BSA dose adjustment arithmetic.

Earlier versions embedded drug-specific doses and ad-hoc renal/hepatic
multipliers. Those values were not a validated prescribing knowledge base and
have been removed. This module now performs arithmetic only on values explicitly
supplied by the caller.
"""

import math
from typing import Any, Dict, Optional


def _nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return value


def calculate_protocol_adjusted_dose(
    bsa: float,
    dose_per_m2: float,
    renal_multiplier: float = 1.0,
    hepatic_multiplier: float = 1.0,
    max_dose_mg: Optional[float] = None,
) -> Dict[str, Any]:
    """Apply caller-supplied protocol values without inferring clinical rules."""
    bsa = _nonnegative("bsa", bsa)
    if bsa == 0:
        raise ValueError("bsa must be greater than zero")
    dose_per_m2 = _nonnegative("dose_per_m2", dose_per_m2)
    renal_multiplier = _nonnegative("renal_multiplier", renal_multiplier)
    hepatic_multiplier = _nonnegative("hepatic_multiplier", hepatic_multiplier)

    base = bsa * dose_per_m2
    adjusted = base * renal_multiplier * hepatic_multiplier
    capped = False
    if max_dose_mg is not None:
        cap = _nonnegative("max_dose_mg", max_dose_mg)
        capped = adjusted > cap
        adjusted = min(adjusted, cap)

    return {
        "bsa_m2": round(bsa, 4),
        "dose_per_m2": round(dose_per_m2, 4),
        "base_dose_mg": round(base, 4),
        "renal_multiplier": round(renal_multiplier, 4),
        "hepatic_multiplier": round(hepatic_multiplier, 4),
        "max_dose_mg": max_dose_mg,
        "dose_capped": capped,
        "adjusted_dose_mg": round(adjusted, 4),
    }


def calculate_bsa_pharmacokinetic_adjustment(
    drug_name: str,
    bsa: float,
    crcl: float = 120.0,
    alt: float = 40.0,
    **protocol: Any,
) -> Dict[str, Any]:
    """Compatibility entry point with unsafe implicit dosing removed.

    Supply dose_per_m2 and any adjustment multipliers explicitly. crcl and alt
    are accepted for compatibility but are not converted into dose multipliers.
    """
    if "dose_per_m2" not in protocol:
        return {
            "error": "No embedded drug dose is available. Supply a verified dose_per_m2 explicitly.",
            "drug": drug_name,
            "crcl": crcl,
            "alt": alt,
        }

    result = calculate_protocol_adjusted_dose(
        bsa=bsa,
        dose_per_m2=protocol["dose_per_m2"],
        renal_multiplier=protocol.get("renal_multiplier", 1.0),
        hepatic_multiplier=protocol.get("hepatic_multiplier", 1.0),
        max_dose_mg=protocol.get("max_dose_mg"),
    )
    result.update({"drug": drug_name, "crcl": crcl, "alt": alt})
    return result


class BsaPharmacokineticAgent:
    """Compatibility wrapper for protocol-supplied dose arithmetic."""

    def __init__(self) -> None:
        self.agent_name = "BsaPharmacokineticAgent"

    def evaluate(self, drug_name: str, bsa: float, crcl: float = 120.0,
                 alt: float = 40.0, **protocol: Any) -> Dict[str, Any]:
        result = calculate_bsa_pharmacokinetic_adjustment(
            drug_name, bsa, crcl, alt, **protocol
        )
        alerts = []
        if "error" in result:
            alerts.append({
                "type": "PROTOCOL_INPUT_REQUIRED",
                "severity": "ERROR",
                "message": result["error"],
                "recommendation": "Use verified prescribing or protocol data; no dose is inferred by this module.",
            })
        return {"pk_result": result, "alerts": alerts}
