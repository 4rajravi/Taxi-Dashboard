import asyncio
import sys
from pathlib import Path

import orjson  # type: ignore
from aiokafka import AIOKafkaConsumer  # type: ignore
from aiokafka.errors import GroupCoordinatorNotAvailableError, ConsumerStoppedError  # type: ignore

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_REDIS_TAXI_DATA_CONSUMER_GROUP,
    KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC,
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


class KafkaRedisTaxiDataConsumer:
    """
    Kafka consumer that ingests messages, buffers them, and writes them in batches to Redis.
    Optimized for performance with buffered writes and reduced Redis round-trips.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger("KafkaRedisConsumer", "redis_consumer.log")
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
            topic=KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC,
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
                KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_REDIS_TAXI_DATA_CONSUMER_GROUP,
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
                    KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC
                )
                if not partitions:
                    raise RuntimeError(
                        f"Partitions for topic {KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC} not found."
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
        Processes an individual Kafka message.
        Attempts to enqueue into async queue for batch Redis writing.
        """
        try:
            taxi_id = msg.get("taxi_id")
            if not taxi_id:
                self.logger.warning("Missing taxi_id in message.")
                return

            await self.queue.put(msg)  # Enqueue the msg

        except Exception as e:
            self.logger.exception("Unexpected error while processing Kafka message.")

    async def write_batches_to_redis(self):
        """
        Writes Kafka messages from the queue to Redis in batches.
        Flushes when:
          - batch reaches the configured size limit
          - a timeout occurs waiting for more messages
        """
        # self.logger.info("Started write_batches_to_redis task.")
        batch = []

        while True:
            try:
                # Wait for a new message with timeout = BATCH_INTERVAL seconds
                item = await asyncio.wait_for(
                    self.queue.get(), timeout=BATCH_INTERVAL_IN_SECONDS
                )
                batch.append(item)

                # Drain any additional messages immediately to fill batch quickly
                while not self.queue.empty() and len(batch) < BATCH_SIZE_LIMIT:
                    msg = await self.queue.get()
                    batch.append(msg)
                    # batch.append(self.queue.get_nowait())

                # If batch size limit reached, flush immediately
                if len(batch) >= BATCH_SIZE_LIMIT:
                    self.logger.info(
                        f"Current queue size: {self.queue.qsize()}. Flushing existing batch..."
                    )
                    await self._flush_batch(batch)

            except asyncio.TimeoutError:
                # Timeout expired without new messages => flush existing batch if not empty
                if batch:
                    await self._flush_batch(batch)

            except Exception as e:
                self.logger.error(f"Unexpected error in write_batches_to_redis: {e}")

    async def _flush_batch(self, batch):
        """
        Writes the current batch to Redis using a pipeline.
        For each message:
        - Updates the 'current' field with the new data.
        - Optionally stores the previous value in 'previous'.
        """
        try:
            async with self.redis.pipeline(transaction=False) as pipe:
                for data in batch:
                    taxi_id = str(data.get("taxi_id"))
                    key = f"taxi:{taxi_id}"
                    pipe.hset(key, mapping={"data": orjson.dumps(data)})
                await pipe.execute()
                self.logger.info(
                    f"[Redis Write Sucess] Wrote {len(batch)} records to Redis."
                )
                batch.clear()  # Reset Batch

        except Exception as e:
            self.logger.error(f"Batch write error: {e}")

    async def start(self):
        """
        Main method that:
        - Starts the Kafka Consumer.
        - Starts the Redis Batch Writer.
        - Continuously processes incoming Kafka messages.
        """
        try:
            self.redis = await initialize_redis_client_connection(self.logger)
            await self.start_kafka_consumer_with_retries()
        except Exception:
            self.logger.error("Could not start Kafka consumer after retries.")
            return

        try:
            writer_task = asyncio.create_task(self.write_batches_to_redis())

            async for msg in self.consumer:
                # self.logger.info(f"Received message: {msg.value}")
                try:
                    await self.process_message(msg.value)
                except Exception as e:
                    self.logger.exception(f"Error processing message {msg}.")
                    writer_task.cancel()  # Ensure writer shuts down gracefully

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


async def run_kafka_redis_taxi_data_consumer():
    try:
        logger = get_logger(
            "KafkaRedisTaxiDataConsumer", "redis_taxi_data_consumer.log"
        )

        logger.info(
            f"Delaying startup by {KAFKA_CONSUMER_STARTUP_DELAY} seconds to wait for Kafka broker readiness..."
        )
        await asyncio.sleep(KAFKA_CONSUMER_STARTUP_DELAY)

        consumer = KafkaRedisTaxiDataConsumer(logger=logger)
        await consumer.start()

    except Exception:
        logger.critical(
            "Fatal error: redis taxi data consumer application could not start",
            exc_info=True,
        )
        sys.exit(1)
