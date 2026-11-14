"""OpenAI Cloud LLM Provider."""
from __future__ import annotations

import os
import time
from typing import Optional

import httpx

from backend.core.logging import get_logger
from backend.llm.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
    ProviderType,
)

logger = get_logger("codesentinel.llm.openai")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Cloud LLM provider using OpenAI v1 Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 45.0,
    ):
        super().__init__(ProviderType.OPENAI, default_model)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if an API key is provided and valid."""
        return bool(self.api_key and len(self.api_key) > 10)

    async def get_status(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus(
                provider=self.provider_type,
                is_available=False,
                configured_model=self.default_model,
                error="OpenAI API key not configured",
            )
        return ProviderStatus(
            provider=self.provider_type,
            is_available=True,
            configured_model=self.default_model,
            available_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"],
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Configure it in Settings.")

        model = request.model or self.default_model
        start = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            latency = (time.perf_counter() - start) * 1000

            if res.status_code != 200:
                raise RuntimeError(f"OpenAI error: HTTP {res.status_code} - {res.text}")

            data = res.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Estimate cost (~$0.15/1M in, $0.60/1M out for mini)
            cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.0000006)

            return GenerationResponse(
                content=choice["message"]["content"],
                provider=self.provider_type,
                model=model,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                total_tokens=total,
                latency_ms=round(latency, 2),
                cost_estimate_usd=round(cost, 6),
                finish_reason=choice.get("finish_reason", "stop"),
            )
