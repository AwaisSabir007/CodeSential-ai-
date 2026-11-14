"""API response schemas using Pydantic v2."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ─── Projects ────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    path: Optional[str] = Field(None, min_length=1, max_length=4096)
    root_path: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None

    def get_path(self) -> str:
        return self.path or self.root_path or ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    excluded_dirs: Optional[str] = None
    excluded_extensions: Optional[str] = None
    scan_sensitivity: str
    enable_semgrep: bool
    enable_bandit: bool
    enable_gitleaks: bool
    enable_pip_audit: bool
    enable_npm_audit: bool
    enable_complexity: bool
    enable_ml_inference: bool
    privacy_mode: str
    updated_at: datetime


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    path: str
    description: Optional[str] = None
    language: Optional[str] = None
    is_active: bool
    monitoring_enabled: bool
    created_at: datetime
    updated_at: datetime
    settings: Optional[ProjectSettingsOut] = None


# ─── Scans ────────────────────────────────────────────────────────────────────

class ScanCreate(BaseModel):
    project_id: str
    scan_type: str = "full"
    target_files: Optional[List[str]] = None
    enabled_scanners: Optional[List[str]] = None


class ScannerRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scanner_name: str
    status: str
    version: Optional[str] = None
    duration_seconds: Optional[float] = None
    findings_count: int
    error_message: Optional[str] = None


class ScanRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    trigger: str
    scan_type: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    files_scanned: int
    findings_count: int
    error_message: Optional[str] = None
    created_at: datetime
    scanner_runs: List[ScannerRunOut] = []


# ─── Findings ─────────────────────────────────────────────────────────────────

class FindingEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_type: str
    content: str
    created_at: datetime


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    scan_run_id: Optional[str] = None
    scanner_name: str
    rule_id: Optional[str] = None
    category: str
    severity: str
    confidence: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    title: str
    description: Optional[str] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    fingerprint: str
    status: str
    verification_state: str
    ml_risk_score: Optional[float] = None
    first_seen: datetime
    last_seen: datetime
    evidence: List[FindingEvidenceOut] = []


class FindingStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|investigating|resolved|accepted_risk|false_positive|reopened)$")


# ─── Investigations ───────────────────────────────────────────────────────────

class InvestigationCreate(BaseModel):
    project_id: str
    finding_ids: List[str] = Field(..., min_length=1)
    llm_provider: Optional[str] = None


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    finding_ids: Optional[str] = None
    status: str
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    plan: Optional[str] = None
    conclusion: Optional[str] = None
    token_usage: int
    iteration_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


# ─── System ───────────────────────────────────────────────────────────────────

class ScannerStatus(BaseModel):
    name: str
    category: str
    available: bool
    version: Optional[str] = None
    supported_languages: List[str] = []


class SystemHealth(BaseModel):
    status: str = "healthy"
    version: str
    database: str = "connected"
    scanners_available: int = 0
    active_scans: int = 0
    monitored_projects: int = 0


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None
    type: str
    title: str
    message: str
    severity: str
    is_read: bool
    reference_id: Optional[str] = None
    created_at: datetime


# ─── Monitoring ───────────────────────────────────────────────────────────────

class MonitoringStatusOut(BaseModel):
    project_id: str
    is_monitoring: bool
    monitored_path: Optional[str] = None


# ─── Generic ──────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
