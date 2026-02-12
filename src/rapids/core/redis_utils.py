import time
import redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def connect_redis(
    host: str = "localhost",
    port: int = 6379,
    retries: int = 5,
    delay_sec: float = 0.5,
    timeout_sec: int = 5,
) -> redis.Redis:
    """
    Connect to Redis with exponential backoff retry logic.
    
    Args:
        host: Redis host.
        port: Redis port.
        retries: Number of connection attempts.
        delay_sec: Initial delay between retries (exponential backoff).
        timeout_sec: Socket timeout per attempt.
        
    Returns:
        Connected Redis client.
        
    Raises:
        RuntimeError: If all connection attempts fail.
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(max(retries, 1)):
        try:
            logger.debug(f"Attempting Redis connection (attempt {attempt + 1}/{retries})")
            client = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
                socket_timeout=timeout_sec,
                socket_connect_timeout=timeout_sec,
            )
            client.ping()
            logger.info(f"Connected to Redis at {host}:{port}")
            return client
        except (redis.RedisError, ConnectionError, OSError) as exc:
            last_error = exc
            logger.warning(f"Redis connection failed (attempt {attempt + 1}/{retries}): {exc}")
            if attempt < retries - 1:
                sleep_time = delay_sec * (2 ** attempt)  # Exponential backoff
                logger.debug(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
    
    raise RuntimeError(
        f"Redis connection failed after {retries} retries "
        f"(host={host}, port={port}): {last_error}"
    )
