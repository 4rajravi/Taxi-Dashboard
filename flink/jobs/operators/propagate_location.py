from datetime import datetime

from pyflink.common import Types  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore

from config.flink_datastream import TAXI_RECORD_TYPE


class PropagateLocationOperator(KeyedProcessFunction):
    """
    Use record timestamps for emission timing - most efficient approach.
    """

    def __init__(self, emit_interval_ms: int = 5000):
        self.emit_interval_ms = emit_interval_ms

    def open(self, runtime_context):
        # Initialize state descriptors for latest location and last emit record time
        self.latest_location_state = runtime_context.get_state(
            ValueStateDescriptor("latest_location", TAXI_RECORD_TYPE)
        )
        self.last_emit_record_time_state = runtime_context.get_state(
            ValueStateDescriptor("last_emit_record_time", Types.LONG())
        )

    def process_element(self, value, ctx):
        """
        Process each element and emit based on the record's timestamp.

        Args:
            value: The input record.
            ctx: The context for accessing time and state.
        """
        # Extract timestamp from the record or use Kafka timestamp
        record_timestamp = value["timestamp"]
        if not record_timestamp:
            return

        # Convert timestamp to milliseconds
        current_record_timestamp_ms = int(
            datetime.strptime(record_timestamp, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
        )

        last_emit_record_time_ms = self.last_emit_record_time_state.value() or 0

        # Update the latest location state
        self.latest_location_state.update(value)

        # Handle trip end scenario
        if value["trip_status"] == "end":
            yield value
            self._clear_all_state()
            return

        # Calculate the time difference since the last emitted record
        time_diff = current_record_timestamp_ms - last_emit_record_time_ms

        # Check if the emit interval has passed or if this is the first record
        emit_record = (
            time_diff >= self.emit_interval_ms or last_emit_record_time_ms == 0
        )

        if emit_record:
            yield value
            self.last_emit_record_time_state.update(current_record_timestamp_ms)

    def _clear_all_state(self):
        """
        Clear all state variables.
        """
        self.latest_location_state.clear()
        self.last_emit_record_time_state.clear()
