from typing import Dict, List
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split


def train_isolation_forest(features: np.ndarray, contamination: float = 0.05) -> IsolationForest:
    """
    Train an Isolation Forest model for anomaly detection.
    
    Args:
        features: Input feature array (n_samples, n_features).
        contamination: Expected proportion of anomalies.
        
    Returns:
        Trained IsolationForest model.
    """
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(features)
    return model


def train_test_evaluation(
    features: np.ndarray,
    labels: np.ndarray,
    contamination: float = 0.20,
) -> Dict[str, float]:
    """
    Train and evaluate Isolation Forest on test set.
    
    Args:
        features: Input feature array (n_samples, n_features).
        labels: Labels (BENIGN or ATTACK).
        contamination: Expected proportion of anomalies.
        
    Returns:
        Dictionary with precision, recall, f1_score, false_positive_rate.
    """
    labels_binary = np.where(labels != "BENIGN", 1, 0)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        labels_binary,
        test_size=0.3,
        random_state=42,
        stratify=labels_binary
    )

    model = train_isolation_forest(X_train, contamination=contamination)

    preds = model.predict(X_test)
    preds_binary = np.where(preds == -1, 1, 0)

    precision = precision_score(y_test, preds_binary)
    recall = recall_score(y_test, preds_binary)
    f1 = f1_score(y_test, preds_binary)

    tn, fp, fn, tp = confusion_matrix(y_test, preds_binary).ravel()
    false_positive_rate = fp / (fp + tn)

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "false_positive_rate": float(false_positive_rate)
    }


def contamination_experiment(
    features: np.ndarray,
    labels: np.ndarray,
    levels: List[float],
) -> List[Dict[str, float]]:
    """
    Run contamination parameter sweep.
    
    Args:
        features: Input feature array.
        labels: Input labels.
        levels: List of contamination levels to sweep.
        
    Returns:
        List of evaluation results for each contamination level.
    """
    results = []

    for c in levels:
        metrics = train_test_evaluation(features, labels, contamination=c)
        metrics["contamination"] = c
        results.append(metrics)

    return results
