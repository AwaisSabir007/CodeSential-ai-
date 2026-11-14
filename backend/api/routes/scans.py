"""Scans API routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.models import MessageResponse, ScanCreate, ScanRunOut
from backend.database.repositories import ProjectRepository, ScanRepository
from backend.database.session import get_db
from backend.services.scan_service import ScanService

router = APIRouter(prefix="/scans", tags=["scans"])


def get_scan_service() -> ScanService:
    from backend.main import app_state
    return app_state["scan_service"]


@router.post("", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    body: ScanCreate,
    session: AsyncSession = Depends(get_db),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Trigger a new scan for a project."""
    repo = ProjectRepository(session)
    project = await repo.get(body.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{body.project_id}' not found")

    scan_id = await scan_service.start_scan(
        project_id=body.project_id,
        project_path=project.path,
        trigger="manual",
        scan_type=body.scan_type,
        target_files=body.target_files,
        enabled_scanners=body.enabled_scanners,
    )
    return {"scan_id": scan_id, "status": "queued", "project_id": body.project_id}


@router.get("", response_model=List[ScanRunOut])
async def list_scans(
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
):
    """List scan runs, optionally filtered by project."""
    repo = ScanRepository(session)
    scans = await repo.list_scan_runs(project_id=project_id, limit=limit, offset=offset)
    return [ScanRunOut.model_validate(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanRunOut)
async def get_scan(
    scan_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get a specific scan run by ID."""
    repo = ScanRepository(session)
    scan = await repo.get_scan_run(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    return ScanRunOut.model_validate(scan)


@router.post("/{scan_id}/cancel", response_model=MessageResponse)
async def cancel_scan(
    scan_id: str,
    scan_service: ScanService = Depends(get_scan_service),
):
    """Cancel an active scan."""
    cancelled = scan_service.cancel_scan(scan_id)
    if cancelled:
        return MessageResponse(message="Scan cancellation requested")
    return MessageResponse(message="Scan is not active or already completed")
