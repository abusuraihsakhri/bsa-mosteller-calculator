# Bsa Mosteller Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

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

Body Surface Area (BSA) Calculator
====================================

Implements multiple BSA formulas:
  - Mosteller:    BSA = sqrt((height_cm × weight_kg) / 3600)
  - Du Bois:      BSA = 0.007184 × height_cm^0.725 × weight_kg^0.425
  - Haycock:      BSA = 0.024265 × height_cm^0.3964 × weight_kg^0.5378
  - Gehan-George: BSA = 0.0235 × height_cm^0.42246 × weight_kg^0.51456

Includes chemotherapy dose calculation: dose = BSA × dose_per_m²

Stdlib only. Usage: python bsa.py --help

Body surface area formulas (adult + pediatric) with cross-formula agreement.

Implements the five standard BSA models:
    Mosteller      sqrt(H * W / 3600)
    DuBois         0.007184 * H^0.725 * W^0.425
    Haycock        0.024265 * H^0.3964 * W^0.5378
    Gehan-George   0.0235    * H^0.42246 * W^0.51456
    Boyd           0.0003207 * H^0.3 * Wg^(0.7285 - 0.0188*log10(Wg))

Reports the mean, spread, and flags disagreement >2% (typical institutional
tolerance for dose-affecting BSA discrepancies).

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`BSAResult`** — dedicated module for b s a result evaluation and state verification.
- **`Anthropometrics`** — dedicated module for anthropometrics evaluation and state verification.
- **`CycleRecord`** — dedicated module for cycle record evaluation and state verification.
- **`BsaPediatricAgent`**: Sub-agent for pediatric BSA adjustments.
- **`DrugProfile`**: PK profile for a drug requiring BSA-based dosing.
- **`BsaPharmacokineticAgent`**: Sub-agent for BSA pharmacokinetic adjustments.

---

## 📐 Mathematical Formulation & Logic

```text
  Implements multiple BSA formulas:
  BSA Formulas
  """Mosteller formula: BSA = sqrt((H × W) / 3600)."""
  """Du Bois formula: BSA = 0.007184 × H^0.725 × W^0.425."""
  """Haycock formula: BSA = 0.024265 × H^0.3964 × W^0.5378."""
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

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
docker build -t bsa-mosteller-calculator .
docker run -p 8000:8000 bsa-mosteller-calculator
```
