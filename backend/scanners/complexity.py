"""Code complexity scanner using radon for Python."""
from __future__ import annotations

import ast
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


class ComplexityScanner(BaseScanner):
    """Code complexity analysis scanner using radon and AST analysis."""

    name = "complexity"
    category = ScannerCategory.COMPLEXITY
    supported_languages = ["python"]

    # Cyclomatic complexity thresholds
    HIGH_COMPLEXITY_THRESHOLD = 10
    VERY_HIGH_COMPLEXITY_THRESHOLD = 20

    def supports(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == ".py"

    async def is_available(self) -> bool:
        code, _, _ = await self._run_subprocess(["radon", "--version"])
        return code == 0

    async def _fetch_version(self) -> Optional[str]:
        code, stdout, _ = await self._run_subprocess(["radon", "--version"])
        if code == 0:
            return stdout.strip()
        return None

    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        findings: List[RawFinding] = []

        if context.target_files:
            py_files = [f for f in context.target_files if f.suffix.lower() == ".py"]
        else:
            py_files = list(context.project_path.rglob("*.py"))
            # Filter out excluded directories
            excluded = {"venv", ".venv", "__pycache__", ".git", "node_modules"}
            py_files = [
                f for f in py_files
                if not any(part in excluded for part in f.parts)
            ]

        for py_file in py_files:
            file_findings = await self._analyze_file(py_file, context.project_path)
            findings.extend(file_findings)

        return findings

    async def _analyze_file(self, file_path: Path, project_path: Path) -> List[RawFinding]:
        findings: List[RawFinding] = []
        try:
            # 1. Use radon cc if available
            radon_findings = await self._radon_complexity(file_path, project_path)
            findings.extend(radon_findings)
        except Exception:
            pass

        try:
            # 2. Deep Time Complexity, Space Complexity, and GPU Acceleration Analysis
            from backend.analysis.performance_engine import ASTComplexityVisitor
            content = file_path.read_text(encoding="utf-8", errors="replace")
            rel_path = str(file_path.relative_to(project_path) if file_path.is_absolute() else file_path)
            tree = ast.parse(content)
            visitor = ASTComplexityVisitor(str(file_path), content, rel_path)
            visitor.visit(tree)

            for hs in visitor.hotspots:
                sev = (
                    FindingSeverity.HIGH if hs.severity == "high"
                    else FindingSeverity.MEDIUM if hs.severity == "medium"
                    else FindingSeverity.LOW
                )
                findings.append(RawFinding(
                    scanner_name=self.name,
                    rule_id=f"PERF_{hs.category.upper()}",
                    category=hs.category,
                    severity=sev,
                    confidence=FindingConfidence.HIGH,
                    file_path=hs.file_path,
                    line_start=hs.line_start,
                    line_end=hs.line_end,
                    title=f"[{hs.estimated_time_complexity}] {hs.issue_description.split('.')[0]}",
                    description=f"{hs.issue_description}\n\nHardware Impact: {hs.hardware_impact}",
                    code_snippet=hs.before_code,
                    recommendation=f"{hs.optimization_recommendation}\n\nSuggested Refactor:\n```python\n{hs.after_code}\n```",
                    raw_metadata={
                        "cyclomatic": hs.cyclomatic_complexity,
                        "time_complexity": hs.estimated_time_complexity,
                        "space_complexity": hs.estimated_space_complexity,
                        "category": hs.category,
                        "after_code": hs.after_code,
                        "hardware_impact": hs.hardware_impact,
                    },
                ))

            if not findings:
                findings.extend(self._ast_complexity(file_path, project_path))

        except Exception:
            pass

        return findings

    async def _radon_complexity(
        self, file_path: Path, project_path: Path
    ) -> List[RawFinding]:
        findings: List[RawFinding] = []
        code, stdout, _ = await self._run_subprocess([
            "radon", "cc", "--json", "--min", "C",  # C = complexity >= 5
            str(file_path)
        ])

        if code != 0 or not stdout.strip():
            return findings

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return findings

        for _filepath, results in data.items():
            for item in results:
                complexity = item.get("complexity", 0)
                name = item.get("name", "unknown")
                lineno = item.get("lineno", 0)
                rank = item.get("rank", "C")

                if complexity >= self.VERY_HIGH_COMPLEXITY_THRESHOLD:
                    severity = FindingSeverity.HIGH
                elif complexity >= self.HIGH_COMPLEXITY_THRESHOLD:
                    severity = FindingSeverity.MEDIUM
                else:
                    severity = FindingSeverity.LOW

                relative_path = str(
                    file_path.relative_to(project_path)
                    if file_path.is_absolute() else file_path
                )

                findings.append(RawFinding(
                    scanner_name=self.name,
                    rule_id="HIGH_COMPLEXITY",
                    category="complexity",
                    severity=severity,
                    confidence=FindingConfidence.HIGH,
                    file_path=relative_path,
                    line_start=lineno,
                    line_end=lineno,
                    title=f"High cyclomatic complexity in '{name}' (CC={complexity}, rank={rank})",
                    description=(
                        f"Function/method '{name}' has a cyclomatic complexity of {complexity} "
                        f"(rank {rank}). High complexity increases the likelihood of bugs and "
                        f"makes the code harder to test and maintain."
                    ),
                    recommendation=(
                        f"Refactor '{name}' to reduce its complexity below "
                        f"{self.HIGH_COMPLEXITY_THRESHOLD}. "
                        "Consider extracting smaller helper functions or simplifying branching logic."
                    ),
                    raw_metadata={"complexity": complexity, "rank": rank, "name": name},
                ))

        return findings

    def _ast_complexity(
        self, file_path: Path, project_path: Path
    ) -> List[RawFinding]:
        """Fallback AST-based complexity estimation."""
        findings: List[RawFinding] = []
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except Exception:
            return findings

        relative_path = str(
            file_path.relative_to(project_path)
            if file_path.is_absolute() else file_path
        )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._count_branches(node)
                if complexity >= self.HIGH_COMPLEXITY_THRESHOLD:
                    severity = (
                        FindingSeverity.HIGH
                        if complexity >= self.VERY_HIGH_COMPLEXITY_THRESHOLD
                        else FindingSeverity.MEDIUM
                    )
                    findings.append(RawFinding(
                        scanner_name=self.name,
                        rule_id="HIGH_COMPLEXITY",
                        category="complexity",
                        severity=severity,
                        confidence=FindingConfidence.MEDIUM,  # AST estimate
                        file_path=relative_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno,
                        title=f"High estimated complexity in '{node.name}' (~{complexity} branches)",
                        description=(
                            f"Function '{node.name}' contains approximately {complexity} "
                            "branch points. This is a heuristic estimate from AST analysis."
                        ),
                        recommendation=(
                            "Refactor to reduce branching. Extract helper functions. "
                            "Install 'radon' for accurate cyclomatic complexity measurement."
                        ),
                        raw_metadata={"estimated_complexity": complexity},
                    ))

        return findings

    def _count_branches(self, node: ast.AST) -> int:
        """Count branch points in a function AST node."""
        count = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (
                ast.If, ast.While, ast.For, ast.ExceptHandler,
                ast.With, ast.Assert,
            )):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
        return count
