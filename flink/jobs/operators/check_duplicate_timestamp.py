from pyflink.common import Types  # type: ignore
from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
from pyflink.datastream.state import ValueStateDescriptor  # type: ignore


class DeduplicateSameTimestampOperator(KeyedProcessFunction):
    """
    Flink stateful operator to deduplicate events with the same taxi_id and timestamp.

    Emits only the latest event for a given timestamp per taxi_id.
    - If an event has the same timestamp as the last seen one and is 'active', it is skipped.
    - If the trip_status is 'end', the state is cleared to reset tracking.

    Assumes the stream is keyed by 'taxi_id'.
    """

    def open(self, ctx):
        """
        Initializes Flink managed state to store the last seen timestamp
        for each taxi_id (key).
        """
        # ValueState to track the last timestamp seen for the current key (taxi_id)
        self.last_timestamp_state = ctx.get_state(
            ValueStateDescriptor("last_timestamp", Types.STRING())
        )

    def process_element(self, value, ctx):
        """
        Processes each incoming event:
        - Skips duplicates if the timestamp is the same as the last one seen for that taxi_id.
        - Emits the event if it is new (i.e., a different timestamp).
        - Clears state when trip ends.
        """
        try:
            current_ts = value["timestamp"]

            # Skip record if timestamp is missing
            if current_ts is None:
                return

            # If the trip ends, yield immediately and clear the state
            if value["trip_status"] == "end":
                yield value
                self.last_timestamp_state.clear()
                return

            # Retrieve last seen timestamp from state
            last_ts = self.last_timestamp_state.value()

            # Suppress duplicate if timestamp is the same and trip is still active
            if last_ts == current_ts and value["trip_status"] == "active":
                return

            # Emit current record and update state
            self.last_timestamp_state.update(current_ts)
            yield value

        except Exception as e:
            # Raise exception to allow external error handling or logging
            raise
