"use client";

import { Suspense } from "react";

import dynamic from "next/dynamic";

import { Card, CardContent } from "@/components/ui/card";

// Loader component to show while the map is loading
export const Loader = () => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
      }}
    >
      <div className="w-1/2 max-w-xs">
        <p className="mb-4 text-center text-slate-500">Loading map...</p>
      </div>
    </div>
  );
};

// Dynamically import the Leaflet-based map component with SSR disabled
const MapContainerWrapper = dynamic(() => import("./map-container-wrapper"), {
  ssr: false, // Disable server-side rendering for Leaflet
  loading: () => <Loader />, // Show Loader while loading
});

// Main wrapper component for the map, handles suspense and loading state
export default function MapClientWrapper() {
  return (
    <section className="flex-1 overflow-hidden p-4 pt-0 z-0">
      <Card className="w-full h-full rounded-xl border-0 shadow-none">
        <CardContent className="p-0 m-0 h-full">
          <Suspense fallback={<Loader />}>
            <MapContainerWrapper />
          </Suspense>
        </CardContent>
      </Card>
    </section>
  );
}
