import os

from fastapi.middleware.cors import CORSMiddleware  # type: ignore


# Function to add CORS middleware to the FastAPI app
def add_cors_middleware(app):
    """
    Adds CORS middleware to the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,  # Allow cookies and authentication headers
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )


class Settings:
    """
    Application settings loaded from environment variables.
    Provides configuration for Redis and WebSocket interval.
    """

    redis_host: str = os.getenv("REDIS_HOST", "redis")  # Redis server hostname
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))  # Redis server port
    redis_db: int = int(os.getenv("REDIS_DB", 0))  # Redis database index
    redis_password: str = os.getenv("REDIS_PASSWORD", None)  # Redis password
    redis_taxi_violation_alerts_stream: str = os.getenv("REDIS_TAXI_VIOLATION_ALERTS_STREAM", "taxi_violation_alerts")  # Redis taxi violation stream
    ws_interval: int = int(os.getenv("WEBSOCKET_INTERVAL_IN_SECONDS", 1))  # Interval for WebSocket updates (in seconds)
    dataset_size: int = int(os.getenv("DATASET_SIZE_LIMIT", 10357))  # dataset size limit
    data_replay_mode: str = os.getenv("DATA_REPLAY_MODE", "actual")  # data replay mode
    data_replay_speed: str = os.getenv("DATA_REPLAY_SPEED", "1.0")  # data replay speed


def get_settings() -> Settings:
    """
    Returns an instance of the Settings class.

    Returns:
        Settings: The application settings.
    """
    return Settings()
