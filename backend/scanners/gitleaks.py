"""Gitleaks secret detection scanner adapter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from backend.core.security import REDACTION_PLACEHOLDER
from backend.scanners.base import (
    BaseScanner,
    FindingConfidence,
    FindingSeverity,
    RawFinding,
    ScanContext,
    ScannerCategory,
)


class GitleaksScanner(BaseScanner):
    """Gitleaks secret and credential detection scanner."""

    name = "gitleaks"
    category = ScannerCategory.SECRET
    supported_languages = ["*"]  # All files

    def supports(self, file_path: str) -> bool:
        # Skip binary and generated files
        excluded = {
            ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
            ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".tar", ".gz",
        }
        return Path(file_path).suffix.lower() not in excluded

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["gitleaks", "version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, _ = await self._run_subprocess(["gitleaks", "version"])
        if code == 0:
            return stdout.strip()
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        args = [
            "gitleaks",
            "detect",
            "--source", str(context.project_path),
            "--report-format", "json",
            "--report-path", "/dev/stdout",
            "--no-git",
            "--exit-code", "0",
        ]

        code, stdout, stderr = await self._run_subprocess(
            args, cwd=context.project_path
        )

        if code not in (0, 1):
            if not stdout.strip():
                raise RuntimeError(f"Gitleaks failed: {stderr[:500]}")

        return self._parse_output(stdout, context.project_path)

    def _parse_output(self, output: str, project_path: Path) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not output.strip() or output.strip() in ("null", "[]"):
            return findings

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return findings

        if not isinstance(data, list):
            return findings

        for result in data:
            try:
                finding = self._parse_result(result, project_path)
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        return findings

    def _parse_result(self, result: dict, project_path: Path) -> Optional[RawFinding]:
        rule_id = result.get("RuleID", result.get("ruleID", "unknown"))
        description = result.get("Description", result.get("description", ""))
        secret = result.get("Secret", result.get("secret", ""))
        file_path = result.get("File", result.get("file", ""))
        line_start = result.get("StartLine", result.get("startLine"))
        line_end = result.get("EndLine", result.get("endLine"))
        match = result.get("Match", result.get("match", ""))
        author = result.get("Author", "")
        commit = result.get("Commit", "")

        # NEVER store or log the actual secret
        # Build description without the secret value
        safe_match = match
        if secret and secret in safe_match:
            safe_match = safe_match.replace(secret, REDACTION_PLACEHOLDER)

        title = f"Potential secret detected: {description}"
        full_description = (
            f"Rule: {rule_id}\n"
            f"Description: {description}\n"
            f"Match (redacted): {safe_match}\n"
        )
        if commit:
            full_description += f"Commit: {commit[:8]}\n"

        recommendation = (
            "Remove the secret from the source code immediately. "
            "Rotate the credential if it was committed to any branch. "
            "Use environment variables or a secrets manager instead. "
            "Consider adding this pattern to .gitignore or .gitleaksignore."
        )

        return RawFinding(
            scanner_name=self.name,
            rule_id=rule_id,
            category="secret_detection",
            severity=FindingSeverity.CRITICAL,
            confidence=FindingConfidence.HIGH,
            file_path=str(Path(file_path).relative_to(project_path))
            if file_path and Path(file_path).is_absolute() else file_path,
            line_start=line_start,
            line_end=line_end,
            title=title,
            description=full_description,
            code_snippet=safe_match[:200] if safe_match else None,  # Redacted match only
            recommendation=recommendation,
            cwe_id="CWE-798",  # Use of Hard-coded Credentials
            raw_metadata={
                "rule_id": rule_id,
                "author": author,
                "commit": commit[:8] if commit else None,
                # DO NOT include "secret" or "match" with actual value
            },
        )
