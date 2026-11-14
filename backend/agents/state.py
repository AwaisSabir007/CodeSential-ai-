"""Investigation state schema for stateful agent workflows."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentFindingContext(BaseModel):
    finding_id: str
    project_id: str
    scanner_name: str
    rule_id: str
    category: str
    severity: str
    file_path: str
    line_number: Optional[int] = 1
    snippet: str = ""
    title: str = ""
    description: str = ""


class InvestigationState(BaseModel):
    investigation_id: str
    project_id: str
    finding: AgentFindingContext
    current_agent: str = "planning"
    status: str = "in_progress"  # in_progress, completed, failed, cancelled

    # Investigation plan
    plan_steps: List[str] = Field(default_factory=list)
    completed_steps: List[str] = Field(default_factory=list)

    # Evidence & Analysis
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    data_flow_analysis: Optional[str] = None
    neural_risk_score: Optional[float] = None
    neural_risk_explanation: Optional[str] = None
    dependency_analysis: Optional[str] = None
    performance_analysis: Optional[str] = None

    # Remediation
    candidate_patch: Optional[str] = None
    patch_explanation: Optional[str] = None
    verification_passed: bool = False
    verification_details: List[str] = Field(default_factory=list)

    # Evaluation
    evaluation_confidence: float = 0.0
    evaluation_summary: Optional[str] = None

    # Execution accounting
    total_tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    tool_call_count: int = 0
    max_tool_calls: int = 15
    error: Optional[str] = None
