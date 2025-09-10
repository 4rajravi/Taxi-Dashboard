# from pyflink.common import Types, Row  # type: ignore
# from pyflink.datastream.functions import KeyedProcessFunction  # type: ignore
# from pyflink.datastream.state import ValueStateDescriptor  # type: ignore

# from config.flink_datastream import TAXI_RECORD_TYPE
# from operators.utils import update_row_fields


# class TripStatusManagerOperator(KeyedProcessFunction):
#     """
#     A Flink operator that marks taxi trips as 'inactive' if no updates arrive
#     within a configured inactivity timeout.
#     """

#     def __init__(self, inactivity_timeout_in_ms: int = 180_000):
#         """
#         Initialize the operator with a custom inactivity timeout.

#         Args:
#             inactivity_timeout_in_ms: Time in milliseconds after which a trip is considered inactive. (default: 180000ms)
#         """
#         self.inactivity_timeout_in_ms = inactivity_timeout_in_ms

#     def open(self, ctx):
#         """
#         Initialize all keyed state descriptors for this operator.

#         Set up Flink keyed state used to track latest event, timer, and trip activity.

#         Args:
#             ctx: KeyedProcessFunction runtime context, used to access Flink state.
#         """
#         # State to hold the most recent location or trip event for the taxi.
#         self.latest_state = ctx.get_state(
#             ValueStateDescriptor("latest_state", TAXI_RECORD_TYPE)
#         )
#         # State to track the next event-time timestamp when an inactivity timer should fire.
#         self.inactive_timer = ctx.get_state(
#             ValueStateDescriptor("inactive_timer", Types.LONG())
#         )
#         # State flag indicating whether the trip is still active
#         self.trip_is_active = ctx.get_state(
#             ValueStateDescriptor("trip_is_active", Types.BOOLEAN())
#         )

#     def process_element(self, value, ctx):
#         """
#         Processes each incoming taxi event and schedules an inactivity timeout.

#         If the trip has ended, the state is cleared. Otherwise, an event-time
#         timer is set for inactivity detection.

#         Args:
#             value: Incoming JSON-encoded taxi event.
#             ctx: Flink context providing timer and state access.

#         Yields:
#             str: A JSON string that holds the original value, unless the trip has ended (in which case it yields and clears).
#         """
#         self.latest_state.update(value)

#         # Initialize trip activity state if unset
#         if self.trip_is_active.value() is None:
#             self.trip_is_active.update(True)

#         # End of trip, emit once and clean up state
#         if value["trip_status"] == "end":
#             self.clear_state()
#             return

#         # Register new inactivity timer based on the event timestamp
#         timeout_ts = ctx.timestamp() + self.inactivity_timeout_in_ms
#         self.inactive_timer.update(timeout_ts)
#         ctx.timer_service().register_event_time_timer(timeout_ts)

#     def on_timer(self, timestamp, ctx):
#         """
#         Called when the registered inactivity timer fires.

#         Marks the taxi trip as 'inactive' if no new updates were received
#         before the timeout.

#         Args:
#             timestamp: Timestamp that triggered the timer.
#             ctx: Flink timer context.

#         Yields:
#             str: A modified JSON string record with 'trip_status' set to 'inactive'.
#         """
#         # Check if the current timer event matches the stored inactivity timer
#         if self.inactive_timer.value() == timestamp:
#             # Retrieve the latest record for this key (taxi ID)
#             latest_record = self.latest_state.value()
#             if latest_record:
#                 # fields = {name: latest_record[name] for name in get_taxi_record_field_names()}
#                 # updated_row = Row(
#                 #     **fields,
#                 #     trip_status="inactive",
#                 # )
#                 updated_row = update_row_fields(
#                     row=latest_record,
#                     updates={
#                         "trip_status": "inactive",
#                     },
#                     schema=TAXI_RECORD_TYPE,
#                 )
#                 yield updated_row
#             # Clear all associated state as the trip is now considered inactive
#             self.clear_state()

#     def clear_state(self):
#         """
#         Clears all state for this key (taxi) after trip ends.
#         """
#         self.latest_state.clear()
#         self.inactive_timer.clear()
#         self.trip_is_active.clear()
