from typing import Optional

import redis.asyncio as redis  # type: ignore
from redis.asyncio import Redis  # type: ignore
from redis.exceptions import ConnectionError  # type: ignore

from config import get_settings


class RedisClient:
    """
    RedisClient provides a singleton-style asynchronous Redis client.
    Handles connection initialization, health check, and cleanup.
    """

    _client: Optional[Redis] = None  # Holds the Redis client instance

    @classmethod
    def get_client(cls) -> Redis:
        """
        Returns the Redis client instance.
        Initializes the client if it does not exist.
        """
        if cls._client is None:
            settings = get_settings()  # Load configuration settings
            cls._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,  # Decode responses as strings
            )
        return cls._client

    @classmethod
    async def initialize(cls) -> None:
        """
        Checks the connection to Redis by sending a PING command.
        Raises RuntimeError if the connection fails.
        """
        try:
            await cls.get_client().ping()  # Test connection
        except ConnectionError as e:
            raise RuntimeError("Failed to connect to Redis") from e

    @classmethod
    async def close(cls) -> None:
        """
        Closes the Redis client connection if it exists.
        Raises RuntimeError if closing fails.
        """
        if cls._client:
            try:
                await cls._client.close()  # Close the connection
                cls._client = None  # Reset the client instance
            except ConnectionError as e:
                raise RuntimeError("Failed to close Redis client.") from e
