import sys
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException  # type: ignore

# Add the current file's parent directory to sys.path for module resolution
sys.path.append(str(Path(__file__).parent))

from config import get_settings
from helpers import parse_json_safely
from redis_client.client import RedisClient
from schemas.violation_alerts import ViolationAlertSchema
from utils.logger import get_logger

# Initialize logger for the FastAPI backend
logger = get_logger("FastAPIBackend", "fastapi-backend.log")
# Create a FastAPI APIRouter instance
router = APIRouter()
# Get a Redis client instance
redis = RedisClient.get_client()
# Load application settings
settings = get_settings()


async def fetch_all_taxis(redis) -> List[Dict[str, any]]:
    """
    Fetch all taxi data from Redis, parse it, and return as a list of TaxiData objects.

    Args:
        redis: Redis client instance.

    Returns:
        List[TaxiData]: List of TaxiData objects sorted by taxi_id.
    """
    try:
        # Retrieve all keys matching the taxi pattern from Redis
        keys = await redis.keys("taxi:*")
        if not keys:
            # Return empty list if no taxi keys found
            return []

        # Use a Redis pipeline to fetch all taxi hashes in a single trip
        pipeline = redis.pipeline()
        for key in keys:
            pipeline.hgetall(key)
        results = await pipeline.execute()

        taxis = []
        # Iterate over each key and its corresponding data
        for key, data in zip(keys, results):
            if not data:
                continue  # Skip if no data found for the key
            taxis.append(parse_json_safely(data.get("data", "{}")))

        # Sort the taxis by taxi_id before returning
        taxis_sorted = sorted(taxis, key=lambda taxi: taxi["taxi_id"])

        return taxis_sorted

    except Exception as e:
        logger.error("Error during fetch_all_taxis: ", exc_info=True)
        raise


@router.get("/taxis", response_model=dict)
async def get_all_taxis():
    """
    FastAPI route to fetch all taxis from Redis and return them as an object.

    Returns:
        dict: Object containing taxi_fleet_size and taxis (list of TaxiData).
    """
    try:
        # Fetch all taxis using the helper function
        taxis = await fetch_all_taxis(redis)
        return {
            "total_taxi_fleet_size": settings.dataset_size,
            "data_replay_mode": settings.data_replay_mode,
            "data_replay_speed": settings.data_replay_speed,
            "taxis": taxis,
        }

    except Exception as e:
        logger.error("Error retrieving taxis from Redis: ", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving taxis from Redis: {str(e)}"
        )


async def fetch_all_incidents(redis) -> List[ViolationAlertSchema]:
    """
    Fetch all violation alert incidents from the Redis stream 'taxi_violation_alerts'.

    Args:
        redis: Redis client instance.

    Returns:
        List[ViolationAlert]: List of violation alert objects sorted by stream ID (chronologically).
    """
    try:
        # Fetch all entries in reverse order (latest first)
        # entries = await redis.xrevrange("taxi_violation_alerts", max='+', min='-', count=50)
        entries = await redis.xrange(
            settings.redis_taxi_violation_alerts_stream, min="-", max="+"
        )

        if not entries:
            return []

        # Reverse to get chronological order
        entries = list(reversed(entries))
        incidents = []
        for stream_id, fields in entries:
            decoded_fields = {
                (k.decode("utf-8") if isinstance(k, bytes) else k): (
                    v.decode("utf-8") if isinstance(v, bytes) else v
                )
                for k, v in fields.items()
            }
            # Create ViolationAlert instance with decoded fields
            incident = ViolationAlertSchema(**decoded_fields)
            incidents.append(incident)

        return incidents

    except Exception as e:
        # Log or raise error as appropriate
        logger.error(f"Error fetching incidents: {e}")
        raise


@router.get("/incidents", response_model=dict)
async def get_all_incidents():
    """
    FastAPI route to fetch all violation alerts from Redis and return them as an object.

    Returns:
        dict: Object containing total_incidents and incidents (list of IncidentData).
    """
    try:
        # Fetch all taxis using the helper function
        incidents = await fetch_all_incidents(redis)
        return {
            "total_incidents": len(incidents),
            "incidents": incidents,
        }

    except Exception as e:
        logger.error(
            "Error retrieving violation alerts incidents from Redis: ", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving violation alerts incidents from Redis: {str(e)}",
        )


@router.get("/taxi/ids", response_model=List[int])
async def get_taxi_ids():
    """
    FastAPI route to fetch all taxi IDs from Redis and return them as a list of integers.

    Returns:
        List[int]: List of taxi IDs.
    """
    try:
        # Fetch all keys matching the taxi pattern
        keys = await redis.keys("taxi:*")
        if not keys:
            return []

        # Extract taxi IDs from the keys
        taxi_ids = [int(key.split(":")[1]) for key in keys]

        return sorted(taxi_ids)

    except Exception as e:
        logger.error("Error retrieving taxi IDs from Redis: ", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error retrieving taxi IDs from Redis: {str(e)}"
        )
