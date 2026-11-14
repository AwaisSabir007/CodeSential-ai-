"""Multi-Agent Investigation Orchestrator."""
from __future__ import annotations

import time
import uuid
from typing import Optional

from backend.agents.deep_learning import DeepLearningAgent
from backend.agents.dependency import DependencyAnalysisAgent
from backend.agents.evaluation import EvaluationAgent
from backend.agents.performance import PerformanceAnalysisAgent
from backend.agents.planning import PlanningAgent
from backend.agents.remediation import RemediationAgent
from backend.agents.security import SecurityInvestigationAgent
from backend.agents.state import AgentFindingContext, InvestigationState
from backend.agents.verification import VerificationAgent
from backend.core.logging import get_logger
from backend.llm.router import LLMRouter, get_router

logger = get_logger("codesentinel.agents.orchestrator")


class AgentOrchestrator:
    """Coordinates state transitions, agent execution graph, and resource limits."""

    def __init__(self, router: Optional[LLMRouter] = None):
        self.router = router or get_router()
        self.planning_agent = PlanningAgent(self.router)
        self.security_agent = SecurityInvestigationAgent(self.router)
        self.dependency_agent = DependencyAnalysisAgent(self.router)
        self.performance_agent = PerformanceAnalysisAgent(self.router)
        self.dl_agent = DeepLearningAgent()
        self.remediation_agent = RemediationAgent(self.router)
        self.verification_agent = VerificationAgent()
        self.evaluation_agent = EvaluationAgent()

    async def execute_investigation(
        self,
        finding_context: AgentFindingContext,
        investigation_id: Optional[str] = None,
    ) -> InvestigationState:
        """Run full multi-agent investigation workflow for a finding."""
        inv_id = investigation_id or f"inv_{uuid.uuid4().hex[:12]}"
        state = InvestigationState(
            investigation_id=inv_id,
            project_id=finding_context.project_id,
            finding=finding_context,
            status="in_progress",
        )

        logger.info("investigation_started", investigation_id=inv_id, rule_id=finding_context.rule_id)
        start_time = time.perf_counter()

        try:
            # Stage 1: Planning
            state.current_agent = "planning"
            state = await self.planning_agent.run(state)

            # Stage 2: Deep Learning Neural Risk Assessment
            state.current_agent = "deep_learning"
            state = await self.dl_agent.run(state)

            # Stage 3: Domain Specialization Branch
            cat = finding_context.category.lower()
            scanner = finding_context.scanner_name.lower()
            if "dependency" in cat or "audit" in scanner:
                state.current_agent = "dependency"
                state = await self.dependency_agent.run(state)
            elif "performance" in cat or "complexity" in scanner:
                state.current_agent = "performance"
                state = await self.performance_agent.run(state)
            else:
                state.current_agent = "security"
                state = await self.security_agent.run(state)

            # Stage 4: Remediation
            state.current_agent = "remediation"
            state = await self.remediation_agent.run(state)

            # Stage 5: Verification
            state.current_agent = "verification"
            state = await self.verification_agent.run(state)

            # Stage 6: Evaluation
            state.current_agent = "evaluation"
            state = await self.evaluation_agent.run(state)

            duration = (time.perf_counter() - start_time) * 1000
            logger.info("investigation_completed", investigation_id=inv_id, duration_ms=round(duration, 2))

        except Exception as e:
            logger.error("investigation_failed", investigation_id=inv_id, error=str(e))
            state.status = "failed"
            state.error = str(e)

        return state
