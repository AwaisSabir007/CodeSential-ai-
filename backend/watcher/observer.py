"""Filesystem watcher using Watchdog with debouncing and hashing."""
from __future__ import annotations

import asyncio
import fnmatch
import time
from pathlib import Path
from threading import Lock
from typing import Callable, Dict, List, Optional, Set

from watchdog.events import (
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.security import compute_file_hash

logger = get_logger(__name__)


class ChangeEvent:
    """A debounced filesystem change event."""

    def __init__(self, project_id: str, changed_files: List[str], event_type: str) -> None:
        self.project_id = project_id
        self.changed_files = changed_files
        self.event_type = event_type
        self.timestamp = time.time()


class DebouncedEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler that:
    - Debounces rapid events
    - Skips excluded paths
    - Uses content hashing to detect real changes
    - Calls back asynchronously
    """

    def __init__(
        self,
        project_id: str,
        project_path: Path,
        callback: Callable,
        loop: asyncio.AbstractEventLoop,
        debounce_seconds: float = 1.5,
        excluded_dirs: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None,
        max_file_size: int = 5 * 1024 * 1024,
    ) -> None:
        super().__init__()
        self.project_id = project_id
        self.project_path = project_path
        self.callback = callback
        self.loop = loop
        self.debounce_seconds = debounce_seconds
        self.excluded_dirs: Set[str] = set(excluded_dirs or [])
        self.excluded_extensions: Set[str] = set(excluded_extensions or [])
        self.max_file_size = max_file_size

        self._lock = Lock()
        self._pending_files: Dict[str, str] = {}  # path -> event_type
        self._debounce_task: Optional[asyncio.TimerHandle] = None
        self._hash_cache: Dict[str, str] = {}

    def _is_excluded(self, path: str) -> bool:
        """Return True if this path should be ignored."""
        p = Path(path)

        # Check directory components
        for part in p.parts:
            if part in self.excluded_dirs:
                return True
            # Glob-style patterns
            for pattern in self.excluded_dirs:
                if fnmatch.fnmatch(part, pattern):
                    return True

        # Check extension
        if p.suffix.lower() in self.excluded_extensions:
            return True

        # Check file size for existing files
        try:
            if p.exists() and p.stat().st_size > self.max_file_size:
                return True
        except OSError:
            return True

        return False

    def _has_content_changed(self, path: str) -> bool:
        """Return True if file content actually changed (using hash)."""
        try:
            p = Path(path)
            if not p.exists() or not p.is_file():
                return True  # Deleted files count as changed
            new_hash = compute_file_hash(p)
            if new_hash is None:
                return True
            old_hash = self._hash_cache.get(path)
            if old_hash == new_hash:
                return False
            self._hash_cache[path] = new_hash
            return True
        except Exception:
            return True

    def _schedule_flush(self) -> None:
        """Schedule a debounced flush."""
        if self._debounce_task:
            try:
                self._debounce_task.cancel()
            except Exception:
                pass
        self._debounce_task = self.loop.call_later(
            self.debounce_seconds, self._flush
        )

    def _flush(self) -> None:
        """Fire the callback with accumulated changes."""
        with self._lock:
            if not self._pending_files:
                return
            changed = list(self._pending_files.keys())
            event_type = "mixed" if len(set(self._pending_files.values())) > 1 else list(self._pending_files.values())[0]
            self._pending_files.clear()

        event = ChangeEvent(
            project_id=self.project_id,
            changed_files=changed,
            event_type=event_type,
        )
        asyncio.run_coroutine_threadsafe(
            self.callback(event), self.loop
        )

    def _handle(self, event: FileSystemEvent, event_type: str) -> None:
        path = event.src_path
        if self._is_excluded(path):
            return
        if event_type == "modified" and not self._has_content_changed(path):
            return

        with self._lock:
            self._pending_files[path] = event_type

        self.loop.call_soon_threadsafe(self._schedule_flush)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event, "deleted")

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            self._handle(event, "moved")


class ProjectWatcher:
    """Manages Watchdog observers for multiple projects."""

    def __init__(self) -> None:
        self._observers: Dict[str, Observer] = {}
        self._handlers: Dict[str, DebouncedEventHandler] = {}

    def start_watching(
        self,
        project_id: str,
        project_path: Path,
        callback: Callable,
        loop: asyncio.AbstractEventLoop,
        excluded_dirs: Optional[List[str]] = None,
        excluded_extensions: Optional[List[str]] = None,
    ) -> None:
        """Start watching a project directory."""
        if project_id in self._observers:
            logger.warning("Already watching project", project_id=project_id)
            return

        settings = get_settings()

        all_excluded_dirs = list(set(
            (excluded_dirs or []) + settings.default_excluded_dirs
        ))
        all_excluded_exts = list(set(
            (excluded_extensions or []) + settings.default_excluded_extensions
        ))

        handler = DebouncedEventHandler(
            project_id=project_id,
            project_path=project_path,
            callback=callback,
            loop=loop,
            debounce_seconds=settings.debounce_seconds,
            excluded_dirs=all_excluded_dirs,
            excluded_extensions=all_excluded_exts,
            max_file_size=settings.max_file_size_bytes,
        )

        observer = Observer()
        observer.schedule(handler, str(project_path), recursive=True)
        observer.start()

        self._observers[project_id] = observer
        self._handlers[project_id] = handler

        logger.info(
            "Started watching project",
            project_id=project_id,
            path=str(project_path),
        )

    def stop_watching(self, project_id: str) -> bool:
        """Stop watching a project."""
        observer = self._observers.pop(project_id, None)
        self._handlers.pop(project_id, None)
        if observer:
            observer.stop()
            observer.join(timeout=5)
            logger.info("Stopped watching project", project_id=project_id)
            return True
        return False

    def stop_all(self) -> None:
        """Stop all project watchers."""
        for project_id in list(self._observers.keys()):
            self.stop_watching(project_id)

    def is_watching(self, project_id: str) -> bool:
        return project_id in self._observers

    def get_watched_projects(self) -> List[str]:
        return list(self._observers.keys())
