"""Developer approval workflow manager for remediation patches."""
from __future__ import annotations

from backend.core.exceptions import RemediationError
from backend.remediation.patches import PatchProposal


class ApprovalStateMachine:
    """Enforces human-in-the-loop review state machine."""

    VALID_TRANSITIONS = {
        "pending": ["verified", "rejected"],
        "verified": ["approved", "rejected"],
        "approved": ["applied", "failed"],
        "applied": ["reverted"],
        "rejected": [],
        "reverted": [],
    }

    @classmethod
    def can_transition(cls, current_status: str, next_status: str) -> bool:
        return next_status in cls.VALID_TRANSITIONS.get(current_status, [])

    @classmethod
    def transition(cls, proposal: PatchProposal, next_status: str) -> PatchProposal:
        if not cls.can_transition(proposal.status, next_status):
            raise RemediationError(
                f"Invalid patch transition: cannot move from '{proposal.status}' to '{next_status}'"
            )
        proposal.status = next_status
        return proposal
