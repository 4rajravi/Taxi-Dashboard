"use client";

import { LatLngExpression } from "leaflet";
import { useEffect } from "react";
import { useMap } from "react-leaflet";

type Props = {
  coordinates: LatLngExpression | null;
  zoom?: number; // Optional
  onZoomConsumed?: () => void; // Optional callback
};

export function MapSetView({ coordinates, zoom, onZoomConsumed }: Props) {
  const map = useMap();

  useEffect(() => {
    if (coordinates) {
      const targetZoom = typeof zoom === "number" ? zoom : map.getZoom();
      map.setView(coordinates, targetZoom);

      if (onZoomConsumed) {
        onZoomConsumed(); // Let parent clear the zoom state
      }
    }
  }, [coordinates, zoom, map, onZoomConsumed]);

  return null;
}
