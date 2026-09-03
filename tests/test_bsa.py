"""Tests for bsa.py -- plain assert statements, stdlib only.

Run with: python test_bsa.py
"""

import csv
import math
import os
import tempfile

import bsa


# ---------------------------------------------------------------------------
# Mosteller formula
# ---------------------------------------------------------------------------

def test_mosteller_standard():
    """170cm, 70kg -> sqrt(170*70/3600) = sqrt(3.3056) ≈ 1.8181."""
    result = bsa.bsa_mosteller(170, 70)
    expected = math.sqrt(170 * 70 / 3600)
    assert math.isclose(result, expected, abs_tol=0.0001), (result, expected)


def test_mosteller_known_value():
    """170cm, 70kg should give ~1.81 m²."""
    result = bsa.bsa_mosteller(170, 70)
    assert math.isclose(result, 1.81, abs_tol=0.02), result


def test_mosteller_small_person():
    """150cm, 45kg -> sqrt(150*45/3600) ≈ 1.3693."""
    result = bsa.bsa_mosteller(150, 45)
    expected = math.sqrt(150 * 45 / 3600)
    assert math.isclose(result, expected, abs_tol=0.0001), (result, expected)


# ---------------------------------------------------------------------------
# Du Bois formula
# ---------------------------------------------------------------------------

def test_dubois_standard():
    """170cm, 70kg -> 0.007184 * 170^0.725 * 70^0.425 ≈ 1.81."""
    result = bsa.bsa_dubois(170, 70)
    assert math.isclose(result, 1.81, abs_tol=0.02), result


def test_dubois_known_reference():
    """Du Bois for 170cm, 70kg is a well-known reference value ~1.8146."""
    result = bsa.bsa_dubois(170, 70)
    expected = 0.007184 * (170 ** 0.725) * (70 ** 0.425)
    assert math.isclose(result, expected, abs_tol=0.0001), (result, expected)


# ---------------------------------------------------------------------------
# Haycock formula
# ---------------------------------------------------------------------------

def test_haycock_standard():
    """170cm, 70kg -> 0.024265 * 170^0.3964 * 70^0.5378."""
    result = bsa.bsa_haycock(170, 70)
    expected = 0.024265 * (170 ** 0.3964) * (70 ** 0.5378)
    assert math.isclose(result, expected, abs_tol=0.0001), (result, expected)


def test_haycock_in_range():
    """Haycock for average adult should be ~1.8 m²."""
    result = bsa.bsa_haycock(170, 70)
    assert 1.7 < result < 1.9, result


# ---------------------------------------------------------------------------
# Gehan-George formula
# ---------------------------------------------------------------------------

def test_gehan_george_standard():
    """170cm, 70kg -> 0.0235 * 170^0.42246 * 70^0.51456."""
    result = bsa.bsa_gehan_george(170, 70)
    expected = 0.0235 * (170 ** 0.42246) * (70 ** 0.51456)
    assert math.isclose(result, expected, abs_tol=0.0001), (result, expected)


def test_gehan_george_in_range():
    """Gehan-George for average adult should be ~1.8 m²."""
    result = bsa.bsa_gehan_george(170, 70)
    assert 1.7 < result < 1.9, result


# ---------------------------------------------------------------------------
# Cross-formula agreement
# ---------------------------------------------------------------------------

def test_formulas_agree_within_tolerance():
    """All four formulas should agree within ~5% for a standard adult."""
    h, w = 170, 70
    values = [
        bsa.bsa_mosteller(h, w),
        bsa.bsa_dubois(h, w),
        bsa.bsa_haycock(h, w),
        bsa.bsa_gehan_george(h, w),
    ]
    mean = sum(values) / len(values)
    for v in values:
        pct_diff = abs(v - mean) / mean * 100
        assert pct_diff < 5, f"Formula deviates {pct_diff:.1f}% from mean"


# ---------------------------------------------------------------------------
# BSA classification
# ---------------------------------------------------------------------------

def test_classify_normal():
    assert "normal" in bsa.classify_bsa(1.8).lower()


def test_classify_below_normal():
    assert "below" in bsa.classify_bsa(1.4).lower()


def test_classify_above_normal():
    assert "above" in bsa.classify_bsa(2.3).lower()


# ---------------------------------------------------------------------------
# Chemotherapy dosing
# ---------------------------------------------------------------------------

def test_chemotherapy_dose():
    """BSA 1.8 m² × 100 mg/m² = 180 mg."""
    result = bsa.chemotherapy_dose(1.8, 100)
    assert math.isclose(result, 180.0, abs_tol=0.01), result


def test_chemotherapy_dose_fractional():
    """BSA 1.65 m² × 75 mg/m² = 123.75 mg."""
    result = bsa.chemotherapy_dose(1.65, 75)
    assert math.isclose(result, 123.75, abs_tol=0.01), result


# ---------------------------------------------------------------------------
# Patient workflow
# ---------------------------------------------------------------------------

def test_calculate_patient_all_formulas():
    result = bsa.calculate_patient("P1", 170, 70)
    assert result.bsa_mosteller is not None
    assert result.bsa_dubois is not None
    assert result.bsa_haycock is not None
    assert result.bsa_gehan_george is not None
    assert result.bsa_mean is not None
    assert result.bsa_classification is not None


def test_calculate_patient_with_chemo():
    result = bsa.calculate_patient("P2", 170, 70, dose_per_m2=100)
    assert result.chemo_dose is not None
    assert result.chemo_dose_per_m2 == 100
    expected = result.primary_bsa() * 100
    assert math.isclose(result.chemo_dose, expected, abs_tol=0.1)


def test_calculate_patient_preferred_formula():
    result = bsa.calculate_patient("P3", 170, 70, preferred_formula="DuBois")
    assert result.preferred_formula == "DuBois"
    assert result.primary_bsa() == result.bsa_dubois


def test_calculate_patient_invalid_height():
    result = bsa.calculate_patient("P4", -170, 70)
    assert len(result.warnings) > 0
    assert result.bsa_mosteller is None


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

def test_batch_csv():
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        out = os.path.join(tmp, "out.csv")
        with open(inp, "w", newline="") as f:
            f.write("patient_id,height_cm,weight_kg,dose_per_m2,preferred_formula\n")
            f.write("A1,170,70,,Mosteller\n")
            f.write("A2,160,55,75,DuBois\n")
        results = bsa.process_csv(inp, out)
        assert len(results) == 2
        assert results[0].bsa_mosteller is not None
        assert results[1].chemo_dose is not None
        assert os.path.exists(out)


def test_boyd_formula():
    """Test Boyd formula for standard adult 170cm, 70kg -> ~1.81 m²."""
    result = bsa.bsa_boyd(170, 70)
    assert 1.75 < result < 1.88, result


def test_gfr_normalization():
    """Test GFR indexing to 1.73 m² BSA."""
    # BSA 2.0 m², raw GFR 100 mL/min -> 100 * (1.73 / 2.0) = 86.5 mL/min/1.73m²
    norm = bsa.normalize_gfr_to_bsa(100.0, 2.0)
    assert math.isclose(norm, 86.5, abs_tol=0.01)
    denorm = bsa.denormalize_gfr_from_bsa(norm, 2.0)
    assert math.isclose(denorm, 100.0, abs_tol=0.01)


def test_calculate_patient_with_gfr():
    result = bsa.calculate_patient("P_GFR", 170, 70, gfr_raw_ml_min=90.0)
    assert result.gfr_raw_ml_min == 90.0
    assert result.gfr_indexed_1_73m2 is not None
    assert result.bsa_boyd is not None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_single():
    rc = bsa.main(["single", "--height", "170", "--weight", "70"])
    assert rc == 0


def test_cli_single_with_dose():
    rc = bsa.main(["single", "--height", "170", "--weight", "70", "--dose-per-m2", "100", "--gfr", "85"])
    assert rc == 0


def test_cli_batch():
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        out = os.path.join(tmp, "out.csv")
        with open(inp, "w", newline="") as f:
            f.write("patient_id,height_cm,weight_kg,dose_per_m2,preferred_formula\n")
            f.write("T1,170,70,,Mosteller\n")
        rc = bsa.main(["batch", "--input", inp, "--output", out])
        assert rc == 0
        assert os.path.exists(out)


def test_cli_batch_short_flags():
    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        out = os.path.join(tmp, "out.csv")
        with open(inp, "w", newline="") as f:
            f.write("patient_id,age,sex,height_cm,weight_kg,dose_per_m2,gfr_raw_ml_min,preferred_formula\n")
            f.write("PT-1,50,M,175,75,100,80,Mosteller\n")
        rc = bsa.main(["batch", "-i", inp, "-o", out])
        assert rc == 0
        assert os.path.exists(out)


def test_batch_sample_csv():
    """Verify processing the project's actual sample.csv."""
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample.csv")
    if os.path.exists(sample_path):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "sample_out.csv")
            rc = bsa.main(["batch", "-i", sample_path, "-o", out])
            assert rc == 0
            assert os.path.exists(out)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all():
    tests = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  PASS: {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL: {t.__name__} -- {e}")
    print(f"\n{passed}/{passed + failed} tests passed.")
    return failed


if __name__ == "__main__":
    import sys
    sys.exit(run_all())
