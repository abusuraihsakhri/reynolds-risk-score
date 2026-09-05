"""
Tests for reynolds.py core calculation functions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import os
import reynolds as r


class TestCalculateScore:
    def test_basic_score(self):
        result = r.calculate_score(value=10, qty=2)
        assert "score" in result
        assert "inputs" in result
        assert result["inputs"] == 2

    def test_empty_inputs_uses_default(self):
        result = r.calculate_score()
        assert result["inputs"] == 1
        assert "score" in result

    def test_string_numeric_inputs(self):
        result = r.calculate_score(a="5.5", b="3.2")
        assert result["inputs"] == 2
        assert "score" in result

    def test_mixed_inputs(self):
        result = r.calculate_score(a=10, b="5.5", c="not_a_number")
        assert result["inputs"] == 2


class TestMELDNa:
    def test_basic_meld(self):
        result = r.calculate_meld_na(
            bilirubin=2.0, creatinine=1.2, inr=1.5,
            sodium=135, dialysis=False, albumin=3.5, sex="M"
        )
        assert "meld_na_score" in result
        assert "risk_tier" in result
        assert result["risk_tier"] in ["LOW", "MODERATE", "HIGH"]

    def test_dialysis_adjustment(self):
        result = r.calculate_meld_na(
            bilirubin=1.0, creatinine=1.0, inr=1.0,
            sodium=140, dialysis=True
        )
        assert result["meld_na_score"] >= 6.0

    def test_none_values_handled(self):
        result = r.calculate_meld_na(
            bilirubin=None, creatinine=None, inr=None,
            sodium=None, dialysis=False
        )
        assert "meld_na_score" in result

    def test_high_meld_tier(self):
        result = r.calculate_meld_na(
            bilirubin=15.0, creatinine=5.0, inr=3.0,
            sodium=125, dialysis=True
        )
        assert result["risk_tier"] == "HIGH"


class TestQTc:
    def test_qtc_with_hr(self):
        result = r.calculate_qtc(qt_ms=400, hr_bpm=75)
        assert "qtc_ms" in result
        assert "prolonged" in result
        assert isinstance(result["prolonged"], bool)

    def test_qtc_with_rr(self):
        result = r.calculate_qtc(qt_ms=400, rr_ms=1000)
        assert "qtc_ms" in result

    def test_prolonged_qtc(self):
        result = r.calculate_qtc(qt_ms=500, hr_bpm=60)
        assert result["prolonged"] is True

    def test_none_values_handled(self):
        result = r.calculate_qtc(qt_ms=None, rr_ms=None, hr_bpm=None)
        assert "qtc_ms" in result


class TestBMIZ:
    def test_basic_bmi(self):
        result = r.calculate_bmi_z(weight_kg=70, height_cm=175, age_months=360, sex="M")
        assert "bmi" in result
        assert "z_score" in result
        assert result["bmi"] > 0

    def test_invalid_height(self):
        result = r.calculate_bmi_z(weight_kg=70, height_cm=0, age_months=360)
        assert "error" in result

    def test_invalid_weight(self):
        result = r.calculate_bmi_z(weight_kg=0, height_cm=175, age_months=360)
        assert "error" in result


class TestHbA1c:
    def test_hba1c_to_eag(self):
        result = r.convert_hba1c(hba1c_percent=7.0)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result
        assert result["hba1c_percent"] == 7.0

    def test_eag_to_hba1c(self):
        result = r.convert_hba1c(eag_mgdl=154.3)
        assert "hba1c_percent" in result
        assert "eag_mgdl" in result

    def test_no_input(self):
        result = r.convert_hba1c()
        assert "error" in result


class TestAPRIFIB4:
    def test_basic_apri_fib4(self):
        result = r.calculate_apri_fib4(
            ast_u_l=80, alt_u_l=60, platelets_109=200, age_years=45
        )
        assert "apri" in result
        assert "fib4" in result
        assert "fib4_risk" in result
        assert result["fib4_risk"] in ["LOW", "INTERMEDIATE", "HIGH"]

    def test_high_fib4(self):
        result = r.calculate_apri_fib4(
            ast_u_l=200, alt_u_l=150, platelets_109=100, age_years=65
        )
        assert result["fib4_risk"] == "HIGH"

    def test_none_values_handled(self):
        result = r.calculate_apri_fib4(ast_u_l=None, alt_u_l=None, platelets_109=None, age_years=None)
        assert "apri" in result
        assert "fib4" in result


class TestAssessRow:
    def test_meld_row(self):
        result = r.assess_row({"bilirubin": 2.0, "creatinine": 1.2, "inr": 1.5, "sodium": 135})
        assert "meld_na_score" in result

    def test_qtc_row(self):
        result = r.assess_row({"qt_ms": 400, "hr_bpm": 75})
        assert "qtc_ms" in result

    def test_bmi_row(self):
        result = r.assess_row({"weight_kg": 70, "height_cm": 175, "age": 30, "sex": "M"})
        assert "bmi" in result

    def test_hba1c_row(self):
        result = r.assess_row({"hba1c_percent": 7.0})
        assert "eag_mgdl" in result

    def test_apri_row(self):
        result = r.assess_row({"ast_u_l": 80, "alt_u_l": 60, "platelets_109": 200, "age_years": 45})
        assert "fib4" in result

    def test_generic_row(self):
        result = r.assess_row({"value": 10, "qty": 2})
        assert "score" in result

    def test_invalid_input(self):
        result = r.assess_row("not a dict")
        assert "error" in result

    def test_empty_dict(self):
        result = r.assess_row({})
        assert "score" in result


class TestProcessCSV:
    def test_process_csv_basic(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("id,value,qty\n")
            f.write("A,10,2\n")
            f.write("B,20,3\n")
            input_path = f.name

        output_path = input_path + ".out.csv"
        try:
            results = r.process_csv(input_path, output_path)
            assert len(results) == 2
            assert os.path.isfile(output_path)
            assert "score" in results[0]
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_process_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            r.process_csv("nonexistent_file.csv", "output.csv")

    def test_process_csv_no_headers(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("")
            input_path = f.name
        output_path = input_path + ".out.csv"
        try:
            with pytest.raises(ValueError, match="no headers"):
                r.process_csv(input_path, output_path)
        finally:
            os.unlink(input_path)


class TestMain:
    def test_single_json(self):
        result = r.main(["single", "--json", '{"value": 10}'])
        assert result == 0

    def test_single_bilirubin(self):
        result = r.main(["single", "--bili", "2.0", "--creat", "1.2", "--inr", "1.5", "--na", "135"])
        assert result == 0

    def test_batch(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("id,value,qty\n")
            f.write("A,10,2\n")
            input_path = f.name
        output_path = input_path + ".out.csv"
        try:
            result = r.main(["batch", "--input", input_path, "--output", output_path])
            assert result == 0
            assert os.path.isfile(output_path)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_batch_missing_file(self):
        result = r.main(["batch", "--input", "nonexistent.csv", "--output", "out.csv"])
        assert result == 1
