from datetime import datetime

from pyflink.common import Types, Row  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE
from operators.utils import haversine, update_row_fields

# Type for storing the last known GPS location and timestamp (in milliseconds)
LAST_LOCATION_TYPE = Types.ROW_NAMED(
    ["latitude", "longitude", "timestamp"],
    [Types.STRING(), Types.STRING(), Types.LONG()],
)


class CalculateSpeedOperator(KeyedProcessFunction):
    """
    Flink stateful operator that calculates the speed (in km/h) between two GPS coordinates.

    - Speed is computed only when a valid previous location and timestamp exist.
    - If the speed exceeds a given threshold (default 300 km/h), it is marked as invalid.
    - When time difference is zero, the last valid speed is reused for "inactive" trips.
    - Adds 'speed' and 'is_valid_speed' fields to each record.
    - Clears state at the end of a trip.
    """

    def __init__(self, speed_threshold_kmph=300):
        """
        Initializes the operator with a speed threshold in km/h.
        Any speed above this threshold is considered invalid.
        """
        self.speed_threshold_kmph = speed_threshold_kmph

    def open(self, ctx):
        """
        Initializes Flink managed state:
        - last_location_state: Stores the most recent GPS point and timestamp.
        - last_valid_speed_state: Caches the most recent valid speed value.
        """
        self.last_location_state = ctx.get_state(
            ValueStateDescriptor("last_location", LAST_LOCATION_TYPE)
        )
        self.last_valid_speed_state = ctx.get_state(
            ValueStateDescriptor("last_valid_speed", Types.FLOAT())
        )

    def process_element(self, value, ctx):
        """
        Processes each incoming taxi record:
        - Parses timestamp and validates input fields.
        - Calculates speed using the Haversine distance between last and current location.
        - If speed exceeds threshold or time diff is zero, it is marked invalid.
        - Emits enriched row with calculated speed and validity.
        - Clears state at the end of the trip.
        """
        try:
            # Extract current coordinates and timestamp string
            current_lat = value["latitude"]
            current_lon = value["longitude"]
            timestamp_str = value["timestamp"]
            trip_status = value["trip_status"]

            # Skip if timestamp is missing
            if not timestamp_str:
                return

            try:
                # Parse string timestamp to datetime and convert to milliseconds
                current_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                current_ts = int(current_dt.timestamp() * 1000)  # ms
            except ValueError as ve:
                return  # Skip record if timestamp is invalid

            # Skip if coordinates or timestamp are invalid
            if None in (current_lat, current_lon, current_ts):
                return

            # Retrieve last known location from state
            last_loc = self.last_location_state.value()
            speed_kmph = 0.0
            is_valid_speed = True

            if last_loc:
                last_lat = last_loc["latitude"]
                last_lon = last_loc["longitude"]
                last_ts = last_loc["timestamp"]

                if None not in (last_lat, last_lon, last_ts):
                    # Compute Haversine distance and time difference in hours
                    distance_km = haversine(
                        float(current_lat),
                        float(current_lon),
                        float(last_lat),
                        float(last_lon),
                    )
                    time_diff_hours = (
                        current_ts - last_ts
                    ) / 3_600_000.0  # convert ms to hours

                    if time_diff_hours > 0:
                        speed_kmph = distance_km / time_diff_hours

                        # Normalize very low speeds to 0
                        if speed_kmph < 0.1:
                            speed_kmph = 0.0

                        # Invalidate speeds that exceed realistic threshold
                        if speed_kmph > self.speed_threshold_kmph:
                            is_valid_speed = False
                            speed_kmph = 0.0
                        else:
                            self.last_valid_speed_state.update(speed_kmph)
                    else:
                        # If no time has passed, fall back to last valid speed for inactive trips
                        if trip_status == "inactive":
                            last_speed = self.last_valid_speed_state.value()
                            if last_speed is not None:
                                speed_kmph = last_speed
                                is_valid_speed = True
                            else:
                                speed_kmph = 0.0
                                is_valid_speed = False
                        else:
                            is_valid_speed = False

            # Enrich the input row with calculated speed and validity flag
            enriched_row = update_row_fields(
                row=value,
                updates={
                    "speed": round(speed_kmph, 2),
                    "is_valid_speed": is_valid_speed,
                },
                schema=TAXI_RECORD_TYPE,
            )

            # Update the last known location state
            self.last_location_state.update(
                Row(latitude=current_lat, longitude=current_lon, timestamp=current_ts)
            )

            # Update the last valid speed if the current one is valid
            if is_valid_speed:
                self.last_valid_speed_state.update(speed_kmph)

            # Emit the enriched record
            yield enriched_row

            # Clear state on trip end
            if trip_status == "end":
                self.last_location_state.clear()
                self.last_valid_speed_state.clear()

        except Exception as e:
            # Raise exception to allow external logging or failure handling
            raise e
