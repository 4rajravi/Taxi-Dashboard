"use client";

import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";

// Custom hook to resize the Leaflet map when its container size changes
export function useResizeMapOnContainerResize(containerId: string) {
  const map = useMap(); // Get the Leaflet map instance from context
  const observerRef = useRef<ResizeObserver | null>(null); // Store the ResizeObserver instance

  useEffect(() => {
    const container = document.getElementById(containerId); // Find the container element by ID
    if (!container) return; // Exit if container is not found

    // Create a ResizeObserver to watch for container size changes
    observerRef.current = new ResizeObserver(() => {
      map.invalidateSize(); // Notify the map to recalculate its size
    });

    observerRef.current.observe(container); // Start observing the container

    // Cleanup: disconnect the observer when the component unmounts or dependencies change
    return () => {
      observerRef.current?.disconnect();
    };
  }, [map, containerId]); // Re-run effect if map or containerId changes
}
