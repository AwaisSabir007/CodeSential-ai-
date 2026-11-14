"""Unit tests for multi-agent investigation orchestrator and worker agents."""
import pytest
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.state import AgentFindingContext


@pytest.mark.asyncio
async def test_agent_orchestrator_full_workflow():
    orchestrator = AgentOrchestrator()
    ctx = AgentFindingContext(
        finding_id="find_test_100",
        project_id="proj_alpha",
        scanner_name="bandit",
        rule_id="B602",
        category="command_injection",
        severity="high",
        file_path="app/server.py",
        line_number=42,
        snippet="subprocess.call(f'rm -rf {path}', shell=True)",
        title="Subprocess call with shell=True",
        description="Dangerous command injection vulnerability",
    )

    state = await orchestrator.execute_investigation(ctx)
    assert state.status == "completed"
    assert len(state.completed_steps) >= 5
    assert state.neural_risk_score is not None
    assert state.neural_risk_score > 0.3
    assert state.candidate_patch is not None
    assert state.evaluation_confidence > 0.5
    assert len(state.evidence) >= 4
