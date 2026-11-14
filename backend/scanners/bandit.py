"""Bandit scanner adapter for Python security analysis."""
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

BANDIT_SEVERITY_MAP = {
    "HIGH": FindingSeverity.HIGH,
    "MEDIUM": FindingSeverity.MEDIUM,
    "LOW": FindingSeverity.LOW,
}

BANDIT_CONFIDENCE_MAP = {
    "HIGH": FindingConfidence.HIGH,
    "MEDIUM": FindingConfidence.MEDIUM,
    "LOW": FindingConfidence.LOW,
}

# Bandit test ID to CWE mapping (partial)
BANDIT_CWE_MAP = {
    "B101": "CWE-617",   # assert_used
    "B102": "CWE-78",    # exec_used
    "B103": "CWE-732",   # set_bad_file_permissions
    "B104": "CWE-605",   # hardcoded_bind_all_interfaces
    "B105": "CWE-259",   # hardcoded_password_string
    "B106": "CWE-259",   # hardcoded_password_funcarg
    "B107": "CWE-259",   # hardcoded_password_default
    "B108": "CWE-377",   # probably_insecure_file_operations
    "B110": "CWE-391",   # try_except_pass
    "B201": "CWE-94",    # flask_debug_true
    "B301": "CWE-502",   # pickle
    "B302": "CWE-502",   # marshal
    "B303": "CWE-327",   # md5
    "B304": "CWE-327",   # ciphers
    "B305": "CWE-327",   # cipher_modes
    "B306": "CWE-377",   # mktemp_q
    "B307": "CWE-78",    # eval
    "B310": "CWE-601",   # urllib_urlopen
    "B311": "CWE-330",   # random
    "B312": "CWE-605",   # telnetlib
    "B313": "CWE-611",   # xml_bad_cElementTree
    "B314": "CWE-611",   # xml_bad_ElementTree
    "B315": "CWE-611",   # xml_bad_expatreader
    "B324": "CWE-327",   # hashlib
    "B401": "CWE-319",   # import_telnetlib
    "B402": "CWE-319",   # import_ftplib
    "B403": "CWE-502",   # import_pickle
    "B404": "CWE-78",    # import_subprocess
    "B501": "CWE-295",   # request_with_no_cert_validation
    "B502": "CWE-326",   # ssl_with_bad_version
    "B601": "CWE-78",    # paramiko_calls
    "B602": "CWE-78",    # subprocess_popen_with_shell_equals_true
    "B603": "CWE-78",    # subprocess_without_shell_equals_true
    "B604": "CWE-78",    # any_other_function_with_shell_equals_true
    "B605": "CWE-78",    # start_process_with_a_shell
    "B606": "CWE-78",    # start_process_with_no_shell
    "B607": "CWE-78",    # start_process_with_partial_path
    "B608": "CWE-89",    # hardcoded_sql_expressions
    "B609": "CWE-78",    # linux_commands_wildcard_injection
    "B701": "CWE-94",    # jinja2_autoescape_false
    "B702": "CWE-79",    # use_of_mako_templates
    "B703": "CWE-116",   # django_mark_safe
}


class BanditScanner(BaseScanner):
    """Bandit Python security linting scanner."""

    name = "bandit"
    category = ScannerCategory.SECURITY
    supported_languages = ["python"]

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".py"

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["bandit", "--version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, stderr = await self._run_subprocess(["bandit", "--version"])
        if code == 0:
            output = stdout or stderr
            for line in output.splitlines():
                if "bandit" in line.lower():
                    return line.strip()
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        args = [
            "bandit",
            "--format", "json",
            "--quiet",
            "-r",
        ]

        if context.target_files:
            py_files = [
                str(f) for f in context.target_files
                if f.suffix.lower() == ".py"
            ]
            if not py_files:
                return []
            args.extend(py_files)
        else:
            args.append(str(context.project_path))

        code, stdout, stderr = await self._run_subprocess(
            args, cwd=context.project_path
        )

        # Bandit exits with 1 when findings are present
        if code not in (0, 1):
            if not stdout.strip():
                raise RuntimeError(f"Bandit failed: {stderr[:500]}")

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
                finding = self._parse_result(result)
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        return findings

    def _parse_result(self, result: dict) -> Optional[RawFinding]:
        test_id = result.get("test_id", "B000")
        test_name = result.get("test_name", "unknown")
        issue_severity = result.get("issue_severity", "MEDIUM").upper()
        issue_confidence = result.get("issue_confidence", "MEDIUM").upper()
        issue_text = result.get("issue_text", "")
        filename = result.get("filename", "")
        line_number = result.get("line_number")
        line_range = result.get("line_range", [])
        code = result.get("code", "")
        more_info = result.get("more_info", "")

        severity = BANDIT_SEVERITY_MAP.get(issue_severity, FindingSeverity.MEDIUM)
        confidence = BANDIT_CONFIDENCE_MAP.get(issue_confidence, FindingConfidence.MEDIUM)
        cwe_id = BANDIT_CWE_MAP.get(test_id)

        line_end = max(line_range) if line_range else line_number

        recommendation = None
        if more_info:
            recommendation = f"See Bandit documentation: {more_info}"

        return RawFinding(
            scanner_name=self.name,
            rule_id=test_id,
            category="security",
            severity=severity,
            confidence=confidence,
            file_path=filename,
            line_start=line_number,
            line_end=line_end,
            title=f"[{test_id}] {test_name.replace('_', ' ').title()}",
            description=issue_text,
            code_snippet=code[:500] if code else None,
            recommendation=recommendation,
            cwe_id=cwe_id,
            raw_metadata={
                "test_id": test_id,
                "test_name": test_name,
                "more_info": more_info,
            },
        )
