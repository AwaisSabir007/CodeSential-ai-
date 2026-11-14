"""Dependency Analysis Agent: analyzes CVEs and upgrade paths."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.llm.base import GenerationRequest, LLMMessage
from backend.llm.router import LLMRouter


class DependencyAnalysisAgent:
    """Investigates package vulnerabilities, breaking change risks, and remediation upgrade paths."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        prompt = (
            f"Analyze dependency finding in project:\n"
            f"Title: {finding.title}\n"
            f"Description: {finding.description}\n"
            f"Rule: {finding.rule_id}\n"
            f"Provide recommended version upgrade, breaking change precautions, and mitigation strategy."
        )

        req = GenerationRequest(
            messages=[
                LLMMessage(role="system", content="You are a DevSecOps Dependency Security Specialist."),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0.1,
            max_tokens=400,
        )

        resp = await self.router.generate(req)
        state.dependency_analysis = resp.content
        state.evidence.append({
            "agent": "DependencyAnalysisAgent",
            "analysis": resp.content,
        })
        state.completed_steps.append("Dependency Advisory & Compatibility Review")
        state.total_tokens_used += resp.total_tokens
        state.estimated_cost_usd += resp.cost_estimate_usd
        state.tool_call_count += 1
        return state
