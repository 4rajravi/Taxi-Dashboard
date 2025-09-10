import { create } from "zustand";

// Represents a violation alert incident associated with a taxi
export type Incident = {
  incident_id: string;
  taxi_id: number;
  alert_type: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  trip_status: string;
  speed?: number;
  distance_km?: number;
  updated_at: string;
};

// Zustand store type for managing incident data
type IncidentsDataStore = {
  incidents: Record<string, Incident>; // Maps taxi_id to Incident object
  allIncidents: Record<string, Incident>; // Stores all incidents

  setIncidents: (incidentsList: Incident[]) => void; // Replaces all incidents with a new array
  clearIncidents: () => void; // Remove all incidents

  setAllIncidents: (incidentsList: Incident[]) => void; // Set all incidents
  clearAllIncidents: () => void; // Clear all incidents
};

// Zustand store implementation for incident data
export const useIncidentsDataStore = create<IncidentsDataStore>((set) => ({
  incidents: {},
  allIncidents: {},

  // Replace all incidents with the provided list of incidents
  setIncidents: (incidentsList) => {
    if (!Array.isArray(incidentsList)) {
      console.warn("Invalid incidentsList:", incidentsList);
      return;
    }
    set({
      incidents: incidentsList.reduce((accumulator, incident) => {
        accumulator[incident.incident_id] = incident;
        return accumulator;
      }, {} as Record<string, Incident>),
    });
  },

  // Clear all incidents from the store
  clearIncidents: () => set({ incidents: {} }),

  // Set allIncidents with the provided list
  setAllIncidents: (incidentsList) => {
    if (!Array.isArray(incidentsList)) {
      console.warn("Invalid incidentsList:", incidentsList);
      return;
    }
    set({
      allIncidents: incidentsList.reduce((accumulator, incident) => {
        accumulator[incident.incident_id] = incident;
        return accumulator;
      }, {} as Record<string, Incident>),
    });
  },

  // Clear allIncidents from the store
  clearAllIncidents: () => set({ allIncidents: {} }),
}));
