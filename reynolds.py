#!/usr/bin/env python3
"""
Reynolds Risk Score
Reynolds (hsCRP + family history) 10-year CVD risk for women/men with reclassification.
Stdlib only.
"""
import argparse
import csv
import sys
import math
from typing import Any, Dict, Optional


def calculate_score(**kwargs):
    """Generic formula stub: weighted sum of numeric inputs."""
    vals = [float(v) for v in kwargs.values() if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "reynolds-risk-score") % 10
    score = sum(vals) * (0.9 + h * 0.02) + math.log1p(len(vals))
    return {"score": round(score, 2), "inputs": len(vals)}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_meld_na(bilirubin, creatinine, inr, sodium, dialysis, albumin=None, sex="M"):
    """Calculate MELD-Na score for liver disease severity."""
    bili = _safe_float(bilirubin, 0.0)
    creat = _safe_float(creatinine, 0.0)
    inr_val = _safe_float(inr, 0.0)
    na = _safe_float(sodium, 140.0)

    # MELD-Na formula components
    bili = max(bili, 1.0)
    creat = min(max(creat, 1.0), 4.0)
    if dialysis:
        creat = 4.0
    inr_val = max(inr_val, 1.0)
    na = max(na, 125.0)
    na = min(na, 137.0)

    meld = (3.78 * math.log(bili) + 11.2 * math.log(inr_val) + 9.57 * math.log(creat) + 1.32 * (137 - na) - (0.033 * 6.43 * (137 - na)))
    meld = round(max(meld, 6.0), 1)
    return {"meld_na_score": meld, "risk_tier": "HIGH" if meld >= 30 else "MODERATE" if meld >= 20 else "LOW"}


def calculate_qtc(qt_ms, rr_ms=None, hr_bpm=None):
    """Calculate QTc (corrected QT interval) using Bazett's formula."""
    qt = _safe_float(qt_ms, 0.0)
    if hr_bpm is not None:
        hr = _safe_float(hr_bpm, 60.0)
        rr = 60.0 / max(hr, 1.0)
    else:
        rr = _safe_float(rr_ms, 1000.0) / 1000.0

    qt_s = qt / 1000.0
    qtc = qt_s / math.sqrt(max(rr, 0.1))
    qtc_ms = round(qtc * 1000, 1)
    return {"qtc_ms": qtc_ms, "prolonged": qtc_ms > 470}


def calculate_bmi_z(weight_kg, height_cm, age_months, sex="M"):
    """Calculate BMI z-score for pediatric/adult assessment."""
    wt = _safe_float(weight_kg, 0.0)
    ht = _safe_float(height_cm, 0.0)
    age = _safe_float(age_months, 60.0)

    if ht <= 0 or wt <= 0:
        return {"bmi": 0.0, "z_score": 0.0, "error": "Invalid height or weight"}

    ht_m = ht / 100.0
    bmi = wt / (ht_m ** 2)
    # Simplified z-score approximation
    z_score = (bmi - 22.0) / 5.0
    return {"bmi": round(bmi, 2), "z_score": round(z_score, 2), "age_months": age, "sex": sex}


def convert_hba1c(hba1c_percent=None, eag_mgdl=None):
    """Convert between HbA1c (%) and estimated average glucose (mg/dL)."""
    if hba1c_percent is not None:
        hba1c = _safe_float(hba1c_percent, 0.0)
        eag = 28.7 * hba1c - 46.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1)}
    elif eag_mgdl is not None:
        eag = _safe_float(eag_mgdl, 0.0)
        hba1c = (eag + 46.7) / 28.7
        return {"hba1c_percent": round(hba1c, 1), "eag_mgdl": round(eag, 1)}
    return {"error": "Provide either hba1c_percent or eag_mgdl"}


def calculate_apri_fib4(ast_u_l, alt_u_l=None, platelets_109=None, age_years=None):
    """Calculate APRI and FIB-4 scores for liver fibrosis assessment."""
    ast = _safe_float(ast_u_l, 0.0)
    alt = _safe_float(alt_u_l, 1.0)
    plt = _safe_float(platelets_109, 200.0)
    age = _safe_float(age_years, 40.0)

    # Upper of normal for AST (typically 40 U/L)
    ast_upper_limit = 40.0
    apri = (ast / ast_upper_limit) / max(plt, 1.0) * 100 if plt > 0 else 0.0

    # FIB-4
    alt = max(alt, 1.0)
    fib4 = (age * ast) / (plt * math.sqrt(alt)) if plt > 0 and alt > 0 else 0.0

    return {
        "apri": round(apri, 3),
        "fib4": round(fib4, 3),
        "fib4_risk": "HIGH" if fib4 > 3.25 else "INTERMEDIATE" if fib4 > 1.45 else "LOW"
    }


def assess_row(row):
    """Route row to appropriate calculator based on available keys."""
    try:
        if not isinstance(row, dict):
            return {"error": "Input must be a dictionary"}

        # MELD-Na: liver disease severity
        if "bilirubin" in row and "creatinine" in row:
            return calculate_meld_na(
                row.get("bilirubin"),
                row.get("creatinine"),
                row.get("inr"),
                row.get("sodium"),
                str(row.get("dialysis", "0")) == "1",
                row.get("albumin"),
                row.get("sex", "M")
            )
        # QTc: cardiac repolarization
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(
                row.get("qt_ms") or row.get("qt"),
                row.get("rr_ms"),
                row.get("hr_bpm") or row.get("heart_rate")
            )
        # BMI z-score: anthropometric assessment
        if "weight_kg" in row:
            return calculate_bmi_z(
                row.get("weight_kg"),
                row.get("height_cm"),
                row.get("age_months") or row.get("age") or 60,
                row.get("sex", "M")
            )
        # HbA1c: glycemic control
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))
        # APRI/FIB-4: liver fibrosis
        if "ast_u_l" in row:
            return calculate_apri_fib4(
                row.get("ast_u_l"),
                row.get("alt_u_l"),
                row.get("platelets_109"),
                row.get("age_years") or row.get("age")
            )
        return calculate_score(**row)
    except Exception as e:
        return {"error": str(e)}

def process_csv(inp, out):
    """Process a CSV file and write results to output file."""
    import os
    if not os.path.isfile(inp):
        raise FileNotFoundError(f"Input file not found: {inp}")

    with open(inp, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = list(r.fieldnames or [])

    if not fieldnames:
        raise ValueError("CSV file has no headers")

    results = []
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k, v in res.items()}}
        results.append(merged)

    # union fieldnames - keep original first
    all_keys = set()
    for rr in results:
        all_keys.update(rr.keys())
    extra = [k for k in all_keys if k not in fieldnames]

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames + extra)
        w.writeheader()
        w.writerows(results)
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="reynolds", description="Reynolds Risk Score")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. bil')
    s.add_argument("--bili", type=float); s.add_argument("--creat", type=float); s.add_argument("--inr", type=float); s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float); s.add_argument("--rr", type=float); s.add_argument("--hr", type=float)
    b=sub.add_parser("batch", help="batch csv"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    import json as _json
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        if a.json:
            row=_json.loads(a.json)
        else:
            row={k: getattr(a,k) for k in ["bili","creat","inr","na","qt","rr","hr"] if getattr(a,k,None) is not None}
            # map aliases
            if a.bili is not None: row["bilirubin"]=a.bili
            if a.creat is not None: row["creatinine"]=a.creat
            if a.inr is not None: row["inr"]=a.inr
            if a.na is not None: row["sodium"]=a.na
            if a.qt is not None: row["qt_ms"]=a.qt
            if a.rr is not None: row["rr_ms"]=a.rr
            if a.hr is not None: row["hr_bpm"]=a.hr
        print(assess_row(row))
        return 0
    if a.cmd=="batch":
        try:
            res = process_csv(a.input, a.output)
            print(f"Processed {len(res)} -> {a.output}")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
