import asyncio
import sys
from pathlib import Path

from aiokafka import AIOKafkaConsumer  # type: ignore
from aiokafka.errors import GroupCoordinatorNotAvailableError, ConsumerStoppedError  # type: ignore
import orjson  # type: ignore

from helpers.influxdb_taxi_data_writer import InfluxDBTaxiDataWriter

# Ensure local imports work correctly
sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_TOPIC,
    KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_GROUP,
    KAFKA_INFLUXDB_CONSUMER_STARTUP_DELAY,
)

sys.path.append(str(Path(__file__).parent))
from utils.logger import get_logger


class KafkaInfluxDBTaxiDataConsumer:
    def __init__(self, logger=None):
        self.logger = logger or get_logger(
            "KafkaInfluxDBTaxiDataConsumer", "influxdb_taxi_data_consumer.log"
        )
        self.consumer = None
        self.influxdb_taxi_data_writer = InfluxDBTaxiDataWriter(logger=logger)

    async def wait_until_topic_available(
        self, topic: str, retries: int = 5, delay: int = 1
    ):
        temp_consumer = AIOKafkaConsumer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await temp_consumer.start()
        try:
            for attempt in range(1, retries + 1):
                partitions = temp_consumer.partitions_for_topic(topic)

                if partitions:
                    self.logger.info(
                        f"Topic '{topic}' is available with partitions: {partitions}"
                    )
                    return

                self.logger.info(
                    f"Waiting for topic '{topic}' (Attempt {attempt}/{retries})..."
                )
                await asyncio.sleep(delay * 2 ** (attempt - 1))

            raise RuntimeError(f"Topic '{topic}' not found after {retries} retries.")
        finally:
            try:
                await temp_consumer.stop()
            except asyncio.CancelledError:
                self.logger.warning("Temp Kafka consumer stop was cancelled.")

    async def start_kafka_influxdb_taxi_data_consumer(
        self, retries: int = 5, delay: int = 1
    ):
        await self.wait_until_topic_available(
            KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_TOPIC, retries, delay
        )

        for attempt in range(1, retries + 1):
            self.consumer = AIOKafkaConsumer(
                KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_GROUP,
                enable_auto_commit=True,
                value_deserializer=orjson.loads,
                auto_offset_reset="earliest",
                max_poll_records=1000,
            )

            try:
                self.logger.info(
                    f"Starting Kafka consumer (Attempt {attempt}/{retries})..."
                )
                await self.consumer.start()

                partitions = self.consumer.partitions_for_topic(
                    KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_TOPIC
                )
                if not partitions:
                    raise RuntimeError(
                        f"No partitions found for topic {KAFKA_INFLUXDB_TAXI_DATA_CONSUMER_TOPIC}"
                    )

                self.logger.info("Kafka consumer started successfully.")
                return

            except GroupCoordinatorNotAvailableError as e:
                self.logger.warning(f"GroupCoordinatorNotAvailableError: {e}")
            except Exception as e:
                self.logger.warning(f"Error starting Kafka consumer: {e}")

            await asyncio.sleep(delay * 2 ** (attempt - 1))

        raise RuntimeError("Failed to start Kafka consumer after retries.")

    async def consume_taxi_data_messages(self):
        try:
            batch = []
            batch_size = 1000  # Optimal batch size depends on system performance and throughput
            batch_write_interval = 1  # Write every second if batch size not reached
            last_write_time = asyncio.get_event_loop().time()
            try:
                async for msg in self.consumer:
                    batch.append(msg.value)
                    current_time = asyncio.get_event_loop().time()
                    
                    if len(batch) >= batch_size or (current_time - last_write_time) >= batch_write_interval:
                        try:
                            self.influxdb_taxi_data_writer.write_taxi_data_to_db(batch)
                            self.logger.info(f"[InfluxDB Write] Batch of {len(batch)} taxi_data")
                            batch.clear()
                            last_write_time = current_time
                        except Exception as e:
                            self.logger.error(f"[InfluxDB Error] Failed to write batch: {e}")
                # Write any remaining messages in the batch
                if batch:
                    try:
                        self.influxdb_taxi_data_writer.write_taxi_data_to_db(batch)
                        self.logger.info(f"[InfluxDB Write] Final batch of {len(batch)} taxi_data")
                    except Exception as e:
                        self.logger.error(f"[InfluxDB Error] Failed to write final batch: {e}")
            except Exception as e:
                self.logger.exception("Unexpected error during message consumption.")
        except ConsumerStoppedError:
            self.logger.error("Kafka consumer stopped unexpectedly.")
        except Exception as e:
            self.logger.exception("Unexpected error during message consumption.")
        finally:
            if self.consumer:
                await self.consumer.stop()

    async def start(self):
        try:
            await self.start_kafka_influxdb_taxi_data_consumer()
            await self.consume_taxi_data_messages()
        except Exception:
            self.logger.critical(
                "Fatal error during KafkaInfluxDBTaxiDataConsumer startup",
                exc_info=True,
            )


async def run_kafka_influxdb_taxi_data_consumer():
    try:
        logger = get_logger(
            "KafkaInfluxDBTaxiDataConsumer", "influxdb_taxi_data_consumer.log"
        )

        logger.info(
            f"Delaying startup by {KAFKA_INFLUXDB_CONSUMER_STARTUP_DELAY} seconds to wait for Kafka broker readiness..."
        )
        await asyncio.sleep(KAFKA_INFLUXDB_CONSUMER_STARTUP_DELAY)

        consumer = KafkaInfluxDBTaxiDataConsumer(logger=logger)
        await consumer.start()

    except Exception:
        logger.critical(
            "Fatal error: influxdb taxi data consumer application could not start",
            exc_info=True,
        )
        sys.exit(1)
