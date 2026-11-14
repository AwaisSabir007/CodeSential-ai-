"""Structured logging configuration for CodeSentinel AI."""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure structlog with appropriate processors."""

    log_level_int = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging for third-party libraries
    logging.basicConfig(
        level=log_level_int,
        stream=sys.stderr,
        format="%(message)s",
    )

    # Silence noisy libraries
    for noisy in ["watchdog", "watchfiles", "httpx", "httpcore"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named structured logger."""
    return structlog.get_logger(name)
