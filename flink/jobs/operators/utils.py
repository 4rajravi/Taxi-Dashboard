import math

from typing import Dict, Any

from pyflink.common import Row  # type: ignore


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points using Haversine formula.
    """
    R = 6371  # Radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def update_row_fields(row: Row, updates: Dict[str, Any], schema) -> Row:
    """
    Returns a new Row with specified fields updated, using the given schema
    to preserve field order and ensure compatibility.

    Args:
        row (Row): The original Row to update.
        updates (Dict[str, Any]): A dictionary of field_name -> new_value.
        schema: A pyflink.common.type.Types.ROW_NAMED schema used to get field names.

    Returns:
        Row: A new Row with the specified fields updated.
    """
    field_names = [
        "taxi_id",
        "longitude",
        "latitude",
        "timestamp",
        "sent_at_utc_ms",
        "trip_status",
        "received_at_utc_ms",
        "speed",
        "is_valid_speed",
        "avg_speed",
        "total_distance_km",
        "distance_from_forbidden_city_km",
        "is_in_range",
    ]

    field_index: Dict[str, int] = {name: idx for idx, name in enumerate(field_names)}

    # Create a list of field values in order
    fields = [row[idx] for idx in range(len(field_names))]

    # Update specified fields
    for name, new_value in updates.items():
        if name not in field_index:
            raise ValueError(f"Field '{name}' is not in the schema.")
        fields[field_index[name]] = new_value

    # Return new Row with updated values
    return Row(**{name: fields[idx] for idx, name in enumerate(field_names)})
