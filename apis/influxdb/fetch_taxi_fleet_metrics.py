import os
import asyncio

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync  # type: ignore

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")


async def get_taxi_fleet_metrics_trend():
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: 0, stop: now())
                |> filter(fn: (r) => 
                    r["_measurement"] == "taxi_fleet_metrics" and
                    (r["_field"] == "active_taxis_count" or
                    r["_field"] == "in_transit_taxis_count" or
                    r["_field"] == "trip_ended_taxis_count"))
                |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
                |> map(fn: (r) => ({{ r with _value: int(v: r._value) }}))
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> keep(columns: ["_time", "active_taxis_count", "in_transit_taxis_count", "trip_ended_taxis_count"])
            """

            records = await query_api.query_stream(flux_query)

            result = []
            async for record in records:
                result.append(
                    {
                        "time": record.get_time().isoformat(),
                        "active_taxis_count": record.values.get(
                            "active_taxis_count", 0
                        ),
                        "in_transit_taxis_count": record.values.get(
                            "in_transit_taxis_count", 0
                        ),
                        "trip_ended_taxis_count": record.values.get(
                            "trip_ended_taxis_count", 0
                        ),
                    }
                )

            return result
    except Exception as e:
        print(f"An error occurred while fetching taxi fleet metrics trend: {e}")
        return []


async def get_taxi_fleet_event_latency_trend():
    try:
        async with InfluxDBClientAsync(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
        ) as client:
            query_api = client.query_api()

            flux_query = f"""
            // Full range latency data
            latencyData = from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -5m, stop: now())
              |> filter(fn: (r) => r._measurement == "taxi_metrics")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> map(fn: (r) => ({{
                  r with
                  latency_in_seconds: (float(v: uint(v: r._time)) - float(v: r.sent_at_utc_ms) * 1000000.0) / 1000000000.0
              }}))
              |> keep(columns: ["_time", "latency_in_seconds"])

            maxLatency = latencyData
              |> max(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "max" }}))

            minLatency = latencyData
              |> min(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "min" }}))

            avgLatency = latencyData
              |> mean(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "mean" }}))

            // Last 5 seconds latency data
            latencyData5s = from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -5s)
              |> filter(fn: (r) => r._measurement == "taxi_metrics")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> map(fn: (r) => ({{
                  r with
                  latency_in_seconds: (float(v: uint(v: r._time)) - float(v: r.sent_at_utc_ms) * 1000000.0) / 1000000000.0
              }}))
              |> keep(columns: ["_time", "latency_in_seconds"])

            max5s = latencyData5s
              |> max(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "max_5s" }}))

            min5s = latencyData5s
              |> min(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "min_5s" }}))

            avg5s = latencyData5s
              |> mean(column: "latency_in_seconds")
              |> map(fn: (r) => ({{ r with stat: "mean_5s" }}))

            union(tables: [maxLatency, minLatency, avgLatency, max5s, min5s, avg5s])
            """

            records = await query_api.query_stream(flux_query)

            values = {}

            async for record in records:
                # print(f"Debug Record Values: {record.values}")
                stat = record.values.get("stat")
                latency = record.values.get("latency_in_seconds")

                if stat and latency is not None:
                    values[stat] = round(latency, 3)

            result = {}
            for stat in ["max", "min", "mean"]:
                current = values.get(stat)
                previous = values.get(f"{stat}_5s")

                change = None
                if current is not None and previous not in (None, 0):
                    change = round(((current - previous) / previous) * 100, 2)

                result[stat] = {
                    "latency_in_seconds": current,
                    "change_from_last_5s_percent": change,
                }

            return result
    except Exception as e:
        print(f"An error occurred while fetching taxi fleet event latency trend: {e}")
        return {}


async def get_taxi_fleet_incidents_trend():
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
                    r._field == "speed"
                )
                |> window(every: 5m)
                |> count()
                |> group(columns: ["_start", "_stop", "alert_type"])  // ensure aggregation by alert_type
                |> sum()
                |> pivot(rowKey: ["_start"], columnKey: ["alert_type"], valueColumn: "_value")
                |> map(fn: (r) => ({{
                    GEOFENCE_VIOLATION: if exists r.GEOFENCE_VIOLATION then int(v: r.GEOFENCE_VIOLATION) else 0,
                    SPEED_VIOLATION: if exists r.SPEED_VIOLATION then int(v: r.SPEED_VIOLATION) else 0,
                    total: (if exists r.GEOFENCE_VIOLATION then int(v: r.GEOFENCE_VIOLATION) else 0) +
                        (if exists r.SPEED_VIOLATION then int(v: r.SPEED_VIOLATION) else 0),
                    time_window: string(v: r._stop)
                }}))
                |> sort(columns: ["_start"], desc: true)
                """

            records = await query_api.query_stream(flux_query)

            trend_data = []
            async for record in records:
                trend_data.append(
                    {
                        "time": record.values.get("time_window", ""),
                        "geofence_violation_count": record.values.get(
                            "GEOFENCE_VIOLATION", 0
                        ),
                        "speed_violation_count": record.values.get(
                            "SPEED_VIOLATION", 0
                        ),
                        "total_violation_count": record.values.get("total", 0),
                    }
                )

            return trend_data
    except Exception as e:
        print(f"An error occurred while fetching taxi fleet incidents trend: {e}")
        return []


def get_influxdb_taxi_fleet_metrics_data():
    async def gather_influxb_queries_result():
        try:
            results = await asyncio.gather(
                get_taxi_fleet_metrics_trend(),
                get_taxi_fleet_event_latency_trend(),
                get_taxi_fleet_incidents_trend(),
            )

            return {
                "fleet_metrics_trend": results[0],
                "fleet_event_latency_trend": results[1],
                "fleet_incidents_trend": results[2],
            }
        except Exception as e:
            print(f"An error occurred while gathering InfluxDB queries result: {e}")
            return {
                "fleet_metrics_trend": [],
                "fleet_event_latency_trend": {},
                "fleet_incidents_trend": [],
            }

    return asyncio.run(gather_influxb_queries_result())
