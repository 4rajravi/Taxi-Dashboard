"use client";

import { useEffect } from "react";
import { useMap } from "react-leaflet";

// Custom hook to resize the Leaflet map when fullscreen mode changes
export function useResizeMapOnFullscreen() {
  const map = useMap(); // Get the map instance from react-leaflet context

  useEffect(() => {
    // Handler to trigger map resize after fullscreen change
    const handleFullscreenChange = () => {
      setTimeout(() => {
        map.invalidateSize(); // Notify Leaflet to recalculate map size
      }, 300); // Delay ensures layout has settled after fullscreen toggle
    };

    // Listen for fullscreen changes on the document
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      // Cleanup listener on unmount or dependency change
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, [map]); // Re-run effect if map instance changes
}
