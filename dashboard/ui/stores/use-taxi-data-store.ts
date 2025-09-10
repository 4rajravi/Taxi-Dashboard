import { create } from "zustand";
import { LatLngExpression } from "leaflet";

// Taxi data
export type Taxi = {
  taxi_id: number;
  timestamp: string;
  longitude: number;
  latitude: number;
  trip_status: string;
  speed: number;
  is_valid_speed: boolean;
  distance_from_forbidden_city_km: number;
  is_in_range: boolean;
  avg_speed: number;
  total_distance_km: number;
  sent_at_utc_ms: number;
  received_at_utc_ms: number;
  processed_at_utc_ms: number;
};

// Zustand store type for managing taxi data
type TaxiDataStore = {
  taxis: Record<number, Taxi>; // Maps taxi_id to Taxi object

  setTaxis: (taxisList: Taxi[]) => void; // Replace all taxis with new array

  clearTaxis: () => void; // Remove all taxis
};
// Zustand store implementation for taxi data
export const useTaxiDataStore = create<
  TaxiDataStore & {
    selectedTaxi: Taxi | null;
    selectedCoordinates: LatLngExpression | null;
    zoomScale: number | undefined;
    setSelectedTaxi: (taxi: Taxi | null) => void;
    setSelectedCoordinates: (coords: LatLngExpression | null) => void;
    setZoomScale: (zoom: number | undefined) => void;
  }
>((set) => ({
  taxis: {},
  selectedTaxi: null,
  selectedCoordinates: null,
  zoomScale: 10,

  // Replace all taxis with the provided list of taxis
  setTaxis: (taxisList) => {
    if (!Array.isArray(taxisList)) {
      console.warn("Invalid taxisList:", taxisList);
      return;
    }

    // set({
    //   taxis: taxisList.reduce((accumulator, taxi) => {
    //     accumulator[taxi.taxi_id] = taxi;
    //     return accumulator;
    //   }, {} as Record<number, Taxi>),
    // })
    set((state) => {
      const updated = { ...state.taxis };
      for (const taxi of taxisList) {
        updated[taxi.taxi_id] = {
          ...updated[taxi.taxi_id],
          ...taxi,
        };
      }
      return { taxis: updated };
    });
  },

  // Clear all taxis from the store
  clearTaxis: () => set({ taxis: {} }),

  // Set selected taxi
  setSelectedTaxi: (taxi) => set({ selectedTaxi: taxi }),

  // Set selected coordinates
  setSelectedCoordinates: (coordinates) =>
    set({ selectedCoordinates: coordinates }),

  // Set zoom scale
  setZoomScale: (zoom) => set({ zoomScale: zoom }),
}));

// Zustand store implementation for managing all taxi IDs
export const useAllTaxiIdsStore = create<{
  allTaxiIds: number[];
  setAllTaxiIds: (ids: number[]) => void;
  clearAllTaxiIds: () => void;
}>((set) => ({
  allTaxiIds: [],

  // Set all taxi IDs
  setAllTaxiIds: (ids) => {
    if (!Array.isArray(ids) || !ids.every((id) => typeof id === "number")) {
      console.warn("Invalid taxi IDs:", ids);
      return;
    }
    set({ allTaxiIds: ids });
  },

  // Clear all taxi IDs
  clearAllTaxiIds: () => set({ allTaxiIds: [] }),
}));
