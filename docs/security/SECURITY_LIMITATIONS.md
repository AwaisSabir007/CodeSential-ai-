# CodeSentinel AI — Security Guarantees & Known Limitations

## 1. Security Guarantees
- **Deterministic Scanning**: Bandit, Semgrep, Gitleaks, and pip-audit execute in deterministic mode without fetching unverified remote rule files.
- **Strict Path Validation**: Project directory registration rejects paths outside valid developer directories and forbids system roots (`/bin`, `/sbin`, `/System`, `C:\Windows`). Symlinks pointing outside authorized project trees are rejected.
- **Redaction of Secrets**: Detected credentials are automatically replaced with `[REDACTED]` prior to persistence, logging, and model prompting.
- **Human-in-the-Loop Review**: Candidate remediation patches cannot be applied automatically. The user must review the unified diff and click "Approve".

---

## 2. Limitations & Scopes
1. **Dynamic Profiling**: Dynamic code profiling is disabled by default to prevent executing untrusted repository scripts without a full hypervisor sandbox.
2. **Scanner Dependency Availability**: If a scanner tool (e.g. `gitleaks` binary) is not installed on the host machine, CodeSentinel gracefully reports the scanner as `unavailable` rather than faking a clean scan.
3. **Statistical AI Risk Scoring**: Neural risk scores and LLM reasoning outputs represent statistical risk heuristics and must never be interpreted as mathematical proofs of total security.
