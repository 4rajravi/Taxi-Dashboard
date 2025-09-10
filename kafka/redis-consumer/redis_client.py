import redis.asyncio as redis  # type: ignore

from redis.backoff import ExponentialBackoff  # type: ignore
from redis.retry import Retry  # type: ignore
from redis.exceptions import ConnectionError, TimeoutError  # type: ignore


class RedisClient:
    """
    Asynchronous Redis client with automatic retry logic and connection management.

    Handles connection establishment, retries for transient errors, and provides
    health monitoring for persistent connections.
    """

    def __init__(self, host, port, db=0, password=None, logger=None):
        """Initialize Redis connection with retry capabilities.

        Args:
            host: Redis server hostname or IP address
            port: Redis server port number
            db: Redis database number (default: 0)
            password: Optional authentication password
            logger: Logger instance for connection events
        """
        self.logger = logger

        # Configure retry strategy for transient network errors
        # Base delay: 0.5s, Max delay: 5s, 5 attempts total
        self.retry = Retry(
            backoff=ExponentialBackoff(base=0.5, cap=5),
            retries=5,
            supported_errors=(ConnectionError, TimeoutError),
        )
        try:
            # Create Redis connection
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                retry=self.retry,
                decode_responses=True,  # Store data as UTF-8 strings
                health_check_interval=30,
            )
            self.logger.info("Connected to Redis successfully.")

        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"Redis connection failed: {e}")
            raise

        except Exception as e:
            self.logger.exception("Unhandled error during Redis client initialization.")
            raise

    def get_client(self) -> redis.Redis:
        """Get the configured Redis client instance.

        Returns:
            Authenticated Redis client with retry capabilities
        """
        return self._client
