"""Unit tests for LLM providers, privacy guard, and router."""
import pytest
from backend.llm.base import GenerationRequest, LLMMessage, ProviderType, RoutingMode
from backend.llm.privacy import PrivacyGuard
from backend.llm.router import LLMRouter, OfflineMockProvider


@pytest.mark.asyncio
async def test_offline_mock_provider():
    mock = OfflineMockProvider()
    assert await mock.is_available() is True

    req = GenerationRequest(
        messages=[LLMMessage(role="user", content="Analyze vulnerability in ping_host")]
    )
    resp = await mock.generate(req)
    assert resp.provider == ProviderType.MOCK
    assert "CodeSentinel Autonomous Security Assessment" in resp.content
    assert resp.total_tokens > 0


@pytest.mark.asyncio
async def test_privacy_guard_sanitizes_prompt():
    guard = PrivacyGuard(allow_cloud_code_sharing=False)
    secret_text = "Here is my key: api_key='secret12345678901234567890' check it"
    sanitized = guard.sanitize_prompt(secret_text)
    assert "secret12345678901234567890" not in sanitized
    assert "[REDACTED]" in sanitized


@pytest.mark.asyncio
async def test_privacy_guard_cloud_blocking():
    guard = PrivacyGuard(allow_cloud_code_sharing=False)
    allowed, reason = guard.check_cloud_transmission(ProviderType.OPENAI, user_explicit_consent=False)
    assert allowed is False
    assert "explicit user consent" in reason

    # Local is always allowed
    allowed_local, _ = guard.check_cloud_transmission(ProviderType.OLLAMA, user_explicit_consent=False)
    assert allowed_local is True


@pytest.mark.asyncio
async def test_llm_router_offline_fallback():
    router = LLMRouter(mode=RoutingMode.LOCAL_FIRST_FALLBACK)
    req = GenerationRequest(
        messages=[LLMMessage(role="user", content="Test prompt without API keys")]
    )
    resp = await router.generate(req)
    assert resp is not None
    assert len(resp.content) > 0
