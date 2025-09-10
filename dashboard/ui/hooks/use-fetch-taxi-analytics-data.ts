import { useEffect, useState } from "react";

import { useTaxiAnalyticsDataStore } from "@/stores/use-taxi-analytics-data-store";

const ANALYTICS_API_URL = "http://localhost:8000/api/analytics";


export function useLoadTaxiAnalyticsData(taxiId: string, refetch: boolean): {
  loadingTaxis: boolean;
  fetchSucceeded: boolean;
} {
  // Get actions from the taxi analytics data store
  const setTaxiAnalyticsData = useTaxiAnalyticsDataStore(
    (state) => state.setTaxiAnalyticsData
  );

  // Local state to track loading status and if fetch was successful or not
  const [loadingTaxis, setLoadingTaxis] = useState(true);
  const [fetchSucceeded, setFetchSucceeded] = useState(false);

  useEffect(() => {
    // Async function to fetch taxi data
    async function loadTaxiAnalyticsData() {
      // Ensure both loading state and fetch status state are set at the start
      setLoadingTaxis(true);
      setFetchSucceeded(false);

      try {
        const response = await fetch(`${ANALYTICS_API_URL}?taxi_id=${taxiId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        setTaxiAnalyticsData(taxiId, data.data); // Update store with fetched taxi analytics data
        setFetchSucceeded(true); // Update fetch status state to true
      } catch (error) {
        console.error("Failed to fetch taxi analytics data:", error);
        setFetchSucceeded(false); // Update fetch status state to false
      } finally {
        setLoadingTaxis(false); // Unset loading state
      }
    }

    loadTaxiAnalyticsData();
    // Only depend on store actions and taxiId to avoid unnecessary reloads
  }, [setTaxiAnalyticsData, taxiId, refetch]);

  return { loadingTaxis, fetchSucceeded };
}
