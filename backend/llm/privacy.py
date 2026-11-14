"""Privacy and Data Protection Guard for LLM queries."""
from __future__ import annotations

from typing import Optional, Tuple

from backend.core.security import redact_secrets
from backend.llm.base import ProviderType


class PrivacyViolationError(Exception):
    """Raised when an operation violates user privacy policies."""
    pass


class PrivacyGuard:
    """Enforces strict developer privacy policies for local and cloud LLM requests."""

    def __init__(self, allow_cloud_code_sharing: bool = False):
        self.allow_cloud_code_sharing = allow_cloud_code_sharing

    def sanitize_prompt(self, text: str) -> str:
        """Strip sensitive credentials, API keys, and tokens from prompts."""
        return redact_secrets(text)

    def check_cloud_transmission(
        self,
        provider: ProviderType,
        source_code_present: bool = True,
        user_explicit_consent: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Validate whether prompt content is permitted to leave the local machine.

        Local-first rule:
        If provider is Ollama or Mock, local execution is always permitted.
        If provider is Cloud (OpenAI, Gemini), explicit user consent is required.
        """
        if provider in (ProviderType.OLLAMA, ProviderType.MOCK):
            return True, None

        if not self.allow_cloud_code_sharing and not user_explicit_consent:
            return (
                False,
                f"Cloud transmission blocked: sending code to {provider.value} requires explicit user consent."
            )

        return True, None
