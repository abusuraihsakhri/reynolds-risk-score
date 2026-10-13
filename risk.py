"""Published Reynolds Risk Score (RRS) 10-year cardiovascular event equations.

Sources:
Ridker et al., JAMA 2007;297:611-619. doi:10.1001/jama.297.6.611
Ridker et al., Circulation 2008;118:2243-2251.
doi:10.1161/CIRCULATIONAHA.108.814251

Unit conventions: blood pressure mmHg; cholesterol mg/dL; hsCRP mg/L;
HbA1c percent (diabetic women only).
Not a diagnostic tool or a replacement for contemporary prevention guidelines.
"""
import math


def _positive_finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def calculate_reynolds_risk(
    *,
    sex: str,
    age: float,
    systolic_bp: float,
    total_cholesterol: float,
    hdl_cholesterol: float,
    hs_crp: float,
    smoker: bool,
    parental_mi_before_60: bool,
    diabetes: bool = False,
    hba1c: float | None = None,
) -> dict:
    """Return original 10-year composite-CVD risk as a percentage (0-100).

    Intended for primary prevention: women >=45 and <80 years; nondiabetic men
    >=50 and <80 years. Do not apply to pre-existing CVD. The male model was
    developed only in men without diabetes. Extrapolation beyond these cohorts
    is not supported. Binary factors must be genuine booleans.
    """
    if not isinstance(sex, str) or sex.strip().lower() not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")
    sex = sex.strip().lower()
    age = _positive_finite("age", age)
    minimum_age = 45 if sex == "female" else 50
    if not minimum_age <= age < 80:
        raise ValueError(f"{sex} model supports ages {minimum_age} to under 80 years")
    bp = _positive_finite("systolic_bp", systolic_bp)
    tc = _positive_finite("total_cholesterol", total_cholesterol)
    hdl = _positive_finite("hdl_cholesterol", hdl_cholesterol)
    crp = _positive_finite("hs_crp", hs_crp)
    for name, value in [
        ("smoker", smoker),
        ("parental_mi_before_60", parental_mi_before_60),
        ("diabetes", diabetes),
    ]:
        if type(value) is not bool:
            raise ValueError(f"{name} must be true or false")

    if sex == "male":
        if diabetes:
            raise ValueError("male Reynolds equation is not validated for diabetes")
        if hba1c is not None:
            raise ValueError("hba1c is used only for diabetic women")
        linear = (
            4.385 * math.log(age)
            + 2.607 * math.log(bp)
            + 0.963 * math.log(tc)
            - 0.772 * math.log(hdl)
            + 0.405 * smoker
            + 0.102 * math.log(crp)
            + 0.541 * parental_mi_before_60
        )
        survival, offset = 0.8990, 33.097
        reference = "Ridker et al. Circulation 2008"
    else:
        if diabetes:
            hba1c = _positive_finite("hba1c", hba1c)
        elif hba1c is not None:
            raise ValueError("hba1c applies only when diabetes is true")
        linear = (
            0.0799 * age
            + 3.137 * math.log(bp)
            + 0.180 * math.log(crp)
            + 1.382 * math.log(tc)
            - 1.172 * math.log(hdl)
            + (0.134 * hba1c if diabetes else 0)
            + 0.818 * smoker
            + 0.438 * parental_mi_before_60
        )
        survival, offset = 0.98634, 22.325
        reference = "Ridker et al. JAMA 2007"

    # expm1 prevents cancellation at very low risk.
    exponent = math.exp(min(linear - offset, 700))
    risk_pct = -100 * math.expm1(math.log(survival) * exponent)
    return {
        "risk_10y_percent": round(min(100.0, max(0.0, risk_pct)), 2),
        "model": sex,
        "outcome": "10-year composite cardiovascular events",
        "reference": reference,
        "note": "Research/education only; assess clinical applicability and local guidelines.",
    }
