"""Base scanner interface for CodeSentinel AI."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScannerStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ScannerCategory(str, Enum):
    SECURITY = "security"
    DEPENDENCY = "dependency"
    SECRET = "secret"
    COMPLEXITY = "complexity"
    PERFORMANCE = "performance"
    STYLE = "style"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RawFinding:
    """A normalized finding from any scanner."""
    scanner_name: str
    rule_id: str
    category: str
    severity: FindingSeverity
    confidence: FindingConfidence
    file_path: str
    line_start: Optional[int]
    line_end: Optional[int]
    title: str
    description: str
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScannerResult:
    """The result of a single scanner execution."""
    scanner_name: str
    status: ScannerStatus
    version: Optional[str]
    findings: List[RawFinding]
    duration_seconds: float
    error_message: Optional[str] = None
    files_scanned: int = 0


@dataclass
class ScanContext:
    """Context passed to each scanner describing what to scan."""
    project_id: str
    project_path: Path
    target_files: Optional[List[Path]] = None  # None = full project scan
    scan_type: str = "full"


class BaseScanner(ABC):
    """Abstract base class for all CodeSentinel scanners."""

    name: str = "base"
    category: ScannerCategory = ScannerCategory.SECURITY
    supported_languages: List[str] = []

    def __init__(self, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = timeout_seconds
        self._version_cache: Optional[str] = None

    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether this scanner's executable is installed."""
        ...

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """Return True if this scanner can analyze the given file."""
        ...

    @abstractmethod
    async def _run_scan(self, context: ScanContext) -> List[RawFinding]:
        """Execute the scan and return raw normalized findings."""
        ...

    async def get_version(self) -> Optional[str]:
        """Return the scanner version string."""
        if self._version_cache is not None:
            return self._version_cache
        self._version_cache = await self._fetch_version()
        return self._version_cache

    async def _fetch_version(self) -> Optional[str]:
        """Override to return the scanner version."""
        return None

    async def scan(self, context: ScanContext) -> ScannerResult:
        """Run the scanner with timeout and error handling."""
        started = datetime.utcnow()

        if not await self.is_available():
            return ScannerResult(
                scanner_name=self.name,
                status=ScannerStatus.UNAVAILABLE,
                version=None,
                findings=[],
                duration_seconds=0.0,
                error_message=f"Scanner '{self.name}' is not installed or not in PATH",
            )

        # Check if there are relevant files
        if context.target_files is not None:
            relevant = [f for f in context.target_files if self.supports(str(f))]
            if not relevant:
                return ScannerResult(
                    scanner_name=self.name,
                    status=ScannerStatus.SKIPPED,
                    version=await self.get_version(),
                    findings=[],
                    duration_seconds=0.0,
                    error_message="No relevant files for this scanner",
                )

        try:
            findings = await asyncio.wait_for(
                self._run_scan(context),
                timeout=self.timeout_seconds,
            )
            duration = (datetime.utcnow() - started).total_seconds()
            return ScannerResult(
                scanner_name=self.name,
                status=ScannerStatus.COMPLETED,
                version=await self.get_version(),
                findings=findings,
                duration_seconds=duration,
                files_scanned=len(context.target_files) if context.target_files else -1,
            )
        except asyncio.TimeoutError:
            duration = (datetime.utcnow() - started).total_seconds()
            return ScannerResult(
                scanner_name=self.name,
                status=ScannerStatus.TIMED_OUT,
                version=await self.get_version(),
                findings=[],
                duration_seconds=duration,
                error_message=f"Scanner timed out after {self.timeout_seconds}s",
            )
        except Exception as exc:
            duration = (datetime.utcnow() - started).total_seconds()
            return ScannerResult(
                scanner_name=self.name,
                status=ScannerStatus.FAILED,
                version=await self.get_version(),
                findings=[],
                duration_seconds=duration,
                error_message=str(exc),
            )

    async def _run_subprocess(
        self, args: List[str], cwd: Optional[Path] = None
    ) -> tuple[int, str, str]:
        """Run an external command and return (returncode, stdout, stderr)."""
        import os
        import sys
        from pathlib import Path
        env = os.environ.copy()
        extra_paths = [
            str(Path(sys.executable).parent),  # venv bin: finds scanners installed with the app
            str(Path.home() / "Library/Python/3.9/bin"),
            str(Path.home() / ".local/bin"),
            "/usr/local/bin",
            "/opt/homebrew/bin",
        ]
        env["PATH"] = ":".join(extra_paths) + ":" + env.get("PATH", "")

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            stdout_bytes, stderr_bytes = await proc.communicate()
            return (
                proc.returncode or 0,
                stdout_bytes.decode("utf-8", errors="replace"),
                stderr_bytes.decode("utf-8", errors="replace"),
            )
        except FileNotFoundError:
            return (-1, "", f"Command not found: {args[0]}")
        except Exception as exc:
            return (-1, "", str(exc))
