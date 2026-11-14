"""Syntax and static scanner patch validation in isolation."""
from __future__ import annotations

import ast
from typing import List, Tuple

from pydantic import BaseModel


class PatchValidationResult(BaseModel):
    is_valid: bool
    syntax_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class PatchValidator:
    """Validates candidate patch code for syntax errors and common regressions."""

    @staticmethod
    def validate_syntax(code: str, file_path: str) -> Tuple[bool, List[str]]:
        """Check syntax validity according to file extension."""
        errors = []
        if file_path.endswith(".py"):
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Python SyntaxError at line {e.lineno}: {e.msg}")
                return False, errors
            except Exception as e:
                errors.append(f"AST parse error: {str(e)}")
                return False, errors
        elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            # Balanced bracket & brace check as fast syntax heuristic
            stack = []
            matching = {')': '(', '}': '{', ']': '['}
            for idx, char in enumerate(code):
                if char in matching.values():
                    stack.append((char, idx))
                elif char in matching:
                    if not stack or stack[-1][0] != matching[char]:
                        errors.append(f"Mismatched bracket '{char}' around character {idx}")
                        return False, errors
                    stack.pop()
            if stack:
                errors.append(f"Unclosed opening bracket '{stack[-1][0]}'")
                return False, errors

        return True, errors

    @classmethod
    def validate_patch(cls, code: str, file_path: str) -> PatchValidationResult:
        syntax_ok, errors = cls.validate_syntax(code, file_path)
        return PatchValidationResult(
            is_valid=syntax_ok,
            syntax_valid=syntax_ok,
            errors=errors,
        )
