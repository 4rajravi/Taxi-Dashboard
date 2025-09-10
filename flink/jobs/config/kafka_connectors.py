from pyflink.common.serialization import SimpleStringSchema  # type: ignore
from pyflink.datastream.connectors.kafka import DeliveryGuarantee  # type: ignore
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer  # type: ignore
from pyflink.datastream.connectors.kafka import KafkaRecordSerializationSchema  # type: ignore
from pyflink.datastream.connectors.kafka import KafkaSink  # type: ignore
from pyflink.datastream.connectors.kafka import KafkaSource  # type: ignore


def get_kafka_source_connector(
    logger: None, bootstrap_server: str, consumer_group_id: str, topics_str: str
) -> KafkaSource:
    """
    Create and return a Kafka source connector for one or more topics using PyFlink.

    Args:
        logger: Logging object
        bootstrap_server (str): Kafka bootstrap server address.
        consumer_group_id (str): Kafka consumer group ID.
        topics (str): Comma-separated topic names to subscribe to (e.g., "topic1,topic2").

    Returns:
        KafkaSource: Configured Kafka source connector for PyFlink.
    """
    try:
        logger.info(
            f"[!] Configuring Kafka Source Connector for topics: {topics_str} ..."
        )

        # Split and clean topic names
        topics = [topic.strip() for topic in topics_str.split(",") if topic.strip()]
        if not topics:
            raise ValueError("No valid Kafka topics provided.")

        # Build the KafkaSource Connector
        kafka_source_connector = (
            KafkaSource.builder()
            .set_bootstrap_servers(bootstrap_server)
            .set_topics(*topics)
            .set_group_id(consumer_group_id)
            .set_starting_offsets(KafkaOffsetsInitializer.earliest())
            .set_value_only_deserializer(SimpleStringSchema())
            .build()
        )

        logger.info(
            f"[✔] Configured Kafka Source Connector successfully for topics: {topics_str}."
        )
        return kafka_source_connector

    except Exception as e:
        logger.error(
            f"[✘] Failed to configure Kafka Source Connector for topics: {topics_str}: {e}"
        )
        raise e


def get_kafka_sink_connector(
    logger: None, bootstrap_server: str, topic: str
) -> KafkaSink:
    """
    Create and return a Kafka sink connector for a specific topic using PyFlink.

    Args:
        logger: Logging object
        bootstrap_server (str): Kafka bootstrap server address.
        topic (str): Kafka topic to produce messages to.

    Returns:
        KafkaSink: Configured Kafka sink connector for PyFlink.
    """
    try:
        logger.info(f"[!] Configuring Kafka Sink Connector for topic: {topic} ...")

        # Build the KafkaSink Connector
        kafka_sink_connector = (
            KafkaSink.builder()
            .set_bootstrap_servers(bootstrap_server)
            .set_record_serializer(
                KafkaRecordSerializationSchema.builder()
                .set_topic(topic)
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
            )
            .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
            .build()
        )

        logger.info(
            f"[✔] Configured Kafka Sink Connector successfully for topic: {topic}."
        )
        return kafka_sink_connector

    except Exception as e:
        logger.error(
            f"[✘] Failed to configure Kafka Sink Connector for topic: {topic}: {e}"
        )
        raise e
