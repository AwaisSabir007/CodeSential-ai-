"""Ollama Local LLM Provider."""
from __future__ import annotations

import time

import httpx

from backend.core.logging import get_logger
from backend.llm.base import (
    BaseLLMProvider,
    GenerationRequest,
    GenerationResponse,
    ProviderStatus,
    ProviderType,
)

logger = get_logger("codesentinel.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider using Ollama HTTP API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        default_model: str = "codellama:7b",
        timeout: float = 60.0,
    ):
        super().__init__(ProviderType.OLLAMA, default_model)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def is_available(self) -> bool:
        """Check if Ollama server is running locally."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def get_status(self) -> ProviderStatus:
        """Fetch running status and installed models."""
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                latency = (time.perf_counter() - start) * 1000
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return ProviderStatus(
                        provider=self.provider_type,
                        is_available=True,
                        configured_model=self.default_model,
                        available_models=models,
                        latency_ms=round(latency, 2),
                    )
                return ProviderStatus(
                    provider=self.provider_type,
                    is_available=False,
                    configured_model=self.default_model,
                    error=f"HTTP {res.status_code}",
                )
        except Exception as e:
            return ProviderStatus(
                provider=self.provider_type,
                is_available=False,
                configured_model=self.default_model,
                error=str(e),
            )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute chat completion via Ollama."""
        model = request.model or self.default_model
        start = time.perf_counter()

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                latency = (time.perf_counter() - start) * 1000

                if res.status_code != 200:
                    raise RuntimeError(f"Ollama error: HTTP {res.status_code} - {res.text}")

                data = res.json()
                content = data.get("message", {}).get("content", "")
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)

                return GenerationResponse(
                    content=content,
                    provider=self.provider_type,
                    model=model,
                    tokens_prompt=prompt_eval_count,
                    tokens_completion=eval_count,
                    total_tokens=prompt_eval_count + eval_count,
                    latency_ms=round(latency, 2),
                    cost_estimate_usd=0.0,  # 100% Free local execution
                )
        except Exception as e:
            logger.error("ollama_generation_failed", error=str(e))
            raise
