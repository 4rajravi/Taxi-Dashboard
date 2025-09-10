import os
import sys

from pyflink.common import Types  # type: ignore

sys.path.append("/opt/flink")

from utils.logger import get_logger
from config.utils.pyflink import get_watermark_strategy
from config.flink_datastream import (
    get_flink_datastream_execution_environment,
    get_kafka_source_datastream,
)
from config.kafka_connectors import get_kafka_source_connector, get_kafka_sink_connector
from config.datastream_transformations import (
    propagate_location,
    calculate_speed,
    calculate_average_speed,
    calculate_distance,
    geofence_violation_alert,
    speed_violation_alert,
    fleet_metrics,
    deduplicate_same_timestamp,
)
from config.utils.pyflink import RowToJson


class FlinkDataStreamingJob:
    """
    FlinkDataStreamingJob is a class that sets up and executes a data streaming job using Apache Flink (PyFlink API).
    The job connects to Kafka as both a source and a sink, processes data using Pyflink Datastream API, and writes the results to the specified Kafka sink.

    This class handles the following:
    - Loading and validating environment variables for the job configuration
    - Configuring the data streaming pipeline using Kafka Source and Kafka Sink and Flink operators
    - Building and executing the Flink streaming job pipeline
    """

    def __init__(self, logger=None):
        """Initializes the FlinkDataStreamingJob with configuration values."""
        self.logger = logger or get_logger("FlinkJob", "flink-job.log")
        self.env = None

        # Load and validate environment variables
        try:
            self.parallelism = int(os.getenv("PARALLELISM", 2))
            self.checkpointing_ms = int(os.getenv("CHECKPOINTING_MS", 60_000))
            self.python_dependencies_path = os.getenv(
                "PYTHON_DEPENDENCIES_PATH", "/opt/flink/jobs"
            )
            self.kafka_connector_jar_file_path = os.getenv(
                "KAFKA_CONNECTOR_JAR_FILE_PATH",
                "file:///opt/flink/lib/flink-connector-kafka-3.2.0-1.18.jar",
            )
            self.bootstrap_server = os.getenv("KAFKA_BROKER_ADDRESS", "localhost:9092")
            self.consumer_group_id = os.getenv(
                "CONSUMER_GROUP_ID", "taxi_stream_consumer_group"
            )
            self.trip_inactivity_timeout_in_seconds = int(
                os.getenv("TRIP_INACTIVITY_TIMEOUT_IN_SECONDS", 180)
            )
            self.trip_emit_interval_in_seconds = int(
                os.getenv("TRIP_EMIT_INTERVAL_IN_SECONDS", 5)
            )
            self.source_topics = os.getenv("KAFKA_SOURCE_TOPICS")
            self.taxi_processed_data_sink_topic = os.getenv(
                "KAFKA_TAXI_PROCESSED_DATA_SINK_TOPIC"
            )
            self.taxi_violation_alerts_sink_topic = os.getenv(
                "KAFKA_TAXI_VIOLATION_ALERTS_SINK_TOPIC"
            )
            self.taxi_fleet_metrics_sink_topic = os.getenv(
                "KAFKA_TAXI_FLEET_METRICS_SINK_TOPIC"
            )
            self.forbidden_city_lat = float(os.getenv("FORBIDDEN_CITY_LAT", 39.9163))
            self.forbidden_city_lon = float(os.getenv("FORBIDDEN_CITY_LON", 116.3972))
            self.geofenceWarning = float(os.getenv("GEOFENCE_WARNING_KM", 10))
            self.geofenceRange = float(os.getenv("GEOFENCE_RANGE_KM", 15))
            self.speedthreshold = int(os.getenv("SPEED_THRESHOLD_KMPH", 50))

            # Validate required environment variables
            if not all(
                [
                    self.source_topics,
                    self.taxi_processed_data_sink_topic,
                    self.taxi_violation_alerts_sink_topic,
                    self.taxi_fleet_metrics_sink_topic,
                ]
            ):
                self.logger.error(
                    "❌ Missing essential environment variables: "
                    "KAFKA_SOURCE_TOPICS, KAFKA_TAXI_PROCESSED_DATA_SINK_TOPIC, KAFKA_TAXI_VIOLATION_ALERTS_SINK_TOPIC, and KAFKA_TAXI_FLEET_METRICS_SINK_TOPIC are required."
                )
                raise EnvironmentError("Essential environment variables not set.")

        except Exception as e:
            self.logger.error(f"❌ Error Initializing FlinkDataStreamingJob: {e}")
            raise e

    def get_source_idleness(self):
        try:
            # Determine how early the Kafka data source should be marked as idle
            # If the inactivity timeout is short (10–30s), use a smaller 5s buffer
            # Otherwise, use a larger 10s buffer
            # If timeout is too small (<10s), default to 0 and log a warning
            if 10 <= self.trip_inactivity_timeout_in_seconds <= 30:
                source_idleness_duration_in_seconds = (
                    self.trip_inactivity_timeout_in_seconds - 5
                )
            elif self.trip_inactivity_timeout_in_seconds > 30:
                source_idleness_duration_in_seconds = (
                    self.trip_inactivity_timeout_in_seconds - 10
                )
            else:
                source_idleness_duration_in_seconds = 0
                logger.warning(
                    f"⚠️ The trip_inactivity_timeout_in_seconds is too low: "
                    f"({self.trip_inactivity_timeout_in_seconds}s); "
                    f"Defaulting source idleness to 0s for WatermarkStrategy."
                )

            return source_idleness_duration_in_seconds

        except Exception as e:
            raise e

    def apply_datastream_transformations(self):
        try:
            # === check duplicate timestamp ===
            self.taxi_processed_data_stream = deduplicate_same_timestamp(
                self.logger, self.taxi_raw_data_stream
            )

            # === propagate taxi location information at regular interval ===
            self.taxi_processed_data_stream = propagate_location(
                self.logger,
                self.taxi_processed_data_stream,
                window_interval=self.trip_emit_interval_in_seconds,
            )

            # === calculate taxi current trip speed ===
            self.taxi_processed_data_stream = calculate_speed(
                self.logger, self.taxi_processed_data_stream
            )

            # === calculate taxi current trip average speed ===
            self.taxi_processed_data_stream = calculate_average_speed(
                self.logger,
                self.taxi_processed_data_stream,
            )

            # === calculate total distance covered by taxi in the entire journey ===
            self.taxi_processed_data_stream = calculate_distance(
                self.logger,
                self.taxi_processed_data_stream,
            )

            # === aggregate fleet metrics ===
            self.taxi_fleet_metrics_stream = fleet_metrics(
                self.logger,
                self.taxi_processed_data_stream,
            )

            # === alert on geofence violation event ===
            (
                self.taxi_processed_data_stream,
                self.taxi_geofence_violation_alerts_stream,
            ) = geofence_violation_alert(
                self.logger,
                self.taxi_processed_data_stream,
                self.forbidden_city_lat,
                self.forbidden_city_lon,
                self.geofenceWarning,
                self.geofenceRange,
            )

            # === alert on speed violation event ===
            self.taxi_speed_violation_alerts_stream = speed_violation_alert(
                self.logger,
                self.taxi_processed_data_stream,
                self.speedthreshold,
            )

            # === union geofence and speed violation alerts streams ===
            self.violation_alerts_stream = (
                self.taxi_geofence_violation_alerts_stream.union(
                    self.taxi_speed_violation_alerts_stream
                )
            )

        except Exception as e:
            raise e

    def sink_output_streams(self):
        try:
            # Sink taxi processed data output stream
            self.taxi_processed_data_stream.map(
                RowToJson(),
                output_type=Types.STRING(),
            ).sink_to(
                get_kafka_sink_connector(
                    self.logger,
                    self.bootstrap_server,
                    self.taxi_processed_data_sink_topic,
                )
            ).name(
                f"KafkaSink_Taxi_Data_{self.taxi_processed_data_sink_topic}"
            )

            # Sink the unified violation alerts stream to the Kafka topic
            self.violation_alerts_stream.sink_to(
                get_kafka_sink_connector(
                    self.logger,
                    self.bootstrap_server,
                    self.taxi_violation_alerts_sink_topic,
                )
            ).name(f"KafkaSink_ViolationAlerts_{self.taxi_violation_alerts_sink_topic}")

            # Sink fleet metrics output stream
            self.taxi_fleet_metrics_stream.sink_to(
                get_kafka_sink_connector(
                    self.logger,
                    self.bootstrap_server,
                    self.taxi_fleet_metrics_sink_topic,
                )
            ).name(f"KafkaSink_Fleet_Metrics_{self.taxi_fleet_metrics_sink_topic}")

        except Exception as e:
            raise e

    def build_stream_processing_pipeline(self):
        """Build and configure the data processing pipeline with Kafka source and sink and using Flink operators."""
        try:
            self.logger.info("⏳ Building Flink DataStream Processing Pipeline...")

            # Configure Kafka Source Connector
            self.kafka_source_connector = get_kafka_source_connector(
                self.logger,
                self.bootstrap_server,
                self.consumer_group_id,
                self.source_topics,
            )

            # Get Kafka source idleness in seconds for WatermarkStrategy
            self.source_idleness_duration_in_seconds = self.get_source_idleness()

            # Configure watermark strategy for event time processing
            self.watermark_strategy = get_watermark_strategy(
                self.logger, self.source_idleness_duration_in_seconds
            )

            # Create DataStream from the given Kafka source topics.
            self.taxi_raw_data_stream = get_kafka_source_datastream(
                self.logger,
                self.env,
                self.kafka_source_connector,
                self.watermark_strategy,
                self.source_topics,
            )

            # DataStream Operators & Transformations
            self.apply_datastream_transformations()

            # Sink all output streams to Kafka Sink topics
            self.sink_output_streams()

            self.logger.info(
                "✅ Flink DataStream Processing Pipeline Built Successfully."
            )

        except Exception as e:
            self.logger.error(f"❌ Error Building DataStream Processing Pipeline: {e}")
            raise e

    def run(self):
        """Run the full Flink job, including setting up environment and executing the pipeline."""
        try:
            # Setup PyFlink streaming job execution environment
            self.env = get_flink_datastream_execution_environment(
                self.logger,
                self.parallelism,
                self.checkpointing_ms,
                self.python_dependencies_path,
                self.kafka_connector_jar_file_path,
            )

            # Build the stream processing pipeline
            self.build_stream_processing_pipeline()

            # Execute the Flink streaming job
            self.logger.info("⏳ Launching FlinkDataStreamingJob Execution...")
            self.env.execute("FlinkDataStreamingJob")
            self.logger.info("✅ FlinkDataStreamingJob Executed Successfully.")

        except Exception as e:
            self.logger.error(f"❌ Error During FlinkDataStreamingJob Execution: {e}")
            raise e


if __name__ == "__main__":
    # Initialize logger
    logger = get_logger("FlinkDataStreamingJob", "flink-job.log")
    logger.info("Starting FlinkDataStreamingJob Initialization...")

    try:
        flink_job = FlinkDataStreamingJob(logger=logger)
        flink_job.run()

    except Exception as e:
        logger.error(f"FlinkDataStreamingJob Initialization Failed: {e}")
        raise e

    logger.info("FlinkDataStreamingJob Completed.")
