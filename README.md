# Reynolds Risk Score

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Reynolds Risk Score calculates 10-year cardiovascular disease (CVD) risk using hsCRP and family history for women and men with reclassification. The system provides multiple clinical calculation modules including MELD-Na, QTc, BMI z-score, HbA1c conversion, and APRI/FIB-4 scores.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_score()`** — Generic weighted sum formula for numeric inputs
- **`calculate_meld_na()`** — MELD-Na score for liver disease severity
- **`calculate_qtc()`** — QTc interval correction using Bazett's formula
- **`calculate_bmi_z()`** — BMI z-score for anthropometric assessment
- **`convert_hba1c()`** — Convert between HbA1c (%) and estimated average glucose (mg/dL)
- **`calculate_apri_fib4()`** — APRI and FIB-4 scores for liver fibrosis assessment
- **`assess_row()`** — Routes input data to appropriate calculator based on available keys
- **`process_csv()`** — Batch process CSV files with clinical data

---

## 📐 Mathematical Formulation & Logic

### MELD-Na Score
```
MELD = 3.78 × ln(bilirubin) + 11.2 × ln(INR) + 9.57 × ln(creatinine) + 1.32 × (137 - Na) - (0.033 × 6.43 × (137 - Na))
```

### QTc (Bazett's Formula)
```
QTc = QT / √(RR)
```

### APRI Score
```
APRI = (AST / AST_upper_limit) / Platelets × 100
```

### FIB-4 Score
```
FIB-4 = (Age × AST) / (Platelets × √ALT)
```

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/reynolds-risk-score.git
cd reynolds-risk-score

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Calculation
```bash
# Using JSON input
python reynolds.py single --json '{"bilirubin": 2.0, "creatinine": 1.2, "inr": 1.5, "sodium": 135}'

# Using named parameters
python reynolds.py single --bili 2.0 --creat 1.2 --inr 1.5 --na 135
```

### 2. Batch CSV Processing
```bash
python reynolds.py batch --input sample.csv --output results.csv
```

### 3. Enterprise CLI (with audit trail)
```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process CSV records
python cli.py batch -i sample.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `id` | Parameter / observation metric | Required |
| `value` | Parameter / observation metric | Required |
| `qty` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for production use:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t reynolds-risk-score .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key reynolds-risk-score

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## 📁 Project Structure

```
reynolds-risk-score/
├── agents/                 # Enterprise agent modules
│   ├── __init__.py
│   ├── api.py             # FastAPI REST server
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── learning.py        # Bayesian calibration engine
│   ├── llm_factory.py     # LLM provider factory
│   ├── metrics.py         # Prometheus metrics
│   ├── models.py          # Pydantic data models
│   ├── streamer.py        # WebSocket telemetry
│   ├── supervisor.py      # Supervisor orchestrator
│   └── workers.py         # Specialized worker agents
├── tests/                 # Test suite
│   ├── test_enrichment.py
│   ├── test_reynolds_core.py
│   └── test_reynolds_risk_score.py
├── web/                   # Operations console UI
│   └── index.html
├── cli.py                 # Enterprise CLI entry point
├── reynolds.py            # Core calculation modules
├── enrichment.py          # Enrichment feature modules
├── simulator.py           # High-throughput simulator
├── pyproject.toml         # Project configuration
├── Dockerfile             # Container build
├── docker-compose.yml     # Container orchestration
└── README.md              # This file
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
