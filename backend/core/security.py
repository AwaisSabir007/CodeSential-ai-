"""Security utilities for CodeSentinel AI."""
from __future__ import annotations

import hashlib
import hmac
import re
from pathlib import Path
from typing import Optional

# Patterns for redacting secrets in output
_SECRET_PATTERNS = [
    re.compile(r'(api[_-]?key\s*[:=]\s*)["\']?([A-Za-z0-9_\-]{20,})["\']?', re.IGNORECASE),
    re.compile(r'(token\s*[:=]\s*)["\']?([A-Za-z0-9_\-\.]{20,})["\']?', re.IGNORECASE),
    re.compile(r'(password\s*[:=]\s*)["\']?([^\s"\']{8,})["\']?', re.IGNORECASE),
    re.compile(r'(secret\s*[:=]\s*)["\']?([A-Za-z0-9_\-\.]{16,})["\']?', re.IGNORECASE),
    re.compile(r'(sk-(?:proj-)?[A-Za-z0-9_\-]{20,})', re.IGNORECASE),  # OpenAI keys (sk- and sk-proj-)
    re.compile(r'(ghp_[A-Za-z0-9]{36,})', re.IGNORECASE),  # GitHub tokens
    re.compile(r'(AIza[0-9A-Za-z_\-]{35,})', re.IGNORECASE),  # Google API keys
]

REDACTION_PLACEHOLDER = "[REDACTED]"


def redact_secrets(text: str) -> str:
    """Replace detected secret patterns with a redaction placeholder."""
    def _replace(m: re.Match) -> str:
        try:
            # Two-group patterns: keep prefix (group 1), replace secret (group 2)
            prefix_end = m.start(2) - m.start(0)
            return m.group(0)[:prefix_end] + REDACTION_PLACEHOLDER
        except IndexError:
            # Single-group patterns: replace the whole match
            return REDACTION_PLACEHOLDER

    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(_replace, text)
    return text


def validate_project_path(path: str | Path, allowed_roots: Optional[list[Path]] = None) -> Path:
    """
    Validate that a project path is safe to monitor.

    - Must be an absolute path
    - Must exist and be a directory
    - Must not be a system-critical directory
    - Must not be a symlink escaping to a restricted area (if allowed_roots provided)
    """
    p = Path(path).resolve()

    if not p.is_absolute():
        raise ValueError(f"Path must be absolute: {path}")

    if not p.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not p.is_dir():
        raise ValueError(f"Path must be a directory: {path}")

    # Block system-critical directories
    forbidden_prefixes = [
        Path("/etc"), Path("/bin"), Path("/sbin"), Path("/usr/bin"),
        Path("/usr/sbin"), Path("/var/run"), Path("/System"),
        Path("/Windows"), Path("C:/Windows"), Path("C:/System32"),
    ]
    p_str = str(p.resolve())
    for forbidden in forbidden_prefixes:
        forbidden_str = str(forbidden.resolve()) if forbidden.exists() else str(forbidden)
        if p_str == forbidden_str or p_str.startswith(forbidden_str + "/") or p_str.startswith(forbidden_str + "\\"):
            raise ValueError(f"Path '{path}' is a system-critical directory")

    if allowed_roots:
        resolved = p.resolve()
        if not any(
            str(resolved).startswith(str(root.resolve()))
            for root in allowed_roots
        ):
            raise ValueError(f"Path '{path}' is outside allowed roots")

    return p


def safe_relative_path(base: Path, target: Path) -> Optional[str]:
    """
    Return a relative path string if target is within base, else None.
    Prevents path traversal attacks.
    """
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        rel = target_resolved.relative_to(base_resolved)
        return str(rel)
    except ValueError:
        return None


def compute_file_hash(path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Compute the hash of a file's content for change detection."""
    try:
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return None


def compute_content_hash(content: str | bytes, algorithm: str = "sha256") -> str:
    """Compute hash of string/bytes content."""
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace")
    return hashlib.new(algorithm, content).hexdigest()


def generate_finding_fingerprint(
    scanner: str,
    rule_id: str,
    file_path: str,
    code_snippet: str,
) -> str:
    """
    Generate a stable fingerprint for a finding based on code context,
    not line numbers.
    """
    content = f"{scanner}:{rule_id}:{file_path}:{code_snippet.strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def verify_local_token(token: str, expected_token: str) -> bool:
    """Constant-time comparison for local API tokens."""
    return hmac.compare_digest(token.encode(), expected_token.encode())
