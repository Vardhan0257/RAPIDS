import argparse
import json
import time
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from rapids.detection.anomaly_model import train_isolation_forest, train_test_evaluation
from rapids.evaluation.model_evaluation import AnomalyDetectorEvaluator
from rapids.reasoning.engine import ReasoningEngine


def load_dataset(csv_path: str, max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
    df = pd.read_csv(csv_path)
    if max_rows:
        df = df.head(max_rows)

    label_col = None
    for col in df.columns:
        col_lower = col.lower()
        if "label" in col_lower or "class" in col_lower:
            label_col = col
            break

    labels = None
    if label_col:
        labels = df[label_col]
        df = df.drop(columns=[label_col])

    df = df.select_dtypes(include=[np.number])
    df = df.replace([np.inf, -np.inf], np.nan)

    if labels is not None:
        combined = df.copy()
        combined["__label__"] = labels
        combined = combined.dropna()
        labels = combined["__label__"].reset_index(drop=True)
        df = combined.drop(columns=["__label__"]).reset_index(drop=True)
    else:
        df = df.dropna().reset_index(drop=True)

    return df, labels


def benchmark_detection(model, scaler, df_features, batch_size=256):
    total = len(df_features)
    if total == 0:
        return None

    latencies = []
    start = time.perf_counter()

    for i in range(0, total, batch_size):
        batch = df_features.iloc[i : i + batch_size].values
        batch_start = time.perf_counter()
        features = scaler.transform(batch)
        _ = model.predict(features)
        batch_time = time.perf_counter() - batch_start
        per_flow = batch_time / max(len(batch), 1)
        latencies.extend([per_flow] * len(batch))

    total_time = time.perf_counter() - start
    throughput = total / total_time if total_time > 0 else 0.0

    latencies_ms = np.array(latencies) * 1000.0
    return {
        "total_flows": total,
        "throughput_fps": throughput,
        "latency_ms": {
            "mean": float(np.mean(latencies_ms)),
            "p50": float(np.quantile(latencies_ms, 0.50)),
            "p95": float(np.quantile(latencies_ms, 0.95)),
        },
    }


def false_positive_stress(model, scaler, df_features, labels, batch_size=256):
    if labels is None:
        return None

    benign_mask = labels.astype(str).str.upper().eq("BENIGN")
    benign_df = df_features[benign_mask]
    if benign_df.empty:
        return None

    total = len(benign_df)
    false_positives = 0

    for i in range(0, total, batch_size):
        batch = benign_df.iloc[i : i + batch_size].values
        features = scaler.transform(batch)
        preds = model.predict(features)
        false_positives += int(np.sum(preds == -1))

    return {
        "benign_flows": total,
        "false_positives": false_positives,
        "false_positive_rate": false_positives / total if total else 0.0,
    }


def attack_path_accuracy(df_features, labels, host_count=20, max_hops=3):
    if labels is None:
        return None

    engine = ReasoningEngine(host_count=host_count, max_hops=max_hops)
    total_anomalies = 0
    path_hits = 0

    for flow, label in zip(df_features.to_dict(orient="records"), labels):
        src, dst = engine.observe_flow(flow)
        if str(label).upper() == "BENIGN":
            continue
        total_anomalies += 1
        paths, _ = engine.handle_anomaly(src, dst, flow)
        if paths:
            path_hits += 1

    return {
        "anomalies": total_anomalies,
        "paths_found": path_hits,
        "path_hit_rate": path_hits / total_anomalies if total_anomalies else 0.0,
    }


def build_report(csv_path: str, max_rows: int, batch_size: int) -> Dict:
    """
    Build comprehensive benchmark report with cross-validation and baselines.
    
    Args:
        csv_path: Path to dataset CSV.
        max_rows: Maximum rows to use.
        batch_size: Batch size for inference.
        
    Returns:
        Dictionary with complete evaluation results.
    """
    df_features, labels = load_dataset(csv_path, max_rows=max_rows)

    scaler = StandardScaler()
    features = scaler.fit_transform(df_features.values)
    model = train_isolation_forest(features, contamination=0.20)

    # Benchmark detection throughput and latency
    detection = benchmark_detection(model, scaler, df_features, batch_size=batch_size)
    
    # Detection metrics with standard train/test
    detection_metrics = None
    if labels is not None and len(labels) > 0:
        detection_metrics = train_test_evaluation(features, labels)
    
    # Cross-validation for robustness
    cv_metrics = None
    if labels is not None and len(labels) > 0:
        evaluator = AnomalyDetectorEvaluator()
        cv_metrics = evaluator.cross_validate_isolation_forest(
            features,
            labels,
            contamination=0.20,
            n_splits=5
        )
    
    # Baseline models for comparison
    baselines = {}
    if labels is not None and len(labels) > 0:
        evaluator = AnomalyDetectorEvaluator()
        try:
            baselines["random_forest_supervised"] = evaluator.baseline_random_forest(features, labels)
        except Exception as e:
            baselines["random_forest_supervised"] = {"error": str(e)}
        
        try:
            baselines["isolation_forest_default"] = evaluator.baseline_isolation_forest_default(features, labels)
        except Exception as e:
            baselines["isolation_forest_default"] = {"error": str(e)}
    
    # False positive stress test
    false_pos = false_positive_stress(model, scaler, df_features, labels, batch_size=batch_size)
    
    # Attack path accuracy
    attack_paths = attack_path_accuracy(df_features, labels)

    return {
        "dataset": csv_path,
        "rows_used": len(df_features),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "detection": detection,
        "detection_metrics": detection_metrics,
        "cross_validation": cv_metrics,
        "baselines": baselines,
        "false_positive_stress": false_pos,
        "attack_path_accuracy": attack_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="RAPIDS Phase 6 benchmarking")
    parser.add_argument("--dataset", default="datasets/sample.csv")
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--output", default="evaluation/benchmark_report.json")
    args = parser.parse_args()

    report = build_report(args.dataset, args.max_rows, args.batch_size)

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print("[*] Benchmark report generated")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
