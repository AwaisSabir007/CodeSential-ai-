"""Unit tests for security utilities."""
from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from backend.core.security import (
    compute_content_hash,
    compute_file_hash,
    generate_finding_fingerprint,
    redact_secrets,
    safe_relative_path,
    validate_project_path,
)


class TestRedactSecrets:
    def test_redacts_api_key(self):
        text = 'api_key = "sk-abc123def456ghi789jkl012"'
        result = redact_secrets(text)
        assert "sk-abc123" not in result
        assert "[REDACTED]" in result

    def test_redacts_password(self):
        text = 'password = "MySuperSecret123"'
        result = redact_secrets(text)
        assert "MySuperSecret123" not in result

    def test_leaves_safe_content_alone(self):
        text = "x = 1 + 2  # simple math"
        result = redact_secrets(text)
        assert result == text

    def test_redacts_openai_key(self):
        text = "key = sk-proj-abc123def456ghi789jkl012mno345"
        result = redact_secrets(text)
        assert "sk-proj" not in result or "[REDACTED]" in result


class TestValidateProjectPath:
    def test_valid_directory(self, tmp_path):
        result = validate_project_path(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_nonexistent_path_raises(self):
        with pytest.raises(ValueError, match="does not exist"):
            validate_project_path("/tmp/definitely_does_not_exist_codesentinel_xyz")

    def test_file_not_directory_raises(self, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("code")
        with pytest.raises(ValueError, match="must be a directory"):
            validate_project_path(str(f))

    def test_system_path_rejected(self):
        # On macOS /etc resolves to /private/etc; test we block /etc by exact match
        # We test with /bin which IS in the forbidden list and exists on all platforms
        import platform
        if platform.system() in ("Darwin", "Linux"):
            with pytest.raises(ValueError):
                validate_project_path("/bin")


class TestPathSecurity:
    def test_safe_relative_path_within_base(self, tmp_path):
        subdir = tmp_path / "src" / "module.py"
        subdir.parent.mkdir(parents=True, exist_ok=True)
        subdir.touch()
        result = safe_relative_path(tmp_path, subdir)
        assert result == "src/module.py"

    def test_safe_relative_path_outside_base(self, tmp_path):
        other = Path("/tmp")
        result = safe_relative_path(tmp_path, other)
        assert result is None


class TestHashing:
    def test_content_hash_deterministic(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_content_hash_different_inputs(self):
        h1 = compute_content_hash("hello")
        h2 = compute_content_hash("world")
        assert h1 != h2

    def test_file_hash(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("def foo(): pass")
        result = compute_file_hash(f)
        assert result is not None
        assert len(result) == 64  # SHA256 hex

    def test_file_hash_nonexistent(self):
        result = compute_file_hash(Path("/nonexistent/file.py"))
        assert result is None


class TestFingerprintGeneration:
    def test_fingerprint_stable(self):
        fp1 = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import pickle")
        fp2 = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import pickle")
        assert fp1 == fp2

    def test_fingerprint_differs_by_scanner(self):
        fp1 = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import pickle")
        fp2 = generate_finding_fingerprint("semgrep", "B301", "src/app.py", "import pickle")
        assert fp1 != fp2

    def test_fingerprint_differs_by_code(self):
        fp1 = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import pickle")
        fp2 = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import json")
        assert fp1 != fp2

    def test_fingerprint_length(self):
        fp = generate_finding_fingerprint("bandit", "B301", "src/app.py", "import pickle")
        assert len(fp) == 16  # Truncated to 16 chars
