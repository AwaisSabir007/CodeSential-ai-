"""SQLAlchemy database models for CodeSentinel AI."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Project(Base):
    """A registered software project being monitored."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(4096), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    monitoring_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    # Relationships
    settings: Mapped[Optional["ProjectSettings"]] = relationship(
        "ProjectSettings", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    scans: Mapped[list["ScanRun"]] = relationship(
        "ScanRun", back_populates="project", cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_projects_path", "path"),
        Index("ix_projects_is_active", "is_active"),
    )


class ProjectSettings(Base):
    """Per-project monitoring and scan configuration."""
    __tablename__ = "project_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    excluded_dirs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    excluded_extensions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    scan_sensitivity: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high
    enable_semgrep: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_bandit: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_gitleaks: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_pip_audit: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_npm_audit: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_complexity: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_ml_inference: Mapped[bool] = mapped_column(Boolean, default=True)
    privacy_mode: Mapped[str] = mapped_column(String(20), default="local_only")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["Project"] = relationship("Project", back_populates="settings")


class ScanRun(Base):
    """A complete scan run for a project."""
    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE")
    )
    trigger: Mapped[str] = mapped_column(String(50), default="manual")  # manual|file_change|git_commit
    scan_type: Mapped[str] = mapped_column(String(20), default="full")  # full|incremental|targeted
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued|running|completed|failed|cancelled
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_files: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship("Project", back_populates="scans")
    scanner_runs: Mapped[list["ScannerRun"]] = relationship(
        "ScannerRun", back_populates="scan_run", cascade="all, delete-orphan", lazy="selectin"
    )
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="scan_run", lazy="selectin")

    __table_args__ = (
        Index("ix_scan_runs_project_id", "project_id"),
        Index("ix_scan_runs_status", "status"),
        Index("ix_scan_runs_created_at", "created_at"),
    )


class ScannerRun(Base):
    """Result of running a single scanner within a scan run."""
    __tablename__ = "scanner_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    scan_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_runs.id", ondelete="CASCADE")
    )
    scanner_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    # queued|running|completed|failed|timed_out|unavailable|skipped|cancelled
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scan_run: Mapped["ScanRun"] = relationship("ScanRun", back_populates="scanner_runs")

    __table_args__ = (
        Index("ix_scanner_runs_scan_run_id", "scan_run_id"),
    )


class Finding(Base):
    """A normalized security or code quality finding."""
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE")
    )
    scan_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("scan_runs.id", ondelete="SET NULL"), nullable=True
    )
    scanner_name: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    # critical|high|medium|low|informational
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    # high|medium|low
    file_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    line_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    line_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cve_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open")
    # open|investigating|resolved|accepted_risk|false_positive|reopened
    verification_state: Mapped[str] = mapped_column(String(30), default="unverified")
    ml_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=_now)

    project: Mapped["Project"] = relationship("Project", back_populates="findings")
    scan_run: Mapped[Optional["ScanRun"]] = relationship("ScanRun", back_populates="findings")
    evidence: Mapped[list["FindingEvidence"]] = relationship(
        "FindingEvidence", back_populates="finding", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_findings_project_id", "project_id"),
        Index("ix_findings_severity", "severity"),
        Index("ix_findings_status", "status"),
        Index("ix_findings_fingerprint", "fingerprint"),
        Index("ix_findings_file_path", "file_path"),
        UniqueConstraint("project_id", "fingerprint", name="uq_findings_project_fingerprint"),
    )


class FindingEvidence(Base):
    """Additional evidence linked to a finding."""
    __tablename__ = "finding_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id", ondelete="CASCADE")
    )
    evidence_type: Mapped[str] = mapped_column(String(50))
    # scanner_output|code_context|ml_prediction|agent_note
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="evidence")


class Investigation(Base):
    """An autonomous AI investigation of one or more findings."""
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE")
    )
    finding_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending|running|completed|failed|cancelled
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    iteration_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        Index("ix_investigations_project_id", "project_id"),
        Index("ix_investigations_status", "status"),
    )


class ProposedPatch(Base):
    """A code patch proposed by the remediation agent."""
    __tablename__ = "proposed_patches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id", ondelete="CASCADE")
    )
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    file_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    original_code: Mapped[str] = mapped_column(Text, nullable=False)
    patched_code: Mapped[str] = mapped_column(Text, nullable=False)
    diff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    side_effects: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending|verified|approved|rejected|applied|failed
    verification_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class ModelPrediction(Base):
    """A neural network vulnerability prediction record."""
    __tablename__ = "model_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    finding_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE")
    )
    file_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    function_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="unknown")
    inference_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        Index("ix_model_predictions_project_id", "project_id"),
    )


class Notification(Base):
    """A notification for the user."""
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # scan_complete|finding_critical|investigation_complete|patch_ready
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
    )
