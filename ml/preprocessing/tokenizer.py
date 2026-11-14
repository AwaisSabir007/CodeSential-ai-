"""Code preprocessing and tokenization for neural vulnerability detection."""
from __future__ import annotations

import re
from typing import Dict


class CodePreprocessor:
    """Preprocesses and normalizes raw code snippets for neural models."""

    @staticmethod
    def clean_code(code: str) -> str:
        """Strip excessive whitespace and normalize line endings."""
        # Replace multiple spaces with single space
        lines = [line.rstrip() for line in code.splitlines()]
        cleaned = "\n".join(lines).strip()
        return cleaned

    @staticmethod
    def extract_features(code: str) -> Dict[str, float]:
        """Extract lexical security indicators for hybrid feature enrichment."""
        text = code.lower()
        return {
            "has_eval_or_exec": 1.0
            if ("eval(" in text or "exec(" in text or "new function(" in text)
            else 0.0,
            "has_subshell": 1.0
            if (
                "subprocess" in text
                or "shell=true" in text
                or "popen" in text
                or "os.system(" in text
                or "child_process" in text
                or ".execsync(" in text
                or re.search(r"\bexec(?:sync)?\s*\(", text) is not None
            )
            else 0.0,
            "has_sql": 1.0
            if (
                "select " in text
                or "insert into" in text
                or "drop table" in text
                or "update " in text and " set " in text
                or "delete from" in text
            )
            else 0.0,
            "has_secrets": 1.0
            if (
                "api_key" in text
                or "apikey" in text
                or "secret" in text
                or "password" in text
                or "private_key" in text
                or "auth_token" in text
                or "access_token" in text
            )
            else 0.0,
            "has_xss_sink": 1.0
            if (
                "innerhtml" in text
                or "outerhtml" in text
                or "document.write(" in text
                or "dangerouslysetinnerhtml" in text
            )
            else 0.0,
            "has_unsafe_deserialization": 1.0
            if (
                "pickle.load" in text
                or "pickle.loads" in text
                or "yaml.load(" in text and "safeloader" not in text and "safe_load" not in text
                or "unserialize(" in text
            )
            else 0.0,
            "token_count": float(len(re.findall(r"\w+", code))),
        }
