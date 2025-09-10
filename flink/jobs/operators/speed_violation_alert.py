import orjson  # type: ignore

from pyflink.common import Types  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore


class SpeedViolationAlertOperator(KeyedProcessFunction):
    """
    Emits an alert to the dashboard whenever a taxi crosses a speed threshold (50 km/h).
    Allows multiple alerts within a trip if speed goes below threshold and then above again.
    Also emits alert on trip end if condition met, then clears state.
    """

    def __init__(self, speedthreshold):
        self.speed_limit_kmph = speedthreshold

    def open(self, ctx):
        self.has_alerted_state = ctx.get_state(
            ValueStateDescriptor("has_alerted", Types.BOOLEAN())
        )

    def process_element(self, value, ctx):
        try:
            speed = value["speed"]
            is_valid_speed = (
                value["is_valid_speed"] if value["is_valid_speed"] is not None else True
            )
            trip_status = value["trip_status"]

            if speed is None or not is_valid_speed:
                return

            has_alerted = self.has_alerted_state.value()

            # Check for speed violation (for both active and end)
            if speed > self.speed_limit_kmph:
                if not has_alerted:
                    self.has_alerted_state.update(True)
                    alert = {
                        "taxi_id": value["taxi_id"],
                        "timestamp": value["timestamp"],
                        "latitude": value["latitude"],
                        "longitude": value["longitude"],
                        "trip_status": trip_status,
                        "speed": round(speed, 2),
                        "alert_type": "SPEED_VIOLATION",
                    }
                    yield orjson.dumps(alert).decode("utf-8")
            else:
                # Reset state if taxi slows down
                if has_alerted:
                    self.has_alerted_state.update(False)

            # Always clear state if trip ended (after processing)
            if trip_status == "end":
                self.has_alerted_state.clear()

        except Exception as e:
            raise
