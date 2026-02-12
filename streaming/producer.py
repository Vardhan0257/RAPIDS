import pandas as pd
import redis
import json


def run_producer(csv_path, stream_name="rapids_stream", max_rows=10000):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    df = pd.read_csv(csv_path)

    # keep only numeric columns
    df = df.select_dtypes(include=["number"])
    df = df.head(max_rows)

    for _, row in df.iterrows():
        data = row.to_dict()
        r.xadd(stream_name, {"flow": json.dumps(data)})

    print(f"Sent {len(df)} flows to stream.")
