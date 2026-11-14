"""npm audit dependency vulnerability scanner adapter."""
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
    "critical": FindingSeverity.CRITICAL,
    "high": FindingSeverity.HIGH,
    "moderate": FindingSeverity.MEDIUM,
    "medium": FindingSeverity.MEDIUM,
    "low": FindingSeverity.LOW,
    "info": FindingSeverity.INFORMATIONAL,
}


class NpmAuditScanner(BaseScanner):
    """npm audit JavaScript/TypeScript dependency vulnerability scanner."""

    name = "npm_audit"
    category = ScannerCategory.DEPENDENCY
    supported_languages = ["javascript", "typescript"]

    def supports(self, file_path: str) -> bool:
        return Path(file_path).name in ("package.json", "package-lock.json")

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["npm", "--version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, _ = await self._run_subprocess(["npm", "--version"])
        if code == 0:
            return f"npm {stdout.strip()}"
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        pkg_json = context.project_path / "package.json"
        if not pkg_json.exists():
            return []

        args = ["npm", "audit", "--json"]
        code, stdout, stderr = await self._run_subprocess(
            args, cwd=context.project_path
        )

        # npm audit returns exit code 1 when vulnerabilities are found
        if code not in (0, 1):
            if not stdout.strip():
                raise RuntimeError(f"npm audit failed: {stderr[:500]}")

        return self._parse_output(stdout, context.project_path)

    def _parse_output(self, output: str, project_path: Path) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not output.strip():
            return findings

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return findings

        # npm audit v7+ format
        vulnerabilities = data.get("vulnerabilities", {})
        for pkg_name, vuln_data in vulnerabilities.items():
            try:
                finding = self._parse_vuln_v7(pkg_name, vuln_data, project_path)
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        # npm audit v6 format (advisories)
        advisories = data.get("advisories", {})
        for _advisory_id, advisory in advisories.items():
            try:
                finding = self._parse_advisory_v6(advisory, project_path)
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        return findings

    def _parse_vuln_v7(
        self, pkg_name: str, data: dict, project_path: Path
    ) -> Optional[RawFinding]:
        severity_str = data.get("severity", "low")
        severity = SEVERITY_MAP.get(severity_str.lower(), FindingSeverity.MEDIUM)
        via = data.get("via", [])
        installed_version = data.get("version", "unknown")
        fix_available = data.get("fixAvailable", False)

        advisory_titles = []
        cve_ids = []
        for v in via:
            if isinstance(v, dict):
                advisory_titles.append(v.get("title", ""))
                cve = v.get("cve", "")
                if cve:
                    cve_ids.append(cve)

        title = f"Vulnerable npm package: {pkg_name}@{installed_version}"
        description = f"Package '{pkg_name}' version {installed_version} has known vulnerabilities.\n"
        if advisory_titles:
            description += f"Issues: {', '.join(t for t in advisory_titles if t)}\n"

        recommendation = (
            f"Run 'npm audit fix' to automatically upgrade safe dependencies. "
            f"Or manually upgrade '{pkg_name}'."
        )
        if not fix_available:
            recommendation = (
                f"No automatic fix available for '{pkg_name}'. "
                "Review manually and consider replacing this dependency."
            )

        return RawFinding(
            scanner_name=self.name,
            rule_id=f"npm-{pkg_name}",
            category="vulnerable_dependency",
            severity=severity,
            confidence=FindingConfidence.HIGH,
            file_path=str(project_path / "package.json"),
            line_start=None,
            line_end=None,
            title=title,
            description=description,
            recommendation=recommendation,
            cve_id=cve_ids[0] if cve_ids else None,
            cwe_id=None,
            raw_metadata={
                "package": pkg_name,
                "installed_version": installed_version,
                "severity": severity_str,
                "fix_available": fix_available,
            },
        )

    def _parse_advisory_v6(
        self, advisory: dict, project_path: Path
    ) -> Optional[RawFinding]:
        severity_str = advisory.get("severity", "low")
        severity = SEVERITY_MAP.get(severity_str.lower(), FindingSeverity.MEDIUM)
        module_name = advisory.get("module_name", "unknown")
        title = advisory.get("title", "")
        overview = advisory.get("overview", "")
        recommendation = advisory.get("recommendation", "Upgrade to a non-vulnerable version.")
        cves = advisory.get("cves", [])
        cwe = advisory.get("cwe", None)

        return RawFinding(
            scanner_name=self.name,
            rule_id=str(advisory.get("id", "unknown")),
            category="vulnerable_dependency",
            severity=severity,
            confidence=FindingConfidence.HIGH,
            file_path=str(project_path / "package.json"),
            line_start=None,
            line_end=None,
            title=f"Vulnerable npm package: {module_name} - {title}",
            description=overview,
            recommendation=recommendation,
            cve_id=cves[0] if cves else None,
            cwe_id=cwe,
            raw_metadata={
                "module": module_name,
                "advisory_id": advisory.get("id"),
            },
        )
