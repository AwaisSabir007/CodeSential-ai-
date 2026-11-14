"""Autonomous Remediation Subsystem."""
from backend.remediation.approval import ApprovalStateMachine
from backend.remediation.diff import DiffHunk, DiffResult, create_unified_diff
from backend.remediation.patches import PatchManager, PatchProposal
from backend.remediation.validation import PatchValidationResult, PatchValidator

__all__ = [
    "DiffResult",
    "DiffHunk",
    "create_unified_diff",
    "PatchValidator",
    "PatchValidationResult",
    "PatchProposal",
    "PatchManager",
    "ApprovalStateMachine",
]
