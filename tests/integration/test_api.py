"""Integration tests for FastAPI REST API endpoints."""
import pytest
import httpx
from backend.main import create_app


@pytest.mark.asyncio
async def test_api_root_and_health():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "CodeSentinel AI"

        res_health = await client.get("/api/v1/system/health")
        health_data = res_health.json()
        assert health_data["status"] in ("healthy", "ok")


@pytest.mark.asyncio
async def test_api_models_endpoints():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res_status = await client.get("/api/v1/models/status")
        assert res_status.status_code == 200
        assert res_status.json()["is_ready"] is True

        res_metrics = await client.get("/api/v1/models/metrics")
        assert res_metrics.status_code == 200

        res_infer = await client.post(
            "/api/v1/models/inference",
            json={"code": "import subprocess\nsubprocess.run(f'cat {file}', shell=True)"}
        )
        assert res_infer.status_code == 200
        infer_data = res_infer.json()
        assert infer_data["risk_score"] > 0.40


@pytest.mark.asyncio
async def test_api_providers_endpoints():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/providers")
        assert res.status_code == 200
        assert "local_only" in res.json()["modes"]


@pytest.mark.asyncio
async def test_api_investigations_and_patches():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/investigations",
            json={
                "project_id": "proj_demo",
                "finding_id": "find_1",
                "scanner_name": "bandit",
                "rule_id": "B602",
                "category": "command_injection",
                "severity": "high",
                "file_path": "main.py",
                "line_number": 10,
                "snippet": "os.system(cmd)",
                "title": "Unsafe command execution",
                "description": "Direct os.system call",
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert len(data["completed_steps"]) >= 5
