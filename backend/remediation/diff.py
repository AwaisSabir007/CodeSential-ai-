"""Diff generation and parsing utilities."""
from __future__ import annotations

import difflib
from typing import Any, Dict, List

from pydantic import BaseModel


class DiffHunk(BaseModel):
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]


class DiffResult(BaseModel):
    file_path: str
    original_code: str
    proposed_code: str
    unified_diff: str
    additions: int
    deletions: int
    hunks: List[Dict[str, Any]] = []


def create_unified_diff(
    original: str,
    modified: str,
    file_path: str = "target_file",
    context_lines: int = 3,
) -> DiffResult:
    """Generate standard unified diff and calculate change metrics."""
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=context_lines,
    )
    diff_text = "".join(diff)

    additions = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))

    return DiffResult(
        file_path=file_path,
        original_code=original,
        proposed_code=modified,
        unified_diff=diff_text,
        additions=additions,
        deletions=deletions,
    )
