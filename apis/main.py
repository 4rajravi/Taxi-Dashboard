import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI  # type: ignore

# Add the current file's parent directory to sys.path for module resolution
sys.path.append(str(Path(__file__).parent))

from redis_client.client import RedisClient
from config import add_cors_middleware
from routes import rest, websocket, analytics  # type: ignore
from utils.logger import get_logger

# Initialize logger for the FastAPI backend
logger = get_logger("FastAPIBackend", "fastapi-backend.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Initializes and closes the Redis connection, logging the process.
    """
    try:
        await RedisClient.initialize()
        logger.info("Redis connection initialized.")
    except Exception as e:
        logger.error("Failed to initialize Redis: ", exc_info=True)
        raise RuntimeError("Startup failed: Cannot connect to Redis")

    yield

    try:
        await RedisClient.close()
        logger.info("Redis connection closed.")
    except Exception as e:
        logger.error("Failed to close Redis connection cleanly: ", exc_info=True)


# Create FastAPI app with custom lifespan handler
app = FastAPI(lifespan=lifespan)

# Add CORS middleware to the app
add_cors_middleware(app)

# Include Analytics, REST and WebSocket routers
app.include_router(analytics.router, prefix="/api")
app.include_router(rest.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns status of the API and Redis connection.
    """
    redis = RedisClient.get_client()
    try:
        pong = await redis.ping()
        return {"status": "ok", "redis": pong}
    except Exception:
        return {"status": "error", "redis": "unreachable"}
