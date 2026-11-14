"""Patches and Autonomous Remediation API routes."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.remediation.approval import ApprovalStateMachine
from backend.remediation.patches import PatchManager, PatchProposal

router = APIRouter(prefix="/patches", tags=["patches"])

# Cache of generated patches
_PATCHES_CACHE: Dict[str, PatchProposal] = {}


class GeneratePatchRequest(BaseModel):
    patch_id: str
    finding_id: str
    file_path: str
    original_code: str
    modified_code: str
    explanation: str


@router.post("/generate", response_model=Dict[str, Any])
async def generate_patch(payload: GeneratePatchRequest):
    """Generate structured candidate patch proposal."""
    proposal = PatchManager.generate_candidate_patch(
        patch_id=payload.patch_id,
        finding_id=payload.finding_id,
        file_path=payload.file_path,
        original_code=payload.original_code,
        modified_code=payload.modified_code,
        explanation=payload.explanation,
    )
    _PATCHES_CACHE[proposal.patch_id] = proposal
    return proposal.model_dump()


@router.get("", response_model=List[Dict[str, Any]])
async def list_patches():
    """List all generated candidate patches."""
    return [p.model_dump() for p in _PATCHES_CACHE.values()]


@router.get("/{patch_id}", response_model=Dict[str, Any])
async def get_patch(patch_id: str):
    patch = _PATCHES_CACHE.get(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return patch.model_dump()


@router.post("/{patch_id}/verify", response_model=Dict[str, Any])
async def verify_patch(patch_id: str):
    patch = _PATCHES_CACHE.get(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    proposal = PatchManager.generate_candidate_patch(
        patch_id=patch.patch_id,
        finding_id=patch.finding_id,
        file_path=patch.file_path,
        original_code=patch.original_code,
        modified_code=patch.modified_code,
        explanation=patch.explanation,
    )
    _PATCHES_CACHE[patch_id] = proposal
    return proposal.model_dump()


@router.post("/{patch_id}/approve", response_model=Dict[str, Any])
async def approve_patch(patch_id: str, apply_immediately: bool = False):
    """Developer human-in-the-loop approval."""
    patch = _PATCHES_CACHE.get(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    # Idempotent: already applied — just return current state without re-transitioning
    if patch.status == "applied":
        return {
            "status": patch.status,
            "patch_id": patch_id,
            "backup_path": None,
            "message": "Patch already applied.",
        }

    # If still in verified/pending state, approve it first
    if patch.status not in ("approved",):
        ApprovalStateMachine.transition(patch, "approved")

    backup_path = None
    if apply_immediately:
        target = Path(patch.file_path)
        if target.exists():
            backup_path = PatchManager.apply_patch_safely(target, patch.modified_code)
        # Transition approved → applied (valid per state machine)
        ApprovalStateMachine.transition(patch, "applied")

    return {
        "status": patch.status,
        "patch_id": patch_id,
        "backup_path": str(backup_path) if backup_path else None,
    }


@router.post("/{patch_id}/reject", response_model=Dict[str, Any])
async def reject_patch(patch_id: str, reason: Optional[str] = None):
    patch = _PATCHES_CACHE.get(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    patch.status = "rejected"
    return {"status": "rejected", "patch_id": patch_id, "reason": reason}


@router.post("/{patch_id}/rollback", response_model=Dict[str, Any])
async def rollback_patch(patch_id: str):
    patch = _PATCHES_CACHE.get(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    target = Path(patch.file_path)
    success = PatchManager.rollback_patch(target)
    if success:
        patch.status = "verified"
    return {"status": "rolled_back" if success else "failed", "patch_id": patch_id}
