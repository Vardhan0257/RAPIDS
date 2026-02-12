from core.config_loader import load_config
from core.logger import setup_logger
from detection.data_loader import load_and_preprocess
from detection.anomaly_model import train_test_evaluation
from evaluation.feature_analysis import feature_impact_experiment


def main():
    config = load_config()
    logger = setup_logger(config)

    logger.info("RAPIDS system starting...")
    logger.info(f"Environment: {config['app']['environment']}")

    dataset_path = "datasets/sample.csv"
    logger.info(f"Loading dataset: {dataset_path}")

    features, labels = load_and_preprocess(dataset_path)
    logger.info(f"Feature matrix shape: {features.shape}")

    logger.info("Running feature impact experiment...")

    feature_counts = [10, 20, 40, 78]
    results = feature_impact_experiment(features, labels, feature_counts)

    for r in results:
        logger.info(
            f"features={r['feature_count']} | "
            f"precision={r['precision']:.4f} | "
            f"recall={r['recall']:.4f} | "
            f"f1={r['f1_score']:.4f} | "
            f"fpr={r['false_positive_rate']:.4f}"
        )

if __name__ == "__main__":
    main()