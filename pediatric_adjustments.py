#!/usr/bin/env python3
"""Pediatric BSA calculations without drug-specific dose recommendations."""

from typing import Any, Dict, Optional

from bsa import bsa_dubois, bsa_haycock, bsa_mosteller


def calculate_bsa_pediatric(
    weight_kg: float,
    height_cm: float,
    age_years: float,
    drug_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate three established BSA formulas for a pediatric record.

    drug_name is retained for API compatibility but is not used to infer a
    dose or cap. Pediatric dosing must be obtained from a verified protocol.
    """
    if age_years < 0:
        raise ValueError("age_years must be non-negative")

    mosteller = bsa_mosteller(height_cm, weight_kg)
    dubois = bsa_dubois(height_cm, weight_kg)
    haycock = bsa_haycock(height_cm, weight_kg)
    values = [mosteller, dubois, haycock]

    return {
        "bsa_mosteller": round(mosteller, 4),
        "bsa_dubois": round(dubois, 4),
        "bsa_haycock": round(haycock, 4),
        "bsa_mean": round(sum(values) / len(values), 4),
        "age_years": float(age_years),
        "drug_name": drug_name,
        "dose_caps": {},
        "notice": "No pediatric dose, cap, or preferred formula is inferred by this module.",
    }


class BsaPediatricAgent:
    """Compatibility wrapper for pediatric BSA calculations."""

    def __init__(self) -> None:
        self.agent_name = "BsaPediatricAgent"

    def evaluate(
        self,
        weight_kg: float,
        height_cm: float,
        age_years: float,
        drug_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = calculate_bsa_pediatric(weight_kg, height_cm, age_years, drug_name)
        return {
            "pediatric_result": result,
            "alerts": [],
            "notice": "Use a verified pediatric protocol for formula selection and dosing.",
        }
