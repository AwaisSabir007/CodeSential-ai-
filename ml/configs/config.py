"""Deep Learning Configuration for CodeBERT Vulnerability Classifier."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class MLConfig(BaseModel):
    model_name: str = "microsoft/codebert-base"
    fallback_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_length: int = 256
    batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 5
    num_classes: int = 2  # 0: benign, 1: vulnerable
    hidden_dropout_prob: float = 0.2

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "datasets"
    checkpoint_dir: Path = Path(__file__).resolve().parent.parent / "checkpoints"
    results_dir: Path = Path(__file__).resolve().parent.parent / "evaluation" / "results"

    # Device
    device: str = "cpu"  # cpu, cuda, or mps
