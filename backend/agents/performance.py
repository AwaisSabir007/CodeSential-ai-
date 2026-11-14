"""Performance Analysis Agent: investigates complexity hotspots and algorithmic efficiency."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.llm.base import GenerationRequest, LLMMessage
from backend.llm.router import LLMRouter


class PerformanceAnalysisAgent:
    """Evaluates algorithmic complexity, nested loops, allocations, and optimization targets."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        prompt = (
            f"Review performance complexity for:\n"
            f"File: {finding.file_path}:{finding.line_number}\n"
            f"Snippet:\n```\n{finding.snippet}\n```\n"
            f"Suggest specific algorithmic optimizations (e.g. O(n^2) to O(n), memoization, generator streams)."
        )

        req = GenerationRequest(
            messages=[
                LLMMessage(role="system", content="You are a Systems Performance and Optimization Engineer."),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0.1,
            max_tokens=400,
        )

        resp = await self.router.generate(req)
        state.performance_analysis = resp.content
        state.evidence.append({
            "agent": "PerformanceAnalysisAgent",
            "analysis": resp.content,
        })
        state.completed_steps.append("Complexity & Performance Review")
        state.total_tokens_used += resp.total_tokens
        state.estimated_cost_usd += resp.cost_estimate_usd
        state.tool_call_count += 1
        return state
