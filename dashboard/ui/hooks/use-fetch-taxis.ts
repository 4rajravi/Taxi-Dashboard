import { useEffect, useState } from "react";

import { useTaxiDataStore } from "@/stores/use-taxi-data-store";
import { useTaxiFleetMetricsStore } from "@/stores/use-taxi-fleet-metrics-store";

const REST_API_URL = "http://localhost:8000/api/taxis";

/**
 * Custom hook to load taxi data from the REST API and manage loading state.
 * Returns a boolean indicating if taxis are still loading.
 */
export function useLoadTaxis(): {
  loadingTaxis: boolean;
  fetchSucceeded: boolean;
} {
  // Get actions from the taxi data store
  const setTaxis = useTaxiDataStore((state) => state.setTaxis);
  const setTotalTaxiFleetSize = useTaxiFleetMetricsStore(
    (state) => state.setTotalTaxiFleetSize
  );
  const setDataReplayMode = useTaxiFleetMetricsStore(
    (state) => state.setDataReplayMode
  );
  const setDataReplaySpeed = useTaxiFleetMetricsStore(
    (state) => state.setDataReplaySpeed
  );

  // Local state to track loading status and if fetch was successful or not
  const [loadingTaxis, setLoadingTaxis] = useState(true);
  const [fetchSucceeded, setFetchSucceeded] = useState(false);

  useEffect(() => {
    // Async function to fetch taxi data
    async function loadTaxis() {
      // Ensure both loading state and fetch status state are set at the start
      setLoadingTaxis(true);
      setFetchSucceeded(false);

      try {
        const response = await fetch(REST_API_URL);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        setTaxis(data.taxis); // Update store with fetched taxis
        setTotalTaxiFleetSize(data.total_taxi_fleet_size); // Update store with fetched total taxi fleet size
        setDataReplayMode(data.data_replay_mode); // Update store with data replay mode
        setDataReplaySpeed(data.data_replay_speed); // Update store with data replay speed
        setFetchSucceeded(true); // Update fetch status state to true
      } catch (error) {
        console.error("Failed to fetch taxis:", error);
        setFetchSucceeded(false); // Update fetch status state to false
      } finally {
        setLoadingTaxis(false); //  Unset loading state
      }
    }

    loadTaxis();
    // Only depend on store actions to avoid unnecessary reloads
  }, [setTaxis, setTotalTaxiFleetSize, setDataReplayMode, setDataReplaySpeed]);

  return { loadingTaxis, fetchSucceeded };
}
