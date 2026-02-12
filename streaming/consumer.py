import redis
import json
import numpy as np
import pandas as pd


def run_consumer(model, scaler, stop_event, stream_name="rapids_stream"):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    last_id = "0-0"
    print("[*] Consumer started. Waiting for flows...")

    try:
        while not stop_event.is_set():
            results = r.xread({stream_name: last_id}, count=1, block=1000)

            for stream, messages in results:
                for msg_id, data in messages:
                    last_id = msg_id
                    flow = json.loads(data["flow"])

                    flow_df = pd.DataFrame([flow])
                    features = scaler.transform(flow_df)

                    pred = model.predict(features)[0]

                    if pred == -1:
                        print(f"[ALERT] Anomalous flow detected: {msg_id}")

    except KeyboardInterrupt:
        pass

    print("[*] Consumer shutting down.")
