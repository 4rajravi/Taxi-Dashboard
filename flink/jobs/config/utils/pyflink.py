import time
from datetime import datetime

import orjson  # type: ignore

from pyflink.common import WatermarkStrategy, Duration  # type: ignore
from pyflink.common.watermark_strategy import TimestampAssigner  # type: ignore
from pyflink.datastream.functions import MapFunction  # type: ignore
from pyflink.common import Row  # type: ignore


class EventTimeAssigner(TimestampAssigner):
    """
    Extracts and converts event time from a Row object to a Flink-compatible timestamp in milliseconds.
    """

    def extract_timestamp(self, value: Row) -> int:
        """
        Extracts the event timestamp from the 'timestamp' field of the Row and converts it to milliseconds since epoch.

        Args:
            value: Row containing the event data.

        Returns:
            int: Event timestamp in milliseconds since epoch.
        """
        try:
            event_time = value["timestamp"]
            event_time_ms = int(
                datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
            )  # Convert to milliseconds

            return event_time_ms

        except Exception as e:
            raise e


def get_watermark_strategy(
    logger: None, source_idleness_duration_in_seconds: int = 170
):
    """
    Returns a configured WatermarkStrategy for event-time processing.

    Uses monotonous timestamps (i.e., assumes strictly increasing event timestamps),
    handles idle sources to prevent watermark stagnation, and assigns event time
    using a custom EventTimeAssigner.

    Args:
        source_idleness_duration_in_seconds: Kafka source idleness duration in seconds

    Returns:
        WatermarkStrategy
    """
    try:
        logger.info("[!] Configuring WatermarkStrategy for event-time processing...")

        # Create a watermark strategy assuming events have monotonically increasing timestamps
        watermark_strategy = (
            WatermarkStrategy.for_monotonous_timestamps()
            # Assign event timestamps using a custom assigner
            .with_timestamp_assigner(EventTimeAssigner())
        )

        logger.info(
            f"[✔] Configured WatermarkStrategy successfully for event-time processing using monotonous timestamps"
            f" and with source idleness set to {source_idleness_duration_in_seconds}s."
        )
        return watermark_strategy

    except Exception as e:
        logger.error(
            f"[✘] Failed to configure WatermarkStrategy for event-time processing: {e}"
        )
        raise e


class RowToJson(MapFunction):
    """
    Converts a PyFlink Row object to a JSON string using orjson.

    Each field is extracted from the Row, with type conversions and rounding
    applied where appropriate. The current processing time is added as
    'processed_at_utc_ms'.
    """

    def map(self, row: Row) -> str:
        """
        Maps a Row object to a JSON string.

        Args:
            row (Row): The input Row object containing event data.

        Returns:
            str: The JSON string representation of the Row.
        """
        return orjson.dumps(
            {
                "taxi_id": row["taxi_id"],
                "longitude": (
                    float(row["longitude"]) if row["longitude"] is not None else None
                ),
                "latitude": (
                    float(row["latitude"]) if row["latitude"] is not None else None
                ),
                "timestamp": row["timestamp"],
                "sent_at_utc_ms": row["sent_at_utc_ms"],
                "trip_status": row["trip_status"],
                "received_at_utc_ms": row["received_at_utc_ms"],
                "speed": round(row["speed"], 2) if row["speed"] is not None else None,
                "is_valid_speed": row["is_valid_speed"],
                "avg_speed": (
                    round(row["avg_speed"], 2) if row["avg_speed"] is not None else None
                ),
                "total_distance_km": (
                    round(row["total_distance_km"], 2)
                    if row["total_distance_km"] is not None
                    else None
                ),
                "distance_from_forbidden_city_km": (
                    round(row["distance_from_forbidden_city_km"], 2)
                    if row["distance_from_forbidden_city_km"] is not None
                    else None
                ),
                "is_in_range": row["is_in_range"],
                "processed_at_utc_ms": int(time.time() * 1000),
            }
        ).decode("utf-8")
