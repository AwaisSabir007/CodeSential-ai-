"""Core configuration for CodeSentinel AI Backend."""
from __future__ import annotations

import secrets
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _user_data_dir() -> Path:
    from platformdirs import user_data_dir

    path = Path(user_data_dir("CodeSentinelAI", "CodeSentinelAI"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _user_env_file() -> str:
    """Per-user config file that persists Settings-UI changes across restarts."""
    return str(_user_data_dir() / ".env")


def _default_database_url() -> str:
    """Resolve the default SQLite location.

    In a packaged (PyInstaller) app the working directory is not writable or
    meaningful, so the database lives in the per-user data directory. During
    development it stays next to the repository as before.
    """
    if getattr(sys, "frozen", False):
        return f"sqlite+aiosqlite:///{_user_data_dir() / 'codesentinel.db'}"
    return "sqlite+aiosqlite:///./codesentinel.db"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        # Later files win: the per-user config (written by the Settings UI,
        # also used by the packaged desktop app) overrides the repo .env.
        env_file=(".env", _user_env_file()),
        env_file_encoding="utf-8",
        env_prefix="CODESENTINEL_",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "CodeSentinel AI"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    workers: int = 1
    reload: bool = False

    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    api_token: Optional[str] = None  # local IPC token
    cors_origins: List[str] = ["http://localhost:1420", "http://localhost:5173", "tauri://localhost"]

    # Database
    database_url: str = Field(default_factory=_default_database_url)
    database_echo: bool = False

    # Filesystem
    max_file_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    debounce_seconds: float = 1.5
    max_watch_projects: int = 20
    default_excluded_dirs: List[str] = [
        ".git", "node_modules", ".venv", "venv", "__pycache__",
        ".pytest_cache", "dist", "build", ".mypy_cache", ".ruff_cache",
        "*.egg-info", ".tox", "coverage", ".coverage", "htmlcov",
        ".DS_Store", "target", ".cargo",
    ]
    default_excluded_extensions: List[str] = [
        ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe",
        ".bin", ".lock", ".sum", ".map", ".min.js", ".min.css",
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".woff",
        ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz",
    ]

    # Scanner
    scanner_timeout_seconds: int = 120
    max_concurrent_scanners: int = 3
    scanner_queue_size: int = 100

    # Agent
    max_agent_iterations: int = 10
    max_agent_tokens: int = 8000
    agent_timeout_seconds: int = 300

    # LLM Providers
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "codellama:7b"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    default_llm_provider: str = "ollama"  # ollama | openai | gemini | none
    # Explicit opt-in for sending (secret-redacted) prompts to cloud providers.
    # Selecting a cloud provider as default_llm_provider also counts as consent.
    allow_cloud_code_sharing: bool = False

    # ML Model
    ml_model_path: Optional[str] = None
    ml_model_threshold: float = 0.5
    ml_enabled: bool = False  # disabled until model is trained

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json | console
    log_file: Optional[str] = None

    # Paths
    @property
    def data_dir(self) -> Path:
        from platformdirs import user_data_dir
        path = Path(user_data_dir("CodeSentinelAI", "CodeSentinelAI"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def models_dir(self) -> Path:
        path = self.data_dir / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the global Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
