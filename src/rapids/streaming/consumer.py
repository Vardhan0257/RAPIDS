"""Stream consumer for real-time anomaly detection and risk reasoning."""
import json
import numpy as np
import time
import logging
import redis
from typing import List, Optional

from rapids.core.redis_utils import connect_redis

logger = logging.getLogger(__name__)


def run_consumer(
    model,
    scaler,
    feature_columns: List[str],
    stop_event,
    reasoning_engine,
    stream_name: str = "rapids_stream",
    redis_host: str = "localhost",
    redis_port: int = 6379,
    connect_retries: int = 5,
    retry_delay_sec: float = 0.5,
    batch_size: int = 200,
    block_ms: int = 200,
) -> None:
    """
    Consume flows from Redis stream and process anomalies.
    
    Args:
        model: Trained anomaly detection model.
        scaler: Fitted feature scaler.
        feature_columns: List of feature column names.
        stop_event: Threading event to signal shutdown.
        reasoning_engine: ReasoningEngine instance.
        stream_name: Redis stream name.
        redis_host: Redis host.
        redis_port: Redis port.
        connect_retries: Connection retry attempts.
        retry_delay_sec: Delay between retries.
        batch_size: Number of flows to batch.
        block_ms: Redis XREAD block timeout.
    """
    try:
        r = connect_redis(redis_host, redis_port, connect_retries, retry_delay_sec)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    last_id = "0-0"
    logger.info(f"[*] Consumer started. Waiting for flows on stream '{stream_name}'...")

    flow_count = 0
    alert_count = 0
    errors_count = 0
    start_time = time.perf_counter()

    try:
        while not stop_event.is_set():
            try:
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
                            logger.warning(f"Message {msg_id} missing 'flow' field")
                            errors_count += 1
                            continue

                        try:
                            flow = json.loads(data["flow"])
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse flow JSON in {msg_id}: {e}")
                            errors_count += 1
                            continue

                        try:
                            vector = [flow[col] for col in feature_columns]
                        except KeyError as e:
                            logger.warning(f"Missing feature {e} in flow {msg_id}")
                            errors_count += 1
                            continue

                        batch_ids.append(msg_id)
                        batch_flows.append(flow)
                        batch_vectors.append(vector)

                    if not batch_vectors:
                        continue

                    # Detect anomalies
                    try:
                        features = np.array(batch_vectors, dtype=float)
                        features = scaler.transform(features)
                        preds = model.predict(features)
                    except Exception as e:
                        logger.error(f"Error during anomaly detection: {e}")
                        errors_count += len(batch_ids)
                        continue

                    flow_count += len(preds)

                    # Process each prediction
                    for msg_id, flow, pred in zip(batch_ids, batch_flows, preds):
                        try:
                            src, dst = reasoning_engine.observe_flow(flow)

                            if pred == -1:  # Anomaly detected
                                alert_count += 1
                                paths, recommendations = reasoning_engine.handle_anomaly(src, dst, flow)

                                # Log outstanding alerts
                                if alert_count % 50 == 0:
                                    logger.info(f"[ALERT] {msg_id} (count={alert_count})")
                                    if paths:
                                        best = paths[0]
                                        path_str = " -> ".join(best["path"])
                                        logger.info(f"[PATH] {path_str} risk={best['risk']:.2f}")
                                    if recommendations:
                                        rec = recommendations[0]
                                        reduction = rec["risk_reduction"] * 100
                                        logger.info(f"[ACTION] {rec['action']}")
                                        logger.info(f"[REDUCTION] {reduction:.0f}%")
                        except Exception as e:
                            logger.warning(f"Error processing flow in message {msg_id}: {e}")
                            errors_count += 1
                            continue

                    # Log statistics every 500 flows
                    if flow_count % 500 == 0:
                        elapsed = time.perf_counter() - start_time
                        fps = flow_count / elapsed if elapsed > 0 else 0
                        error_rate = (errors_count / flow_count * 100) if flow_count > 0 else 0
                        logger.info(
                            f"[STATS] flows={flow_count} "
                            f"time={elapsed:.2f}s "
                            f"throughput={fps:.2f} flows/sec "
                            f"alerts={alert_count} "
                            f"errors={errors_count} ({error_rate:.1f}%)"
                        )

            except redis.RedisError as e:
                logger.error(f"Redis error during xread: {e}")
                errors_count += 1
                time.sleep(retry_delay_sec)
            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}")
                errors_count += 1
                time.sleep(retry_delay_sec)

    except KeyboardInterrupt:
        logger.info("[*] Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in consumer: {e}")
    finally:
        logger.info("[*] Consumer shutting down.")
        elapsed = time.perf_counter() - start_time
        fps = flow_count / elapsed if elapsed > 0 else 0
        logger.info(
            f"[FINAL] Processed {flow_count} flows in {elapsed:.2f}s "
            f"({fps:.2f} fps), {alert_count} alerts, {errors_count} errors"
        )
