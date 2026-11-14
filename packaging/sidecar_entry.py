"""PyInstaller entrypoint for the CodeSentinel backend sidecar.

Runs the FastAPI application with uvicorn, bound to localhost only.
Host/port can be overridden with CODESENTINEL_HOST / CODESENTINEL_PORT.

When CODESENTINEL_PARENT_WATCHDOG=1 (set by the Tauri desktop shell), a
watchdog thread monitors the desktop app process and terminates the backend
if the app dies without cleaning up — this covers force-quit and crashes,
where the PyInstaller bootloader cannot forward any signal.
"""
from __future__ import annotations

import multiprocessing
import os
import threading
import time


def _start_parent_watchdog() -> None:
    """Exit when the process that spawned our bootloader disappears."""
    try:
        import psutil

        me = psutil.Process(os.getpid())
        parent = me.parent()  # PyInstaller onefile bootloader (or shell in dev)
        anchor = parent.parent() if parent else None  # the Tauri desktop app
        anchor_pid = anchor.pid if anchor else None
    except Exception:
        anchor_pid = None

    if not anchor_pid or anchor_pid <= 1:
        return

    def _watch() -> None:
        import psutil

        while True:
            time.sleep(2.0)
            if not psutil.pid_exists(anchor_pid):
                os._exit(0)

    threading.Thread(target=_watch, name="parent-watchdog", daemon=True).start()


def main() -> None:
    import uvicorn

    from backend.main import app

    if os.environ.get("CODESENTINEL_PARENT_WATCHDOG") == "1":
        _start_parent_watchdog()

    host = os.environ.get("CODESENTINEL_HOST", "127.0.0.1")
    port = int(os.environ.get("CODESENTINEL_PORT", "8765"))
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
