import { useEffect, useState } from "react";

import { useTaxiFleetAnalyticsDataStore } from "@/stores/use-taxi-fleet-analytics-data-store";

const FLEET_ANALYTICS_API_URL = "http://localhost:8000/api/analytics/fleet";


export function useLoadTaxiFleetAnalyticsData(refetch: boolean): {
  loadingTaxis: boolean;
  fetchSucceeded: boolean;
} {
  // Get actions from the taxi fleet analytics data store
  const setTaxiFleetAnalyticsData = useTaxiFleetAnalyticsDataStore(
    (state) => state.setTaxiFleetAnalyticsData
  );

  // Local state to track loading status and if fetch was successful or not
  const [loadingTaxis, setLoadingTaxis] = useState(true);
  const [fetchSucceeded, setFetchSucceeded] = useState(false);

  useEffect(() => {
    // Async function to fetch taxi fleet data
    async function loadTaxiFleetAnalyticsData() {
      // Ensure both loading state and fetch status state are set at the start
      setLoadingTaxis(true);
      setFetchSucceeded(false);

      try {
        const response = await fetch(`${FLEET_ANALYTICS_API_URL}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        setTaxiFleetAnalyticsData(data.data); // Update store with fetched taxi fleet analytics data
        setFetchSucceeded(true); // Update fetch status state to true
      } catch (error) {
        console.error("Failed to fetch taxi fleet analytics data:", error);
        setFetchSucceeded(false); // Update fetch status state to false
      } finally {
        setLoadingTaxis(false); // Unset loading state
      }
    }

    loadTaxiFleetAnalyticsData();
    // Only depend on store actions and taxiId to avoid unnecessary reloads
  }, [setTaxiFleetAnalyticsData, refetch]);

  return { loadingTaxis, fetchSucceeded };
}
