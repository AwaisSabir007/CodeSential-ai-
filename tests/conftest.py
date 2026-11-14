"""Test configuration: force a hermetic environment.

Tests must never contact cloud LLM providers, depend on the developer's local
.env / per-user config, or write to the real application database. This runs
before any backend import.
"""
import os
import tempfile

# No cloud LLM calls in tests — force the deterministic mock provider.
os.environ["CODESENTINEL_DEFAULT_LLM_PROVIDER"] = "none"
os.environ["CODESENTINEL_ALLOW_CLOUD_CODE_SHARING"] = "false"
os.environ["CODESENTINEL_GEMINI_API_KEY"] = ""
os.environ["CODESENTINEL_OPENAI_API_KEY"] = ""

# Isolate the database so tests never touch the real codesentinel.db.
_test_db = os.path.join(tempfile.gettempdir(), "codesentinel_test.db")
if os.path.exists(_test_db):
    try:
        os.remove(_test_db)
    except OSError:
        pass
os.environ["CODESENTINEL_DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_db}"
