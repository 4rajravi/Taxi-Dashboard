import asyncio

from write_taxi_data_to_influxdb import run_kafka_influxdb_taxi_data_consumer
from write_taxi_violation_alerts_to_influxdb import run_kafka_influxdb_taxi_violation_alerts_consumer
from write_taxi_fleet_metrics_to_influxdb import run_kafka_influxdb_taxi_fleet_metrics_consumer

async def main():
    await asyncio.gather(
        # Start the asynchronous Kafka InfluxDB consumer to write taxi data to InfluxDB
        run_kafka_influxdb_taxi_data_consumer(),
        # Start the asynchronous Kafka InfluxDB consumer to write taxi violation alerts to Redis Hash
        run_kafka_influxdb_taxi_violation_alerts_consumer(),
        # Start the asynchronous Kafka InfluxDB consumer to write taxi fleet metrics to InfluxDB
        run_kafka_influxdb_taxi_fleet_metrics_consumer(),
    )


if __name__ == "__main__":
    """
    Entry point for the Kafka-to-InfluxDB consumer applications.

    This script initializes and runs the InfluxDB consumers responsible
    for processing Kafka topic messages related to taxi data, violation alerts, fleet metrics.
    """
    asyncio.run(main())
