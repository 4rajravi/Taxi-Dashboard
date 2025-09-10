import os

from influxdb_client import InfluxDBClient, Point, WritePrecision  # type: ignore
from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore


class InfluxDBTaxiDataWriter:
    def __init__(self, logger=None):
        self.logger = logger

        # Load InfluxDB configuration
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN")
        self.org = os.getenv("INFLUXDB_ORG")
        self.bucket = os.getenv("INFLUXDB_BUCKET")

        if not all([self.url, self.token, self.org, self.bucket]):
            self.logger.warning("InfluxDB environment variables are not fully set.")

        # Initialize client and write API
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_taxi_data_to_db(self, taxi_data):
        """
        Write taxi data to InfluxDB. Accepts either a single dict or list of dicts.
        """
        try:
            # Handle both single message and batch of messages
            if isinstance(taxi_data, list):
                # Process each message in the batch
                points = []
                for single_taxi_data in taxi_data:
                    if not isinstance(single_taxi_data, dict):
                        self.logger.warning(
                            f"Skipping non-dict message: {type(single_taxi_data)}"
                        )
                        continue

                    point = self._create_point_from_taxi_data(single_taxi_data)
                    if point:
                        points.append(point)

                if points:
                    self.write_api.write(bucket=self.bucket, record=points)
                    self.logger.info(f"✅ Written {len(points)} taxi data points.")
                else:
                    self.logger.warning("No valid points to write in batch")

            else:
                # Handle single message (backward compatibility)
                point = self._create_point_from_taxi_data(taxi_data)
                if point:
                    self.write_api.write(bucket=self.bucket, record=point)
                    self.logger.info(
                        f"✅ Written taxi data point for taxi_id={taxi_data.get('taxi_id')}"
                    )

        except Exception as e:
            self.logger.error(f"❌ Failed to write to InfluxDB: {e}", exc_info=True)

    def _create_point_from_taxi_data(self, taxi_data: dict):
        """Create a single InfluxDB point from a taxi data dictionary."""
        try:
            point = (
                Point("taxi_metrics")
                .tag("taxi_id", str(taxi_data.get("taxi_id", "unknown")))
                .tag("trip_status", str(taxi_data.get("trip_status", "active")))
                .field("speed", float(taxi_data.get("speed", 0.0)))
                .field("avg_speed", float(taxi_data.get("avg_speed", 0.0)))
                .field("latitude", float(taxi_data.get("latitude", 0.0)))
                .field("longitude", float(taxi_data.get("longitude", 0.0)))
                .field("is_valid_speed", bool(taxi_data.get("is_valid_speed", True)))
                .field(
                    "distance_from_forbidden_city_km",
                    float(taxi_data.get("distance_from_forbidden_city_km", 0.0)),
                )
                .field("is_in_range", bool(taxi_data.get("is_in_range", True)))
                .field("distance_km", float(taxi_data.get("distance_km", 0.0)))
                .field("timestamp", taxi_data.get("timestamp", "unknown"))
                .field("sent_at_utc_ms", float(taxi_data.get("sent_at_utc_ms", 0.0)))
                .field(
                    "received_at_utc_ms",
                    float(taxi_data.get("received_at_utc_ms", 0.0)),
                )
                .time(taxi_data["processed_at_utc_ms"], WritePrecision.MS)
            )
            return point
        except KeyError as e:
            self.logger.error(f"Missing required field in taxi data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating point from taxi data: {e}")
            return None

    def write_taxi_data_point_to_db(self, taxi_data: dict):
        return self.write_taxi_data_to_db(taxi_data)
