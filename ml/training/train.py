"""ML evaluation harness for the vulnerability risk scorer.

NOTE: This is a reference scaffold, NOT a real training loop. It evaluates the current
deterministic heuristic predictor on a small internal sample and records metrics. It does
NOT perform gradient-based fine-tuning of CodeBERT — the ``train_epoch`` method reports a
placeholder loss curve only. Real CodeBERT fine-tuning on a public dataset (Devign /
CodeXGLUE) on a GPU is future work; see docs/research/ACADEMIC_REPORT.md section 6.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from ml.configs.config import MLConfig
from ml.datasets.loader import VulnerabilityDatasetLoader
from ml.evaluation.metrics import EvaluationReport, compute_classification_metrics
from ml.inference.predictor import NeuralVulnerabilityPredictor


class VulnerabilityTrainer:
    """Trains and fine-tunes code vulnerability neural models."""

    def __init__(self, config: Optional[MLConfig] = None):
        self.config = config or MLConfig()
        self.loader = VulnerabilityDatasetLoader()

    def train_epoch(self, samples: List[Any], epoch: int) -> float:
        """Placeholder for a training epoch — does NOT perform gradient updates.

        Returns an illustrative loss value only. Real CodeBERT fine-tuning is future work
        (see module docstring and docs/research/ACADEMIC_REPORT.md section 6).
        """
        # Placeholder loss curve — NOT a measured training loss.
        base_loss = 0.65 / (1.0 + 0.3 * epoch)
        return round(base_loss, 4)

    def evaluate(self, samples: List[Any]) -> EvaluationReport:
        """Run inference evaluation on held-out samples and calculate academic metrics."""
        predictor = NeuralVulnerabilityPredictor()
        y_true = [s.label for s in samples]
        y_scores = []
        y_pred = []
        latencies = []

        for s in samples:
            res = predictor.predict(s.code)
            score = res["risk_score"]
            y_scores.append(score)
            y_pred.append(1 if score >= 0.50 else 0)
            latencies.append(res["latency_ms"])

        return compute_classification_metrics(y_true, y_pred, y_scores, latencies)

    def run_full_pipeline(self) -> Dict[str, Any]:
        """Execute full training, validation, and test evaluation pipeline."""
        start_time = time.perf_counter()
        train_set, val_set, test_set = self.loader.get_splits()

        training_history = []
        for epoch in range(1, self.config.epochs + 1):
            loss = self.train_epoch(train_set, epoch)
            training_history.append({"epoch": epoch, "loss": loss})

        val_metrics = self.evaluate(val_set)
        test_metrics = self.evaluate(test_set)
        duration = time.perf_counter() - start_time

        result = {
            "model": self.config.model_name,
            "epochs": self.config.epochs,
            "train_samples": len(train_set),
            "val_samples": len(val_set),
            "test_samples": len(test_set),
            "history": training_history,
            "test_metrics": test_metrics.model_dump(),
            "duration_seconds": round(duration, 2),
        }

        # Save results
        out_dir = self.config.results_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "experiment_metrics.json").write_text(json.dumps(result, indent=2))

        return result


if __name__ == "__main__":
    trainer = VulnerabilityTrainer()
    res = trainer.run_full_pipeline()
    print("Evaluation harness complete (heuristic scorer; no gradient training performed):")
    print(json.dumps(res, indent=2))
