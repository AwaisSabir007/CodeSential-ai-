"""Neural Model Insights and Inference API routes."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from ml.configs.config import MLConfig
from ml.experiments.ablation import run_ablation_study
from ml.inference.predictor import NeuralVulnerabilityPredictor

router = APIRouter(prefix="/models", tags=["models"])
_predictor = NeuralVulnerabilityPredictor()
_config = MLConfig()


class InferenceRequest(BaseModel):
    code: str


@router.get("/status")
async def get_model_status():
    """Return model runtime status, architecture, and deployment environment."""
    return {
        "model_name": _config.model_name,
        "version": _predictor.model_version,
        "device": _config.device,
        "is_ready": True,
        "engine": "CodeBERT Neural Feature Classifier",
        "supported_languages": ["python", "javascript", "typescript"],
    }


@router.get("/metrics")
async def get_model_metrics():
    """Return academic research metrics, confusion matrix, and ablation results."""
    ablation_file = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "experiments" / "ablation_results.json"
    if ablation_file.exists():
        try:
            return json.loads(ablation_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Run on demand if not present
    return run_ablation_study()


@router.post("/inference")
async def run_model_inference(payload: InferenceRequest):
    """Run real-time neural vulnerability prediction on a code snippet."""
    return _predictor.predict(payload.code)
