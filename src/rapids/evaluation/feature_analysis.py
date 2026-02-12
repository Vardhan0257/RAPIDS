import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from rapids.detection.anomaly_model import train_test_evaluation


def feature_impact_experiment(features, labels, feature_counts):
    # Convert labels to binary
    labels_binary = np.where(labels != "BENIGN", 1, 0)

    # Train a supervised model to estimate feature importance
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(features, labels_binary)

    importances = rf.feature_importances_
    ranked_indices = np.argsort(importances)[::-1]

    results = []

    for count in feature_counts:
        selected = ranked_indices[:count]
        reduced_features = features[:, selected]

        metrics = train_test_evaluation(reduced_features, labels)
        metrics["feature_count"] = count
        results.append(metrics)

    return results
