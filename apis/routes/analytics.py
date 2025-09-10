from fastapi import APIRouter, HTTPException, Query  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore

from influxdb.fetch_taxi_metrics import get_influxdb_taxi_data  # type: ignore
from influxdb.fetch_taxi_fleet_metrics import get_influxdb_taxi_fleet_metrics_data # type: ignore

router = APIRouter()


@router.get("/analytics")
def get_taxi_analytics(
    taxi_id: str = Query(
        ..., description="Taxi ID to fetch data for analytics dashboard from InfluxDB"
    )
):
    try:
        result = get_influxdb_taxi_data(taxi_id)
        return JSONResponse(content={"success": True, "data": result}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/fleet")
def get_taxi_fleet_analytics():
    try:
        result = get_influxdb_taxi_fleet_metrics_data()
        return JSONResponse(content={"success": True, "data": result}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
