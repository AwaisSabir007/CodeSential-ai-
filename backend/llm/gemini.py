"""Google Gemini LLM Provider."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx

from backend.core.logging import get_logger
from backend.llm.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
    ProviderType,
)

logger = get_logger("codesentinel.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Cloud LLM provider using Generative Language REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gemini-2.5-flash",
        timeout: float = 45.0,
    ):
        super().__init__(ProviderType.GEMINI, default_model)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        self.timeout = timeout

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    async def get_status(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus(
                provider=self.provider_type,
                is_available=False,
                configured_model=self.default_model,
                error="Gemini API key not configured",
            )
        return ProviderStatus(
            provider=self.provider_type,
            is_available=True,
            configured_model=self.default_model,
            available_models=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest"],
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("Gemini API key is missing. Configure it in Settings.")

        model = request.model or self.default_model
        start = time.perf_counter()

        # API key goes in the header, never the URL (URLs end up in logs).
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": self.api_key}

        # Format messages for Gemini API
        contents = []
        for msg in request.messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        generation_config: Dict[str, Any] = {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        }
        # Flash models are hybrid-reasoning: without a cap, internal "thinking"
        # consumes the output token budget and can truncate small responses.
        if "flash" in model:
            generation_config["thinkingConfig"] = {"thinkingBudget": 0}

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Retry transient overload/rate-limit responses with backoff.
            attempts = 3
            for attempt in range(attempts):
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code in (429, 503) and attempt < attempts - 1:
                    import asyncio

                    delay = 2.0 * (attempt + 1)
                    logger.warning(
                        "gemini_transient_error_retrying",
                        status=res.status_code,
                        attempt=attempt + 1,
                        delay_s=delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                break
            latency = (time.perf_counter() - start) * 1000

            if res.status_code != 200:
                raise RuntimeError(f"Gemini error: HTTP {res.status_code} - {res.text}")

            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("No candidate responses returned by Gemini")

            first = candidates[0]
            text = first.get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)
            total = usage.get("totalTokenCount", prompt_tokens + completion_tokens)

            cost = (prompt_tokens * 0.000000075) + (completion_tokens * 0.0000003)

            return GenerationResponse(
                content=text,
                provider=self.provider_type,
                model=model,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                total_tokens=total,
                latency_ms=round(latency, 2),
                cost_estimate_usd=round(cost, 6),
                finish_reason=first.get("finishReason", "STOP"),
            )
