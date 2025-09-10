from pydantic import BaseModel, Field  # type: ignore
from typing import Optional

# ViolationAlertSchema represents a violation alert triggered by a taxi.
class ViolationAlertSchema(BaseModel):
    incident_id: str = Field(..., description="Incident ID") # Unique identifier for the incident
    taxi_id: int = Field(..., description="ID of the taxi") # Unique identifier for the taxi
    alert_type: str = Field(..., description="Type of violation alert") # Nature of the violation
    timestamp: str = Field(..., description="Actual event timestamp of the alert") # Actual event time when the violation happened
    latitude: float = Field(..., description="Latitude coordinate") # Latitude location of the taxi during the alert
    longitude: float = Field(..., description="Longitude coordinate") # Longitude location of the taxi during the alert
    trip_status: str = Field(..., description="Current status of the trip") # Status of the trip at the time of violation
    speed: Optional[float] = Field(None, description="Speed of the taxi") # (Optional) Speed in km/h when the alert occurred
    distance_km: Optional[float] = Field(None, description="Distance traveled in kilometers") # (Optional) Distance traveled during the trip
    updated_at: str = Field(..., description="Processing timestamp of the alert ") # Processing time when the alert was triggered
