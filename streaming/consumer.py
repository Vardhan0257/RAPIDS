import redis
import json
import numpy as np
import time
import pandas as pd


def run_consumer(model, scaler, feature_columns, stop_event, stream_name="rapids_stream"):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    last_id = "0-0"
    print("[*] Consumer started. Waiting for flows...")

    flow_count = 0
    start_time = time.time()

    while not stop_event.is_set():
        results = r.xread({stream_name: last_id}, count=10, block=1000)

        if not results:
            continue

        for stream, messages in results:
            for msg_id, data in messages:
                last_id = str(msg_id)

                if "flow" not in data:
                    continue

                flow = json.loads(data["flow"])

                row_df = pd.DataFrame([flow], columns=feature_columns)
                features = scaler.transform(row_df)

                pred = model.predict(features)[0]
                flow_count += 1

                if pred == -1:
                    print(f"[ALERT] {msg_id}")

                # Print stats every 500 flows
                if flow_count % 500 == 0:
                    elapsed = time.time() - start_time
                    fps = flow_count / elapsed
                    print(
                        f"[STATS] flows={flow_count} "
                        f"time={elapsed:.2f}s "
                        f"throughput={fps:.2f} flows/sec"
                    )

    print("[*] Consumer shutting down.")
