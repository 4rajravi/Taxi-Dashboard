import orjson  # type: ignore

from pyflink.common import Types  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction, RuntimeContext  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore
from pyflink.datastream import OutputTag  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE

from operators.utils import haversine, update_row_fields

# Side‑output tag for geofence alerts
geofence_alert_output_tag = OutputTag("geofence-alerts", Types.STRING())


class GeofenceViolationAlertOperator(KeyedProcessFunction):
    """
    Emits `is_in_range` flag on the main stream.
    Emits a side-output alert when a taxi with is_valid_speed is True crosses into the warning ring,
    re-arming the alert if the taxi returns inside the safe zone.
    """

    def __init__(
        self,
        forbidden_city_lat: float,
        forbidden_city_lon: float,
        warning_radius_km: float,
        discard_radius_km: float,
    ):
        self.forbidden_city_lat = forbidden_city_lat
        self.forbidden_city_lon = forbidden_city_lon
        self.warning_radius_km = warning_radius_km
        self.discard_radius_km = discard_radius_km

    def open(self, ctx: RuntimeContext):
        # Boolean flag state: whether we've already warned since last safe‑zone entry
        self.has_warned = ctx.get_state(
            ValueStateDescriptor("has_warned", Types.BOOLEAN())
        )

    def process_element(self, value, ctx):
        """
        value: JSON string of taxi event containing at least
               { "taxi_id", "latitude", "longitude", "timestamp", "trip_status", "is_valid_speed", ... }
        Yields:
          - json-serialized record to main stream
          - (geofence_alert_output_tag, json-serialized alert) to side output when needed
        """
        taxi_id = value["taxi_id"]
        lat = value["latitude"]
        lon = value["longitude"]
        is_valid_speed = (
            value["is_valid_speed"] if value["is_valid_speed"] is not None else True
        )

        # Always emit the record, even if coords are missing or speed invalid
        if lat is None or lon is None:
            return

        # Compute distance from forbidden city
        distance_km = haversine(
            float(lat), float(lon), self.forbidden_city_lat, self.forbidden_city_lon
        )
        warned = self.has_warned.value() or False

        # Re‑arm alert if returned inside safe zone
        if distance_km <= self.warning_radius_km and warned:
            self.has_warned.update(False)

        # Enrich record for main stream
        enriched_row = update_row_fields(
            row=value,
            updates={
                "distance_from_forbidden_city_km": round(distance_km, 2),
                "is_in_range": distance_km <= self.discard_radius_km,
            },
            schema=TAXI_RECORD_TYPE,
        )

        # Emit enriched record
        yield enriched_row

        # Side‑output alert only if:
        #    - taxi is between warning and discard radius
        #    - has not yet been warned
        #    - AND is_valid_speed == True
        if (
            self.warning_radius_km < distance_km <= self.discard_radius_km
            and not warned
            and is_valid_speed is True
        ):
            alert = {
                "taxi_id": taxi_id,
                "latitude": float(lat),
                "longitude": float(lon),
                "timestamp": value["timestamp"],
                "trip_status": value["trip_status"],
                "distance_km": round(distance_km, 2),
                "alert_type": "GEOFENCE_VIOLATION",
            }
            yield geofence_alert_output_tag, orjson.dumps(alert).decode("utf-8")
            self.has_warned.update(True)

        # --- Trip-end resets state ---
        if value["trip_status"] == "end":
            self.has_warned.clear()
