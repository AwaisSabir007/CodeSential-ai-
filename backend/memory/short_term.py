"""Short-term agent memory for tracking in-flight investigations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentStepTrace(BaseModel):
    step_id: str
    agent_name: str
    action: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    status: str = "completed"  # completed, failed, skipped


class ShortTermMemory(BaseModel):
    """Ephemeral state memory for an active multi-agent investigation."""
    investigation_id: str
    project_id: str
    finding_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    traces: List[AgentStepTrace] = Field(default_factory=list)
    scratchpad: Dict[str, Any] = Field(default_factory=dict)
    tool_call_count: int = 0
    max_tool_calls: int = 15

    def add_step(
        self,
        agent_name: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        duration_ms: float = 0.0,
        status: str = "completed",
    ) -> AgentStepTrace:
        step = AgentStepTrace(
            step_id=f"step_{len(self.traces) + 1}",
            agent_name=agent_name,
            action=action,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            status=status,
        )
        self.traces.append(step)
        self.tool_call_count += 1
        return step

    def get_summary(self) -> str:
        lines = [f"Investigation {self.investigation_id} Summary:"]
        for t in self.traces:
            lines.append(f"- [{t.agent_name}] {t.action}: {t.status} ({t.duration_ms:.1f}ms)")
        return "\n".join(lines)
