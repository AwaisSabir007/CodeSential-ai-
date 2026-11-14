"""Scan orchestration service."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.core.logging import get_logger
from backend.database.repositories import ScanRepository
from backend.database.session import get_db_session
from backend.findings.normalization import FindingsNormalizer
from backend.scanners.base import ScanContext
from backend.scanners.registry import ScanRunner
from backend.watcher.observer import ChangeEvent, ProjectWatcher

logger = get_logger(__name__)

# Global SSE event queue for real-time notifications
_event_queue: asyncio.Queue = asyncio.Queue(maxsize=500)


async def push_event(event_type: str, data: dict) -> None:
    """Push a real-time event to the SSE queue."""
    try:
        await asyncio.wait_for(
            _event_queue.put({"type": event_type, "data": data, "ts": datetime.utcnow().isoformat()}),
            timeout=0.1,
        )
    except (asyncio.TimeoutError, asyncio.QueueFull):
        pass  # Drop event if queue is full


async def get_event_queue() -> asyncio.Queue:
    return _event_queue


class ScanService:
    """
    Orchestrates full scan lifecycle:
    1. Creates ScanRun record
    2. Runs scanners concurrently
    3. Normalizes and persists findings
    4. Updates run status
    5. Pushes real-time events
    """

    def __init__(self) -> None:
        self._runner = ScanRunner()
        self._active_scans: Dict[str, asyncio.Task] = {}

    async def start_scan(
        self,
        project_id: str,
        project_path: str,
        trigger: str = "manual",
        scan_type: str = "full",
        target_files: Optional[List[str]] = None,
        enabled_scanners: Optional[List[str]] = None,
    ) -> str:
        """Start an async scan and return the scan_run_id."""
        async with get_db_session() as session:
            scan_repo = ScanRepository(session)
            scan_run = await scan_repo.create_scan_run(
                project_id=project_id,
                trigger=trigger,
                scan_type=scan_type,
                target_files=target_files,
            )
            scan_id = scan_run.id

        await push_event("scan_started", {
            "scan_id": scan_id,
            "project_id": project_id,
            "trigger": trigger,
        })

        task = asyncio.create_task(
            self._execute_scan(
                scan_id=scan_id,
                project_id=project_id,
                project_path=project_path,
                target_files=target_files,
                enabled_scanners=enabled_scanners,
            )
        )
        self._active_scans[scan_id] = task
        task.add_done_callback(lambda _: self._active_scans.pop(scan_id, None))

        return scan_id

    async def _execute_scan(
        self,
        scan_id: str,
        project_id: str,
        project_path: str,
        target_files: Optional[List[str]],
        enabled_scanners: Optional[List[str]],
    ) -> None:
        """Execute the scan asynchronously."""
        logger.info("Scan executing", scan_id=scan_id, project_id=project_id)
        started = datetime.utcnow()

        async with get_db_session() as session:
            scan_repo = ScanRepository(session)
            await scan_repo.update_scan_status(scan_id, "running", started_at=started)

        context = ScanContext(
            project_id=project_id,
            project_path=Path(project_path),
            target_files=[Path(f) for f in target_files] if target_files else None,
        )

        try:
            results = await self._runner.run_all(context, enabled_scanners)

            total_findings = 0
            async with get_db_session() as session:
                scan_repo = ScanRepository(session)
                normalizer = FindingsNormalizer(session)

                for result in results:
                    # Record scanner run
                    sr = await scan_repo.create_scanner_run(scan_id, result.scanner_name)
                    duration = result.duration_seconds
                    findings_count = len(result.findings)

                    await scan_repo.update_scanner_run(sr.id, **{
                        "status": result.status.value,
                        "version": result.version,
                        "started_at": started,
                        "completed_at": datetime.utcnow(),
                        "duration_seconds": duration,
                        "findings_count": findings_count,
                        "error_message": result.error_message,
                    })
                    total_findings += findings_count

                # Normalize and persist all findings
                new_count, updated_count = await normalizer.process_scanner_results(
                    project_id=project_id,
                    scan_run_id=scan_id,
                    project_path=project_path,
                    results=results,
                )

                # Update scan run status
                duration_total = (datetime.utcnow() - started).total_seconds()
                await scan_repo.update_scan_status(
                    scan_id,
                    "completed",
                    duration_seconds=duration_total,
                    findings_count=total_findings,
                )

            await push_event("scan_completed", {
                "scan_id": scan_id,
                "project_id": project_id,
                "total_findings": total_findings,
                "new_findings": new_count,
                "duration_seconds": duration_total,
            })

            logger.info(
                "Scan completed",
                scan_id=scan_id,
                total_findings=total_findings,
                new_findings=new_count,
            )

        except asyncio.CancelledError:
            async with get_db_session() as session:
                scan_repo = ScanRepository(session)
                await scan_repo.update_scan_status(scan_id, "cancelled")
            await push_event("scan_cancelled", {"scan_id": scan_id, "project_id": project_id})
            raise

        except Exception as exc:
            logger.error("Scan failed", scan_id=scan_id, error=str(exc))
            async with get_db_session() as session:
                scan_repo = ScanRepository(session)
                await scan_repo.update_scan_status(
                    scan_id, "failed", error_message=str(exc)[:1000]
                )
            await push_event("scan_failed", {
                "scan_id": scan_id,
                "project_id": project_id,
                "error": str(exc)[:200],
            })

    def cancel_scan(self, scan_id: str) -> bool:
        """Cancel an active scan."""
        task = self._active_scans.get(scan_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def get_active_scan_ids(self) -> List[str]:
        return list(self._active_scans.keys())


class MonitoringService:
    """Manages filesystem monitoring for projects."""

    def __init__(self, scan_service: ScanService) -> None:
        self._scan_service = scan_service
        self._watcher = ProjectWatcher()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def start_monitoring(
        self,
        project_id: str,
        project_path: str,
        excluded_dirs: Optional[List[str]] = None,
    ) -> None:
        """Start filesystem monitoring for a project."""
        loop = self._loop or asyncio.get_event_loop()
        self._watcher.start_watching(
            project_id=project_id,
            project_path=Path(project_path),
            callback=self._on_change,
            loop=loop,
            excluded_dirs=excluded_dirs,
        )
        await push_event("monitoring_started", {
            "project_id": project_id,
            "path": project_path,
        })

    async def stop_monitoring(self, project_id: str) -> bool:
        """Stop filesystem monitoring for a project."""
        result = self._watcher.stop_watching(project_id)
        if result:
            await push_event("monitoring_stopped", {"project_id": project_id})
        return result

    async def _on_change(self, event: ChangeEvent) -> None:
        """Callback triggered when files change."""
        logger.info(
            "File change detected",
            project_id=event.project_id,
            files_count=len(event.changed_files),
            event_type=event.event_type,
        )

        await push_event("file_changed", {
            "project_id": event.project_id,
            "files": event.changed_files[:20],  # Limit for event payload
            "event_type": event.event_type,
        })

        # Retrieve project path from DB and trigger incremental scan
        try:
            from backend.database.repositories import ProjectRepository
            async with get_db_session() as session:
                repo = ProjectRepository(session)
                project = await repo.get(event.project_id)
                if project and project.is_active:
                    await self._scan_service.start_scan(
                        project_id=event.project_id,
                        project_path=project.path,
                        trigger="file_change",
                        scan_type="incremental",
                        target_files=event.changed_files,
                    )
        except Exception as exc:
            logger.error(
                "Failed to trigger scan on file change",
                project_id=event.project_id,
                error=str(exc),
            )

    def is_monitoring(self, project_id: str) -> bool:
        return self._watcher.is_watching(project_id)

    def get_monitored_projects(self) -> List[str]:
        return self._watcher.get_watched_projects()

    def stop_all(self) -> None:
        self._watcher.stop_all()
