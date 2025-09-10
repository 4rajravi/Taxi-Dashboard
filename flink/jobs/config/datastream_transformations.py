from pyflink.common import Types, Time  # type: ignore
from pyflink.datastream import OutputTag  # type: ignore
from pyflink.datastream.window import TumblingEventTimeWindows  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE

from operators.check_duplicate_timestamp import DeduplicateSameTimestampOperator
from operators.propagate_location import PropagateLocationOperator
from operators.calculate_speed import CalculateSpeedOperator
from operators.calculate_average_speed import CalculateAverageSpeedOperator
from operators.calculate_distance import CalculateDistanceOperator
from operators.geofence_violation_alert import (
    GeofenceViolationAlertOperator,
    geofence_alert_output_tag,
)
from operators.speed_violation_alert import SpeedViolationAlertOperator
from operators.fleet_metrics import FleetMetricsOperator

GEOFENCE_VIOLATION_TAG = OutputTag("geofence-violation", Types.STRING())


def deduplicate_same_timestamp(logger, datastream):
    """
    Removes duplicate taxi events that have the same timestamp for a given taxi_id.

    Args:
        logger: Logger instance for logging messages.
        datastream: DataStream of taxi events (should be keyed by 'taxi_id').

    Returns:
        DataStream: Stream with duplicate timestamp events filtered out.
    """
    try:
        logger.info("[!] Setting up DeduplicateSameTimestampOperator...")

        datastream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(
                DeduplicateSameTimestampOperator(),
                output_type=TAXI_RECORD_TYPE,
            )
            .name("DeduplicateSameTimestampOperator")
        )

        logger.info("[✔] Deduplication setup complete.")
        return datastream

    except Exception as e:
        logger.error(f"[✘] Failed to set up deduplication operator: {e}")
        raise e


def propagate_location(logger: None, datastream, window_interval: int = 5):
    """
    Propagates the last known location for each taxi at regular intervals.

    Args:
        logger: Logger object for logging messages.
        datastream (DataStream): The input datastream of raw taxi data.
        window_interval (int): Interval in seconds to emit the last known location.

    Returns:
        DataStream: The processed datastream with propagated location information.
    """
    try:
        logger.info("[!] Setting up PropagateLocationOperator...")

        datastream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(
                PropagateLocationOperator(emit_interval_ms=window_interval * 1000),
                output_type=TAXI_RECORD_TYPE,
            )
            .name("PropagateLocationOperator")
        )

        logger.info("[✔] PropagateLocationOperator setup complete.")
        return datastream

    except Exception as e:
        logger.error(f"[✘] Failed to setup PropagateLocationOperator: {e}")
        raise e


def calculate_speed(logger: None, datastream):
    """
    Apply speed calculation logic to each taxi's stream.
    Calculates the speed between successive GPS points for each taxi using state.

    Args:
        logger: Logger object for logging messages.
        datastream (DataStream): Input keyed stream of JSON taxi events.

    Returns:
        DataStream: Stream with added 'speed' and 'valid_speed' keys.
    """
    try:
        logger.info("[!] Setting up CalculateSpeedOperator...")

        datastream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(CalculateSpeedOperator(), output_type=TAXI_RECORD_TYPE)
            .name("CalculateSpeedOperator")
        )

        logger.info("[✔] CalculateSpeedOperator setup complete.")
        return datastream

    except Exception as e:
        logger.error(f"[✘] Failed to setup CalculateSpeedOperator: {e}")
        raise e


def calculate_average_speed(logger: None, datastream):
    """
    Calculate the average speed for each taxi over a defined trip window.
    Applies a stateful operator to track average speed per taxi.

    Args:
        logger: Logger object for logging messages.
        datastream (DataStream): Stream with per-taxi calculated speeds.

    Returns:
        DataStream: Stream with added 'average_speed' and potentially other summary stats.
    """
    try:
        logger.info("[!] Setting up CalculateAverageSpeedOperator...")

        datastream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(
                CalculateAverageSpeedOperator(),
                output_type=TAXI_RECORD_TYPE,
            )
            .name("CalculateAverageSpeedOperator")
        )

        logger.info("[✔] CalculateAverageSpeedOperator setup complete.")
        return datastream

    except Exception as e:
        logger.error(f"[✘] Failed to setup CalculateAverageSpeedOperator: {e}")
        raise e


def calculate_distance(logger: None, datastream):
    """
    Apply distance calculation logic to each taxi's stream.

    Calculates the cumulative Haversine distance between successive GPS points
    for each taxi using stateful processing. It accounts for edge cases like:
        - First coordinate in the stream
        - Invalid or missing coordinates
        - Same timestamp events (uses latest)
        - Speed = 0 (filtered upstream)
        - Trip end (clears state)

    Args:
        logger: Logger object for logging debug/error messages.
        datastream (DataStream): Input keyed stream of JSON taxi events.

    Returns:
        DataStream: Stream with added 'total_distance_km' key in each event.
    """
    try:
        logger.info("[!] Setting up CalculateDistanceOperator...")

        datastream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(
                CalculateDistanceOperator(),
                output_type=TAXI_RECORD_TYPE,
            )
            .name("CalculateDistanceOperator")
        )

        logger.info("[✔] CalculateDistanceOperator setup complete.")
        return datastream

    except Exception as e:
        logger.error(f"[✘] Failed to setup CalculateDistanceOperator: {e}")
        raise e


def geofence_violation_alert(
    logger: None,
    stream,
    forbidden_lat,
    forbidden_lon,
    warning_radius_km,
    discard_radius_km,
):
    """
    Applies geofencing logic to a keyed PyFlink data stream of taxi events.

    Logic:
        - Adds `distance_from_forbidden_city_km` and `in_range` flag to each record.
        - Emits a single warning alert to side output when a taxi first crosses into the warning ring.
        - All enriched events continue on the main stream.

    Args:
        logger: Logger instance for structured logging.
        stream: PyFlink DataStream of JSON taxi events.
        forbidden_lat: Latitude of the Forbidden City.
        forbidden_lon: Longitude of the Forbidden City.
        warning_radius_km: Warning radius (e.g., 10km).
        discard_radius_km: Discard radius (e.g., 15km).

    Returns:
        Tuple[DataStream, DataStream]: (main_enriched_stream, side_output_alert_stream)
    """
    try:
        logger.info("Initializing geofence violation alert transformation...")

        processed_stream = (
            stream.key_by(lambda row: row["taxi_id"])
            .process(
                GeofenceViolationAlertOperator(
                    forbidden_lat,
                    forbidden_lon,
                    warning_radius_km,
                    discard_radius_km,
                ),
                output_type=TAXI_RECORD_TYPE,
            )
            .name("GeofenceViolationAlertOperator")
        )

        side_output_stream = processed_stream.get_side_output(geofence_alert_output_tag)

        return processed_stream, side_output_stream

    except Exception as e:
        logger.error(f"Failed to apply geofence violation alert: {e}", exc_info=True)
        raise


def speed_violation_alert(logger: None, datastream, speedthreshold):
    """
    Detects speed violations in the stream and emits alerts when taxis exceed the speed threshold.

    Args:
        logger: Logger for diagnostics.
        datastream (DataStream): Input stream with 'speed' and 'valid_speed'.

    Returns:
        DataStream: Stream of JSON alert messages.
    """
    try:
        logger.info("[!] Setting up SpeedViolationAlertOperator...")

        alert_stream = (
            datastream.key_by(lambda row: row["taxi_id"])
            .process(
                SpeedViolationAlertOperator(speedthreshold),
                output_type=Types.STRING(),
            )
            .name("SpeedViolationAlertOperator")
        )

        logger.info("[✔] SpeedViolationAlertOperator setup complete.")
        return alert_stream

    except Exception as e:
        logger.error(f"[✘] Failed to setup SpeedViolationAlertOperator: {e}")
        raise e


def fleet_metrics(logger: None, datastream):
    """
    Aggregates fleet-level metrics (active, inactive, ended trips, total distance)
    and calculates percentage change from the last window.


    Emits a JSON string every window with current counts and % changes.


    Args:
        logger: Logger instance
        datastream: DataStream of enriched taxi JSON records


    Returns:
        DataStream: Stream of fleet metric JSON strings
    """
    try:
        logger.info("[!] Setting up DistanceAccumulator...")

        result_stream = datastream.process(
            FleetMetricsOperator(),
            output_type=Types.STRING(),
        ).name("FleetMetricsOperator")

        logger.info("[✔] FleetMetricsOperator setup complete.")
        return result_stream

    except Exception as e:
        logger.error(f"[✘] Failed to setup FleetMetricsOperator: {e}")
        raise e


# def trip_status_manager(
#     logger: None, datastream, inactivity_timeout_in_ms: int = 180_000
# ):
#     """
#     Process the keyed raw taxi datastream to manage trip status updates
#     (e.g., handling active/inactive taxi state based on location activity).

#     Args:
#         logger: Logger object for logging messages.
#         datastream (DataStream): The input stream of raw taxi data as JSON strings.

#     Returns:
#         DataStream: The processed datastream with trip status updates for each taxi.
#     """
#     # Key the datastream by taxi_id and apply stateful operator to manage trip state
#     try:
#         logger.info("[!] Setting up TripStatusManagerOperator...")
#         inactivity_timeout_in_ms = inactivity_timeout_in_ms

#         datastream = (
#             datastream.key_by(lambda row: row["taxi_id"])
#             .process(
#                 TripStatusManagerOperator(inactivity_timeout_in_ms),
#                 output_type=TAXI_RECORD_TYPE,
#             )
#             .name("TripStatusManagerOperator")
#         )

#         logger.info("[✔] TripStatusManagerOperator setup complete.")
#         return datastream

#     except Exception as e:
#         logger.error(f"[✘] Failed to setup TripStatusManagerOperator: {e}")
#         raise e
