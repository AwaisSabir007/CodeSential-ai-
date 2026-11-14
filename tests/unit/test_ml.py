"""Unit tests for ML CodeBERT predictor and evaluation metrics."""
import pytest
from ml.inference.predictor import NeuralVulnerabilityPredictor
from ml.evaluation.metrics import compute_classification_metrics


def test_neural_predictor_detects_command_injection():
    predictor = NeuralVulnerabilityPredictor()
    vuln_code = "import subprocess\ndef run(host):\n    subprocess.run(f'ping {host}', shell=True)"
    res = predictor.predict(vuln_code)
    assert res["risk_score"] > 0.40
    assert any("CWE-78" in cwe for cwe in res["cwe_suggestions"])


def test_neural_predictor_benign_code():
    predictor = NeuralVulnerabilityPredictor()
    benign_code = "def add(a, b):\n    return a + b"
    res = predictor.predict(benign_code)
    assert res["risk_score"] < 0.30
    assert res["risk_label"] == "benign"


def test_compute_classification_metrics():
    y_true = [1, 0, 1, 0]
    y_pred = [1, 0, 1, 0]
    y_scores = [0.9, 0.1, 0.8, 0.2]

    metrics = compute_classification_metrics(y_true, y_pred, y_scores)
    assert metrics.accuracy == 1.0
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1_score == 1.0
    assert metrics.true_positives == 2
    assert metrics.true_negatives == 2
