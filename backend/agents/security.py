"""Security Investigation Agent: inspects code context and traces data flow."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.llm.base import GenerationRequest, LLMMessage
from backend.llm.router import LLMRouter


class SecurityInvestigationAgent:
    """Analyzes AST taint flow, source-to-sink reachability, and correlates scanner outputs."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        prompt = (
            f"Analyze the following potential security vulnerability in {finding.file_path}:\n"
            f"Scanner: {finding.scanner_name} | Rule: {finding.rule_id} | Category: {finding.category}\n"
            f"Code snippet around line {finding.line_number}:\n```\n{finding.snippet}\n```\n"
            f"Provide:\n"
            f"1. Is this a confirmed finding or likely false positive?\n"
            f"2. Data-flow analysis (source of untrusted input to dangerous sink)\n"
            f"3. Why this is exploitable: impact and preconditions (conceptual, no exploit payloads)\n"
        )

        req = GenerationRequest(
            messages=[
                LLMMessage(role="system", content="You are a Principal Application Security Engineer."),
                LLMMessage(role="user", content=prompt),
            ],
            temperature=0.1,
            max_tokens=600,
        )

        resp = await self.router.generate(req)
        state.data_flow_analysis = resp.content
        state.evidence.append({
            "agent": "SecurityInvestigationAgent",
            "analysis": resp.content,
            "provider": resp.provider.value,
        })
        state.completed_steps.append("Security Code & Data-Flow Analysis")
        state.total_tokens_used += resp.total_tokens
        state.estimated_cost_usd += resp.cost_estimate_usd
        state.tool_call_count += 1
        return state
