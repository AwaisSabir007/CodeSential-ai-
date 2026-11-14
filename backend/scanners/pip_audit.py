"""pip-audit dependency vulnerability scanner adapter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from backend.scanners.base import (
    BaseScanner,
    FindingConfidence,
    FindingSeverity,
    RawFinding,
    ScanContext,
    ScannerCategory,
)

SEVERITY_MAP = {
    "CRITICAL": FindingSeverity.CRITICAL,
    "HIGH": FindingSeverity.HIGH,
    "MODERATE": FindingSeverity.MEDIUM,
    "MEDIUM": FindingSeverity.MEDIUM,
    "LOW": FindingSeverity.LOW,
}

MANIFEST_FILES = {
    "requirements.txt", "requirements-dev.txt", "requirements-test.txt",
    "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg",
    "pyproject.toml", "poetry.lock",
}


class PipAuditScanner(BaseScanner):
    """pip-audit Python dependency vulnerability scanner."""

    name = "pip_audit"
    category = ScannerCategory.DEPENDENCY
    supported_languages = ["python"]

    def supports(self, file_path: str) -> bool:
        return Path(file_path).name in MANIFEST_FILES

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["pip-audit", "--version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, _ = await self._run_subprocess(["pip-audit", "--version"])
        if code == 0:
            return stdout.strip()
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        # Find the best requirements file to audit
        req_file = self._find_requirements_file(context.project_path)

        if not req_file:
            # Project does not specify Python dependencies, skip
            return []

        args = [
            "pip-audit",
            "--format", "json",
            "--requirement", str(req_file),
        ]

        code, stdout, stderr = await self._run_subprocess(
            args, cwd=context.project_path
        )

        if code not in (0, 1):
            if not stdout.strip():
                raise RuntimeError(f"pip-audit failed: {stderr[:500]}")

        return self._parse_output(stdout, context.project_path)

    def _find_requirements_file(self, project_path: Path) -> Optional[Path]:
        priority = [
            "requirements.txt",
            "requirements-dev.txt",
            "Pipfile.lock",
            "poetry.lock",
        ]
        for name in priority:
            candidate = project_path / name
            if candidate.exists():
                return candidate
        return None

    def _parse_output(self, output: str, project_path: Path) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not output.strip():
            return findings

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return findings

        dependencies = data.get("dependencies", [])
        for dep in dependencies:
            vulns = dep.get("vulns", [])
            package_name = dep.get("name", "unknown")
            installed_version = dep.get("version", "unknown")

            for vuln in vulns:
                try:
                    finding = self._parse_vuln(
                        package_name, installed_version, vuln, project_path
                    )
                    if finding:
                        findings.append(finding)
                except Exception:
                    continue

        return findings

    def _parse_vuln(
        self,
        package_name: str,
        installed_version: str,
        vuln: dict,
        project_path: Path,
    ) -> Optional[RawFinding]:
        vuln_id = vuln.get("id", "UNKNOWN")
        description = vuln.get("description", "")
        aliases = vuln.get("aliases", [])
        fix_versions = vuln.get("fix_versions", [])

        cve_id = None
        for alias in aliases:
            if alias.startswith("CVE-"):
                cve_id = alias
                break

        # Map severity from aliases or default
        severity = FindingSeverity.HIGH  # Conservative default for dependency vulns

        fix_info = ""
        if fix_versions:
            fix_info = f" Fixed in: {', '.join(fix_versions)}."
            recommendation = (
                f"Upgrade '{package_name}' from {installed_version} to "
                f"{fix_versions[-1]} or later.{fix_info}"
            )
        else:
            recommendation = (
                f"No known fix available for '{package_name}' {installed_version}. "
                "Consider finding an alternative package or applying mitigations."
            )

        req_files = list(project_path.glob("requirements*.txt"))
        file_path = str(req_files[0]) if req_files else str(project_path / "requirements.txt")

        return RawFinding(
            scanner_name=self.name,
            rule_id=vuln_id,
            category="vulnerable_dependency",
            severity=severity,
            confidence=FindingConfidence.HIGH,
            file_path=file_path,
            line_start=None,
            line_end=None,
            title=f"Vulnerable dependency: {package_name}=={installed_version} ({vuln_id})",
            description=(
                f"Package '{package_name}' version {installed_version} "
                f"has a known vulnerability ({vuln_id}).\n\n{description}"
            ),
            recommendation=recommendation,
            cve_id=cve_id,
            cwe_id=None,
            raw_metadata={
                "package": package_name,
                "installed_version": installed_version,
                "vuln_id": vuln_id,
                "aliases": aliases,
                "fix_versions": fix_versions,
            },
        )
