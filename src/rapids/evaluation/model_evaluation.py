"""Rigorous model evaluation with cross-validation and baselines."""
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.covariance import EllipticEnvelope
from sklearn.svm import OneClassSVM
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, roc_curve,
    precision_recall_curve, auc as sklearn_auc
)


class AnomalyDetectorEvaluator:
    """Evaluate anomaly detection models with cross-validation."""
    
    @staticmethod
    def cross_validate_isolation_forest(
        features: np.ndarray,
        labels: np.ndarray,
        contamination: float = 0.20,
        n_splits: int = 5,
    ) -> Dict[str, Any]:
        """
        Cross-validate Isolation Forest with stratified k-fold.
        
        Args:
            features: Feature array.
            labels: Binary labels (0=BENIGN, 1=ATTACK).
            contamination: Contamination parameter.
            n_splits: Number of CV folds.
            
        Returns:
            Dictionary with per-fold and aggregate metrics.
        """
        labels_binary = np.where(labels != "BENIGN", 1, 0)
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        fold_metrics = []
        for fold_idx, (train_idx, test_idx) in enumerate(skf.split(features, labels_binary)):
            X_train, X_test = features[train_idx], features[test_idx]
            y_train, y_test = labels_binary[train_idx], labels_binary[test_idx]
            
            model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train)
            
            preds = model.predict(X_test)
            preds_binary = np.where(preds == -1, 1, 0)
            
            precision = float(precision_score(y_test, preds_binary, zero_division=0))
            recall = float(recall_score(y_test, preds_binary, zero_division=0))
            f1 = float(f1_score(y_test, preds_binary, zero_division=0))
            
            fold_metrics.append({
                "fold": fold_idx + 1,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            })
        
        # Aggregate metrics
        precisions = [m["precision"] for m in fold_metrics]
        recalls = [m["recall"] for m in fold_metrics]
        f1s = [m["f1"] for m in fold_metrics]
        
        return {
            "model": "IsolationForest",
            "per_fold": fold_metrics,
            "mean_precision": float(np.mean(precisions)),
            "std_precision": float(np.std(precisions)),
            "mean_recall": float(np.mean(recalls)),
            "std_recall": float(np.std(recalls)),
            "mean_f1": float(np.mean(f1s)),
            "std_f1": float(np.std(f1s)),
        }
    
    @staticmethod
    def baseline_random_forest(
        features: np.ndarray,
        labels: np.ndarray,
        test_size: float = 0.3,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Train a supervised Random Forest baseline for comparison.
        
        Args:
            features: Feature array.
            labels: Labels.
            test_size: Test split ratio.
            random_state: Random seed.
            
        Returns:
            Dictionary with RF metrics.
        """
        from sklearn.model_selection import train_test_split
        
        labels_binary = np.where(labels != "BENIGN", 1, 0)
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels_binary,
            test_size=test_size,
            random_state=random_state,
            stratify=labels_binary
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        preds = model.predict(X_test_scaled)
        proba = model.predict_proba(X_test_scaled)[:, 1]
        
        precision = float(precision_score(y_test, preds, zero_division=0))
        recall = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        auc = float(roc_auc_score(y_test, proba))
        
        return {
            "model": "RandomForest (Supervised)",
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "auc_roc": auc,
            "note": "Supervised baseline—not directly comparable to unsupervised IsolationForest",
        }
    
    @staticmethod
    def baseline_isolation_forest_default(
        features: np.ndarray,
        labels: np.ndarray,
        test_size: float = 0.3,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Isolation Forest with default contamination (0.1) baseline.
        
        Args:
            features: Feature array.
            labels: Labels.
            test_size: Test split ratio.
            random_state: Random seed.
            
        Returns:
            Dictionary with IF metrics.
        """
        from sklearn.model_selection import train_test_split
        
        labels_binary = np.where(labels != "BENIGN", 1, 0)
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels_binary,
            test_size=test_size,
            random_state=random_state,
            stratify=labels_binary
        )
        
        model = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # Default
            random_state=random_state,
            n_jobs=-1
        )
        model.fit(X_train)
        
        preds = model.predict(X_test)
        preds_binary = np.where(preds == -1, 1, 0)
        
        precision = float(precision_score(y_test, preds_binary, zero_division=0))
        recall = float(recall_score(y_test, preds_binary, zero_division=0))
        f1 = float(f1_score(y_test, preds_binary, zero_division=0))
        
        return {
            "model": "IsolationForest (contamination=0.1)",
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    
    @staticmethod
    def compute_threshold_analysis(
        features: np.ndarray,
        labels: np.ndarray,
        model: IsolationForest,
        test_size: float = 0.3,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Analyze model performance across different decision thresholds.
        
        Args:
            features: Feature array.
            labels: Labels.
            model: Pre-trained IsolationForest.
            test_size: Test split ratio.
            random_state: Random seed.
            
        Returns:
            Analysis of precision, recall, F1 at multiple thresholds.
        """
        from sklearn.model_selection import train_test_split
        
        labels_binary = np.where(labels != "BENIGN", 1, 0)
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels_binary,
            test_size=test_size,
            random_state=random_state,
            stratify=labels_binary
        )
        
        # Get anomaly scores (negative for anomalies)
        scores = model.score_samples(X_test)
        
        thresholds = np.percentile(scores, [10, 20, 30, 40, 50, 60, 70, 80, 90])
        threshold_results = []
        
        for threshold in thresholds:
            preds = (scores <= threshold).astype(int)
            
            precision = float(precision_score(y_test, preds, zero_division=0))
            recall = float(recall_score(y_test, preds, zero_division=0))
            f1 = float(f1_score(y_test, preds, zero_division=0))
            
            threshold_results.append({
                "threshold": float(threshold),
                "precision": precision,
                "recall": recall,
                "f1": f1,
            })
        
        return {
            "model": "IsolationForest Threshold Analysis",
            "thresholds": threshold_results,
        }
