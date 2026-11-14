"""LLM Providers and Routing settings API routes."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.config import get_settings
from backend.llm.base import ProviderType, RoutingMode
from backend.llm.router import get_router, rebuild_router

router = APIRouter(prefix="/providers", tags=["providers"])

# Keys that may be persisted to the per-user config file.
_PERSISTABLE = {
    "default_llm_provider": "CODESENTINEL_DEFAULT_LLM_PROVIDER",
    "allow_cloud_code_sharing": "CODESENTINEL_ALLOW_CLOUD_CODE_SHARING",
    "gemini_api_key": "CODESENTINEL_GEMINI_API_KEY",
    "gemini_model": "CODESENTINEL_GEMINI_MODEL",
    "openai_api_key": "CODESENTINEL_OPENAI_API_KEY",
    "openai_model": "CODESENTINEL_OPENAI_MODEL",
    "ollama_base_url": "CODESENTINEL_OLLAMA_BASE_URL",
    "ollama_default_model": "CODESENTINEL_OLLAMA_DEFAULT_MODEL",
}


class UpdateProviderSettingsRequest(BaseModel):
    routing_mode: Optional[RoutingMode] = None
    allow_cloud_code_sharing: Optional[bool] = None
    default_llm_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_default_model: Optional[str] = None


def _persist_user_env(updates: dict) -> None:
    """Merge key=value pairs into the per-user .env (survives restarts and
    is the only config source available to the packaged desktop app)."""
    from backend.core.config import _user_env_file

    path = Path(_user_env_file())
    existing: dict = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    existing.update(updates)
    body = "\n".join(f"{k}={v}" for k, v in sorted(existing.items()))
    path.write_text(
        "# CodeSentinel AI — per-user configuration (managed by Settings UI)\n"
        "# This file holds credentials. Do not share or commit it.\n" + body + "\n",
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass


@router.get("")
async def get_providers():
    _router = get_router()
    return {
        "modes": [m.value for m in RoutingMode],
        "active_mode": _router.mode.value,
        "providers": [p.value for p in ProviderType],
    }


@router.get("/status")
async def get_providers_status():
    """Check connectivity and configured models for all LLM providers."""
    return await get_router().get_all_statuses()


@router.patch("/settings")
async def update_provider_settings(payload: UpdateProviderSettingsRequest):
    settings = get_settings()
    changed = payload.model_dump(exclude_none=True)

    # Apply to the live settings singleton.
    persist: dict = {}
    for field, value in changed.items():
        if field == "routing_mode":
            continue
        if hasattr(settings, field):
            setattr(settings, field, value)
        if field in _PERSISTABLE:
            persist[_PERSISTABLE[field]] = str(value).lower() if isinstance(value, bool) else str(value)

    if persist:
        _persist_user_env(persist)

    # Rebuild the shared router so providers pick up new keys/models/mode.
    _router = rebuild_router()
    if payload.routing_mode is not None:
        _router.mode = payload.routing_mode
    if payload.allow_cloud_code_sharing is not None:
        _router.privacy_guard.allow_cloud_code_sharing = payload.allow_cloud_code_sharing

    return {
        "active_mode": _router.mode.value,
        "allow_cloud_code_sharing": _router.privacy_guard.allow_cloud_code_sharing,
        "persisted": sorted(persist.keys()),
    }
