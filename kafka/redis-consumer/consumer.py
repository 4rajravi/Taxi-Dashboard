import asyncio

from write_taxi_data_to_redis import run_kafka_redis_taxi_data_consumer
from write_taxi_violation_alerts_to_redis import (
    run_kafka_redis_violation_alerts_consumer,
)
from write_taxi_fleet_metrics_to_redis import run_kafka_redis_taxi_fleet_metrics_consumer

async def main():
    await asyncio.gather(
        # Start the asynchronous Kafka Redis consumer to write taxi data to Redis Hash
        run_kafka_redis_taxi_data_consumer(),
        # Start the asynchronous Kafka Redis consumer to write taxi violation alerts to Redis Stream
        run_kafka_redis_violation_alerts_consumer(),
        run_kafka_redis_taxi_fleet_metrics_consumer(),
    )


if __name__ == "__main__":
    """
    Entry point for the Kafka-to-Redis consumer applications.

    This script initializes and runs the Redis consumers responsible
    for processing Kafka topic messages related to taxi data, violation alerts, fleet metrics.
    """
    asyncio.run(main())
