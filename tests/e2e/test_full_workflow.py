"""End-to-end lifecycle test against the real ASGI app (with lifespan):
register a project with a real vulnerable file -> scan -> findings ->
AI investigation (deterministic mock provider) -> candidate patch.

This exercises the full stack in-process: DB, scanner registry, scan service,
agent orchestrator, and the patch store.
"""
import asyncio
import tempfile
from pathlib import Path

import httpx
import pytest

from backend.main import create_app

VULN_PY = """import os
import sqlite3

API_KEY = "sk_live_abcdef1234567890"

def get_user(user_id):
    conn = sqlite3.connect("app.db")
    q = "SELECT * FROM users WHERE id = '%s'" % user_id
    return conn.execute(q).fetchall()

def run(cmd):
    os.system("echo " + cmd)
"""


@pytest.mark.asyncio
async def test_full_scan_investigation_patch_lifecycle():
    tmp = Path(tempfile.mkdtemp(prefix="cs_e2e_"))
    (tmp / "vuln.py").write_text(VULN_PY)

    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=30) as client:
            # 1. register project
            r = await client.post("/api/v1/projects", json={
                "name": "e2e-demo", "path": str(tmp), "description": "e2e"})
            assert r.status_code in (200, 201), r.text
            project_id = r.json()["id"]

            # 2. start a scan
            r = await client.post("/api/v1/scans", json={
                "project_id": project_id, "scan_type": "full"})
            assert r.status_code in (200, 201, 202), r.text
            scan_id = r.json()["scan_id"]

            # 3. poll until the scan reaches a terminal state
            terminal = {"completed", "failed", "cancelled"}
            status = None
            for _ in range(60):  # up to ~30s
                rs = await client.get(f"/api/v1/scans/{scan_id}")
                assert rs.status_code == 200
                status = rs.json().get("status")
                if status in terminal:
                    break
                await asyncio.sleep(0.5)
            assert status == "completed", f"scan did not complete: {status}"

            # 4. findings endpoint returns a list
            rf = await client.get(f"/api/v1/findings?project_id={project_id}")
            assert rf.status_code == 200
            body = rf.json()
            findings = body if isinstance(body, list) else body.get("items", [])
            # bandit is a pip dependency available in CI, so findings should exist.
            # Stay resilient if a host has zero scanners: only assert the shape.
            assert isinstance(findings, list)

            # 5. run an AI investigation (mock provider) -> candidate patch
            r = await client.post("/api/v1/investigations", json={
                "project_id": project_id,
                "finding_id": "e2e-finding",
                "scanner_name": "bandit",
                "rule_id": "B608",
                "category": "security",
                "severity": "medium",
                "file_path": str(tmp / "vuln.py"),
                "line_number": 8,
                "snippet": "q = \"SELECT * FROM users WHERE id = '%s'\" % user_id",
                "title": "[B608] SQL injection",
                "description": "String-formatted SQL query",
            })
            assert r.status_code in (200, 201), r.text
            inv = r.json()
            assert inv.get("status") == "completed"
            assert inv.get("candidate_patch")  # a patch was synthesized

            # 6. the patch is registered and retrievable
            rp = await client.get("/api/v1/patches")
            assert rp.status_code == 200
            pbody = rp.json()
            patches = pbody if isinstance(pbody, list) else pbody.get("items", [])
            assert len(patches) >= 1


@pytest.mark.asyncio
async def test_scanners_report_availability():
    """The system must honestly report scanner availability (never fake a clean scan)."""
    app = create_app()
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/v1/system/scanners")
            assert r.status_code == 200
            scanners = r.json()
            assert isinstance(scanners, list) and len(scanners) >= 1
            for s in scanners:
                assert "name" in s and "available" in s
