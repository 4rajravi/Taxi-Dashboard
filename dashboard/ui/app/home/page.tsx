"use client";

import MapClientWrapper from "@/components/map/map-client-wrapper";
import FleetStatsWrapper from "@/components/fleet-stats/fleet-stats-wrapper";

export default function HomePage() {
  return (
    <div className="flex flex-col h-full w-full">
      <FleetStatsWrapper />
      <MapClientWrapper />
    </div>
  );
}
