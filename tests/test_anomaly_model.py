"""Test suite for anomaly detection module."""
import numpy as np
import pytest
from rapids.detection.anomaly_model import (
    train_isolation_forest,
    train_test_evaluation,
    contamination_experiment,
)


@pytest.fixture
def sample_features():
    """Generate sample feature data."""
    np.random.seed(42)
    # Normal data
    normal = np.random.normal(loc=0, scale=1, size=(1000, 10))
    # Anomalous data
    anomaly = np.random.uniform(low=5, high=10, size=(50, 10))
    features = np.vstack([normal, anomaly])
    return features


@pytest.fixture
def sample_labels(sample_features):
    """Generate corresponding labels."""
    labels = np.array(["BENIGN"] * 1000 + ["ATTACK"] * 50)
    return labels


def test_train_isolation_forest(sample_features):
    """Test Isolation Forest training."""
    model = train_isolation_forest(sample_features, contamination=0.05)
    assert model is not None
    assert hasattr(model, "predict")


def test_isolation_forest_predictions(sample_features):
    """Test that model produces binary predictions."""
    model = train_isolation_forest(sample_features, contamination=0.05)
    preds = model.predict(sample_features[:10])
    assert all(p in [-1, 1] for p in preds)


def test_train_test_evaluation(sample_features, sample_labels):
    """Test evaluation metrics."""
    metrics = train_test_evaluation(sample_features, sample_labels, contamination=0.20)
    
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "false_positive_rate" in metrics
    
    # Check metric bounds
    assert 0 <= metrics["precision"] <= 1
    assert 0 <= metrics["recall"] <= 1
    assert 0 <= metrics["f1_score"] <= 1
    assert 0 <= metrics["false_positive_rate"] <= 1


def test_contamination_experiment(sample_features, sample_labels):
    """Test contamination sweep."""
    levels = [0.05, 0.10, 0.20]
    results = contamination_experiment(sample_features, sample_labels, levels)
    
    assert len(results) == 3
    assert all("contamination" in r for r in results)
    assert [r["contamination"] for r in results] == levels


def test_higher_contamination_higher_recall(sample_features, sample_labels):
    """Test that higher contamination generally improves recall."""
    low_cont = train_test_evaluation(sample_features, sample_labels, contamination=0.05)
    high_cont = train_test_evaluation(sample_features, sample_labels, contamination=0.30)
    
    # Higher contamination should catch more anomalies (higher recall)
    assert high_cont["recall"] >= low_cont["recall"] * 0.9
