import redis
import json
import numpy as np
import time


def run_consumer(model, scaler, stream_name="rapids_stream", batch_size=100):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    last_id = "0-0"
    print("[*] Consumer started. Waiting for flows...")

    flow_count = 0
    start_time = time.time()

    while True:
        results = r.xread({stream_name: last_id}, count=batch_size, block=0)

        batch_features = []
        batch_ids = []

        for stream, messages in results:
            for msg_id, data in messages:
                last_id = msg_id
                flow = json.loads(data["flow"])

                features = np.array(list(flow.values()))
                batch_features.append(features)
                batch_ids.append(msg_id)

        if not batch_features:
            continue

        # Convert to numpy batch
        batch_features = np.array(batch_features)
        batch_features = scaler.transform(batch_features)

        t0 = time.time()
        preds = model.predict(batch_features)
        latency = (time.time() - t0) / len(preds)

        for msg_id, pred in zip(batch_ids, preds):
            flow_count += 1
            if pred == -1:
                print(f"[ALERT] {msg_id}")

        # Stats every 1000 flows
        if flow_count % 1000 < batch_size:
            elapsed = time.time() - start_time
            fps = flow_count / elapsed
            print(
                f"[STATS] flows={flow_count} "
                f"time={elapsed:.2f}s "
                f"throughput={fps:.2f} flows/sec "
                f"avg_latency={latency*1000:.2f} ms"
            )
