import time
import redis


def connect_redis(host, port, retries=5, delay_sec=0.5):
    last_error = None
    for _ in range(max(retries, 1)):
        try:
            client = redis.Redis(host=host, port=port, decode_responses=True)
            client.ping()
            return client
        except (redis.RedisError, ConnectionError) as exc:
            last_error = exc
            time.sleep(delay_sec)
    raise RuntimeError(f"Redis connection failed after {retries} retries: {last_error}")
