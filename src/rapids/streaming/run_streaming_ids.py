import threading
import pandas as pd
from sklearn.preprocessing import StandardScaler

from rapids.core.config_loader import load_config
from rapids.core.logger import setup_logger, log_event
from rapids.detection.anomaly_model import train_isolation_forest
from rapids.streaming.producer import run_producer
from rapids.streaming.consumer import run_consumer
from rapids.reasoning.engine import ReasoningEngine


def main():
    config = load_config()
    logger = setup_logger(config)

    dataset_path = config["dataset"]["path"]
    log_event(logger, "dataset.load", path=dataset_path)

    df = pd.read_csv(dataset_path)

    label_col = None
    for col in df.columns:
        if "label" in col.lower():
            label_col = col
            break

    if label_col:
        df = df.drop(columns=[label_col])

    df = df.select_dtypes(include=["number"])
    df = df.replace([float("inf"), -float("inf")], float("nan"))
    df = df.dropna()

    feature_columns = df.columns.tolist()

    scaler = StandardScaler()
    features = scaler.fit_transform(df.values)


    log_event(logger, "model.train", model="IsolationForest")
    model = train_isolation_forest(features, contamination=0.20)

    stop_event = threading.Event()
    reasoning_engine = ReasoningEngine(
        host_count=config["reasoning"]["host_count"],
        max_hops=config["reasoning"]["max_hops"],
    )

    consumer_thread = threading.Thread(
        target=run_consumer,
        args=(
            model,
            scaler,
            feature_columns,
            stop_event,
            reasoning_engine,
            config["streaming"]["stream_name"],
            config["redis"]["host"],
            config["redis"]["port"],
            config["redis"]["connect_retries"],
            config["redis"]["retry_delay_sec"],
            config["streaming"]["batch_size"],
            config["streaming"]["block_ms"],
        )
    )
    consumer_thread.start()

    try:
        run_producer(
            dataset_path,
            stream_name=config["streaming"]["stream_name"],
            max_rows=config["streaming"]["max_rows"],
            target_fps=config["streaming"]["target_fps"],
            redis_host=config["redis"]["host"],
            redis_port=config["redis"]["port"],
            connect_retries=config["redis"]["connect_retries"],
            retry_delay_sec=config["redis"]["retry_delay_sec"],
        )
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C detected. Stopping...")

    stop_event.set()
    consumer_thread.join()

    print("[*] Streaming IDS stopped.")

if __name__ == "__main__":
    main()