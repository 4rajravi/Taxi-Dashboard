import asyncio

from aiokafka import AIOKafkaConsumer  # type: ignore

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
)
from redis_client import RedisClient  # type: ignore


async def initialize_redis_client_connection(logger: None):
    """
    Initializes Redis client and verifies connection via ping.
    Raises an error if the Redis connection cannot be established.
    """
    try:
        redis = await RedisClient(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            logger=logger,
        ).get_client()

        logger.info("Pinging Redis to test connection...")
        result = await redis.ping()
        if not result:
            raise ConnectionError("Redis ping failed.")
        else:
            logger.info("Redis ping successful.")
            return redis

    except Exception:
        logger.exception("Failed to initialize Redis client.")


async def wait_until_topic_available(
    logger: None, topic: str, retries: int = 5, delay: int = 1
):
    """
    Waits until the specified Kafka topic becomes available.
    Uses exponential backoff between retries.
    """
    temp_consumer = AIOKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    )
    await temp_consumer.start()

    try:
        for attempt in range(1, retries + 1):
            partitions = temp_consumer.partitions_for_topic(topic)

            if partitions:
                logger.info(
                    f"Topic '{topic}' is available with partitions: {partitions}"
                )
                return

            logger.info(
                f"Topic '{topic}' not yet available. Retry {attempt}/{retries}..."
            )
            await asyncio.sleep(delay * 2 ** (attempt - 1))
        raise RuntimeError(
            f"Topic '{topic}' not found in Kafka after {retries} retries."
        )

    finally:
        try:
            await temp_consumer.stop()
        except asyncio.CancelledError:
            logger.warning(
                "CancelledError occurred while stopping temp Kafka consumer (harmless)."
            )
