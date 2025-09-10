import asyncio
import sys
from pathlib import Path

import orjson  # type: ignore
from aiokafka import AIOKafkaConsumer  # type: ignore
from aiokafka.errors import GroupCoordinatorNotAvailableError, ConsumerStoppedError  # type: ignore

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_GROUP,
    KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC,
    KAFKA_CONSUMER_STARTUP_DELAY,
    BATCH_INTERVAL_IN_SECONDS,
    BATCH_SIZE_LIMIT,
    ASYNCIO_QUEUE_SIZE_LIMIT,
)
from consumer_utils import (
    initialize_redis_client_connection,
    wait_until_topic_available,
)

sys.path.append(str(Path(__file__).parent))
from utils.logger import get_logger


class KafkaRedisTaxiFleetMetricsConsumer:
    """
    Kafka consumer that ingests fleet metrics messages, buffers them using asyncio queue,
    and writes them in batches to Redis. Only stores the latest message for current state.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger(
            "KafkaRedisTaxiFleetMetricsConsumer", "redis_taxi_fleet_metrics_consumer.log"
        )
        self.redis = None
        self.consumer = None
        # Async queue to buffer incoming Kafka messages for batch processing
        self.queue = asyncio.Queue(maxsize=ASYNCIO_QUEUE_SIZE_LIMIT)

    async def start_kafka_consumer_with_retries(self, retries: int = 5, delay: int = 1):
        """
        Starts the Kafka consumer, retrying with exponential backoff if the group coordinator is not available.
        Also ensures the topic is available before starting.
        """
        await wait_until_topic_available(
            logger=self.logger,
            topic=KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC,
            retries=retries,
            delay=delay,
        )

        for attempt in range(1, retries + 1):
            if self.consumer is not None:
                try:
                    # Stop previous consumer if still running before retrying
                    if not self.consumer._closed:
                        await self.consumer.stop()
                except Exception:
                    pass  # Ignore stop errors here

            self.consumer = AIOKafkaConsumer(
                KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_GROUP,
                enable_auto_commit=True,
                auto_commit_interval_ms=60000,
                value_deserializer=orjson.loads,
                auto_offset_reset="earliest",
                max_poll_records=1000,
            )

            self.logger.info(
                f"Attempting to start Kafka consumer (Attempt {attempt}/{retries})..."
            )
            try:
                await self.consumer.start()

                # Verify topic is in metadata
                partitions = self.consumer.partitions_for_topic(
                    KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC
                )
                if not partitions:
                    raise RuntimeError(
                        f"Partitions for topic {KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC} not found."
                    )

                self.logger.info("Kafka consumer started successfully.")
                return
            except GroupCoordinatorNotAvailableError as e:
                self.logger.warning(
                    f"GroupCoordinatorNotAvailableError: {e}. Retrying in {delay * 2 ** (attempt - 1)} seconds..."
                )
            except Exception as e:
                self.logger.warning(
                    f"Unexpected error while starting Kafka consumer: {e}. Retrying in {delay * 2 ** (attempt - 1)} seconds..."
                )

            await asyncio.sleep(delay * 2 ** (attempt - 1))

        self.logger.error("Failed to start Kafka consumer after multiple attempts.")
        raise RuntimeError("Kafka consumer failed to start after retries.")

    async def process_message(self, msg: dict):
        """
        Processes each Kafka message and enqueues it for batch writing.
        """
        try:
            if not msg.get("active_taxis") or not msg.get("trip_ended_taxis"):
                self.logger.warning("Fleet metrics message missing required fields.")
                return

            await self.queue.put(msg)

        except Exception as e:
            self.logger.exception("Error processing fleet metrics message.")

    async def write_batches_to_redis(self):
        """
        Collects messages in batches from the queue and writes to Redis.
        For fleet metrics, only stores the latest message as current state.
        Flushes on batch size limit or timeout.
        """
        batch = []

        while True:
            try:
                # Wait for a message with timeout
                item = await asyncio.wait_for(
                    self.queue.get(), timeout=BATCH_INTERVAL_IN_SECONDS
                )
                batch.append(item)

                # Collect more messages until batch limit or queue is empty
                while not self.queue.empty() and len(batch) < BATCH_SIZE_LIMIT:
                    msg = await self.queue.get()
                    batch.append(msg)

                if len(batch) >= BATCH_SIZE_LIMIT:
                    self.logger.info(
                        f"Batch size reached: {len(batch)}. Writing to Redis..."
                    )
                    await self._flush_batch(batch)

            except asyncio.TimeoutError:
                # Timeout reached, flush any pending messages
                if batch:
                    await self._flush_batch(batch)

            except Exception as e:
                self.logger.error(f"Unexpected error in write_batches_to_redis: {e}")

    async def _flush_batch(self, batch):
        """
        Flushes the batch to Redis. For fleet metrics, only the latest message is stored.
        """
        try:
            if not batch:
                return

            # For fleet metrics, we only need the latest message as current state
            latest_msg = batch[-1]
            
            await self.redis.hset("fleet", "metrics", orjson.dumps(latest_msg))
            self.logger.info(
                f"[Redis Write Success] Write batch of {len(batch)} messages to Redis."
            )
            batch.clear()

        except Exception as e:
            self.logger.error(f"Redis batch write error: {e}")

    async def start(self):
        """
        Main method that:
        - Initializes Redis
        - Starts the Kafka Consumer
        - Starts message processing and writer tasks
        """
        try:
            self.redis = await initialize_redis_client_connection(self.logger)
            await self.start_kafka_consumer_with_retries()
        except Exception:
            self.logger.error("Could not start Kafka consumer after retries.")
            return

        try:
            # Start the batch writer task
            writer_task = asyncio.create_task(self.write_batches_to_redis())

            # Process incoming Kafka messages
            async for msg in self.consumer:
                try:
                    await self.process_message(msg.value)
                except Exception as e:
                    self.logger.exception(f"Error processing message {msg}.")

            # Wait for writer task to complete
            await writer_task

        except ConsumerStoppedError:
            self.logger.error(
                "Consumer stopped unexpectedly. This may be due to earlier startup failure."
            )
        except asyncio.CancelledError:
            self.logger.info("Kafka consumer cancelled by event loop.")
        except Exception as e:
            self.logger.exception("Unexpected error during Kafka consumption.")
        finally:
            self.logger.info("Shutting down consumer and Redis client...")
            if self.consumer:
                await self.consumer.stop()
            if self.redis:
                await self.redis.aclose()
            self.logger.info("Shutdown complete")


async def run_kafka_redis_taxi_fleet_metrics_consumer():
    try:
        logger = get_logger(
            "KafkaRedisTaxiFleetMetricsConsumer",
            "redis_taxi_fleet_metrics_consumer.log",
        )

        logger.info(
            f"Delaying startup by {KAFKA_CONSUMER_STARTUP_DELAY} seconds to wait for Kafka broker readiness..."
        )
        await asyncio.sleep(KAFKA_CONSUMER_STARTUP_DELAY)

        consumer = KafkaRedisTaxiFleetMetricsConsumer(logger=logger)
        await consumer.start()

    except Exception:
        logger.critical(
            "Fatal error: redis taxi fleet metrics consumer application could not start",
            exc_info=True,
        )
        sys.exit(1)
