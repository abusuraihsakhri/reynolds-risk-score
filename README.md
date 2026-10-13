# Reynolds Risk Score

A research/education implementation of the **original, sex-specific Reynolds Risk Score** equations for estimating 10-year composite cardiovascular event risk. The application accepts blood pressure, cholesterol, high-sensitivity CRP, smoking, and parental history of myocardial infarction before age 60. The women's model additionally accounts for HbA1c when diabetes is present.

**Clinical limitation:** This project has not undergone independent clinical software validation. It is not intended for diagnosis, prescribing, or treatment decisions. Refer to current local primary-prevention guidelines.

## Browser application

The `web/` calculator runs entirely in the browser using plain JavaScript, without a backend, external libraries, cookies, or input uploads. It is suitable for GitHub Pages. Its build is defined in `.github/workflows/pages.yml`; public availability requires GitHub Pages to be enabled with **GitHub Actions** as its source. Do not assume a deployment is live until the Pages workflow and URL have been verified.

Alternatively, open `web/index.html` locally or serve it over HTTP. Enter the clinical risk factors and select **Calculate 10-year risk**.

## Model scope

| | Women | Men |
|---|---|---|
| Derivation publication | Ridker et al., JAMA 2007 | Ridker et al., Circulation 2008 |
| Age range supported here | 45–79 years | 50–79 years |
| Diabetes | HbA1c (%) required when diabetic | **Not supported**; men in the derivation cohort did not have diabetes |
| Units | SBP: mmHg; cholesterol: mg/dL; hsCRP: mg/L | Same |

Both equations are for **primary prevention in people free of known cardiovascular disease**. Outcomes include myocardial infarction, ischemic stroke, coronary revascularization, and cardiovascular death. Risk estimates may not calibrate to contemporary populations and clinical practice. They should not be treated as current guideline-defined ASCVD risk.

### Equations

Women:

```text
B = 0.0799*age + 3.137*ln(SBP) + 0.180*ln(hsCRP)
    + 1.382*ln(total cholesterol) - 1.172*ln(HDL)
    + 0.134*HbA1c [if diabetic]
    + 0.818 [if smoker] + 0.438 [if parental MI before 60]
10-year risk (%) = 100 * (1 - 0.98634 ^ exp(B - 22.325))
```

Men:

```text
B = 4.385*ln(age) + 2.607*ln(SBP) + 0.963*ln(total cholesterol)
    - 0.772*ln(HDL) + 0.405 [if smoker]
    + 0.102*ln(hsCRP) + 0.541 [if parental MI before 60]
10-year risk (%) = 100 * (1 - 0.8990 ^ exp(B - 33.097))
```

Sources:

- Ridker PM et al. *JAMA*. 2007;297:611–619. [doi:10.1001/jama.297.6.611](https://doi.org/10.1001/jama.297.6.611)
- Ridker PM et al. *Circulation*. 2008;118:2243–2251. [doi:10.1161/CIRCULATIONAHA.108.814251](https://doi.org/10.1161/CIRCULATIONAHA.108.814251)

## Python CLI and REST API

Python 3.10+:

```bash
git clone https://github.com/abusuraihsakhri/reynolds-risk-score.git
cd reynolds-risk-score
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Calculate cardiovascular risk:

```bash
reynolds risk --sex female --age 55 --sbp 125 --tc 208 --hdl 52 --crp 2
# {"risk_10y_percent": 1.49, ...}
```

Add `--smoker`, `--parental-mi`, or (women only) `--diabetes --hba1c 7.1` when appropriate. `risk.py` exposes `calculate_reynolds_risk(...)` as a standard-library function. Invalid or out-of-scope inputs raise `ValueError`.

```bash
reynolds serve --host 127.0.0.1 --port 8000
# Browser page: http://127.0.0.1:8000/
# POST http://127.0.0.1:8000/api/risk with JSON risk factors
```

The pre-existing audit CLI/API remains available (`reynolds audit`, `reynolds verify-audit`, `/api/audit`). These generic operational checks **are not cardiovascular risk assessment**. The unrelated helper functions in `reynolds.py`, including its demonstration-only generic score, are legacy and are not clinically validated. `python reynolds.py batch --input risk.csv --output results.csv` supports Reynolds risk columns with the names defined in `risk.py`.

## Testing and security

```bash
python -m pytest -v
node --check web/risk.js
node --check web/app.js
node --test web/risk.test.cjs
```

Automated tests check known formula vectors, invalid data, Python/JavaScript consistency of expected outputs, CLI/API responses, CSV processing, and audit-log HMAC tampering. No Python runtime, Pyodide, server, or API key is required by the browser calculator.

The browser calculator processes inputs in memory without network calls or browser storage. The optional FastAPI service receives JSON over HTTP; do not send real patient identifiers to the demonstration audit endpoints. The audit ledger is **in-memory**, not a persistent or regulatory-compliant audit system, and its regex identifier checks are not comprehensive PHI de-identification. For the backend audit functionality, provide a strong `AUDIT_SECRET_KEY` environment variable. Docker Compose requires it explicitly.

## Deployment and licensing

```bash
AUDIT_SECRET_KEY='replace-with-a-long-random-secret' docker compose up --build
```

The container serves the same browser calculator and FastAPI endpoints on port 8000. GitHub Pages can host only the standalone static calculator (not the Python API or the operational audit service).

Tested via CI on Python 3.10–3.12; browser code uses standard modern JavaScript without build tooling. MIT License; see [LICENSE](LICENSE).
