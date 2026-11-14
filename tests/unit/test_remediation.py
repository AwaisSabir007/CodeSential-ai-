"""Unit tests for diff generator, patch validation, and approval workflow."""
import pytest
from pathlib import Path
import tempfile
from backend.remediation.diff import create_unified_diff
from backend.remediation.validation import PatchValidator
from backend.remediation.patches import PatchManager
from backend.remediation.approval import ApprovalStateMachine


def test_diff_creation():
    orig = "def fetch():\n    return False\n"
    mod = "def fetch():\n    return True\n"
    diff = create_unified_diff(orig, mod, file_path="test.py")
    assert diff.additions == 1
    assert diff.deletions == 1
    assert "-    return False" in diff.unified_diff
    assert "+    return True" in diff.unified_diff


def test_patch_validation_python():
    valid_code = "def secure_query(user_id):\n    return db.query(user_id)\n"
    invalid_code = "def broken(:\n    syntax error\n"

    res_valid = PatchValidator.validate_patch(valid_code, "app.py")
    assert res_valid.is_valid is True

    res_invalid = PatchValidator.validate_patch(invalid_code, "app.py")
    assert res_invalid.is_valid is False
    assert len(res_invalid.errors) > 0


def test_patch_application_and_backup():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "app.py"
        target.write_text("orig_content = 1\n")

        backup = PatchManager.apply_patch_safely(target, "mod_content = 2\n")
        assert backup.exists()
        assert target.read_text() == "mod_content = 2\n"

        # Test rollback
        rolled_back = PatchManager.rollback_patch(target)
        assert rolled_back is True
        assert target.read_text() == "orig_content = 1\n"


def test_approval_state_machine():
    proposal = PatchManager.generate_candidate_patch(
        patch_id="p1",
        finding_id="f1",
        file_path="service.py",
        original_code="old = 1",
        modified_code="new = 2",
        explanation="Safe refactor",
    )
    assert proposal.status == "verified"
    ApprovalStateMachine.transition(proposal, "approved")
    assert proposal.status == "approved"
