import threading
from core.config_loader import load_config
from core.logger import setup_logger
from detection.anomaly_model import train_isolation_forest
from sklearn.preprocessing import StandardScaler

from streaming.producer import run_producer_from_dataframe
from streaming.consumer import run_consumer


def main():
    config = load_config()
    logger = setup_logger(config)

    dataset_path = "datasets/sample.csv"
    logger.info("Loading dataset for model training...")

    import pandas as pd
    import numpy as np

    df = pd.read_csv(dataset_path)

    # Detect label column
    label_col = None
    for col in df.columns:
        if "label" in col.lower():
            label_col = col
            break

    if label_col:
        df = df.drop(columns=[label_col])

    df = df.select_dtypes(include=["number"])
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    # Keep a copy for streaming
    stream_df = df.copy()

    scaler = StandardScaler()
    features = scaler.fit_transform(df)

    logger.info("Training Isolation Forest...")
    model = train_isolation_forest(features, contamination=0.20)

    # Create shutdown signal
    stop_event = threading.Event()

    # Start consumer thread
    consumer_thread = threading.Thread(
        target=run_consumer,
        args=(model, scaler, stop_event),
    )
    consumer_thread.start()

    try:
        # Start producer using cleaned data
        run_producer_from_dataframe(stream_df, max_rows=5000)
    except KeyboardInterrupt:
        print("[*] Stopping producer...")

    # Signal consumer to stop
    stop_event.set()

    consumer_thread.join()
    print("[*] Streaming IDS stopped.")


if __name__ == "__main__":
    main()
