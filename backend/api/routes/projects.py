"""Projects API routes."""
from __future__ import annotations

import asyncio
import logging
import platform
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from backend.api.schemas.models import (
    MessageResponse,
    MonitoringStatusOut,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from backend.core.security import validate_project_path
from backend.database.repositories import ProjectRepository
from backend.database.session import get_db
from backend.services.scan_service import MonitoringService, ScanService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_scan_service() -> ScanService:
    from backend.main import app_state
    return app_state["scan_service"]


def get_monitoring_service() -> MonitoringService:
    from backend.main import app_state
    return app_state["monitoring_service"]


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
):
    """List all registered projects."""
    repo = ProjectRepository(session)
    projects = await repo.list_all(active_only=active_only)
    return [ProjectOut.model_validate(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_db),
):
    """Register a new project for monitoring."""
    # Validate path
    try:
        validated_path = validate_project_path(body.get_path())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = ProjectRepository(session)

    # Check for duplicates
    existing = await repo.get_by_path(str(validated_path))
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project at path '{validated_path}' is already registered",
        )

    project = await repo.create(
        name=body.name,
        path=str(validated_path),
        description=body.description,
        language=body.language,
    )
    return ProjectOut.model_validate(project)


@router.post("/browse-folder")
async def browse_folder():
    """Opens a native OS folder selection dialog and returns the selected directory path."""
    selected_path = ""
    system = platform.system()
    try:
        if system == "Darwin":
            cmd = [
                "osascript",
                "-e",
                'POSIX path of (choose folder with prompt "Select Project Folder to Monitor with CodeSentinel AI")',
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                selected_path = stdout.decode().strip()
                if selected_path.endswith("/"):
                    selected_path = selected_path[:-1]
        elif system == "Linux":
            proc = await asyncio.create_subprocess_exec(
                "zenity", "--file-selection", "--directory", "--title=Select Project Folder",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                selected_path = stdout.decode().strip()
        elif system == "Windows":
            ps_script = "[System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null; $f = New-Object System.Windows.Forms.FolderBrowserDialog; if($f.ShowDialog() -eq 'OK'){ $f.SelectedPath }"
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                selected_path = stdout.decode().strip()
    except Exception as e:
        logger.warning("Native folder picker failed: %s", e)

    if not selected_path:
        return {"path": "", "name": "", "status": "cancelled"}

    p = Path(selected_path)
    return {"path": str(p), "name": p.name, "status": "selected"}


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get a specific project by ID."""
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Update project metadata."""
    repo = ProjectRepository(session)
    project = await repo.update(
        project_id,
        **{k: v for k, v in body.model_dump().items() if v is not None}
    )
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Delete a project and its data."""
    monitoring_service.stop_monitoring if monitoring_service.is_monitoring(project_id) else None
    if monitoring_service.is_monitoring(project_id):
        await monitoring_service.stop_monitoring(project_id)

    repo = ProjectRepository(session)
    deleted = await repo.delete(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return MessageResponse(message="Project deleted successfully")


@router.post("/{project_id}/monitor/start", response_model=MessageResponse)
async def start_monitoring(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Start filesystem monitoring for a project."""
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if monitoring_service.is_monitoring(project_id):
        return MessageResponse(message="Already monitoring this project")

    await monitoring_service.start_monitoring(project_id, project.path)
    await repo.update_monitoring(project_id, enabled=True)

    return MessageResponse(message="Monitoring started", detail=project.path)


@router.post("/{project_id}/monitor/stop", response_model=MessageResponse)
async def stop_monitoring(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Stop filesystem monitoring for a project."""
    repo = ProjectRepository(session)
    await repo.update_monitoring(project_id, enabled=False)
    stopped = await monitoring_service.stop_monitoring(project_id)
    if stopped:
        return MessageResponse(message="Monitoring stopped")
    return MessageResponse(message="Project was not being monitored")


@router.get("/{project_id}/monitor/status", response_model=MonitoringStatusOut)
async def monitoring_status(
    project_id: str,
    session: AsyncSession = Depends(get_db),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Get monitoring status for a project."""
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    path = project.path if project else None
    return MonitoringStatusOut(
        project_id=project_id,
        is_monitoring=monitoring_service.is_monitoring(project_id),
        monitored_path=path,
    )


@router.get("/{project_id}/optimization")
async def get_project_optimization(
    project_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Run real-time deep algorithmic complexity, space efficiency, and GPU bottleneck analysis."""
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    from backend.analysis.performance_engine import PerformanceEngine
    summary = PerformanceEngine.analyze_project(Path(project.path))

    return {
        "project_id": project_id,
        "total_files_analyzed": summary.total_files_analyzed,
        "total_functions_analyzed": summary.total_functions_analyzed,
        "average_cyclomatic_complexity": summary.average_cyclomatic_complexity,
        "maintainability_index": summary.maintainability_index,
        "time_complexity_distribution": summary.time_complexity_distribution,
        "gpu_optimization_count": summary.gpu_optimization_count,
        "hotspots": [
            {
                "function": h.function_name,
                "file": f"{h.file_path}:{h.line_start}",
                "file_path": h.file_path,
                "line_start": h.line_start,
                "line_end": h.line_end,
                "cyclomatic": h.cyclomatic_complexity,
                "loop_depth": h.loop_depth,
                "time_complexity": h.estimated_time_complexity,
                "space_complexity": h.estimated_space_complexity,
                "category": h.category,
                "severity": h.severity,
                "issue": h.issue_description,
                "optimization": h.optimization_recommendation,
                "before_code": h.before_code,
                "after_code": h.after_code,
                "hardware_impact": h.hardware_impact,
            }
            for h in summary.hotspots
        ],
    }
