import redis
import json
import numpy as np
from detection.anomaly_model import train_isolation_forest


def run_consumer(model, stream_name="rapids_stream"):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    last_id = "0-0"

    while True:
        results = r.xread({stream_name: last_id}, count=1, block=0)

        for stream, messages in results:
            for msg_id, data in messages:
                last_id = msg_id
                flow = json.loads(data["flow"])

                features = np.array(list(flow.values())).reshape(1, -1)
                pred = model.predict(features)[0]

                if pred == -1:
                    print(f"[ALERT] Anomalous flow detected: {msg_id}")
