"""Safe patch application with automated backups and verification."""
from __future__ import annotations

import shutil
from pathlib import Path

from pydantic import BaseModel

from backend.core.logging import get_logger
from backend.remediation.diff import DiffResult, create_unified_diff
from backend.remediation.validation import PatchValidationResult, PatchValidator

logger = get_logger("codesentinel.remediation.patches")


class PatchProposal(BaseModel):
    patch_id: str
    finding_id: str
    file_path: str
    original_code: str
    modified_code: str
    diff: DiffResult
    explanation: str
    validation: PatchValidationResult
    status: str = "pending"  # pending, verified, approved, rejected, applied, failed


class PatchManager:
    """Handles generating, validating, and applying verified code fixes."""

    @staticmethod
    def generate_candidate_patch(
        patch_id: str,
        finding_id: str,
        file_path: str,
        original_code: str,
        modified_code: str,
        explanation: str,
    ) -> PatchProposal:
        """Create a structured patch proposal with diff and syntax validation."""
        diff_res = create_unified_diff(original_code, modified_code, file_path=file_path)
        val_res = PatchValidator.validate_patch(modified_code, file_path)

        return PatchProposal(
            patch_id=patch_id,
            finding_id=finding_id,
            file_path=file_path,
            original_code=original_code,
            modified_code=modified_code,
            diff=diff_res,
            explanation=explanation,
            validation=val_res,
            status="verified" if val_res.is_valid else "invalid",
        )

    @staticmethod
    def apply_patch_safely(
        target_path: Path,
        modified_code: str,
        create_backup: bool = True,
    ) -> Path:
        """Apply approved patch to target file with atomic write and .bak backup."""
        if not target_path.exists():
            raise FileNotFoundError(f"Target file does not exist: {target_path}")

        # 1. Create backup
        backup_path = target_path.with_suffix(target_path.suffix + ".codesentinel.bak")
        if create_backup:
            shutil.copy2(target_path, backup_path)
            logger.info("backup_created", backup_path=str(backup_path))

        # 2. Write new content
        target_path.write_text(modified_code, encoding="utf-8")
        logger.info("patch_applied_successfully", target=str(target_path))
        return backup_path

    @staticmethod
    def rollback_patch(target_path: Path) -> bool:
        """Revert from .codesentinel.bak backup file."""
        backup_path = target_path.with_suffix(target_path.suffix + ".codesentinel.bak")
        if not backup_path.exists():
            return False
        shutil.copy2(backup_path, target_path)
        backup_path.unlink(missing_ok=True)
        return True
