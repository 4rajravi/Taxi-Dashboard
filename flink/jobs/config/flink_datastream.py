import time

import orjson  # type: ignore

from pyflink.datastream import StreamExecutionEnvironment  # type: ignore
from pyflink.datastream.state_backend import EmbeddedRocksDBStateBackend  # type: ignore
from pyflink.common.typeinfo import Types  # type: ignore
from pyflink.common import Row  # type: ignore
from pyflink.datastream.functions import MapFunction  # type: ignore
from pyflink.datastream.checkpointing_mode import CheckpointingMode  # type: ignore


TAXI_RECORD_TYPE = Types.ROW_NAMED(
    [
        "taxi_id",
        "longitude",
        "latitude",
        "timestamp",
        "sent_at_utc_ms",
        "trip_status",
        "received_at_utc_ms",
        "speed",
        "is_valid_speed",
        "avg_speed",
        "total_distance_km",
        "distance_from_forbidden_city_km",
        "is_in_range",
    ],
    [
        Types.INT(),
        Types.STRING(),
        Types.STRING(),
        Types.STRING(),
        Types.LONG(),
        Types.STRING(),
        Types.LONG(),
        Types.FLOAT(),
        Types.BOOLEAN(),
        Types.FLOAT(),
        Types.FLOAT(),
        Types.FLOAT(),
        Types.BOOLEAN(),
    ],
)


class ParseMessageToRow(MapFunction):
    """
    MapFunction to parse a JSON string message into a PyFlink Row object
    with the schema defined by TAXI_RECORD_TYPE.
    """

    def map(self, msg: str) -> Row:
        """
        Parse a JSON string and convert it to a Row object.

        Args:
            msg (str): JSON string representing a taxi record.

        Returns:
            Row: Row object with fields populated from the JSON message.

        Raises:
            Exception: If parsing or field extraction fails.
        """
        try:
            data = orjson.loads(msg)

            return Row(
                taxi_id=data.get("taxi_id"),
                longitude=(
                    str(data.get("longitude"))
                    if data.get("longitude") is not None
                    else None
                ),
                latitude=(
                    str(data.get("latitude"))
                    if data.get("latitude") is not None
                    else None
                ),
                timestamp=data.get("timestamp"),
                sent_at_utc_ms=data.get("sent_at_utc_ms"),
                trip_status=data.get("trip_status"),
                received_at_utc_ms=int(time.time() * 1000),
                speed=data.get("speed"),
                is_valid_speed=data.get("is_valid_speed"),
                avg_speed=data.get("avg_speed"),
                total_distance_km=data.get("total_distance_km"),
                distance_from_forbidden_city_km=data.get(
                    "distance_from_forbidden_city_km"
                ),
                is_in_range=data.get("is_in_range"),
            )

        except Exception as e:
            raise e


def get_flink_datastream_execution_environment(
    logger: None,
    parallelism: int = 2,
    checkpointing_ms: int = 60_000,
    python_dependencies_path: str = None,
    kafka_connector_jar_file_path: str = None,
) -> StreamExecutionEnvironment:
    """
    Set up and return a configured PyFlink stream execution environment.

    Args:
        logger: Logging object
        parallelism (int): Number of parallel subtasks for task execution.
        checkpointing_ms (int): Interval (in milliseconds) at which Flink will take state snapshots.
        python_dependencies_path (str): External Python files dependency path.
        kafka_connector_jar_file_path (str): Kafka connector JAR file absolute path.

    Returns:
        StreamExecutionEnvironment: The configured Flink stream execution environment.
    """
    try:
        logger.info("⏳ Setting up Flink job stream execution environment...")

        # Get the default Flink stream execution environment
        env = StreamExecutionEnvironment.get_execution_environment()

        # Set the state backend to EmbeddedRocksDB with incremental checkpointing enabled
        env.set_state_backend(
            EmbeddedRocksDBStateBackend(enable_incremental_checkpointing=True)
        )

        # Set the parallelism level for the environment
        env.set_parallelism(parallelism)

        # env.get_config().set_auto_watermark_interval(200)

        # # Configure checkpoint settings (OPTIMIZED FOR LOW LATENCY)
        env.enable_checkpointing(checkpointing_ms)

        checkpoint_config = env.get_checkpoint_config()
        checkpoint_config.set_checkpointing_mode(CheckpointingMode.AT_LEAST_ONCE)
        # checkpoint_config.set_checkpoint_timeout(5 * 60 * 1000)
        # checkpoint_config.set_max_concurrent_checkpoints(1)
        # checkpoint_config.set_min_pause_between_checkpoints(5_000)

        # Add external Python files (e.g., user-defined operators, other python files)
        if python_dependencies_path:
            env.add_python_file(python_dependencies_path)

        # Register Kafka connector JAR (absolute path required)
        env.add_jars(kafka_connector_jar_file_path)

        logger.info("✅ Flink job stream execution environment set up successfully.")
        return env

    except Exception as e:
        logger.error(f"❌ Failed to setup Flink job stream execution environment: {e}")
        raise e


def get_kafka_source_datastream(
    logger: None,
    env,
    kafka_source,
    watermark_strategy,
    topics: str,
):
    """Create a DataStream from the given Kafka source.

    Use processing time semantics instead of event time processing.

    Args:
        logger: Logging object
        env: Flink stream execution environment object
        kafka_source: A configured Kafka source object
        watermark_strategy: Watermark strategy for event time streams
        topics: Kafka source topics

    Returns:
        A DataStream of raw JSON strings
    """
    try:
        logger.info(f"[!] Setting up DataStream from the Kafka topics: {topics}")

        # Create a DataStream from the given Kafka source.
        from_source = env.from_source(
            kafka_source,
            watermark_strategy,
            f"Kafka_Source_{topics}",
        ).map(ParseMessageToRow(), output_type=TAXI_RECORD_TYPE)

        logger.info(
            f"[✔] Successfully setup DataStream from the Kafka topics: {topics}"
        )
        return from_source

    except Exception as e:
        logger.error(
            f"[✘] Failed to setup DataStream from the Kafka topics: {topics}: {e}"
        )
        raise e
