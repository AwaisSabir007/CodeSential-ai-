# CodeSentinel AI — Commercial SaaS Roadmap & Enterprise Architecture

## 1. Evolution from Local-First to Commercial SaaS
While the initial release prioritizes a local-first architecture for developer privacy and offline reliability, the internal data model and interfaces are designed to transition smoothly to a cloud SaaS tier.

```
┌─────────────────────────────────┐
│     CodeSentinel Local Desktop  │
│  (Tauri 2 + Python Local-First) │
└────────────────┬────────────────┘
                 │ (Encrypted Metadata Sync)
                 ▼
┌─────────────────────────────────┐
│     CodeSentinel Cloud Hub      │
│  - Multi-Tenant PostgreSQL      │
│  - Team Workspaces & RBAC       │
│  - Centralized Vulnerability    │
│    Dashboards & Trends          │
│  - GitHub / GitLab App Webhooks │
│  - Organization Security Policy │
│  - Enterprise SAML SSO / Okta   │
└─────────────────────────────────┘
```

---

## 2. Phased Roadmap
- **Phase 1 (Current)**: Local-first desktop platform, Watchdog real-time file watcher, CodeBERT neural model, multi-agent remediation, SQLite persistence.
- **Phase 2 (Team Sync)**: Opt-in cloud sync for anonymized findings metadata and team-wide security policy enforcement.
- **Phase 3 (Enterprise SaaS)**: Private VPC deployments, CI/CD GitHub Actions integration, centralized compliance auditing (SOC 2, ISO 27001).
