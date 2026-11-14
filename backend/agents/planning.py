"""Planning Agent: triages findings and devises bounded investigation strategy."""
from __future__ import annotations

from backend.agents.state import InvestigationState
from backend.llm.router import LLMRouter


class PlanningAgent:
    """Constructs prioritized, bounded investigation plan based on finding category & risk."""

    def __init__(self, router: LLMRouter):
        self.router = router

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        steps = [
            f"1. Inspect AST and context around {finding.file_path}:{finding.line_number}",
            "2. Evaluate neural vulnerability risk score for snippet",
        ]

        if "dependency" in finding.category.lower() or "audit" in finding.scanner_name.lower():
            steps.append("3. Cross-reference CVE advisory and verify dependency upgrade compatibility")
        elif "performance" in finding.category.lower() or "complexity" in finding.scanner_name.lower():
            steps.append("3. Profile cyclomatic complexity and algorithmic hot spots")
        else:
            steps.append("3. Trace data-flow and taint source-to-sink paths")

        steps.extend([
            "4. Formulate minimal non-breaking remediation patch",
            "5. Execute isolated verification & AST validation",
            "6. Synthesize final evidence report",
        ])

        state.plan_steps = steps
        state.completed_steps.append("Planning & Triage")
        state.tool_call_count += 1
        return state
