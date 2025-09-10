import os
import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision  # type: ignore
from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore


class InfluxDBTaxiFleetMetricsWriter:
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

    def write_fleet_metrics_to_db(self, fleet_metrics):
        """
        Write fleet metrics to InfluxDB. Accepts either a single dict or list of dicts.
        """
        try:
            # Handle both single message and batch of messages
            if isinstance(fleet_metrics, list):
                # Process each message in the batch
                points = []
                for single_metric in fleet_metrics:
                    if not isinstance(single_metric, dict):
                        self.logger.warning(f"Skipping non-dict message: {type(single_metric)}")
                        continue
                        
                    point = self._create_point_from_metric(single_metric)
                    if point:
                        points.append(point)
                
                if points:
                    self.write_api.write(bucket=self.bucket, record=points)
                    self.logger.info(f"✅ Written {len(points)} fleet metrics data points.")
                else:
                    self.logger.warning("No valid points to write in batch")
                    
            else:
                # Handle single message (backward compatibility)
                point = self._create_point_from_metric(fleet_metrics)
                if point:
                    self.write_api.write(bucket=self.bucket, record=point)
                    self.logger.info("✅ Written fleet metrics data point.")

        except Exception as e:
            self.logger.error(f"❌ Failed to write to InfluxDB: {e}", exc_info=True)

    def _create_point_from_metric(self, fleet_metric: dict):
        """Create a single InfluxDB point from a fleet metric dictionary."""
        try:
            point = (
                Point("taxi_fleet_metrics")
                .field("active_taxis_count", fleet_metric["active_taxis"]["count"])
                .field("active_taxis_change", fleet_metric["active_taxis"]["change_from_last_hour"])
                .field("trip_ended_taxis_count", fleet_metric["trip_ended_taxis"]["count"])
                .field("trip_ended_taxis_change", fleet_metric["trip_ended_taxis"]["change_from_last_hour"])
                .field("total_distance_km", fleet_metric["total_distance"]["distance"])
                .field("total_distance_change", fleet_metric["total_distance"]["change_from_last_hour"])
                .field("in_transit_taxis_count", fleet_metric["in_transit_taxis"]["count"])
                .field("in_transit_taxis_change", fleet_metric["in_transit_taxis"]["change_from_last_hour"])
                .time(datetime.datetime.now(datetime.timezone.utc), WritePrecision.MS)
            )
            return point
        except KeyError as e:
            self.logger.error(f"Missing required field in fleet metric: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error creating point from metric: {e}")
            return None