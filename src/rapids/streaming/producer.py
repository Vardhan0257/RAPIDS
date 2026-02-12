import pandas as pd
import json
import time
import numpy as np

from rapids.core.redis_utils import connect_redis


def run_producer(
    csv_path,
    stream_name="rapids_stream",
    max_rows=10000,
    delay=0.001,
    target_fps=None,
    redis_host="localhost",
    redis_port=6379,
    connect_retries=5,
    retry_delay_sec=0.5,
):
    r = connect_redis(redis_host, redis_port, connect_retries, retry_delay_sec)

    df = pd.read_csv(csv_path)

    # Drop label column
    label_col = None
    for col in df.columns:
        if "label" in col.lower():
            label_col = col
            break

    if label_col:
        df = df.drop(columns=[label_col])

    # Keep numeric columns only
    df = df.select_dtypes(include=["number"])

    # Clean data
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    df = df.head(max_rows)

    if df.empty:
        print("[!] No rows to stream.")
        return

    print(f"[*] Sending {len(df)} flows to stream...")

    interval = None
    if target_fps:
        interval = 1.0 / float(target_fps)

    start_time = time.perf_counter()
    sent = 0

    for row in df.itertuples(index=False):
        data = dict(zip(df.columns, row))
        r.xadd(stream_name, {"flow": json.dumps(data)})
        sent += 1

        if interval is None:
            time.sleep(delay)
        else:
            next_time = start_time + (sent * interval)
            sleep_for = next_time - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)

    print("[*] Producer finished sending flows.")
