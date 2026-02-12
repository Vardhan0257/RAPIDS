import redis
import json
import time


def run_producer_from_dataframe(df, stream_name="rapids_stream", max_rows=10000, delay=0.001):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    df = df.head(max_rows)

    print(f"[*] Sending {len(df)} flows to stream...")

    for _, row in df.iterrows():
        data = row.to_dict()
        r.xadd(stream_name, {"flow": json.dumps(data)})
        time.sleep(delay)

    print("[*] Producer finished sending flows.")
