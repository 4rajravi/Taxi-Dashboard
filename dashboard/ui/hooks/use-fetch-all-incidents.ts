"use client";

import { useEffect, useState } from "react";

import { useIncidentsDataStore } from "@/stores/use-incidents-data-store";

const REST_API_URL = "http://localhost:8000/api/incidents";

/**
 * Custom hook to load taxi data from the REST API and manage loading state.
 * Returns a boolean indicating if taxis are still loading.
 */
export function useLoadAllIncidents(refetch: boolean): {
  fetchSucceeded: boolean;
} {
  const setAllIncidents = useIncidentsDataStore(
    (state) => state.setAllIncidents
  );

  const [fetchSucceeded, setFetchSucceeded] = useState(false);

  useEffect(() => {
    async function loadAllIncidents() {
      setFetchSucceeded(false);

      try {
        const response = await fetch(REST_API_URL);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        setAllIncidents(data.incidents);
        setFetchSucceeded(true);
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
        setFetchSucceeded(false);
      }
    }

    loadAllIncidents();
    // Depend on refetch to trigger reload
  }, [setAllIncidents, refetch]);

  return { fetchSucceeded };
}
