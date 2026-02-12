import os
import sys
from pathlib import Path
import pytest
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def sample_dataset_path():
    """Return path to sample dataset."""
    return ROOT / "datasets" / "sample.csv"


@pytest.fixture
def random_seed():
    """Set and return random seed for reproducibility."""
    seed = 42
    np.random.seed(seed)
    return seed


@pytest.fixture
def sample_anomaly_data():
    """Generate sample data with known anomalies."""
    np.random.seed(42)
    # Normal data
    normal = np.random.normal(loc=0, scale=1, size=(500, 20))
    # Anomalous data
    anomaly = np.random.uniform(low=5, high=10, size=(50, 20))
    features = np.vstack([normal, anomaly])
    labels = np.array(["BENIGN"] * 500 + ["ATTACK"] * 50)
    return features, labels
