"""Curated code vulnerability dataset loader with real-world vulnerability benchmarks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel


class VulnerabilitySample(BaseModel):
    id: str
    code: str
    label: int  # 0: benign, 1: vulnerable
    cwe: str
    language: str
    description: str


# Curated benchmark dataset of real vulnerable and secure code pairs for Python and JS
CURATED_BENCHMARK_DATA: List[Dict[str, Any]] = [
    {
        "id": "vuln_cwe89_01",
        "code": "def get_user(db, user_id):\n    query = f'SELECT * FROM users WHERE id = {user_id}'\n    return db.execute(query)",
        "label": 1,
        "cwe": "CWE-89",
        "language": "python",
        "description": "SQL Injection via string formatting",
    },
    {
        "id": "benign_cwe89_01",
        "code": "def get_user(db, user_id):\n    query = 'SELECT * FROM users WHERE id = :user_id'\n    return db.execute(query, {'user_id': user_id})",
        "label": 0,
        "cwe": "CWE-89",
        "language": "python",
        "description": "Safe parameterized SQL query",
    },
    {
        "id": "vuln_cwe78_01",
        "code": "import subprocess\ndef ping_host(host):\n    return subprocess.run(f'ping -c 1 {host}', shell=True, capture_output=True)",
        "label": 1,
        "cwe": "CWE-78",
        "language": "python",
        "description": "OS Command Injection via shell=True",
    },
    {
        "id": "benign_cwe78_01",
        "code": "import subprocess\ndef ping_host(host):\n    return subprocess.run(['ping', '-c', '1', host], shell=False, capture_output=True)",
        "label": 0,
        "cwe": "CWE-78",
        "language": "python",
        "description": "Safe array-based command execution without shell",
    },
    {
        "id": "vuln_cwe798_01",
        "code": "AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'\ndef upload_s3(data):\n    client = boto3.client('s3', aws_secret_access_key=AWS_SECRET_KEY)\n    return client.put(data)",
        "label": 1,
        "cwe": "CWE-798",
        "language": "python",
        "description": "Hardcoded AWS secret credentials",
    },
    {
        "id": "benign_cwe798_01",
        "code": "import os\ndef upload_s3(data):\n    secret = os.environ.get('AWS_SECRET_KEY')\n    client = boto3.client('s3', aws_secret_access_key=secret)\n    return client.put(data)",
        "label": 0,
        "cwe": "CWE-798",
        "language": "python",
        "description": "Credential loaded safely from environment variable",
    },
    {
        "id": "vuln_cwe94_01",
        "code": "function runUserCalculation(userInput) {\n    return eval(userInput);\n}",
        "label": 1,
        "cwe": "CWE-94",
        "language": "javascript",
        "description": "Direct JavaScript code injection via eval()",
    },
    {
        "id": "benign_cwe94_01",
        "code": "function runUserCalculation(userInput) {\n    const num = parseFloat(userInput);\n    return isNaN(num) ? 0 : num * 2;\n}",
        "label": 0,
        "cwe": "CWE-94",
        "language": "javascript",
        "description": "Safe numeric input parsing without eval",
    },
    {
        "id": "vuln_cwe22_01",
        "code": "def read_file(base_dir, user_file):\n    path = os.path.join(base_dir, user_file)\n    with open(path, 'r') as f:\n        return f.read()",
        "label": 1,
        "cwe": "CWE-22",
        "language": "python",
        "description": "Path Traversal vulnerability allowing ../ escapes",
    },
    {
        "id": "benign_cwe22_01",
        "code": "def read_file(base_dir, user_file):\n    resolved = (Path(base_dir) / user_file).resolve()\n    if not str(resolved).startswith(str(Path(base_dir).resolve())):\n        raise ValueError('Access Denied')\n    return resolved.read_text()",
        "label": 0,
        "cwe": "CWE-22",
        "language": "python",
        "description": "Path Traversal mitigation with resolve boundary check",
    },
]


class VulnerabilityDatasetLoader:
    """Loads and splits vulnerability datasets for neural model training and validation."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path

    def load_dataset(self) -> List[VulnerabilitySample]:
        samples = []
        # Load curated benchmark samples
        for item in CURATED_BENCHMARK_DATA:
            samples.append(VulnerabilitySample(**item))

        # If disk dataset JSON exists, extend
        if self.data_path and self.data_path.exists():
            try:
                disk_data = json.loads(self.data_path.read_text(encoding="utf-8"))
                for item in disk_data:
                    samples.append(VulnerabilitySample(**item))
            except Exception:
                pass

        return samples

    def get_splits(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Tuple[List[VulnerabilitySample], List[VulnerabilitySample], List[VulnerabilitySample]]:
        samples = self.load_dataset()
        n = len(samples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train = samples[:train_end]
        val = samples[train_end:val_end]
        test = samples[val_end:]
        return train, val, test
