from core.config_loader import load_config
from core.logger import setup_logger
from detection.data_loader import load_and_preprocess
from detection.anomaly_model import train_test_evaluation


def main():
    config = load_config()
    logger = setup_logger(config)

    logger.info("RAPIDS system starting...")
    logger.info(f"Environment: {config['app']['environment']}")

    dataset_path = "datasets/sample.csv"
    logger.info(f"Loading dataset: {dataset_path}")

    features, labels = load_and_preprocess(dataset_path)
    logger.info(f"Feature matrix shape: {features.shape}")

    logger.info("Running train/test evaluation...")
    metrics = train_test_evaluation(features, labels)

    for key, value in metrics.items():
        logger.info(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()