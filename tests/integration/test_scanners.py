"""Integration tests for the scanner adapters."""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from backend.scanners.bandit import BanditScanner
from backend.scanners.base import ScanContext, ScannerStatus
from backend.scanners.complexity import ComplexityScanner
from backend.scanners.semgrep import SemgrepScanner


VULNERABLE_PYTHON = '''
import subprocess
import pickle
import os

def execute_command(user_input):
    """Dangerous: OS command injection."""
    result = subprocess.run(user_input, shell=True)
    return result

def deserialize_data(data):
    """Dangerous: unsafe deserialization."""
    return pickle.loads(data)

def run_eval(code):
    """Dangerous: arbitrary code execution."""
    return eval(code)

API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"

def complex_function(x, y, z, w):
    """High cyclomatic complexity."""
    if x > 0:
        if y > 0:
            if z > 0:
                if w > 0:
                    for i in range(x):
                        for j in range(y):
                            if i > j:
                                result = i * j
                            elif i == j:
                                result = i + j
                            else:
                                result = i - j
                    return result
                else:
                    return -1
            elif z < 0:
                return -2
            else:
                return 0
        else:
            return -3
    else:
        return -4
'''

SAFE_PYTHON = '''
"""A simple safe module."""
import json
from pathlib import Path

def read_config(path: Path) -> dict:
    """Safely read a JSON config file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
'''


@pytest.fixture
def vulnerable_project(tmp_path):
    """Create a temp project with known-vulnerable code."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "vulnerable.py").write_text(VULNERABLE_PYTHON)
    (src / "safe.py").write_text(SAFE_PYTHON)
    return tmp_path


@pytest.fixture
def scan_context(vulnerable_project):
    return ScanContext(
        project_id="test-project",
        project_path=vulnerable_project,
    )


class TestBanditScanner:
    @pytest.mark.asyncio
    async def test_bandit_availability(self):
        scanner = BanditScanner()
        available = await scanner.is_available()
        # Either available or not — both are valid
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_bandit_scans_vulnerable_code(self, scan_context):
        scanner = BanditScanner()
        if not await scanner.is_available():
            pytest.skip("Bandit not installed")

        result = await scanner.scan(scan_context)
        assert result.status in (ScannerStatus.COMPLETED, ScannerStatus.SKIPPED)

        if result.status == ScannerStatus.COMPLETED:
            assert len(result.findings) > 0
            # Should find subprocess or pickle issues
            rule_ids = {f.rule_id for f in result.findings}
            assert bool(rule_ids.intersection({"B301", "B404", "B602", "B603", "B307"}))

    @pytest.mark.asyncio
    async def test_bandit_supports_python(self):
        scanner = BanditScanner()
        assert scanner.supports("app.py")
        assert scanner.supports("/path/to/main.py")

    @pytest.mark.asyncio
    async def test_bandit_ignores_non_python(self):
        scanner = BanditScanner()
        assert not scanner.supports("app.js")
        assert not scanner.supports("index.ts")
        assert not scanner.supports("style.css")


class TestComplexityScanner:
    @pytest.mark.asyncio
    async def test_complexity_scans_code(self, scan_context):
        scanner = ComplexityScanner()
        result = await scanner.scan(scan_context)
        assert result.status in (
            ScannerStatus.COMPLETED, ScannerStatus.UNAVAILABLE, ScannerStatus.SKIPPED
        )

    @pytest.mark.asyncio
    async def test_ast_complexity_analysis(self, tmp_path):
        """Test fallback AST complexity analysis."""
        src = tmp_path / "complex.py"
        src.write_text(VULNERABLE_PYTHON)

        scanner = ComplexityScanner()
        context = ScanContext(project_id="test", project_path=tmp_path)

        # Use AST directly
        findings = scanner._ast_complexity(src, tmp_path)
        # Should detect the complex_function
        assert any("complex_function" in f.title for f in findings)


class TestSemgrepScanner:
    @pytest.mark.asyncio
    async def test_semgrep_availability(self):
        scanner = SemgrepScanner()
        available = await scanner.is_available()
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_semgrep_supports_extensions(self):
        scanner = SemgrepScanner()
        assert scanner.supports("app.py")
        assert scanner.supports("index.js")
        assert scanner.supports("component.tsx")
        assert not scanner.supports("image.jpg")
        assert not scanner.supports("binary.exe")
