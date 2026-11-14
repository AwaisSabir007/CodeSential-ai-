"""Semgrep scanner adapter for CodeSentinel AI."""
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

SEMGREP_SEVERITY_MAP = {
    "ERROR": FindingSeverity.HIGH,
    "WARNING": FindingSeverity.MEDIUM,
    "INFO": FindingSeverity.LOW,
    "CRITICAL": FindingSeverity.CRITICAL,
}

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java",
    ".go", ".c", ".cpp", ".cs", ".rb", ".php",
}

# Bundled local rule packs (deterministic, offline). Falls back to the remote
# "auto" config only if the bundled rules directory is missing.
BUNDLED_RULES_DIR = Path(__file__).resolve().parents[2] / "rules"


class SemgrepScanner(BaseScanner):
    """Semgrep static analysis scanner."""

    name = "semgrep"
    category = ScannerCategory.SECURITY
    supported_languages = ["python", "javascript", "typescript"]

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["semgrep", "--version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, _ = await self._run_subprocess(["semgrep", "--version"])
        if code == 0:
            return stdout.strip().split("\n")[0]
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        config = str(BUNDLED_RULES_DIR) if BUNDLED_RULES_DIR.is_dir() else "auto"
        args = [
            "semgrep",
            "--config", config,
            "--json",
            "--no-git-ignore",
            "--timeout", "60",
            "--metrics=off",
            "--disable-version-check",
        ]

        if context.target_files:
            relevant = [
                str(f) for f in context.target_files
                if f.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
            if not relevant:
                return []
            args.extend(relevant)
        else:
            args.append(str(context.project_path))

        code, stdout, stderr = await self._run_subprocess(
            args, cwd=context.project_path
        )

        # Semgrep exits with 1 when findings are found (non-error)
        if code not in (0, 1):
            if not stdout.strip():
                raise RuntimeError(f"Semgrep failed: {stderr[:500]}")

        return self._parse_output(stdout, context.project_path)

    def _parse_output(self, output: str, project_path: Path) -> List[RawFinding]:
        findings: List[RawFinding] = []
        if not output.strip():
            return findings

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return findings

        for result in data.get("results", []):
            try:
                finding = self._parse_result(result, project_path)
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        return findings

    def _parse_result(self, result: dict, project_path: Path) -> Optional[RawFinding]:
        check_id = result.get("check_id", "unknown")
        # Local rule packs produce long dotted IDs that embed the absolute rules path
        # (e.g. "Users.macbookpro....rules.python.codesentinel.python.sql-injection-format").
        # Show a clean, short rule name instead.
        short_id = check_id
        if "codesentinel." in check_id:
            short_id = check_id.rsplit("codesentinel.", 1)[1]
        short_id = short_id.rsplit(".", 1)[-1]  # final segment, e.g. "sql-injection-format"
        path = result.get("path", "")
        start = result.get("start", {})
        end = result.get("end", {})
        extra = result.get("extra", {})
        message = extra.get("message", "")
        severity_str = extra.get("severity", "WARNING").upper()
        metadata = extra.get("metadata", {})
        fix = extra.get("fix", "")

        severity = SEMGREP_SEVERITY_MAP.get(severity_str, FindingSeverity.MEDIUM)
        confidence_str = metadata.get("confidence", "MEDIUM").upper()
        confidence = {
            "HIGH": FindingConfidence.HIGH,
            "MEDIUM": FindingConfidence.MEDIUM,
            "LOW": FindingConfidence.LOW,
        }.get(confidence_str, FindingConfidence.MEDIUM)

        # Derive category from metadata
        category = metadata.get("category", "security")
        if "cwe" in metadata:
            cwe_list = metadata["cwe"]
            if isinstance(cwe_list, list):
                cwe_id = cwe_list[0] if cwe_list else None
            else:
                cwe_id = str(cwe_list)
        else:
            cwe_id = None

        recommendation = fix if fix else metadata.get("fix", None)
        if not recommendation:
            references = metadata.get("references", [])
            if references:
                recommendation = f"See: {references[0]}"

        lines_content = extra.get("lines", "")

        return RawFinding(
            scanner_name=self.name,
            rule_id=short_id,
            category=category,
            severity=severity,
            confidence=confidence,
            file_path=path,
            line_start=start.get("line"),
            line_end=end.get("line"),
            title=f"[{short_id}] {message[:100]}",
            description=message,
            code_snippet=lines_content[:500] if lines_content else None,
            recommendation=recommendation,
            cwe_id=cwe_id,
            raw_metadata=metadata,
        )
