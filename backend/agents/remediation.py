"""Remediation Agent: synthesizes minimal non-breaking candidate patches."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.llm.base import GenerationRequest, LLMMessage
from backend.llm.router import LLMRouter


class RemediationAgent:
    """Generates precise, minimal code repairs that preserve original semantics."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        prompt = (
            f"Generate a secure replacement for the following code snippet from {finding.file_path}:\n"
            f"Vulnerability: {finding.title} ({finding.category})\n"
            f"Existing Code:\n```\n{finding.snippet}\n```\n"
            f"Rules:\n"
            f"1. Fix the vulnerability completely.\n"
            f"2. Keep the fix minimal and non-breaking.\n"
            f"3. Return ONLY the replacement code inside a ```code block followed by a brief explanation."
        )

        req = GenerationRequest(
            messages=[
                LLMMessage(role="system", content="You are a Principal Software Security Engineer specializing in automated remediation."),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0.1,
            max_tokens=600,
        )

        resp = await self.router.generate(req)
        content = resp.content

        # Extract code if present
        candidate_code = finding.snippet
        explanation = content
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                candidate_code = parts[1].strip()
                # strip optional language tag like python or ts
                if "\n" in candidate_code and not candidate_code.startswith("def ") and not candidate_code.startswith("import ") and not candidate_code.startswith("const "):
                    first_line, rest = candidate_code.split("\n", 1)
                    if len(first_line) < 15 and not any(ch in first_line for ch in "=(){};:"):
                        candidate_code = rest
                if len(parts) >= 3:
                    explanation = parts[2].strip()

        state.candidate_patch = candidate_code
        state.patch_explanation = explanation
        state.evidence.append({
            "agent": "RemediationAgent",
            "patch_generated": True,
            "explanation": explanation,
        })
        state.completed_steps.append("Candidate Remediation Patch Synthesis")
        state.total_tokens_used += resp.total_tokens
        state.estimated_cost_usd += resp.cost_estimate_usd
        state.tool_call_count += 1
        return state
