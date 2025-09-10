import sys
import time
import asyncio
from pathlib import Path
from typing import Set

from fastapi import APIRouter, WebSocket, Query  # type: ignore
from starlette.websockets import WebSocketDisconnect  # type: ignore

# Add the current file's parent directory to sys.path for module resolution
sys.path.append(str(Path(__file__).parent))

from config import get_settings
from helpers import parse_json_safely
from redis_client.client import RedisClient
from utils.logger import get_logger

# Initialize logger for the FastAPI backend
logger = get_logger("FastAPIBackend", "fastapi-backend.log")
# Create an API router instance
router = APIRouter()
# Get a Redis client instance
redis = RedisClient.get_client()
# Set to keep track of all active WebSocket connections
ws_taxis_active_connections: Set[WebSocket] = set()
ws_incidents_active_connections: Set[WebSocket] = set()
ws_taxi_fleet_metrics_active_connections: Set[WebSocket] = set()
# Load application settings
settings = get_settings()


async def fetch_all_taxis():
    """
    Fetch all taxi states from Redis using a single pipeline operation.

    Returns:
        List of dictionaries containing taxi_id, current, and previous state.
    """
    keys = await redis.keys("taxi:*")
    if not keys:
        return []

    # Use a Redis pipeline to fetch all taxi hashes in one network round-trip
    pipeline = redis.pipeline()
    for key in keys:
        pipeline.hgetall(key)
    results = await pipeline.execute()

    taxis = []
    for key, data in zip(keys, results):
        if not data:
            continue
        taxis.append(parse_json_safely(data.get("data", "{}")))

    return taxis


async def fetch_all_incidents():
    """
    Fetch the last 50 violation alert incidents from Redis stream in chronological order.

    Returns:
        List[dict]: List of  dictionaries containing incidents.
    """
    entries = await redis.xrevrange(
        settings.redis_taxi_violation_alerts_stream, max="+", min="-", count=50
    )

    if not entries:
        return []

    # Reverse to get chronological order
    entries = list(reversed(entries))

    incidents = []

    for stream_id, fields in entries:
        incident = {
            (k.decode("utf-8") if isinstance(k, bytes) else k): (
                v.decode("utf-8") if isinstance(v, bytes) else v
            )
            for k, v in fields.items()
        }

        incidents.append(incident)

    return incidents


async def fetch_taxi_fleet_metrics():
    """
    Fetch taxi fleet metrics from Redis.

    Returns:
        dict: Parsed metrics data including current taxi fleet size.
    """
    data = await redis.hget("fleet", "metrics")
    taxi_keys = await redis.keys("taxi:*")
    current_taxi_fleet_size = len(taxi_keys)
    if not data:
        return {"current_taxi_fleet_size": current_taxi_fleet_size}
    # If data is bytes, decode to string
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    metrics = parse_json_safely(data)
    metrics["current_taxi_fleet_size"] = current_taxi_fleet_size
    return metrics


async def broadcast_taxis(ws_interval: int):
    """
    Continuously broadcast all taxis to connected WebSocket clients at a fixed interval.

    This function loops while there are active WebSocket connections, fetches the current
    state of all taxis, and sends that data to each connected client. The loop ensures
    that each broadcast cycle (including fetch and send time) occurs approximately every
    `ws_interval` seconds by accounting for elapsed time.
    """
    try:
        while ws_taxis_active_connections:
            # Record start time of this broadcast cycle
            start = time.monotonic()

            # Fetch the latest taxi data from Redis
            taxis = await fetch_all_taxis()

            # Sort taxis by taxi_id
            taxis_sorted = sorted(taxis, key=lambda taxi: taxi["taxi_id"])

            # Broadcast taxi data to each connected WebSocket client
            TAXI_BATCH_SIZE = 1000
            total_batches = (len(taxis_sorted) + TAXI_BATCH_SIZE - 1) // TAXI_BATCH_SIZE

            for ws in list(ws_taxis_active_connections):
                try:
                    for batch_num, i in enumerate(
                        range(0, len(taxis_sorted), TAXI_BATCH_SIZE), start=1
                    ):
                        batch = taxis_sorted[i : i + TAXI_BATCH_SIZE]
                        logger.info(
                            f"[taxis_data] Sending taxi batch {batch_num}/{total_batches} "
                            f"with {len(batch)} taxis to client {ws.client}."
                        )
                        await ws.send_json(
                            {
                                "taxis": batch,
                                "batch_num": batch_num,
                                "total_batches": total_batches,
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"[taxis_data] Failed to send data to client {ws.client}. Disconnecting. Error: {str(e)}"
                    )
                    await disconnect(ws, ws_taxis_active_connections)

            # Calculate elapsed time for this cycle
            elapsed = time.monotonic() - start
            logger.info(
                f"[taxis_data] Processing time for latest cycle: {elapsed:.3f} seconds"
            )
            # Sleep for the remaining interval duration, if any
            logger.info(
                f"[taxis_data] Sleeping time for latest cycle: {(ws_interval - elapsed):.3f} seconds"
            )
            ws_sleep_interval = ws_interval - elapsed
            if ws_sleep_interval > 0:
                await asyncio.sleep(max(0, ws_sleep_interval))

    except asyncio.CancelledError:
        logger.info("[taxis_data] Broadcasting task was cancelled.")


async def broadcast_incidents(ws_interval: int):
    """
    Continuously broadcast all incidents to connected WebSocket clients at a fixed interval.

    This function loops while there are active WebSocket connections, fetches the current
    state of all taxis, and sends that data to each connected client. The loop ensures
    that each broadcast cycle (including fetch and send time) occurs approximately every
    `ws_interval` seconds by accounting for elapsed time.
    """
    try:
        while ws_incidents_active_connections:
            # Record start time of this broadcast cycle
            start = time.monotonic()

            # Fetch the latest incident data from Redis
            incidents = await fetch_all_incidents()

            # Broadcast incident data to each connected WebSocket client
            for ws in list(ws_incidents_active_connections):
                try:
                    await ws.send_json(
                        {
                            "total_incidents": len(incidents),
                            "incidents": incidents,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"[violation_alerts] Failed to send data to client {ws.client}. Disconnecting. Error: {str(e)}"
                    )
                    # Gracefully disconnect clients that can't be reached
                    await disconnect(ws, ws_taxis_active_connections)

            # Calculate elapsed time for this cycle
            elapsed = time.monotonic() - start
            logger.info(
                f"[violation_alerts] Processing time for latest cycle: {elapsed:.3f} seconds"
            )
            # Sleep for the remaining interval duration, if any
            logger.info(
                f"[violation_alerts] Sleeping time for latest cycle: {(ws_interval - elapsed):.3f} seconds"
            )
            ws_sleep_interval = ws_interval - elapsed
            if ws_sleep_interval > 0:
                await asyncio.sleep(max(0, ws_sleep_interval))

    except asyncio.CancelledError:
        logger.info("[violation_alerts] Broadcasting task was cancelled.")


async def broadcast_taxi_fleet_metrics(ws_interval: int):
    """
    Continuously broadcast all incidents to connected WebSocket clients at a fixed interval.

    This function loops while there are active WebSocket connections, fetches the current
    state of all taxis, and sends that data to each connected client. The loop ensures
    that each broadcast cycle (including fetch and send time) occurs approximately every
    `ws_interval` seconds by accounting for elapsed time.
    """
    try:
        while ws_taxi_fleet_metrics_active_connections:
            # Record start time of this broadcast cycle
            start = time.monotonic()

            # Fetch the latest incident data from Redis
            taxi_fleet_metrics = await fetch_taxi_fleet_metrics()

            # Broadcast incident data to each connected WebSocket client
            for ws in list(ws_taxi_fleet_metrics_active_connections):
                try:
                    await ws.send_json(
                        {
                            "taxi_fleet_metrics": taxi_fleet_metrics,
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"[taxi_fleet_metrics] Failed to send data to client {ws.client}. Disconnecting. Error: {str(e)}"
                    )
                    # Gracefully disconnect clients that can't be reached
                    await disconnect(ws, ws_taxis_active_connections)

            # Calculate elapsed time for this cycle
            elapsed = time.monotonic() - start
            logger.info(
                f"[taxi_fleet_metrics] Processing time for latest cycle: {elapsed:.3f} seconds"
            )
            # Sleep for the remaining interval duration, if any
            logger.info(
                f"[taxi_fleet_metrics] Sleeping time for latest cycle: {(ws_interval - elapsed):.3f} seconds"
            )
            ws_sleep_interval = ws_interval - elapsed
            if ws_sleep_interval > 0:
                await asyncio.sleep(max(0, ws_sleep_interval))

    except asyncio.CancelledError:
        logger.info("[taxi_fleet_metrics] Broadcasting task was cancelled.")


async def disconnect(websocket: WebSocket, active_connections):
    """Remove disconnected client and close connection."""
    if websocket in active_connections:
        active_connections.remove(websocket)

        # Attempt to close the WebSocket only if it's still open
        try:
            await websocket.close()
        except Exception as e:
            logger.info(f"WebSocket already closed or error during close: {e}")

        logger.info(
            "Client disconnected. Active connections: %d", len(active_connections)
        )


@router.websocket("/ws/taxis")
async def websocket_get_taxis(
    websocket: WebSocket, ws_interval: int = Query(settings.ws_interval, ge=1, le=10)
):
    """WebSocket endpoint for clients to receive periodic taxi updates."""
    await websocket.accept()

    ws_taxis_active_connections.add(websocket)
    logger.info(
        "[taxis_data] WebSocket Client Connected. Active Connections: %d",
        len(ws_taxis_active_connections),
    )

    # Start broadcaster only once
    if len(ws_taxis_active_connections) == 1:
        broadcaster_taxis_task = asyncio.create_task(broadcast_taxis(ws_interval))
        logger.info("[taxis_data] Broadcasting task started.")

    try:
        while True:
            # Wait for keep connection alive pings from client, otherwise connection drops silently
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        logger.warning(
            f"[taxis_data] WebSocketDisconnect {str(e.code)}: Client disconnected with reason {str(e)}."
        )
        await disconnect(websocket, ws_taxis_active_connections)
    finally:
        # Cleanup: cancel broadcaster if no clients left
        if not ws_taxis_active_connections and "broadcaster_taxis_task" in locals():
            broadcaster_taxis_task.cancel()
            logger.info("[taxis_data] No clients. Broadcasting task cancelled.")


@router.websocket("/ws/incidents")
async def websocket_get_incidents(
    websocket: WebSocket, ws_interval: int = Query(settings.ws_interval, ge=1, le=10)
):
    """WebSocket endpoint for clients to receive periodic incident updates."""
    await websocket.accept()

    ws_incidents_active_connections.add(websocket)
    logger.info(
        "[violation_alerts] WebSocket Client Connected. Active Connections: %d",
        len(ws_incidents_active_connections),
    )

    # Start broadcaster only once
    if len(ws_incidents_active_connections) == 1:
        broadcaster_incidents_task = asyncio.create_task(
            broadcast_incidents(ws_interval)
        )
        logger.info("[violation_alerts] Broadcasting task started.")

    try:
        while True:
            # Wait for keep connection alive pings from client, otherwise connection drops silently
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        logger.warning(
            f"[violation_alerts] WebSocketDisconnect {str(e.code)}: Client disconnected with reason {str(e)}."
        )
        await disconnect(websocket, ws_incidents_active_connections)
    finally:
        # Cleanup: cancel broadcaster if no clients left
        if (
            not ws_incidents_active_connections
            and "broadcaster_incidents_task" in locals()
        ):
            broadcaster_incidents_task.cancel()
            logger.info("[violation_alerts] No clients. Broadcasting task cancelled.")


@router.websocket("/ws/taxi_fleet_metrics")
async def websocket_get_taxi_fleet_metrics(
    websocket: WebSocket, ws_interval: int = Query(settings.ws_interval, ge=1, le=10)
):
    """WebSocket endpoint for clients to receive periodic incident updates."""
    await websocket.accept()

    ws_taxi_fleet_metrics_active_connections.add(websocket)
    logger.info(
        "[taxi_fleet_metrics] WebSocket Client Connected. Active Connections: %d",
        len(ws_taxi_fleet_metrics_active_connections),
    )

    # Start broadcaster only once
    if len(ws_taxi_fleet_metrics_active_connections) == 1:
        broadcaster_taxi_fleet_metrics_task = asyncio.create_task(
            broadcast_taxi_fleet_metrics(ws_interval)
        )
        logger.info("[taxi_fleet_metrics] Broadcasting task started.")

    try:
        while True:
            # Wait for keep connection alive pings from client, otherwise connection drops silently
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        logger.warning(
            f"[taxi_fleet_metrics] WebSocketDisconnect {str(e.code)}: Client disconnected with reason {str(e)}."
        )
        await disconnect(websocket, ws_taxi_fleet_metrics_active_connections)
    finally:
        # Cleanup: cancel broadcaster if no clients left
        if (
            not ws_taxi_fleet_metrics_active_connections
            and "broadcaster_taxi_fleet_metrics_task" in locals()
        ):
            broadcaster_taxi_fleet_metrics_task.cancel()
            logger.info("[taxi_fleet_metrics] No clients. Broadcasting task cancelled.")
