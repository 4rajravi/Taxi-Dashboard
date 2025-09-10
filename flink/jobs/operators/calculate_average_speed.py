from pyflink.common import Types  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE
from operators.utils import update_row_fields


class CalculateAverageSpeedOperator(KeyedProcessFunction):
    """
    Flink stateful operator to compute the average speed for each taxi based on
    valid speed records. Maintains per-key (e.g., per-taxi) total speed, count,
    and last computed average to handle incomplete or irregular data streams.

    Emits enriched records with an 'avg_speed' field at each step.
    Clears state when a trip ends.
    """

    def open(self, ctx):
        """
        Initializes Flink value states:
        - total_speed_state: Sum of all valid speed values seen.
        - count_state: Number of valid speed measurements.
        - last_avg_state: Most recent computed average speed.
        """
        self.total_speed_state = ctx.get_state(
            ValueStateDescriptor("total_speed", Types.FLOAT())
        )
        self.count_state = ctx.get_state(
            ValueStateDescriptor("speed_count", Types.LONG())
        )
        self.last_avg_state = ctx.get_state(
            ValueStateDescriptor("last_avg_speed", Types.FLOAT())
        )

    def process_element(self, value, ctx):
        """
        Processes each incoming record to update speed stats and emit enriched data.

        - If the speed is invalid or missing, emits the last known average if trip ends.
        - For valid speed records with trip status 'active' or 'end', updates state,
          computes new average, and emits enriched output.
        - For 'inactive' trips or other cases, emits last known average.
        - Clears state on trip end.
        """
        try:
            trip_status = value["trip_status"]
            is_valid_speed = (
                value["is_valid_speed"] if value["is_valid_speed"] is not None else True
            )
            speed = value["speed"]

            # If speed is invalid or missing, only act if trip ends
            if not is_valid_speed or speed is None:
                if trip_status == "end":
                    last_avg = self.last_avg_state.value()

                    # Emit final record with last known average speed
                    enriched_row = update_row_fields(
                        row=value,
                        updates={
                            "avg_speed": (
                                round(last_avg, 2) if last_avg is not None else 0.0
                            ),
                        },
                        schema=TAXI_RECORD_TYPE,
                    )

                    yield enriched_row

                    # Clear all speed-related state
                    self.total_speed_state.clear()
                    self.count_state.clear()
                    self.last_avg_state.clear()
                return

            # Retrieve current state values or initialize
            total_speed = self.total_speed_state.value() or 0.0
            count = self.count_state.value() or 0

            if trip_status in ("active", "end"):
                # Update total speed and count with current record
                total_speed += speed
                count += 1

                self.total_speed_state.update(total_speed)
                self.count_state.update(count)

                # Compute new average speed
                avg_speed = total_speed / count if count > 0 else 0.0

                # Emit enriched record with updated average
                enriched_row = update_row_fields(
                    row=value,
                    updates={"avg_speed": round(avg_speed, 2)},
                    schema=TAXI_RECORD_TYPE,
                )

                # Save new average in state
                self.last_avg_state.update(avg_speed)

                yield enriched_row

                # Clear states if the trip has ended
                if trip_status == "end":
                    self.total_speed_state.clear()
                    self.count_state.clear()
                    self.last_avg_state.clear()

            else:  # For 'inactive' or unrecognized trip status
                last_avg = self.last_avg_state.value()

                # Emit record with the last known average speed
                enriched_row = update_row_fields(
                    row=value,
                    updates={
                        "avg_speed": (
                            round(last_avg, 2) if last_avg is not None else 0.0
                        ),
                    },
                    schema=TAXI_RECORD_TYPE,
                )

                yield enriched_row

        except Exception as e:
            # Forward exception for external handling/logging
            raise
