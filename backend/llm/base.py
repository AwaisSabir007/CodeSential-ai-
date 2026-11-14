"""Base LLM provider interfaces and data structures."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    MOCK = "mock"


class RoutingMode(str, Enum):
    LOCAL_ONLY = "local_only"
    OPENAI_ONLY = "openai_only"
    GEMINI_ONLY = "gemini_only"
    HYBRID = "hybrid"
    LOCAL_FIRST_FALLBACK = "local_first_fallback"


class LLMMessage(BaseModel):
    role: str = Field(..., description="system | user | assistant")
    content: str


class GenerationRequest(BaseModel):
    messages: List[LLMMessage]
    temperature: float = 0.2
    max_tokens: int = 2048
    model: Optional[str] = None
    stream: bool = False
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    content: str
    provider: ProviderType
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_estimate_usd: float = 0.0
    finish_reason: str = "stop"


class ProviderStatus(BaseModel):
    provider: ProviderType
    is_available: bool
    configured_model: str
    available_models: List[str] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    def __init__(self, provider_type: ProviderType, default_model: str):
        self.provider_type = provider_type
        self.default_model = default_model

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider backend is reachable and configured."""
        ...

    @abstractmethod
    async def get_status(self) -> ProviderStatus:
        """Return provider status and available models."""
        ...

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate response from the model."""
        ...
