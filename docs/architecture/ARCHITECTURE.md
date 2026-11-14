# CodeSentinel AI — System Architecture & Technical Specifications

## 1. Logical Architecture

```
Developer IDE (VS Code / Cursor / Antigravity)
       │ (writes files)
       ▼
Local Filesystem
       │
       ▼
Filesystem Watcher Service (Watchdog, Event Coalescing, 1.5s Debounce)
       │
       ▼
Content Hashing & Change Snapshot Engine (SHA-256 Checksums)
       │
       ▼
Scan Scheduler (Queue, Cancellation, Resource Throttling)
       │
       ├──► Security Scanners (Semgrep, Bandit, Gitleaks, pip-audit, npm audit, Radon)
       │
       ▼
Normalized Findings Engine (Deduplication, Correlated Fingerprints)
       │
       ├──► Local SQLite Database (SQLAlchemy 2.0 Async, Migrations)
       │
       ├──► Deep Learning Neural Head (CodeBERT Statistical Risk Scoring)
       │
       ├──► Multi-Agent Investigation Engine (LangGraph State Machine)
       │       ├── Planning Agent
       │       ├── Deep Learning Agent
       │       ├── Security Investigation Agent (Taint / Sinks)
       │       ├── Dependency Analysis Agent
       │       ├── Performance Optimization Agent
       │       ├── Remediation Agent
       │       ├── Verification Agent (AST Syntax Clearance)
       │       └── Evaluation Agent (Evidence Confidence)
       │
       ├──► Autonomous Remediation Engine (Unified Diffs, .bak Backups, Approval Gate)
       │
       ▼
FastAPI Localhost REST & SSE Events Server (Port 8765)
       │
       ▼
Tauri 2 + React + TypeScript Desktop Application (Port 5173 / Native Window)
```

---

## 2. Non-Negotiable Security Principles
1. **Local-First Privacy**: Source code is stored and scanned exclusively on the local machine by default. No code leaves localhost without explicit opt-in settings.
2. **Credential Redaction**: Detected API keys, bearer tokens, and private keys are redacted (`[REDACTED]`) before appearing in logs, databases, or AI prompts.
3. **No Silent Code Execution**: The agent never modifies code without developer review. All proposed fixes require explicit human approval.
4. **AST Validation Before Remediation**: Candidate patches undergo abstract syntax tree validation to guarantee no syntax errors or breaking regressions.
5. **Atomic Backup & Rollback**: Applying any patch creates an atomic `<file>.codesentinel.bak` copy, allowing instant 1-click rollback.
