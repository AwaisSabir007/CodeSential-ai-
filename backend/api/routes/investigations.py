"""Investigations API routes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.state import AgentFindingContext, InvestigationState

router = APIRouter(prefix="/investigations", tags=["investigations"])

# In-memory store for active and completed investigations
_INVESTIGATIONS_CACHE: Dict[str, InvestigationState] = {}
_orchestrator = AgentOrchestrator()


class TriggerInvestigationRequest(BaseModel):
    project_id: str
    finding_id: str
    scanner_name: str
    rule_id: str
    category: str
    severity: str
    file_path: str
    line_number: Optional[int] = 1
    snippet: str = ""
    title: str = ""
    description: str = ""


@router.post("", response_model=Dict[str, Any])
async def trigger_investigation(payload: TriggerInvestigationRequest):
    """Trigger an autonomous multi-agent security investigation."""
    ctx = AgentFindingContext(**payload.model_dump())
    state = await _orchestrator.execute_investigation(ctx)
    _INVESTIGATIONS_CACHE[state.investigation_id] = state

    # If a candidate patch was synthesized, register it as a formal PatchProposal
    if state.candidate_patch:
        try:
            from backend.api.routes.patches import _PATCHES_CACHE
            from backend.remediation.patches import PatchManager
            patch_id = f"patch_{state.investigation_id}"
            proposal = PatchManager.generate_candidate_patch(
                patch_id=patch_id,
                finding_id=payload.finding_id,
                file_path=payload.file_path,
                original_code=payload.snippet or state.candidate_patch,
                modified_code=state.candidate_patch,
                explanation=state.patch_explanation or "Automated remediation patch synthesized by multi-agent investigation.",
            )
            _PATCHES_CACHE[patch_id] = proposal
        except Exception:
            pass

    return state.model_dump()


@router.get("", response_model=List[Dict[str, Any]])
async def list_investigations(project_id: Optional[str] = None):
    """List recent investigations."""
    res = list(_INVESTIGATIONS_CACHE.values())
    if project_id:
        res = [inv for inv in res if inv.project_id == project_id]
    return [inv.model_dump() for inv in res]


@router.get("/{investigation_id}", response_model=Dict[str, Any])
async def get_investigation(investigation_id: str):
    """Get full state and evidence trace of an investigation."""
    inv = _INVESTIGATIONS_CACHE.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv.model_dump()


@router.post("/{investigation_id}/cancel")
async def cancel_investigation(investigation_id: str):
    inv = _INVESTIGATIONS_CACHE.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    inv.status = "cancelled"
    return {"status": "cancelled", "investigation_id": investigation_id}
