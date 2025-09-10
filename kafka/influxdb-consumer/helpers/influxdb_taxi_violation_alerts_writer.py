import os
from datetime import datetime, timezone

from influxdb_client import InfluxDBClient, Point, WritePrecision  # type: ignore
from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore


class InfluxDBTaxiViolationAlertsWriter:
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

    def write_taxi_violation_alerts_to_db(self, violation_alerts):
        """
        Write taxi violation alerts to InfluxDB. Accepts either a single dict or list of dicts.
        """
        try:
            # Handle both single message and batch of messages
            if isinstance(violation_alerts, list):
                # Process each message in the batch
                points = []
                for single_alert in violation_alerts:
                    if not isinstance(single_alert, dict):
                        self.logger.warning(
                            f"Skipping non-dict message: {type(single_alert)}"
                        )
                        continue

                    point = self._create_point_from_violation_alert(single_alert)
                    if point:
                        points.append(point)

                if points:
                    self.write_api.write(bucket=self.bucket, record=points)
                    self.logger.info(
                        f"✅ Written {len(points)} taxi violation alert points."
                    )
                else:
                    self.logger.warning("No valid points to write in batch")

            else:
                # Handle single message (backward compatibility)
                point = self._create_point_from_violation_alert(violation_alerts)
                if point:
                    self.write_api.write(bucket=self.bucket, record=point)
                    self.logger.info(
                        f"✅ Written taxi violation alert point for taxi_id={violation_alerts.get('taxi_id')}"
                    )

        except Exception as e:
            self.logger.error(f"❌ Failed to write to InfluxDB: {e}", exc_info=True)

    def _create_point_from_violation_alert(self, taxi_violation_alert: dict):
        """Create a single InfluxDB point from a taxi violation alert dictionary."""
        try:
            point = (
                Point("taxi_violation_alerts")
                .tag("taxi_id", str(taxi_violation_alert.get("taxi_id", "unknown")))
                .tag(
                    "alert_type", str(taxi_violation_alert.get("alert_type", "unknown"))
                )
                .field(
                    "distance_km", float(taxi_violation_alert.get("distance_km", 0.0))
                )
                .field("speed", float(taxi_violation_alert.get("speed", 0.0)))
                .time(datetime.now(timezone.utc), WritePrecision.MS)
            )
            return point
        except KeyError as e:
            self.logger.error(f"Missing required field in violation alert: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating point from violation alert: {e}")
            return None

    def write_taxi_violation_alerts_point_to_db(self, taxi_violation_alert: dict):
        return self.write_taxi_violation_alerts_to_db(taxi_violation_alert)
