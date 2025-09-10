"use client";

import { useRef, useEffect } from "react";

import FleetStatsCard from "@/components/fleet-stats/fleet-stats-card";

import { useLoadTaxis } from "@/hooks/use-fetch-taxis";
import { useTaxiFleetMetricsWebSocket } from "@/hooks/use-taxi-fleet-metrics-websocket";

import { useTaxiFleetMetricsStore } from "@/stores/use-taxi-fleet-metrics-store";

export default function FleetStatsWrapper() {
  const { loadingTaxis, fetchSucceeded } = useLoadTaxis();

  // Start incidents websocket only after taxis are loaded successfully
  useTaxiFleetMetricsWebSocket(fetchSucceeded && !loadingTaxis);

  const taxiFleetMetrics = useTaxiFleetMetricsStore(
    (state) => state.taxiFleetMetrics
  );

  function usePrevious<T>(value: T): T | undefined {
    const ref = useRef<T | undefined>(undefined);
    useEffect(() => {
      ref.current = value;
    }, [value]);
    return ref.current;
  }

  const currentActiveTaxis = taxiFleetMetrics?.active_taxis?.count ?? 0;
  const previousActiveTaxis = usePrevious(currentActiveTaxis) ?? 0;

  const currentInTransitTaxis = taxiFleetMetrics?.in_transit_taxis?.count ?? 0;
  const previousInTransitTaxis = usePrevious(currentInTransitTaxis) ?? 0;

  const currentTripEndedTaxis = taxiFleetMetrics?.trip_ended_taxis?.count ?? 0;
  const previousTripEndedTaxis = usePrevious(currentTripEndedTaxis) ?? 0;

  const currentTotalDistance = taxiFleetMetrics?.total_distance?.distance ?? 0;
  const previousTotalDistance = usePrevious(currentTotalDistance) ?? 0;

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4 px-4 py-2 mb-2">
      <FleetStatsCard
        label="Connected Taxis"
        previousValue={previousActiveTaxis}
        currentValue={currentActiveTaxis}
        trend={
          (taxiFleetMetrics?.active_taxis?.change_from_last_hour ?? 0) > 0
            ? `+${taxiFleetMetrics?.active_taxis?.change_from_last_hour ?? 0}%`
            : (taxiFleetMetrics?.active_taxis?.change_from_last_hour ?? 0) < 0
            ? `-${Math.abs(
                taxiFleetMetrics?.active_taxis?.change_from_last_hour ?? 0
              )}%`
            : "0%"
        }
        trendPositive={
          (taxiFleetMetrics?.active_taxis?.change_from_last_hour ?? 0) >= 0
        }
        cardTheme="bg-white text-slate-900"
      />
      <FleetStatsCard
        label="In Transit Taxis"
        previousValue={previousInTransitTaxis}
        currentValue={currentInTransitTaxis}
        trend={
          (taxiFleetMetrics?.in_transit_taxis?.change_from_last_hour ?? 0) > 0
            ? `+${
                taxiFleetMetrics?.in_transit_taxis?.change_from_last_hour ?? 0
              }%`
            : (taxiFleetMetrics?.in_transit_taxis?.change_from_last_hour ?? 0) < 0
            ? `-${Math.abs(
                taxiFleetMetrics?.in_transit_taxis?.change_from_last_hour ?? 0
              )}%`
            : "0%"
        }
        trendPositive={
          (taxiFleetMetrics?.in_transit_taxis?.change_from_last_hour ?? 0) >= 0
        }
        cardTheme="bg-white text-slate-900"
      />
      <FleetStatsCard
        label="Trip Ended Taxis"
        previousValue={previousTripEndedTaxis}
        currentValue={currentTripEndedTaxis}
        trend={
          (taxiFleetMetrics?.trip_ended_taxis?.change_from_last_hour ?? 0) > 0
            ? `+${
                taxiFleetMetrics?.trip_ended_taxis?.change_from_last_hour ?? 0
              }%`
            : (taxiFleetMetrics?.trip_ended_taxis?.change_from_last_hour ?? 0) <
              0
            ? `-${Math.abs(
                taxiFleetMetrics?.trip_ended_taxis?.change_from_last_hour ?? 0
              )}%`
            : "0%"
        }
        trendPositive={
          (taxiFleetMetrics?.trip_ended_taxis?.change_from_last_hour ?? 0) >= 0
        }
        cardTheme="bg-white text-slate-900"
      />
      <FleetStatsCard
        label="Total Distance Run (km)"
        previousValue={previousTotalDistance}
        currentValue={currentTotalDistance}
        trend={
          (taxiFleetMetrics?.total_distance?.change_from_last_hour ?? 0) > 0
            ? `+${
                taxiFleetMetrics?.total_distance?.change_from_last_hour ?? 0
              }%`
            : (taxiFleetMetrics?.total_distance?.change_from_last_hour ?? 0) < 0
            ? `-${Math.abs(
                taxiFleetMetrics?.total_distance?.change_from_last_hour ?? 0
              )}%`
            : "0%"
        }
        trendPositive={
          (taxiFleetMetrics?.total_distance?.change_from_last_hour ?? 0) >= 0
        }
        cardTheme="bg-white text-slate-900"
      />
    </section>
  );
}
