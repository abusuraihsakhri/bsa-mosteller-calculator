import math

import pytest

import bsa
from bsa_formulas import Anthropometrics, compute_all_bsa
from dose_recalculation import CycleRecord, calculate_dose, calvert_carboplatin, check_cycle_to_cycle_change
from pediatric_adjustments import calculate_bsa_pediatric
from pharmacokinetic_adjustments import (
    calculate_bsa_pharmacokinetic_adjustment,
    calculate_protocol_adjusted_dose,
)


def test_formula_functions_reject_invalid_values():
    functions = [
        bsa.bsa_mosteller,
        bsa.bsa_dubois,
        bsa.bsa_haycock,
        bsa.bsa_gehan_george,
        bsa.bsa_boyd,
    ]
    for fn in functions:
        with pytest.raises(ValueError):
            fn(0, 70)
        with pytest.raises(ValueError):
            fn(170, -1)
        with pytest.raises(ValueError):
            fn(math.inf, 70)


def test_invalid_formula_falls_back_with_warning():
    result = bsa.calculate_patient("P", 170, 70, preferred_formula="not-a-formula")
    assert result.preferred_formula == "Mosteller"
    assert result.primary_bsa() == result.bsa_mosteller
    assert any("Unknown BSA formula" in warning for warning in result.warnings)


def test_cli_invalid_input_does_not_crash(capsys):
    rc = bsa.main(["single", "--height", "-170", "--weight", "70"])
    captured = capsys.readouterr()
    assert rc == 2
    assert "Calculation not performed" in captured.out


def test_negative_optional_inputs_are_not_calculated():
    result = bsa.calculate_patient("P", 170, 70, dose_per_m2=-1, gfr_raw_ml_min=-1)
    assert result.chemo_dose is None
    assert result.gfr_indexed_1_73m2 is None
    assert len(result.warnings) >= 2


def test_formula_comparison_has_no_pediatric_weight_heuristic():
    result = compute_all_bsa(Anthropometrics(122, 24))
    assert result["preferred_formula"] == "Mosteller"
    assert "protocol" in result["selection_note"].lower()


def test_dose_helper_has_no_implicit_rounding_or_cap():
    result = calculate_dose(2.03, 100)
    assert result["nominal_dose_mg"] == 203.0
    assert result["administered_dose_mg"] == 203.0
    assert result["rounding_rule"] == "none"
    assert result["bsa_capped"] is False

    configured = calculate_dose(2.03, 100, round_to_mg=5, institutional_bsa_cap=2.0)
    assert configured["effective_bsa_m2"] == 2.0
    assert configured["administered_dose_mg"] == 200.0


def test_cycle_threshold_is_caller_supplied():
    prev = CycleRecord(1, 2.0)
    curr = CycleRecord(2, 2.2)
    result = check_cycle_to_cycle_change(prev, curr)
    assert result["threshold_pct"] is None
    assert result["threshold_exceeded"] is None

    configured = check_cycle_to_cycle_change(prev, curr, threshold_pct=5)
    assert configured["threshold_exceeded"] is True


def test_calvert_has_no_default_gfr_cap():
    uncapped = calvert_carboplatin(5, 150)
    assert uncapped["gfr_cap"] is None
    assert uncapped["gfr_used"] == 150

    capped = calvert_carboplatin(5, 150, gfr_cap=125)
    assert capped["gfr_used"] == 125


def test_pediatric_module_does_not_mislabel_dubois_or_infer_caps():
    result = calculate_bsa_pediatric(24, 122, 7, drug_name="example")
    assert "bsa_dubois" in result
    assert "bsa_fujimoto" not in result
    assert result["dose_caps"] == {}
    assert "No pediatric dose" in result["notice"]


def test_pharmacokinetic_module_requires_explicit_protocol_dose():
    legacy = calculate_bsa_pharmacokinetic_adjustment("example", 1.8)
    assert "error" in legacy

    result = calculate_protocol_adjusted_dose(
        1.8,
        100,
        renal_multiplier=0.8,
        hepatic_multiplier=1.0,
        max_dose_mg=150,
    )
    assert result["base_dose_mg"] == 180.0
    assert result["adjusted_dose_mg"] == 144.0
