"""System/health API routes and SSE events endpoint."""
from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.schemas.models import ScannerStatus, SystemHealth
from backend.core.config import get_settings
from backend.scanners.registry import ScannerRegistry
from backend.services.scan_service import MonitoringService, ScanService, get_event_queue

router = APIRouter(prefix="/system", tags=["system"])


def get_scan_service() -> ScanService:
    from backend.main import app_state
    return app_state.get("scan_service")


def get_monitoring_service() -> MonitoringService:
    from backend.main import app_state
    return app_state.get("monitoring_service")


@router.get("/health", response_model=SystemHealth)
@router.get("/status")
async def health_check(
    scan_service: ScanService = Depends(get_scan_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Health check endpoint."""
    settings = get_settings()
    scanner_statuses = ScannerRegistry._availability_cache
    available_count = sum(1 for v in scanner_statuses.values() if v)

    active_scans = len(scan_service.get_active_scan_ids()) if scan_service else 0
    monitored_projects = len(monitoring_service.get_monitored_projects()) if monitoring_service else 0

    return SystemHealth(
        status="healthy",
        version=settings.app_version,
        database="connected",
        scanners_available=available_count,
        active_scans=active_scans,
        monitored_projects=monitored_projects,
    )


@router.get("/scanners", response_model=List[ScannerStatus])
async def list_scanners():
    """Get status of all registered scanners."""
    statuses = await ScannerRegistry.get_scanner_status()
    return [ScannerStatus(**s) for s in statuses]


@router.get("/system/status")
async def system_status(
    scan_service: ScanService = Depends(get_scan_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """Detailed system status."""
    import psutil
    settings = get_settings()

    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "active_scans": scan_service.get_active_scan_ids(),
        "monitored_projects": monitoring_service.get_monitored_projects(),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
    }


@router.get("/events")
async def sse_events():
    """
    Server-Sent Events stream for real-time notifications.
    Connect from the frontend to receive scan, finding, and monitoring events.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await get_event_queue()
        # Send connected event
        yield f"data: {json.dumps({'type': 'connected', 'data': {}})}\n\n"

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
