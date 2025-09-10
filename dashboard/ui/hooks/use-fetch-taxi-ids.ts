import { useEffect, useState } from "react";

import { useAllTaxiIdsStore } from "@/stores/use-taxi-data-store";

const REST_API_URL = "http://localhost:8000/api/taxi/ids";

/**
 * Custom hook to load taxi IDs from the REST API and manage loading state.
 * Returns a boolean indicating if taxi IDs are still loading.
 */
export function useFetchTaxiIds(): {
  loadingTaxiIds: boolean;
  fetchSucceeded: boolean;
} {
  // Get actions from the taxi IDs store
  const setAllTaxiIds = useAllTaxiIdsStore((state) => state.setAllTaxiIds);

  // Local state to track loading status and if fetch was successful or not
  const [loadingTaxiIds, setLoadingTaxiIds] = useState(true);
  const [fetchSucceeded, setFetchSucceeded] = useState(false);

  useEffect(() => {
    // Async function to fetch taxi IDs
    async function loadTaxiIds() {
      // Ensure both loading state and fetch status state are set at the start
      setLoadingTaxiIds(true);
      setFetchSucceeded(false);

      try {
        const response = await fetch(REST_API_URL);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const taxiIds = await response.json();

        setAllTaxiIds(taxiIds); // Update store with fetched taxi IDs
        setFetchSucceeded(true); // Update fetch status state to true
      } catch (error) {
        console.error("Failed to fetch taxi IDs:", error);
        setFetchSucceeded(false); // Update fetch status state to false
      } finally {
        setLoadingTaxiIds(false); // Unset loading state
      }
    }

    loadTaxiIds();
    // Only depend on store action to avoid unnecessary reloads
  }, [setAllTaxiIds]);

  return { loadingTaxiIds, fetchSucceeded };
}
