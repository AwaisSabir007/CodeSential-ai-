"""Findings normalization and persistence service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.core.security import generate_finding_fingerprint, redact_secrets
from backend.database.models import Finding
from backend.database.repositories import FindingRepository
from backend.scanners.base import RawFinding, ScannerResult

logger = get_logger(__name__)


class FindingsNormalizer:
    """Normalizes raw scanner findings into the database schema."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = FindingRepository(session)

    async def process_scanner_results(
        self,
        project_id: str,
        scan_run_id: str,
        project_path: str,
        results: List[ScannerResult],
    ) -> tuple[int, int]:
        """
        Normalize and persist all scanner results.
        Returns (new_count, updated_count).
        """
        new_count = 0
        updated_count = 0
        seen_fingerprints: set[str] = set()
        completed_scanners: list[str] = []

        for result in results:
            if result.status.value in ("completed", "success"):
                completed_scanners.append(result.scanner_name)

            if not result.findings:
                continue

            for raw_finding in result.findings:
                try:
                    finding, is_new = await self._persist_finding(
                        project_id=project_id,
                        scan_run_id=scan_run_id,
                        project_path=project_path,
                        raw=raw_finding,
                    )
                    seen_fingerprints.add(finding.fingerprint)
                    if is_new:
                        new_count += 1
                    else:
                        updated_count += 1
                except Exception as exc:
                    logger.error(
                        "Failed to persist finding",
                        scanner=raw_finding.scanner_name,
                        error=str(exc),
                    )

        # Resolve findings from completed scanners that were not seen
        resolved_count = 0
        if completed_scanners:
            resolved_count = await self.repo.resolve_unseen_findings(
                project_id=project_id,
                scanner_names=completed_scanners,
                seen_fingerprints=seen_fingerprints,
            )

        logger.info(
            "Findings persisted",
            new=new_count,
            updated=updated_count,
            resolved=resolved_count,
        )
        return new_count, updated_count

    async def _persist_finding(
        self,
        project_id: str,
        scan_run_id: str,
        project_path: str,
        raw: RawFinding,
    ) -> tuple[Finding, bool]:
        # Normalize file path to be relative to project
        file_path = self._normalize_path(raw.file_path, project_path)

        # Generate stable fingerprint
        code_context = raw.code_snippet or ""
        fingerprint = generate_finding_fingerprint(
            scanner=raw.scanner_name,
            rule_id=raw.rule_id or "unknown",
            file_path=file_path,
            code_snippet=code_context,
        )

        # Redact any secrets from description / code
        safe_description = redact_secrets(raw.description or "")
        safe_snippet = redact_secrets(raw.code_snippet or "") if raw.code_snippet else None

        raw_metadata = raw.raw_metadata.copy()
        # Remove any potential secret fields from raw metadata
        for sensitive_key in ("secret", "match", "token", "password", "key"):
            raw_metadata.pop(sensitive_key, None)

        finding, is_new = await self.repo.upsert(
            project_id=project_id,
            scan_run_id=scan_run_id,
            scanner_name=raw.scanner_name,
            fingerprint=fingerprint,
            rule_id=raw.rule_id,
            category=raw.category,
            severity=raw.severity.value,
            confidence=raw.confidence.value,
            file_path=file_path,
            line_start=raw.line_start,
            line_end=raw.line_end,
            title=raw.title[:512],
            description=safe_description,
            code_snippet=safe_snippet,
            recommendation=raw.recommendation,
            cwe_id=raw.cwe_id,
            cve_id=raw.cve_id,
            raw_output=json.dumps(raw_metadata),
        )

        return finding, is_new

    def _normalize_path(self, file_path: str, project_path: str) -> str:
        """Convert absolute file path to relative project path."""
        if not file_path:
            return "unknown"
        try:
            fp = Path(file_path)
            pp = Path(project_path)
            if fp.is_absolute():
                try:
                    return str(fp.relative_to(pp))
                except ValueError:
                    return file_path
            return file_path
        except Exception:
            return file_path
