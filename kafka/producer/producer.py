import os
import sys
import json
import asyncio
import pandas as pd  # type: ignore
from pathlib import Path

from aiokafka import AIOKafkaProducer  # type: ignore
from aiokafka.errors import KafkaConnectionError, KafkaError  # type: ignore

# Ensure relative imports work (for local modules)
sys.path.append(str(Path(__file__).parent))

from datareader import DataReader
from utils.logger import get_logger


def get_env_vars() -> dict:
    """Helper function to load environment variables."""
    env_vars = {}

    # Load and validate DATASET_SIZE
    try:
        dataset_size_limit = int(os.getenv("DATASET_SIZE_LIMIT", 10357))
        if dataset_size_limit < 1 or dataset_size_limit > 10357:
            raise ValueError(
                "DATASET_SIZE_LIMIT must be an integer between 1 and 10357."
            )
        env_vars["dataset_size_limit"] = dataset_size_limit

    except Exception as e:
        raise RuntimeError(f"Failed to determine data size limit: {e}")

    # Load and validate DATA_REPLAY_MODE
    try:
        data_replay_mode = os.getenv("DATA_REPLAY_MODE", "actual").lower()
        if data_replay_mode not in {"actual", "simulated"}:
            raise ValueError(
                f"Invalid DATA_REPLAY_MODE: '{data_replay_mode}'. Must be either 'actual' or 'simulated'."
            )
        env_vars["data_replay_mode"] = data_replay_mode

    except Exception as e:
        raise RuntimeError(f"Failed to determine data replay mode: {e}")

    # Load and validate DATA_REPLAY_SPEED
    try:
        data_replay_speed = float(os.getenv("DATA_REPLAY_SPEED", "1.0"))
        allowed_data_replay_speeds = {1.0, 1.5, 2.0, 2.5, 3.0}
        if data_replay_speed not in allowed_data_replay_speeds:
            raise ValueError(
                f"DATA_REPLAY_SPEED must be one of {sorted(allowed_data_replay_speeds)}"
            )
        env_vars["data_replay_speed"] = data_replay_speed

    except Exception as e:
        raise RuntimeError(f"Failed to determine data replay speed: {e}")

    return env_vars


class TaxiKafkaProducerAsync:
    """
    Asynchronous Kafka producer for sending cleaned taxi data in batches.
    """

    def __init__(
        self,
        input_dir="data/",
        output_dir="data/processed",
        pkl_file="merged_cleaned_data.pkl",
        kafka_bootstrap=os.getenv("KAFKA_BROKER_ADDRESS", "localhost:9092"),
        topic=os.getenv("KAFKA_TOPIC", "sample_kafka_topic"),
        logger=None,
    ):  # Accept logger as parameter
        self.logger = logger or get_logger(
            "TaxiKafkaProducerAsync", "producer.log"
        )  # Use passed-in logger or fallback
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.pkl_path = self.output_dir / pkl_file
        self.kafka_bootstrap = kafka_bootstrap
        self.topic = topic
        self.producer: AIOKafkaProducer | None = None

    async def prepare_data(self, dataset_size_limit: int = 10357):
        """Process raw data and generate cleaned pickle file."""
        self.logger.info("Running DataReader to generate cleaned data...")
        try:
            reader = DataReader(
                dataset_size_limit=dataset_size_limit,
                input_dir=self.input_dir,
                output_dir=self.output_dir,
                output_file=self.pkl_path.name,
            )
            reader.process()
            self.logger.info("DataReader completed successfully.")
        except Exception as e:
            self.logger.error(f"Failed to process data: {e}")
            raise

    def batch_by_timestamp(self, df: pd.DataFrame) -> pd.core.groupby.DataFrameGroupBy:
        """Group DataFrame by 1-second timestamp intervals."""
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.sort_values(by="timestamp", inplace=True)
        df["batch_time"] = df["timestamp"].dt.floor("1s")
        return df.groupby("batch_time")

    async def start_producer_with_retry(self, retries=5, delay=1):
        """
        Starts the Kafka producer with retry logic and ensures the topic exists.

        Retries connection attempts and waits for the specified topic to appear
        in the Kafka cluster metadata before proceeding.

        Parameters:
            retries (int): Number of retry attempts before failing.
            delay (int): Delay (in seconds) between retries.
        """
        for attempt in range(1, retries + 1):
            try:
                self.logger.info(
                    f"Attempting to start Kafka producer (Attempt {attempt}/{retries})..."
                )

                # Try to start the Kafka producer
                await self.producer.start()

                # Check if the topic is available in cluster metadata
                partitions = await self.producer.partitions_for(self.topic)
                if partitions is None:
                    self.logger.warning(
                        f"Kafka topic '{self.topic}' not found in cluster metadata after connection. "
                        f"Waiting for topic to appear..."
                    )
                    await asyncio.sleep(delay)
                    continue  # Retry if topic not available
                else:
                    self.logger.info(
                        f"Kafka producer started and connected to broker. Topic '{self.topic}' is available."
                    )
                    return
            except KafkaConnectionError as e:
                self.logger.warning(
                    f"Kafka connection failed: {e}. Retrying in {delay} second(s)..."
                )
            except KafkaError as e:
                self.logger.warning(
                    f"Kafka error on start: {e}. Retrying in {delay} second(s)..."
                )
            await asyncio.sleep(delay)

        self.logger.error(
            "Failed to start Kafka producer and confirm topic availability after multiple attempts."
        )
        raise RuntimeError(
            "Kafka producer could not connect or find topic after retries."
        )

    async def send_data(self, data_replay_mode: str = "actual", data_replay_speed: float = 1.0):
        """Send data to Kafka in timestamp-based batches with adjustable replay speed."""
        if not self.pkl_path.exists():
            raise FileNotFoundError(f"{self.pkl_path} does not exist.")

        df = pd.read_pickle(self.pkl_path)
        if df.empty:
            self.logger.warning("No data to send.")
            return

        grouped = self.batch_by_timestamp(df)

        self.logger.info(
            f"Initializing Kafka producer for topic '{self.topic}' with bootstrap server '{self.kafka_bootstrap}...'"
        )

        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        try:
            # Start Kafka producer with retry attempts
            await self.start_producer_with_retry()

            total_sent = 0
            prev_batch_time = None

            for batch_time, group in grouped:
                send_tasks = []

                # Respect real timestamp delay between event batches
                if prev_batch_time is not None:
                    if data_replay_mode == "actual":
                        delay = (batch_time - prev_batch_time).total_seconds() / data_replay_speed
                        if delay > 0:
                            self.logger.info(
                                f"[ACTUAL REPLAY MODE: {data_replay_speed}x SPEED] Delaying next batch send by {delay:.2f} seconds. Next batch time: {batch_time}."
                            )
                            await asyncio.sleep(delay)
                        else:
                            self.logger.warning(f"[Actual Mode] Non-positive delay ({delay:.2f}s) detected. Skipping sleep.")
                    elif data_replay_mode == "simulated":
                        delay = 1.0 / data_replay_speed
                        self.logger.info(
                            f"[SIMULATED REPLAY MODE: {data_replay_speed}x SPEED] Fixed delay of {delay:.2f} seconds between batches."
                        )
                        await asyncio.sleep(delay)
                else:
                    self.logger.info(f"Sending messages in {data_replay_mode.upper()} replay mode at {data_replay_speed}x speed.")

                for _, row in group.iterrows():
                    # Get current UTC time in milliseconds for this batch
                    current_utc_ms = int(pd.Timestamp.utcnow().timestamp() * 1000)
                    message = {
                        "taxi_id": row["taxi_id"],
                        "timestamp": str(row["timestamp"]),
                        "longitude": row["longitude"],
                        "latitude": row["latitude"],
                        "trip_status": row["trip_status"],
                        "sent_at_utc_ms": current_utc_ms,
                    }
                    send_tasks.append(
                        self.producer.send_and_wait(
                            topic=self.topic,
                            value=message,
                            key=str(message["taxi_id"]).encode(),
                        )
                    )

                await asyncio.gather(*send_tasks)

                self.logger.info(
                    f"Sent {len(group)} messages for batch time {batch_time}."
                )

                total_sent += len(group)
                prev_batch_time = batch_time

            self.logger.info(
                f"All messages sent successfully. Total messages: {total_sent}."
            )
        except KafkaConnectionError as e:
            self.logger.error(f"Could not connect to Kafka: {e}")
        except KafkaError as e:
            self.logger.error(f"Kafka error: {e}")
        finally:
            if self.producer:
                await self.producer.stop()
                self.logger.info("Kafka producer connection closed.")

    async def run(
        self,
        dataset_size_limit: int = 10357,
        data_replay_mode: str = "actual",
        data_replay_speed: float = 1.0,
    ):
        """Run data processing and streaming."""
        await self.prepare_data(dataset_size_limit=dataset_size_limit)
        await self.send_data(
            data_replay_mode=data_replay_mode, data_replay_speed=data_replay_speed
        )


if __name__ == "__main__":
    env_vars = get_env_vars()
    logger = get_logger("TaxiKafkaProducer", "producer.log")

    logger.info("Starting TaxiKafkaProducerAsync initialization...")
    kafka_producer = TaxiKafkaProducerAsync(logger=logger)
    logger.info(
        f"Running TaxiKafkaProducerAsync with dataset size limit: {env_vars['dataset_size_limit']}."
    )

    try:
        asyncio.run(
            kafka_producer.run(
                dataset_size_limit=env_vars["dataset_size_limit"],
                data_replay_mode=env_vars["data_replay_mode"],
                data_replay_speed=env_vars["data_replay_speed"],
            )
        )
        logger.info("TaxiKafkaProducerAsync finished successfully.")
    except Exception as e:
        logger.exception("Unhandled exception occurred during producer execution.")
