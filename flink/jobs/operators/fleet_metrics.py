from datetime import datetime, timedelta

import orjson  # type: ignore

from pyflink.datastream import ProcessFunction  # type: ignore


class FleetMetricsOperator(ProcessFunction):
    """
    Tracks and computes various fleet-level metrics for a fleet of taxis in real-time.

    It maintains sets of taxi IDs representing different statuses (active, ended, in-transit, in-range)
    and a list for per-taxi distances. Every 5 seconds, it computes the percent change in these metrics
    compared to the last interval, and emits a JSON-encoded summary.

    Metrics Tracked:
    - Active taxis: currently in an active trip.
    - Ended taxis: have completed their trips.
    - In-transit taxis: actively moving (speed > 0.1).
    - In-range taxis: currently within a monitored geographical area.
    - Cumulative distance: total distance covered by all taxis.
    """

    def open(self, runtime_context):
        """
        Initializes all sets and baseline snapshots for metric tracking.
        """
        # List to store total distance for each taxi by taxi_id - 1
        self.distance_list = [0] * 10357  # Max 10357 taxis

        # Sets to track current states
        self.active_taxis_set = set()
        self.ended_taxis_set = set()
        self.in_transit_taxis_set = set()
        # self.in_range_taxis_set = set()

        self.baseline_time = None  # Time of last snapshot update

        # Snapshot copies for percent change calculation every 5 seconds
        self.baseline_active_taxis = set()
        self.baseline_ended_taxis = set()
        self.baseline_cumulative_distance = 0.0
        self.baseline_in_transit_taxis = set()
        # self.baseline_in_range_taxis = set()

        # Percent change values
        self.change_in_active_taxi = 0.0
        self.change_in_ended_taxi = 0.0
        self.change_in_cumulative_distance = 0.0
        self.change_in_in_transit_taxi = 0.0
        # self.change_in_in_range_taxi = 0.0

    @staticmethod
    def safe_percent_change(current, previous):
        """
        Safely compute percent change, returning 0 if previous value is zero.
        """
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 2)

    def process_element(self, value, ctx):
        """
        Processes each event and updates metrics:
        - Updates sets based on `trip_status`, and `speed`.
        - Updates total distance per taxi.
        - Every 5 seconds, computes percent change in metrics.
        - Emits a JSON-encoded dictionary of current metrics and changes.
        """
        taxi_id = value["taxi_id"]
        trip_status = value["trip_status"]
        event_time_str = value["timestamp"]
        speed = float(value["speed"]) if value["speed"] is not None else 0.0
        distance = (
            float(value["total_distance_km"])
            if value["total_distance_km"] is not None
            else 0.0
        )
        # in_range = value["is_in_range"] if value["is_in_range"] is not None else True

        # Convert string timestamp to datetime object
        try:
            current_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Invalid timestamp format: {event_time_str}")
            return

        # Track active/ended/in-transit status based on trip_status and speed
        if trip_status == "active":
            self.active_taxis_set.add(taxi_id)
            self.ended_taxis_set.discard(taxi_id)
            if speed > 0.1:
                self.in_transit_taxis_set.add(taxi_id)
            else:
                self.in_transit_taxis_set.discard(taxi_id)

        elif trip_status == "end":
            self.ended_taxis_set.add(taxi_id)
            self.active_taxis_set.discard(taxi_id)
            self.in_transit_taxis_set.discard(taxi_id)

        # Update per-taxi distance in list
        self.distance_list[taxi_id - 1] = distance
        total_distance = sum(self.distance_list)

        # # Track in-range taxis
        # if in_range:
        #     self.in_range_taxis_set.add(taxi_id)
        # else:
        #     self.in_range_taxis_set.discard(taxi_id)

        # Initialize snapshot time if not yet set
        if not self.baseline_time:
            self.baseline_time = current_time

        # Every 5 seconds, compute percent changes and update baseline
        if current_time - self.baseline_time >= timedelta(seconds=5):
            self.change_in_active_taxi = FleetMetricsOperator.safe_percent_change(
                len(self.active_taxis_set), len(self.baseline_active_taxis)
            )
            self.change_in_ended_taxi = FleetMetricsOperator.safe_percent_change(
                len(self.ended_taxis_set), len(self.baseline_ended_taxis)
            )
            self.change_in_cumulative_distance = (
                FleetMetricsOperator.safe_percent_change(
                    total_distance, self.baseline_cumulative_distance
                )
            )
            self.change_in_in_transit_taxi = FleetMetricsOperator.safe_percent_change(
                len(self.in_transit_taxis_set), len(self.baseline_in_transit_taxis)
            )
            # self.change_in_in_range_taxi = FleetMetricsOperator.safe_percent_change(
            #     len(self.in_range_taxis_set), len(self.baseline_in_range_taxis)
            # )

            # Update baseline snapshots
            self.baseline_active_taxis = self.active_taxis_set.copy()
            self.baseline_ended_taxis = self.ended_taxis_set.copy()
            self.baseline_cumulative_distance = total_distance
            self.baseline_in_transit_taxis = self.in_transit_taxis_set.copy()
            # self.baseline_in_range_taxis = self.in_range_taxis_set.copy()

            self.baseline_time = current_time

        # Dictionary of percent changes from last 5-second snapshot
        changed_metric = {
            "active_taxis": self.change_in_active_taxi,
            "ended_taxis": self.change_in_ended_taxi,
            "cumulative_distance": self.change_in_cumulative_distance,
            "in_transit_taxis": self.change_in_in_transit_taxi,
            # "in_range_taxis": self.change_in_in_range_taxi,
        }

        # Final output structure with current counts and changes
        result = {
            "active_taxis": {
                "count": len(self.active_taxis_set),
                "change_from_last_hour": changed_metric["active_taxis"],
            },
            "inactive_taxis": {
                "count": 0,
                "change_from_last_hour": 0,
            },  # not computed
            "trip_ended_taxis": {
                "count": len(self.ended_taxis_set),
                "change_from_last_hour": changed_metric["ended_taxis"],
            },
            "total_distance": {
                "distance": round(total_distance, 2),
                "change_from_last_hour": changed_metric["cumulative_distance"],
            },
            "in_transit_taxis": {
                "count": len(self.in_transit_taxis_set),
                "change_from_last_hour": changed_metric["in_transit_taxis"],
            },
            # "in_range_taxis": {
            #     "count": len(self.in_range_taxis_set),
            #     "change_from_last_hour": changed_metric["in_range_taxis"],
            # },
        }

        # Emit result as JSON string
        yield orjson.dumps(result).decode("utf-8")
