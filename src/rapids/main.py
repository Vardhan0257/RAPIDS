from rapids.core.config_loader import load_config
from rapids.core.logger import setup_logger, log_event
from rapids.detection.data_loader import load_and_preprocess
from rapids.detection.anomaly_model import train_test_evaluation
from rapids.evaluation.feature_analysis import feature_impact_experiment


def main():
    config = load_config()
    logger = setup_logger(config)

    log_event(logger, "app.start", environment=config["app"]["environment"])

    dataset_path = config["dataset"]["path"]
    log_event(logger, "dataset.load", path=dataset_path)

    features, labels = load_and_preprocess(dataset_path)
    log_event(logger, "dataset.features", rows=features.shape[0], cols=features.shape[1])

    log_event(logger, "feature_impact.start")

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