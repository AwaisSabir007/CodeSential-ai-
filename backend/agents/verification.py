"""Verification Agent: checks patch syntax, AST integrity, and scanner clearance."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.remediation.validation import PatchValidator


class VerificationAgent:
    """Verifies that generated code repairs do not introduce syntax or structural defects."""

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        patch_code = state.candidate_patch or finding.snippet

        val_result = PatchValidator.validate_patch(patch_code, finding.file_path)

        state.verification_passed = val_result.is_valid
        if val_result.is_valid:
            state.verification_details = ["Syntax parsed cleanly without AST errors", "No mismatched blocks detected"]
        else:
            state.verification_details = val_result.errors

        state.evidence.append({
            "agent": "VerificationAgent",
            "passed": val_result.is_valid,
            "details": state.verification_details,
        })
        state.completed_steps.append("Patch Verification & AST Syntax Clearance")
        state.tool_call_count += 1
        return state
