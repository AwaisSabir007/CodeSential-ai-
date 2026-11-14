"""Semantic vector memory retrieval."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.memory.embeddings import EmbeddingGenerator


class MemoryRecord(BaseModel):
    record_id: str
    project_id: str
    category: str
    title: str
    content: str
    remediation_hint: Optional[str] = None
    embedding: List[float] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SemanticRetriever:
    """Manages semantic memory index and similarity search for code security insights."""

    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None):
        self.generator = embedding_generator or EmbeddingGenerator()
        self.records: List[MemoryRecord] = []

    def add_finding_record(
        self,
        record_id: str,
        project_id: str,
        category: str,
        title: str,
        content: str,
        remediation_hint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Store a finding summary into semantic memory."""
        text = f"{title} {category} {content}"
        emb = self.generator.embed_text(text)
        record = MemoryRecord(
            record_id=record_id,
            project_id=project_id,
            category=category,
            title=title,
            content=content,
            remediation_hint=remediation_hint,
            embedding=emb,
            metadata=metadata or {},
        )
        self.records.append(record)
        return record

    def search_similar(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 5,
        threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Search similar past records using cosine similarity."""
        query_vec = self.generator.embed_text(query)
        matches = []

        for r in self.records:
            if project_id and r.project_id != project_id:
                continue

            sim = EmbeddingGenerator.cosine_similarity(query_vec, r.embedding)
            if sim >= threshold:
                matches.append({
                    "record_id": r.record_id,
                    "title": r.title,
                    "category": r.category,
                    "remediation_hint": r.remediation_hint,
                    "similarity": round(sim, 4),
                    "metadata": r.metadata,
                })

        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:limit]

    def clear_project(self, project_id: str) -> int:
        """Remove all records for a project (privacy compliance)."""
        before = len(self.records)
        self.records = [r for r in self.records if r.project_id != project_id]
        return before - len(self.records)
