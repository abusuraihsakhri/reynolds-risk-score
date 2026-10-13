"""Reference-vector and failure-mode checks for the published Reynolds equations."""
import math
import pytest

from risk import calculate_reynolds_risk
from cli import main


@pytest.mark.parametrize("inputs,expected", [
    (dict(sex="female", age=55, systolic_bp=125, total_cholesterol=208,
          hdl_cholesterol=52, hs_crp=2, smoker=False,
          parental_mi_before_60=False), 1.49),
    (dict(sex="female", age=65, systolic_bp=150, total_cholesterol=240,
          hdl_cholesterol=42, hs_crp=4, smoker=True,
          parental_mi_before_60=True, diabetes=True, hba1c=8.2), 66.83),
    (dict(sex="male", age=60, systolic_bp=130, total_cholesterol=205,
          hdl_cholesterol=48, hs_crp=2, smoker=False,
          parental_mi_before_60=False), 7.99),
    (dict(sex="male", age=70, systolic_bp=160, total_cholesterol=245,
          hdl_cholesterol=35, hs_crp=6, smoker=True,
          parental_mi_before_60=True), 70.72),
])
def test_published_equations_reference_vectors(inputs, expected):
    assert calculate_reynolds_risk(**inputs)["risk_10y_percent"] == expected


BASE = dict(sex="female", age=55, systolic_bp=125,
            total_cholesterol=208, hdl_cholesterol=52, hs_crp=2,
            smoker=False, parental_mi_before_60=False)


@pytest.mark.parametrize("mutation", [
    {"sex": "unknown"}, {"age": 40}, {"age": float("nan")},
    {"systolic_bp": 0}, {"hs_crp": -1}, {"hs_crp": float("inf")},
    {"total_cholesterol": 0}, {"hdl_cholesterol": 0},
    {"smoker": 1}, {"parental_mi_before_60": "false"},
    {"diabetes": True}, {"hba1c": 7},
])
def test_invalid_inputs_rejected(mutation):
    with pytest.raises(ValueError):
        calculate_reynolds_risk(**(BASE | mutation))


def test_diabetic_woman_requires_hba1c():
    with pytest.raises(ValueError, match="hba1c"):
        calculate_reynolds_risk(**(BASE | {"diabetes": True}))


def test_diabetic_male_not_supported():
    with pytest.raises(ValueError, match="not validated"):
        calculate_reynolds_risk(**(BASE | {"sex": "male", "age": 60, "diabetes": True}))


def test_prediction_increases_with_smoking():
    non_smoker = calculate_reynolds_risk(**BASE)["risk_10y_percent"]
    smoker = calculate_reynolds_risk(**(BASE | {"smoker": True}))["risk_10y_percent"]
    assert smoker > non_smoker


def test_cli_risk(capsys):
    args = ["risk", "--sex", "female", "--age", "55", "--sbp", "125",
            "--tc", "208", "--hdl", "52", "--crp", "2"]
    assert main(args) == 0
    assert '"risk_10y_percent": 1.49' in capsys.readouterr().out
    assert main(args + ["--diabetes"]) == 2
    assert "Invalid input" in capsys.readouterr().err


def test_api_risk():
    from fastapi.testclient import TestClient
    from agents.api import app
    with TestClient(app) as client:
        response = client.post("/api/risk", json=BASE)
        assert response.status_code == 200
        assert response.json()["risk_10y_percent"] == 1.49
        invalid = client.post("/api/risk", json=BASE | {"hs_crp": 0})
        assert invalid.status_code == 422
        index = client.get("/")
        assert index.status_code == 200
        assert "Reynolds Risk Score" in index.text


def test_tampered_hmac_is_detected():
    from agents.base import AuditTrail
    audit = AuditTrail(secret_key="testing-key-not-production")
    audit.log("tester", "tests", "CHECK", {"status": "OK"})
    assert audit.verify_integrity() is True
    safe_snapshot = audit.get_trail()
    safe_snapshot[0]["current_hash"] = "tampered"
    assert audit.verify_integrity() is True
    audit.logs[0]["timestamp"] = "modified"
    assert audit.verify_integrity() is False


def test_legacy_csv_reynolds_routing(tmp_path):
    from reynolds import assess_row, process_csv
    row = {"sex": "female", "age": "55", "systolic_bp": "125",
           "total_cholesterol": "208", "hdl_cholesterol": "52", "hs_crp": "2",
           "smoker": "false", "parental_mi_before_60": "no"}
    assert assess_row(row)["risk_10y_percent"] == 1.49
    assert "error" in assess_row(row | {"smoker": "not sure"})
    assert "error" in assess_row({"sex": "female", "systolic_bp": "125"})
    path = tmp_path / "cases.csv"
    result = tmp_path / "output.csv"
    import csv
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    processed = process_csv(path, result)
    assert processed[0]["risk_10y_percent"] == "1.49"
    assert "risk_10y_percent" in result.read_text()
