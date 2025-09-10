import asyncio
import sys
import time
import secrets
from pathlib import Path

from aiokafka import AIOKafkaConsumer  # type: ignore
from aiokafka.errors import GroupCoordinatorNotAvailableError, ConsumerStoppedError  # type: ignore
import orjson  # type: ignore

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_GROUP,
    KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC,
    KAFKA_CONSUMER_STARTUP_DELAY,
    BATCH_INTERVAL_IN_SECONDS,
    BATCH_SIZE_LIMIT,
    ASYNCIO_QUEUE_SIZE_LIMIT,
    REDIS_TAXI_VIOLATION_ALERTS_STREAM,
)
from consumer_utils import (
    initialize_redis_client_connection,
    wait_until_topic_available,
)

sys.path.append(str(Path(__file__).parent))
from utils.logger import get_logger


class KafkaRedisViolationAlertConsumer:
    """
    Kafka consumer that ingests violation alerts, buffers them,
    and writes them in batches to a Redis Stream using XADD.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger(
            "ViolationAlertConsumer", "violation_alerts.log"
        )
        self.redis = None
        self.consumer = None
        # Async queue to buffer incoming Kafka messages for batch processing
        self.queue = asyncio.Queue(maxsize=ASYNCIO_QUEUE_SIZE_LIMIT)

    async def start_kafka_consumer_with_retries(self, retries: int = 5, delay: int = 1):
        """
        Starts the Kafka consumer with retries and ensures the topic is available.
        Implements exponential backoff if startup fails.
        """
        await wait_until_topic_available(
            logger=self.logger,
            topic=KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC,
            retries=retries,
            delay=delay,
        )

        for attempt in range(1, retries + 1):
            if self.consumer is not None:
                try:
                    if not self.consumer._closed:
                        await self.consumer.stop()
                except Exception:
                    pass  # Safe to ignore

            self.consumer = AIOKafkaConsumer(
                KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_GROUP,
                enable_auto_commit=True,
                auto_commit_interval_ms=60000,
                value_deserializer=orjson.loads,
                auto_offset_reset="earliest",
                max_poll_records=1000,
            )

            self.logger.info(
                f"Starting Kafka consumer for violation alerts (Attempt {attempt}/{retries})..."
            )

            try:
                await self.consumer.start()

                partitions = self.consumer.partitions_for_topic(
                    KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC
                )
                if not partitions:
                    raise RuntimeError(
                        f"No partitions found for topic {KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC}."
                    )

                self.logger.info("Violation alert Kafka consumer started successfully.")
                return
            except GroupCoordinatorNotAvailableError as e:
                self.logger.warning(
                    f"Coordinator error: {e}. Retrying in {delay * 2 ** (attempt - 1)}s..."
                )
            except Exception as e:
                self.logger.warning(
                    f"Startup error: {e}. Retrying in {delay * 2 ** (attempt - 1)}s..."
                )

            await asyncio.sleep(delay * 2 ** (attempt - 1))

        self.logger.error("Failed to start Kafka consumer after retries.")
        raise RuntimeError("Kafka consumer failed after multiple retries.")

    async def process_message(self, msg: dict):
        """
        Processes each Kafka message and enqueues it for batch writing.
        """
        try:
            if not msg.get("taxi_id"):
                self.logger.warning("Violation alert missing taxi_id.")
                return
            if not msg.get("alert_type"):
                self.logger.warning("Violation alert missing alert_type.")
                return

            await self.queue.put(msg)

        except Exception as e:
            self.logger.exception("Error processing violation alert message.")

    async def write_batches_to_redis(self):
        """
        Collects messages in batches from the queue and writes to Redis Stream.
        Flushes on batch size limit or timeout.
        """
        batch = []

        while True:
            try:
                item = await asyncio.wait_for(
                    self.queue.get(), timeout=BATCH_INTERVAL_IN_SECONDS
                )
                batch.append(item)

                while not self.queue.empty() and len(batch) < BATCH_SIZE_LIMIT:
                    msg = await self.queue.get()
                    batch.append(msg)

                if len(batch) >= BATCH_SIZE_LIMIT:
                    self.logger.info(
                        f"Batch size reached: {len(batch)}. Writing to Redis stream..."
                    )
                    await self._flush_batch(batch)

            except asyncio.TimeoutError:
                if batch:
                    await self._flush_batch(batch)

            except Exception as e:
                self.logger.error(f"Unexpected error in write_batches_to_redis: {e}")

    async def _flush_batch(self, batch):
        """
        Flushes the batch to Redis stream using XADD for each violation alert.
        """
        try:
            async with self.redis.pipeline(transaction=False) as pipe:
                for data in batch:
                    fields = {
                        "incident_id": secrets.token_hex(8),
                        "taxi_id": data.get("taxi_id"),
                        "alert_type": data.get("alert_type"),
                        "timestamp": data.get("timestamp"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),
                        "trip_status": data.get("trip_status"),
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    }

                    if data.get("alert_type") == "GEOFENCE_VIOLATION":
                        fields["distance_km"] = data.get("distance_km")

                    if data.get("alert_type") == "SPEED_VIOLATION":
                        fields["speed"] = data.get("speed")

                    # Add to Redis stream
                    pipe.xadd(name=REDIS_TAXI_VIOLATION_ALERTS_STREAM, fields=fields)

                await pipe.execute()
                self.logger.info(
                    f"[Redis Stream Write Success] Flushed {len(batch)} records."
                )
                batch.clear()

        except Exception as e:
            self.logger.error(f"Error flushing batch to Redis stream: {e}")

    async def start(self):
        """
        Main execution method:
        - Initializes Redis
        - Starts Kafka consumer
        - Starts message processing and writer task
        """
        try:
            self.redis = await initialize_redis_client_connection(self.logger)
            await self.start_kafka_consumer_with_retries()
        except Exception:
            self.logger.error("Failed to initialize consumer or Redis client.")
            return

        try:
            writer_task = asyncio.create_task(self.write_batches_to_redis())

            async for msg in self.consumer:
                try:
                    await self.process_message(msg.value)
                except Exception:
                    self.logger.exception("Error handling Kafka message.")
                    writer_task.cancel()

            await writer_task

        except ConsumerStoppedError:
            self.logger.error("Kafka consumer stopped unexpectedly.")
        except asyncio.CancelledError:
            self.logger.info("Consumer cancelled.")
        except Exception as e:
            self.logger.exception("Unhandled exception in Kafka consumer loop.")
        finally:
            self.logger.info("Shutting down consumer and Redis...")
            if self.consumer:
                await self.consumer.stop()
            if self.redis:
                await self.redis.aclose()
            self.logger.info("Shutdown complete.")


async def run_kafka_redis_violation_alerts_consumer():
    """
    Entry point for running the Violation Alert Kafka-Redis consumer.
    """
    try:
        logger = get_logger(
            "KafkaRedisViolationAlertsConsumer", "redis_violation_alerts_consumer.log"
        )

        logger.info(
            f"Delaying startup by {KAFKA_CONSUMER_STARTUP_DELAY}s to wait for Kafka broker readiness..."
        )
        await asyncio.sleep(KAFKA_CONSUMER_STARTUP_DELAY)

        consumer = KafkaRedisViolationAlertConsumer(logger=logger)
        await consumer.start()

    except Exception:
        logger.critical(
            "Fatal error: Violation alert consumer could not start", exc_info=True
        )
        sys.exit(1)
