"""Deep Learning Agent: invokes the risk model and interprets vulnerability risk scores."""
from __future__ import annotations

from typing import Optional

from backend.agents.state import InvestigationState
from ml.inference.predictor import NeuralVulnerabilityPredictor


class DeepLearningAgent:
    """Invokes the risk-scoring model to obtain a statistical vulnerability risk score."""

    def __init__(self, predictor: Optional[NeuralVulnerabilityPredictor] = None):
        self.predictor = predictor or NeuralVulnerabilityPredictor()

    async def run(self, state: InvestigationState) -> InvestigationState:
        finding = state.finding
        prediction = self.predictor.predict(finding.snippet or finding.title)

        state.neural_risk_score = round(prediction["risk_score"], 4)
        state.neural_risk_explanation = (
            f"CodeBERT Neural Model inference: {prediction['risk_label'].upper()} "
            f"(Score: {prediction['risk_score']:.2%}, Confidence: {prediction['confidence']:.2%}). "
            f"Note: Neural scoring is a statistical risk estimate trained on vulnerability datasets."
        )
        state.evidence.append({
            "agent": "DeepLearningAgent",
            "model_version": prediction.get("model_version", "codebert-v1"),
            "risk_score": prediction["risk_score"],
            "risk_label": prediction["risk_label"],
            "inference_latency_ms": prediction.get("latency_ms", 5.0),
        })
        state.completed_steps.append("Neural Vulnerability Assessment")
        state.tool_call_count += 1
        return state
