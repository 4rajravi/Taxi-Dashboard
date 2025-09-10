"use client";

import { useResizeMapOnContainerResize } from "@/hooks/use-resize-map-on-container-resize";

// This component handles resizing the map when the map container's size changes using hooks.
export function MapResize() {
  useResizeMapOnContainerResize("map-container");

  return null;
}
