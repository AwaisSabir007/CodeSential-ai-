"""Database repositories for CRUD operations."""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Finding,
    FindingEvidence,
    Investigation,
    Notification,
    Project,
    ProjectSettings,
    ScannerRun,
    ScanRun,
)


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        name: str,
        path: str,
        description: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Project:
        project = Project(name=name, path=path, description=description, language=language)
        self.session.add(project)
        settings = ProjectSettings(project_id=project.id)
        self.session.add(settings)
        project.settings = settings
        await self.session.flush()
        return project

    async def get(self, project_id: str) -> Optional[Project]:
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.settings))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_path(self, path: str) -> Optional[Project]:
        result = await self.session.execute(
            select(Project).where(Project.path == path)
        )
        return result.scalar_one_or_none()

    async def list_all(self, active_only: bool = True) -> Sequence[Project]:
        stmt = select(Project).options(selectinload(Project.settings))
        if active_only:
            stmt = stmt.where(Project.is_active == True)  # noqa: E712 (SQLAlchemy column comparison)
        stmt = stmt.order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_monitoring(self, project_id: str, enabled: bool) -> bool:
        result = await self.session.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(monitoring_enabled=enabled, updated_at=datetime.utcnow())
            .returning(Project.id)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, project_id: str) -> bool:
        project = await self.get(project_id)
        if project is None:
            return False
        # Clean up child records to prevent foreign key cascade blocks in SQLite
        await self.session.execute(
            delete(FindingEvidence).where(
                FindingEvidence.finding_id.in_(
                    select(Finding.id).where(Finding.project_id == project_id)
                )
            )
        )
        await self.session.execute(delete(Finding).where(Finding.project_id == project_id))
        await self.session.execute(
            delete(ScannerRun).where(
                ScannerRun.scan_run_id.in_(
                    select(ScanRun.id).where(ScanRun.project_id == project_id)
                )
            )
        )
        await self.session.execute(delete(ScanRun).where(ScanRun.project_id == project_id))
        await self.session.execute(delete(Investigation).where(Investigation.project_id == project_id))
        await self.session.execute(delete(ProjectSettings).where(ProjectSettings.project_id == project_id))
        await self.session.delete(project)
        await self.session.flush()
        return True

    async def update(self, project_id: str, **kwargs) -> Optional[Project]:
        kwargs["updated_at"] = datetime.utcnow()
        await self.session.execute(
            update(Project).where(Project.id == project_id).values(**kwargs)
        )
        return await self.get(project_id)


class ScanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_scan_run(
        self,
        project_id: str,
        trigger: str = "manual",
        scan_type: str = "full",
        target_files: Optional[List[str]] = None,
    ) -> ScanRun:
        scan = ScanRun(
            project_id=project_id,
            trigger=trigger,
            scan_type=scan_type,
            target_files=json.dumps(target_files) if target_files else None,
        )
        self.session.add(scan)
        await self.session.flush()
        return scan

    async def get_scan_run(self, scan_id: str) -> Optional[ScanRun]:
        result = await self.session.execute(
            select(ScanRun)
            .options(selectinload(ScanRun.scanner_runs))
            .where(ScanRun.id == scan_id)
        )
        return result.scalar_one_or_none()

    async def list_scan_runs(
        self,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ScanRun]:
        stmt = select(ScanRun)
        if project_id:
            stmt = stmt.where(ScanRun.project_id == project_id)
        stmt = stmt.order_by(ScanRun.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_scan_status(
        self,
        scan_id: str,
        status: str,
        **kwargs,
    ) -> None:
        kwargs["status"] = status
        if status == "running" and "started_at" not in kwargs:
            kwargs["started_at"] = datetime.utcnow()
        if status in ("completed", "failed", "cancelled") and "completed_at" not in kwargs:
            kwargs["completed_at"] = datetime.utcnow()
        await self.session.execute(
            update(ScanRun).where(ScanRun.id == scan_id).values(**kwargs)
        )

    async def create_scanner_run(
        self, scan_run_id: str, scanner_name: str
    ) -> ScannerRun:
        sr = ScannerRun(scan_run_id=scan_run_id, scanner_name=scanner_name)
        self.session.add(sr)
        await self.session.flush()
        return sr

    async def update_scanner_run(self, scanner_run_id: str, **kwargs) -> None:
        await self.session.execute(
            update(ScannerRun).where(ScannerRun.id == scanner_run_id).values(**kwargs)
        )


class FindingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        project_id: str,
        scan_run_id: str,
        scanner_name: str,
        fingerprint: str,
        **kwargs,
    ) -> tuple[Finding, bool]:
        """Insert or update a finding by fingerprint. Returns (finding, is_new)."""
        result = await self.session.execute(
            select(Finding).where(
                and_(Finding.project_id == project_id, Finding.fingerprint == fingerprint)
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.last_seen = datetime.utcnow()
            existing.scan_run_id = scan_run_id
            # Update some mutable fields
            for key in ("severity", "confidence", "line_start", "line_end",
                        "description", "recommendation", "code_snippet"):
                if key in kwargs:
                    setattr(existing, key, kwargs[key])
            return existing, False
        finding = Finding(
            project_id=project_id,
            scan_run_id=scan_run_id,
            scanner_name=scanner_name,
            fingerprint=fingerprint,
            **kwargs,
        )
        self.session.add(finding)
        await self.session.flush()
        return finding, True

    async def get(self, finding_id: str) -> Optional[Finding]:
        result = await self.session.execute(
            select(Finding)
            .options(selectinload(Finding.evidence))
            .where(Finding.id == finding_id)
        )
        return result.scalar_one_or_none()

    async def list_findings(
        self,
        project_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        scanner_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Finding]:
        stmt = select(Finding).options(selectinload(Finding.evidence))
        if project_id:
            stmt = stmt.where(Finding.project_id == project_id)
        if severity:
            stmt = stmt.where(Finding.severity == severity)
        if status:
            stmt = stmt.where(Finding.status == status)
        if scanner_name:
            stmt = stmt.where(Finding.scanner_name == scanner_name)
        stmt = stmt.order_by(
            Finding.severity.desc(), Finding.last_seen.desc()
        ).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, finding_id: str, status: str) -> bool:
        result = await self.session.execute(
            update(Finding)
            .where(Finding.id == finding_id)
            .values(status=status)
            .returning(Finding.id)
        )
        return result.scalar_one_or_none() is not None

    async def resolve_unseen_findings(
        self,
        project_id: str,
        scanner_names: List[str],
        seen_fingerprints: set[str],
        target_files: Optional[List[str]] = None,
    ) -> int:
        stmt = select(Finding).where(
            and_(
                Finding.project_id == project_id,
                Finding.scanner_name.in_(scanner_names),
                Finding.status == "open",
            )
        )
        if target_files:
            stmt = stmt.where(Finding.file_path.in_(target_files))
        result = await self.session.execute(stmt)
        findings = result.scalars().all()
        count = 0
        for f in findings:
            if f.fingerprint not in seen_fingerprints:
                f.status = "resolved"
                f.last_seen = datetime.utcnow()  # Finding has no updated_at column
                count += 1
        await self.session.flush()
        return count

    async def count_by_severity(self, project_id: str) -> dict:
        result = await self.session.execute(
            select(Finding.severity, func.count(Finding.id))
            .where(
                and_(Finding.project_id == project_id, Finding.status == "open")
            )
            .group_by(Finding.severity)
        )
        return dict(result.all())

    async def add_evidence(
        self, finding_id: str, evidence_type: str, content: str
    ) -> FindingEvidence:
        evidence = FindingEvidence(
            finding_id=finding_id, evidence_type=evidence_type, content=content
        )
        self.session.add(evidence)
        await self.session.flush()
        return evidence


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        type: str,
        title: str,
        message: str,
        severity: str = "info",
        project_id: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> Notification:
        n = Notification(
            type=type, title=title, message=message,
            severity=severity, project_id=project_id,
            reference_id=reference_id,
        )
        self.session.add(n)
        await self.session.flush()
        return n

    async def list_unread(self, limit: int = 50) -> Sequence[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.is_read == False)  # noqa: E712 (SQLAlchemy column comparison)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def mark_read(self, notification_id: str) -> None:
        await self.session.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )
