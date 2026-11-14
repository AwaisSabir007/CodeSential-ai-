"""Long-term persistent memory backed by SQLite."""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Finding,
    ProposedPatch,
)


class LongTermMemory:
    """Interfaces with database to retrieve historical developer actions and patterns."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feedback_for_rule(self, rule_id: str) -> List[Dict[str, Any]]:
        """Retrieve past developer decisions (e.g. false positives) for this rule."""
        stmt = (
            select(Finding)
            .where(Finding.rule_id == rule_id)
            .where(Finding.status == "false_positive")
            .order_by(desc(Finding.updated_at))
            .limit(20)
        )
        res = await self.session.execute(stmt)
        items = res.scalars().all()
        return [
            {
                "finding_id": item.id,
                "status": item.status,
                "rule_id": item.rule_id,
            }
            for item in items
        ]

    async def get_accepted_patches_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Find patches that were successfully approved and applied for a similar category."""
        stmt = (
            select(ProposedPatch)
            .where(ProposedPatch.status == "approved")
            .order_by(desc(ProposedPatch.created_at))
            .limit(10)
        )
        res = await self.session.execute(stmt)
        patches = res.scalars().all()
        return [
            {
                "patch_id": p.id,
                "summary": p.explanation,
                "diff": p.diff_content,
            }
            for p in patches
        ]
