"""Unit tests for agent memory and semantic retrieval."""
import pytest
from backend.memory.embeddings import EmbeddingGenerator
from backend.memory.retrieval import SemanticRetriever
from backend.memory.short_term import ShortTermMemory


def test_short_term_memory():
    mem = ShortTermMemory(
        investigation_id="inv_test_1",
        project_id="proj_1",
        finding_id="find_1",
    )
    step = mem.add_step(
        agent_name="PlanningAgent",
        action="triage",
        input_data={"finding": "CWE-89"},
        output_data={"priority": "high"},
        duration_ms=15.2,
    )
    assert len(mem.traces) == 1
    assert mem.tool_call_count == 1
    assert "PlanningAgent" in mem.get_summary()


def test_embedding_generator_and_cosine():
    gen = EmbeddingGenerator(dimension=64)
    vec1 = gen.embed_text("sql injection select from users")
    vec2 = gen.embed_text("sql injection parameterized query")
    vec3 = gen.embed_text("css flexbox layout styling")

    sim_related = EmbeddingGenerator.cosine_similarity(vec1, vec2)
    sim_unrelated = EmbeddingGenerator.cosine_similarity(vec1, vec3)

    assert sim_related > sim_unrelated


def test_semantic_retriever():
    retriever = SemanticRetriever()
    retriever.add_finding_record(
        record_id="rec_1",
        project_id="proj_1",
        category="injection",
        title="SQL Injection vulnerability",
        content="Untrusted user input concatenated into SQL string query",
        remediation_hint="Use parameterized bindings",
    )
    retriever.add_finding_record(
        record_id="rec_2",
        project_id="proj_1",
        category="crypto",
        title="Weak MD5 hash algorithm",
        content="MD5 is cryptographically broken",
        remediation_hint="Use SHA-256 or bcrypt",
    )

    results = retriever.search_similar("database sql query injection", project_id="proj_1")
    assert len(results) > 0
    assert results[0]["record_id"] == "rec_1"
    assert "SQL" in results[0]["title"]
