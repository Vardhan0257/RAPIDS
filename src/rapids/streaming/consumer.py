import json
import numpy as np
import time

from rapids.core.redis_utils import connect_redis

def run_consumer(
    model,
    scaler,
    feature_columns,
    stop_event,
    reasoning_engine,
    stream_name="rapids_stream",
    redis_host="localhost",
    redis_port=6379,
    connect_retries=5,
    retry_delay_sec=0.5,
    batch_size=200,
    block_ms=200,
):
    r = connect_redis(redis_host, redis_port, connect_retries, retry_delay_sec)

    last_id = "0-0"
    print("[*] Consumer started. Waiting for flows...")

    flow_count = 0
    alert_count = 0
    start_time = time.perf_counter()

    while not stop_event.is_set():
        results = r.xread({stream_name: last_id}, count=batch_size, block=block_ms)

        if not results:
            continue

        for stream, messages in results:
            batch_ids = []
            batch_vectors = []
            batch_flows = []

            for msg_id, data in messages:
                last_id = str(msg_id)

                if "flow" not in data:
                    continue

                flow = json.loads(data["flow"])
                try:
                    vector = [flow[col] for col in feature_columns]
                except KeyError:
                    continue
                batch_ids.append(msg_id)
                batch_flows.append(flow)
                batch_vectors.append(vector)

            if not batch_vectors:
                continue

            features = np.array(batch_vectors, dtype=float)
            features = scaler.transform(features)
            preds = model.predict(features)

            flow_count += len(preds)

            for msg_id, flow, pred in zip(batch_ids, batch_flows, preds):
                src, dst = reasoning_engine.observe_flow(flow)
                if pred == -1:
                    alert_count += 1
                    paths, recommendations = reasoning_engine.handle_anomaly(src, dst, flow)
                    if alert_count % 50 == 0:
                        print(f"[ALERT] {msg_id} (count={alert_count})")
                        if paths:
                            best = paths[0]
                            path_str = " -> ".join(best["path"])
                            print(f"[PATH] {path_str} risk={best['risk']:.2f}")
                        if recommendations:
                            rec = recommendations[0]
                            reduction = rec["risk_reduction"] * 100
                            print(f"[ACTION] {rec['action']}")
                            print(f"[REDUCTION] {reduction:.0f}%")

            # Print stats every 500 flows
            if flow_count % 500 == 0:
                elapsed = time.perf_counter() - start_time
                fps = flow_count / elapsed
                print(
                    f"[STATS] flows={flow_count} "
                    f"time={elapsed:.2f}s "
                    f"throughput={fps:.2f} flows/sec"
                )

    print("[*] Consumer shutting down.")
