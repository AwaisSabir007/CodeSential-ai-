"""Scanner registry and orchestration."""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Sequence, Type

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.scanners.bandit import BanditScanner
from backend.scanners.base import BaseScanner, ScanContext, ScannerResult, ScannerStatus
from backend.scanners.complexity import ComplexityScanner
from backend.scanners.gitleaks import GitleaksScanner
from backend.scanners.npm_audit import NpmAuditScanner
from backend.scanners.pip_audit import PipAuditScanner
from backend.scanners.semgrep import SemgrepScanner

logger = get_logger(__name__)


class ScannerRegistry:
    """Central registry for all available scanners."""

    _scanners: Dict[str, BaseScanner] = {}
    _availability_cache: Dict[str, bool] = {}

    @classmethod
    def register_defaults(cls, timeout_seconds: Optional[int] = None) -> None:
        """Register all built-in scanners."""
        settings = get_settings()
        timeout = timeout_seconds or settings.scanner_timeout_seconds

        scanner_classes: List[Type[BaseScanner]] = [
            SemgrepScanner,
            BanditScanner,
            GitleaksScanner,
            PipAuditScanner,
            NpmAuditScanner,
            ComplexityScanner,
        ]

        for scanner_cls in scanner_classes:
            instance = scanner_cls(timeout_seconds=timeout)
            cls._scanners[instance.name] = instance

        logger.info("Scanner registry initialized", count=len(cls._scanners))

    @classmethod
    def get(cls, name: str) -> Optional[BaseScanner]:
        return cls._scanners.get(name)

    @classmethod
    def all_scanners(cls) -> Sequence[BaseScanner]:
        return list(cls._scanners.values())

    @classmethod
    async def check_availability(cls) -> Dict[str, bool]:
        """Check availability of all registered scanners."""
        results = {}
        for name, scanner in cls._scanners.items():
            try:
                available = await scanner.is_available()
                results[name] = available
                cls._availability_cache[name] = available
            except Exception as exc:
                logger.warning("Scanner availability check failed", scanner=name, error=str(exc))
                results[name] = False
        return results

    @classmethod
    async def get_available_scanners(cls) -> List[BaseScanner]:
        """Return only scanners that are currently available."""
        availability = await cls.check_availability()
        return [
            scanner for name, scanner in cls._scanners.items()
            if availability.get(name, False)
        ]

    @classmethod
    async def get_scanner_status(cls) -> List[dict]:
        """Return status info for all scanners."""
        results = []
        for name, scanner in cls._scanners.items():
            available = cls._availability_cache.get(name)
            if available is None:
                try:
                    available = await scanner.is_available()
                    cls._availability_cache[name] = available
                except Exception:
                    available = False

            version = None
            if available:
                try:
                    version = await scanner.get_version()
                except Exception:
                    pass

            results.append({
                "name": name,
                "category": scanner.category.value,
                "available": available,
                "version": version,
                "supported_languages": scanner.supported_languages,
            })
        return results


class ScanRunner:
    """Orchestrates running multiple scanners concurrently."""

    def __init__(self, max_concurrent: Optional[int] = None) -> None:
        settings = get_settings()
        self.max_concurrent = max_concurrent or settings.max_concurrent_scanners
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def run_all(
        self,
        context: ScanContext,
        enabled_scanners: Optional[List[str]] = None,
    ) -> List[ScannerResult]:
        """Run all (or specified) available scanners concurrently."""
        scanners = ScannerRegistry.all_scanners()

        if enabled_scanners is not None:
            scanners = [s for s in scanners if s.name in enabled_scanners]

        tasks = [
            self._run_scanner(scanner, context)
            for scanner in scanners
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results: List[ScannerResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                scanner_name = scanners[i].name if i < len(scanners) else "unknown"
                logger.error(
                    "Scanner raised unexpected exception",
                    scanner=scanner_name,
                    error=str(result),
                )
                final_results.append(ScannerResult(
                    scanner_name=scanner_name,
                    status=ScannerStatus.FAILED,
                    version=None,
                    findings=[],
                    duration_seconds=0.0,
                    error_message=str(result),
                ))
            else:
                final_results.append(result)

        return final_results

    async def _run_scanner(
        self, scanner: BaseScanner, context: ScanContext
    ) -> ScannerResult:
        """Run a single scanner with concurrency limiting."""
        async with self._semaphore:
            logger.info(
                "Starting scanner",
                scanner=scanner.name,
                project=context.project_id,
            )
            result = await scanner.scan(context)
            logger.info(
                "Scanner completed",
                scanner=scanner.name,
                status=result.status,
                findings=len(result.findings),
                duration=f"{result.duration_seconds:.1f}s",
            )
            return result
