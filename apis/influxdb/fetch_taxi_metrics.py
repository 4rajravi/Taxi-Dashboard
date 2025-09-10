import os
import asyncio

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync  # type: ignore

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")


async def get_taxi_event_latency_trend(taxi_id: str):
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: 0, stop: now())
              |> filter(fn: (r) => r._measurement == "taxi_metrics" and r.taxi_id == "{taxi_id}")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> map(fn: (r) => ({{
                  _time: r._time,
                  event_latency_in_seconds: (float(v: uint(v: r._time)) - float(v: r.sent_at_utc_ms) * 1000000.0) / 1000000000.0
              }}))
              |> keep(columns: ["_time", "event_latency_in_seconds"])
            """

            records = await query_api.query_stream(flux_query)

            results = [
                {
                    "time": (
                        record["_time"].isoformat(timespec="milliseconds")
                        if hasattr(record["_time"], "isoformat")
                        else record["_time"]
                    ),
                    "event_latency_in_seconds": record["event_latency_in_seconds"],
                }
                async for record in records
            ]

            return results
    except Exception as e:
        print(f"An error occurred while fetching taxi event latency trend: {e}")
        return []


async def get_taxi_speed_trend(taxi_id: str):
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: 0, stop: now())
              |> filter(fn: (r) => r._measurement == "taxi_metrics" and r._field == "speed" and r.taxi_id == "{taxi_id}")
              |> keep(columns: ["_time", "_value"])
            """

            records = await query_api.query_stream(flux_query)

            results = [
                {
                    "time": (
                        record["_time"].isoformat(timespec="milliseconds")
                        if hasattr(record["_time"], "isoformat")
                        else record["_time"]
                    ),
                    "speed_in_km_per_hour": record["_value"],
                }
                async for record in records
            ]

            return results
    except Exception as e:
        print(f"An error occurred while fetching taxi speed trend: {e}")
        return []


async def get_taxi_average_speed_trend(taxi_id: str):
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: 0, stop: now())
              |> filter(fn: (r) => r._measurement == "taxi_metrics" and r._field == "avg_speed" and r.taxi_id == "{taxi_id}")
              |> keep(columns: ["_time", "_value"])
            """

            records = await query_api.query_stream(flux_query)

            results = [
                {
                    "time": (
                        record["_time"].isoformat(timespec="milliseconds")
                        if hasattr(record["_time"], "isoformat")
                        else record["_time"]
                    ),
                    "average_speed_in_km_per_hour": record["_value"],
                }
                async for record in records
            ]

            return results
    except Exception as e:
        print(f"An error occurred while fetching taxi average speed trend: {e}")
        return []


async def get_taxi_incidents_trend(taxi_id: str):
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: 0, stop: now())
                |> filter(fn: (r) =>
                    r._measurement == "taxi_violation_alerts" and
                    r._field == "speed" and
                    r.taxi_id == "{taxi_id}"
                )
                |> window(every: 5m)
                |> count()
                |> pivot(rowKey: ["_start", "taxi_id"], columnKey: ["alert_type"], valueColumn: "_value")
                |> map(fn: (r) => ({{
                    GEOFENCE_VIOLATION: if exists r.GEOFENCE_VIOLATION then int(v: r.GEOFENCE_VIOLATION) else 0,
                    SPEED_VIOLATION: if exists r.SPEED_VIOLATION then int(v: r.SPEED_VIOLATION) else 0,
                    total: (if exists r.GEOFENCE_VIOLATION then int(v: r.GEOFENCE_VIOLATION) else 0) +
                        (if exists r.SPEED_VIOLATION then int(v: r.SPEED_VIOLATION) else 0),
                    time_window: string(v: r._stop),
                    taxi_id: r.taxi_id,
                }}))
                |> sort(columns: ["_start"], desc: true)
                |> fill(column: "GEOFENCE_VIOLATION", value: 0)
                |> fill(column: "SPEED_VIOLATION", value: 0)
                |> fill(column: "total", value: 0)
            """

            records = await query_api.query_stream(flux_query)

            raw_records = []
            async for record in records:
                raw_records.append({
                    "time": record.values.get("time_window", ""),
                    "geofence_violation_count": record.values.get("GEOFENCE_VIOLATION", 0),
                    "speed_violation_count": record.values.get("SPEED_VIOLATION", 0),
                })

            return raw_records
    except Exception as e:
        print(f"An error occurred while fetching taxi incidents trend: {e}")
        return []


def get_influxdb_taxi_data(taxi_id):
    try:
        async def gather_influxb_queries_result():
            results = await asyncio.gather(
                get_taxi_event_latency_trend(taxi_id),
                get_taxi_speed_trend(taxi_id),
                get_taxi_average_speed_trend(taxi_id),
                get_taxi_incidents_trend(taxi_id),
            )

            return {
                "event_latency_trend": results[0],
                "speed_trend": results[1],
                "average_speed_trend": results[2],
                "incidents_trend": results[3],
            }

        return asyncio.run(gather_influxb_queries_result())
    except Exception as e:
        print(f"An error occurred while fetching InfluxDB taxi data: {e}")
        return {
            "event_latency_trend": [],
            "speed_trend": [],
            "average_speed_trend": [],
            "incidents_trend": [],
        }
