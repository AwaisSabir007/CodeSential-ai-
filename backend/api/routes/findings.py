"""Findings API routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.models import FindingOut, FindingStatusUpdate, MessageResponse
from backend.database.repositories import FindingRepository
from backend.database.session import get_db

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("", response_model=List[FindingOut])
async def list_findings(
    project_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    scanner_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
):
    """List findings with optional filters."""
    repo = FindingRepository(session)
    findings = await repo.list_findings(
        project_id=project_id,
        severity=severity,
        status=status,
        scanner_name=scanner_name,
        limit=limit,
        offset=offset,
    )
    return [FindingOut.model_validate(f) for f in findings]


@router.get("/{finding_id}", response_model=FindingOut)
async def get_finding(
    finding_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get a specific finding by ID."""
    repo = FindingRepository(session)
    finding = await repo.get(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found")
    return FindingOut.model_validate(finding)


@router.patch("/{finding_id}", response_model=MessageResponse)
async def update_finding_status(
    finding_id: str,
    body: FindingStatusUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Update the status of a finding (e.g., mark as false positive)."""
    repo = FindingRepository(session)
    updated = await repo.update_status(finding_id, body.status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found")
    return MessageResponse(message=f"Finding status updated to '{body.status}'")
