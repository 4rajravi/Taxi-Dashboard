"use client";

import { useMemo } from "react";
import L from "leaflet";
import { Marker } from "react-leaflet";

import { Taxi } from "@/stores/use-taxi-data-store";

export function MapMarker({
  taxi,
  onClick,
  isSelected,
}: {
  taxi: Taxi;
  onClick: () => void;
  isSelected: boolean;
}) {
  const taxiIcon = useMemo(() => {
    let iconUrl = "/taxi-icon.png";
    let iconCustomClass = "";

    if (taxi && typeof taxi === "object" && "trip_status" in taxi) {
      if (
        taxi.is_in_range &&
        taxi.trip_status === "active" &&
        taxi.speed == 0 &&
        taxi.is_valid_speed
      ) {
        iconUrl = "/connected-taxi-icon.png";
      } else if (
        taxi.is_in_range &&
        taxi.trip_status === "active" &&
        taxi.speed > 0 &&
        taxi.is_valid_speed
      ) {
        iconUrl = "/in-transit-taxi-icon.png";
      } else if (taxi.is_in_range && taxi.trip_status === "end") {
        iconUrl = "/trip-ended-taxi-icon.png";
      } else {
        iconUrl = "/taxi-icon.png";
      }
    }

    if (isSelected) {
      iconUrl = "/selected-taxi-icon.png";
      iconCustomClass =
        "outline outline-dashed outline-1 outline-indigo-900 shadow-lg";
    }
    const taxiIcon = L.icon({
      iconUrl: iconUrl,
      iconSize: [24, 24], // size in pixels
      iconAnchor: [16, 16], // center of icon (for accurate placement)
      className: `rounded-full border-2 border-white ${iconCustomClass}`,
    });
    return taxiIcon;
  }, [taxi, isSelected]);

  // Check if object has latitude and longitude properties
  const hasCoordinates = (
    obj: unknown
  ): obj is { latitude: number; longitude: number } =>
    !!obj &&
    typeof obj === "object" &&
    obj !== null &&
    "latitude" in obj &&
    typeof (obj as { latitude: unknown }).latitude === "number" &&
    "longitude" in obj &&
    typeof (obj as { longitude: unknown }).longitude === "number";

  // Extract coordinates from taxi if available, otherwise default to (0, 0)
  const coordinates = hasCoordinates(taxi)
    ? { latitude: taxi.latitude, longitude: taxi.longitude }
    : { latitude: 0, longitude: 0 };

  return useMemo(
    () => (
      <Marker
        position={[coordinates.latitude, coordinates.longitude]}
        icon={taxiIcon}
        eventHandlers={{
          click: () => onClick(),
        }}
      />
    ),
    [coordinates.latitude, coordinates.longitude, onClick, taxiIcon]
  );
}
