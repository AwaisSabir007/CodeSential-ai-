"""CodeSentinel AI Backend — FastAPI Application Entry Point."""
from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict

import click
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import get_settings
from backend.core.exceptions import (
    CodeSentinelError,
    FindingNotFoundError,
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    ScanNotFoundError,
)
from backend.core.logging import configure_logging, get_logger
from backend.database.session import create_tables
from backend.scanners.registry import ScannerRegistry
from backend.services.scan_service import MonitoringService, ScanService

# Global state accessible by route handlers
app_state: Dict[str, Any] = {}

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    logger.info("Starting CodeSentinel AI Backend", version=settings.app_version)

    # Initialize database
    await create_tables()
    logger.info("Database initialized")

    # Initialize scanner registry
    ScannerRegistry.register_defaults()
    availability = await ScannerRegistry.check_availability()
    available = [name for name, avail in availability.items() if avail]
    unavailable = [name for name, avail in availability.items() if not avail]
    logger.info(
        "Scanner availability checked",
        available=available,
        unavailable=unavailable,
    )

    # Initialize services
    scan_service = ScanService()
    monitoring_service = MonitoringService(scan_service)
    monitoring_service.set_loop(asyncio.get_event_loop())

    app_state["scan_service"] = scan_service
    app_state["monitoring_service"] = monitoring_service

    logger.info("CodeSentinel AI Backend ready", host=settings.host, port=settings.port)

    yield  # Application runs here

    # Cleanup
    logger.info("Shutting down CodeSentinel AI Backend")
    monitoring_service.stop_all()
    logger.info("All monitors stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CodeSentinel AI",
        description="Agentic AI Code Security and Vulnerability Detection Platform",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS for local Tauri/Vite frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Security Headers enforcing Antigravity / Vibe-Check guidelines
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "connect-src 'self' http://127.0.0.1:8765 http://localhost:5173 ws://127.0.0.1:8765 ws://localhost:5173; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        )
        return response

    # Exception handlers
    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found_handler(request: Request, exc: ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(ProjectAlreadyExistsError)
    async def project_exists_handler(request: Request, exc: ProjectAlreadyExistsError):
        return JSONResponse(status_code=409, content={"error": str(exc)})

    @app.exception_handler(FindingNotFoundError)
    async def finding_not_found_handler(request: Request, exc: FindingNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(ScanNotFoundError)
    async def scan_not_found_handler(request: Request, exc: ScanNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(CodeSentinelError)
    async def generic_codesentinel_handler(request: Request, exc: CodeSentinelError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    # Include routers
    from backend.api.routes import (
        findings,
        investigations,
        models,
        patches,
        projects,
        providers,
        scans,
        system,
    )

    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(scans.router, prefix="/api/v1")
    app.include_router(findings.router, prefix="/api/v1")
    app.include_router(investigations.router, prefix="/api/v1")
    app.include_router(patches.router, prefix="/api/v1")
    app.include_router(models.router, prefix="/api/v1")
    app.include_router(providers.router, prefix="/api/v1")
    app.include_router(system.router, prefix="/api/v1")
    from backend.api.routes import ws
    app.include_router(ws.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "name": "CodeSentinel AI",
            "version": settings.app_version,
            "status": "running",
            "docs": "/api/docs",
        }

    return app


# Application instance
app = create_app()


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

@click.group()
def cli():
    """CodeSentinel AI CLI."""
    pass


@cli.command()
@click.option("--host", default=None, help="Host to bind")
@click.option("--port", default=None, type=int, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the CodeSentinel AI backend server."""
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=host or settings.host,
        port=port or settings.port,
        reload=reload or settings.reload,
        log_level="warning",  # structlog handles our logging
    )


@cli.command()
@click.argument("project_path")
@click.option("--scanners", "-s", multiple=True, help="Specific scanners to run")
def scan(project_path: str, scanners: tuple):
    """Scan a project directory from the command line."""
    import asyncio

    from backend.core.security import validate_project_path
    from backend.database.session import create_tables
    from backend.scanners.base import ScanContext
    from backend.scanners.registry import ScannerRegistry

    async def _run():
        configure_logging()
        await create_tables()
        ScannerRegistry.register_defaults()

        try:
            path = validate_project_path(project_path)
        except ValueError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

        context = ScanContext(
            project_id="cli",
            project_path=path,
        )

        from backend.scanners.registry import ScanRunner
        runner = ScanRunner()
        enabled = list(scanners) if scanners else None
        results = await runner.run_all(context, enabled)

        total_findings = 0
        for result in results:
            click.echo(
                f"\n{'='*60}\n"
                f"Scanner: {result.scanner_name} | Status: {result.status.value} | "
                f"Findings: {len(result.findings)} | Duration: {result.duration_seconds:.1f}s"
            )
            if result.error_message:
                click.echo(f"  Error: {result.error_message}")
            for f in result.findings:
                click.echo(
                    f"  [{f.severity.value.upper()}] {f.file_path}:{f.line_start} "
                    f"- {f.title[:80]}"
                )
            total_findings += len(result.findings)

        click.echo(f"\nTotal findings: {total_findings}")

    asyncio.run(_run())


def cli_main():
    cli()


if __name__ == "__main__":
    cli()
