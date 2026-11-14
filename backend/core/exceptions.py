"""Custom exceptions for CodeSentinel AI."""
from __future__ import annotations


class CodeSentinelError(Exception):
    """Base exception for CodeSentinel AI."""
    pass


class ProjectNotFoundError(CodeSentinelError):
    """Raised when a project cannot be found."""
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project '{project_id}' not found")
        self.project_id = project_id


class ProjectAlreadyExistsError(CodeSentinelError):
    """Raised when trying to add a project that already exists."""
    def __init__(self, path: str) -> None:
        super().__init__(f"Project at path '{path}' already registered")
        self.path = path


class InvalidPathError(CodeSentinelError):
    """Raised when a path is outside allowed roots or invalid."""
    def __init__(self, path: str, reason: str = "invalid or unauthorized") -> None:
        super().__init__(f"Path '{path}' is {reason}")
        self.path = path


class ScannerNotAvailableError(CodeSentinelError):
    """Raised when a required scanner is not installed."""
    def __init__(self, scanner_name: str) -> None:
        super().__init__(f"Scanner '{scanner_name}' is not available")
        self.scanner_name = scanner_name


class ScanTimeoutError(CodeSentinelError):
    """Raised when a scan exceeds its time limit."""
    def __init__(self, scanner_name: str, timeout: int) -> None:
        super().__init__(f"Scanner '{scanner_name}' timed out after {timeout}s")
        self.scanner_name = scanner_name
        self.timeout = timeout


class FindingNotFoundError(CodeSentinelError):
    """Raised when a finding cannot be found."""
    def __init__(self, finding_id: str) -> None:
        super().__init__(f"Finding '{finding_id}' not found")
        self.finding_id = finding_id


class ScanNotFoundError(CodeSentinelError):
    """Raised when a scan cannot be found."""
    def __init__(self, scan_id: str) -> None:
        super().__init__(f"Scan '{scan_id}' not found")
        self.scan_id = scan_id


class InvestigationNotFoundError(CodeSentinelError):
    """Raised when an investigation cannot be found."""
    def __init__(self, investigation_id: str) -> None:
        super().__init__(f"Investigation '{investigation_id}' not found")
        self.investigation_id = investigation_id


class LLMProviderError(CodeSentinelError):
    """Raised when an LLM provider fails."""
    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(f"LLM provider '{provider}' error: {reason}")
        self.provider = provider


class RemediationError(CodeSentinelError):
    """Raised when remediation fails."""
    pass


class ConfigurationError(CodeSentinelError):
    """Raised when configuration is invalid."""
    pass
