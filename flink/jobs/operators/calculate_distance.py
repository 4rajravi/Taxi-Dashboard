from pyflink.common import Types, Row  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE
from operators.utils import haversine, update_row_fields

# State type to store the last known location and timestamp
LAST_LOCATION_TYPE = Types.ROW_NAMED(
    ["latitude", "longitude", "timestamp"],
    [Types.STRING(), Types.STRING(), Types.STRING()],
)


class CalculateDistanceOperator(KeyedProcessFunction):
    """
    Flink stateful operator to calculate the cumulative distance travelled by each taxi
    based on GPS coordinates (latitude and longitude) using the Haversine formula.

    - Updates state only for valid speed records.
    - Emits enriched records with 'total_distance_km'.
    - Clears state when a trip ends.
    """

    def open(self, ctx):
        """
        Initializes Flink managed state:
        - last_location_state: Stores the most recent valid location and timestamp.
        - total_distance_state: Stores the running total distance travelled (in kilometers).
        """
        self.last_location_state = ctx.get_state(
            ValueStateDescriptor("last_location", LAST_LOCATION_TYPE)
        )
        self.total_distance_state = ctx.get_state(
            ValueStateDescriptor("total_distance", Types.FLOAT())
        )

    def process_element(self, value, ctx):
        """
        Processes each incoming taxi record:
        - Skips processing if required fields are missing or speed is invalid.
        - Computes the distance from the previous valid location using the Haversine formula.
        - Updates states accordingly.
        - Emits the record with an updated 'total_distance_km' field.
        - Clears states if trip ends.
        """
        try:
            # Extract required fields from the input record
            lat = value["latitude"]
            lon = value["longitude"]
            ts = value["timestamp"]
            trip_status = value["trip_status"]
            is_valid_speed = (
                value["is_valid_speed"] if value["is_valid_speed"] is not None else True
            )

            # Skip processing if GPS or timestamp fields are missing
            if None in (lat, lon, ts):
                return

            # Skip if the record's speed is invalid
            if is_valid_speed is False:
                return

            # Retrieve previous location and total distance from state
            last_loc = self.last_location_state.value()
            total_distance = self.total_distance_state.value() or 0.0

            if last_loc:
                last_lat = last_loc["latitude"]
                last_lon = last_loc["longitude"]

                # Compute distance if previous location was valid
                if None not in (last_lat, last_lon):
                    distance = haversine(
                        float(lat), float(lon), float(last_lat), float(last_lon)
                    )
                    total_distance += distance
                    self.total_distance_state.update(total_distance)

            # Update the last known location in state
            self.last_location_state.update(
                Row(latitude=lat, longitude=lon, timestamp=ts)
            )

            # Add cumulative distance to the output record
            enriched_row = update_row_fields(
                row=value,
                updates={
                    "total_distance_km": round(total_distance, 3),
                },
                schema=TAXI_RECORD_TYPE,
            )

            yield enriched_row

            # Clear state if the trip has ended
            if trip_status == "end":
                self.last_location_state.clear()
                self.total_distance_state.clear()

        except Exception as e:
            # Reraise exception to allow external handling/logging
            raise
