# CodeSentinel AI 🛡️

> **Cross-Platform, Local-First, Agentic AI Code Security, Vulnerability Detection, Performance Analysis, and Autonomous Remediation Platform.**

[![Python Tests](https://img.shields.io/badge/Python%20Tests-45%20Passed-emerald.svg)](tests/)
[![Tauri 2](https://img.shields.io/badge/Desktop-Tauri%202%20%2B%20React-indigo.svg)](apps/desktop/)
[![Risk Model](https://img.shields.io/badge/Risk%20Scoring-Heuristic%20(CodeBERT%20roadmap)-blue.svg)](ml/)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

---

## 🌟 Overview & Core Vision
CodeSentinel AI is an intelligent, locally installed security assistant designed to continuously watch software projects being developed in modern AI-assisted IDEs (such as **Google Antigravity**, **Cursor**, and **VS Code**).

Whenever code is saved or modified:
1. **Real-time Filesystem Monitoring**: Watchdog observer detects file writes, creations, and deletions with a 1.5s coalescing debounce window and SHA-256 content hashing.
2. **Multi-Engine Security Scanners**: Runs deterministic static analysis (Semgrep, Bandit), secret detection (Gitleaks), dependency CVE auditing (pip-audit, npm audit), and cyclomatic complexity (Radon / AST).
3. **Risk Scoring**: Scores suspicious code with a deterministic, explainable lexical/feature-based risk model that returns a 0–1 vulnerability risk score and candidate CWE tags. (A fine-tuned **CodeBERT** neural model, `microsoft/codebert-base`, is architected and scaffolded in `ml/` as the next step — see the roadmap note below. It is not trained yet.)
4. **Autonomous Multi-Agent Investigation**: State machine coordinates specialized agents:
   - **Planning Agent**: Triages findings and formulates bounded investigation plans.
   - **Security Investigation Agent**: Traces data flow and untrusted taint reachability.
   - **Dependency & Performance Agents**: Investigates CVE upgrades and algorithmic bottlenecks.
   - **Remediation Agent**: Formulates minimal, non-breaking candidate repairs.
   - **Verification Agent**: Runs AST syntax checks and scanner clearance in isolation.
   - **Evaluation Agent**: Audits evidence quality and computes final confidence scores.
5. **Human-in-the-Loop Remediation**: Inspect unified diffs in the desktop dashboard and apply fixes with 1-click atomic rollback (`.bak` backups).

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Rust toolchain** (for compiling the Tauri native desktop app)

### 1. Install Backend Dependencies
```bash
pip install -r pyproject.toml
# Or install core dependencies directly:
pip install fastapi uvicorn pydantic watchdog sqlalchemy aiosqlite httpx pytest pytest-asyncio
```

### 2. Run Test Suite
```bash
python3 -m pytest tests/ -v
```
*(45 unit & integration tests pass cleanly)*

### 3. Run the ML evaluation harness
```bash
python3 ml/training/train.py
python3 ml/experiments/ablation.py
```
*(Evaluates the current heuristic risk scorer on a small internal sample and runs the 3-stage ablation. This is a reference scaffold — it does **not** perform real gradient training; CodeBERT fine-tuning on a public dataset is future work.)*

### 4. Start the FastAPI Backend
```bash
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```
Swagger API documentation available at: `http://127.0.0.1:8765/api/docs`

### 5. Launch the Desktop Application
```bash
cd apps/desktop
npm install
npm run dev
```
Open `http://localhost:5173` in your browser, or run `npm run tauri dev` to launch the native native desktop window.

---

## 🔬 Risk Model & Roadmap (ANN / Deep Learning)
The risk-scoring layer is designed around CodeBERT, with a clear path from the current shipping model to a trained neural one:
- **Today (shipping)**: a deterministic, explainable lexical/feature risk scorer. Fast (<1 ms), no model download, fully offline. It is a heuristic — not a trained neural network.
- **Designed architecture**: CodeBERT (`microsoft/codebert-base`) + Dense Classification Head + Dropout (0.2) + Softmax, scaffolded in `ml/` (config, dataset loader, training loop, evaluation metrics).
- **Roadmap (next step)**: fine-tune the CodeBERT head on a public vulnerability dataset (e.g. Devign / CodeXGLUE defect-detection) on a GPU, then swap it in behind the same inference interface.
- **Illustrative ablation** (⚠️ measured on a **small internal sample (~12 labeled pairs)**, not a published benchmark — indicative only, not a scientific result): static-only vs. +risk-model vs. full agentic system. See [docs/research/ACADEMIC_REPORT.md](docs/research/ACADEMIC_REPORT.md) for the method and the honesty caveats.

---

## 🔒 Security Principles
- **Local-First Privacy**: Source code is never sent to cloud AI providers without explicit toggle consent.
- **Automated Secret Redaction**: Credentials and tokens are redacted (`[REDACTED]`) before database storage or LLM prompting.
- **Never Modify Code Silently**: All proposed patches require human developer confirmation via the unified diff viewer.
