import { GaugeIcon, MapIcon } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { useIncidentsWebSocket } from "@/hooks/use-incidents-websocket";
import { useLoadTaxis } from "@/hooks/use-fetch-taxis";

import {
  useIncidentsDataStore,
  Incident,
} from "@/stores/use-incidents-data-store";
import { useTaxiDataStore } from "@/stores/use-taxi-data-store";

// Card component for displaying a single incident
function IncidentCard({
  children,
  incident,
}: {
  children: React.ReactNode;
  incident: Incident;
}) {
  function handleIncidentClick(incident: Incident): void {
    // Access taxi data store actions
    const setSelectedTaxi = useTaxiDataStore.getState().setSelectedTaxi;
    const setSelectedCoordinates =
      useTaxiDataStore.getState().setSelectedCoordinates;
    const taxis = useTaxiDataStore.getState().taxis;

    // Find the taxi by incident.taxi_id
    const selectedTaxi = Object.values(taxis).find(
      (taxi) => String(taxi.taxi_id) === String(incident.taxi_id)
    );

    if (selectedTaxi) {
      setSelectedTaxi(selectedTaxi);
      setSelectedCoordinates([incident.latitude, incident.longitude]);
      useTaxiDataStore.getState().setZoomScale(20);
    }
  }

  return (
    <Alert
      key={`${incident.taxi_id}-${incident.timestamp}`}
      className="cursor-pointer border-0 px-0 py-2 mb-1"
      onClick={() => handleIncidentClick(incident)}
    >
      {children}
    </Alert>
  );
}

// Main component to display the incident feed
export default function IncidentLiveFeed() {
  // Load taxis data and track loading/success state
  const { loadingTaxis, fetchSucceeded } = useLoadTaxis();

  // Start incidents websocket only after taxis are loaded successfully
  useIncidentsWebSocket(fetchSucceeded && !loadingTaxis);

  // Get incidents as an array from the store
  const incidents = Object.values(
    useIncidentsDataStore((state) => state.incidents)
  );

  function sortIncidentsByUpdatedAt(a: Incident, b: Incident): number {
    // Sort descending: most recent first
    const dateA = new Date(a.updated_at).getTime();
    const dateB = new Date(b.updated_at).getTime();
    return dateB - dateA;
  }
  // Formats a UTC timestamp into a relative time string (e.g., "5 minutes ago")
  function formatTimeAgo(updated_at: string): React.ReactNode {
    // Parse as UTC by appending 'Z' if not present
    const updatedDate = new Date(
      updated_at.endsWith("Z") ? updated_at : updated_at + "Z"
    );
    // Use Date.now() for current UTC time
    const diffMs = Date.now() - updatedDate.getTime();

    const seconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} day${days > 1 ? "s" : ""} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    } else if (minutes > 0) {
      return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    } else {
      return `${seconds} second${seconds !== 1 ? "s" : ""} ago`;
    }
  }

  return (
    <Card className="w-full h-[83vh] max-h-[83vh] flex flex-col border-0">
      <CardContent className="flex-1 overflow-y-auto p-0 pr-2 scrollbar-hide">
        {(!incidents || incidents.length === 0) && (
          <div className="flex items-center justify-center h-full w-full">
            <Label className="text-center text-gray-300 text-m font-light">
              No new incidents
            </Label>
          </div>
        )}
        {/* Show the most recent incidents in reverse order */}
        {incidents &&
          incidents
            .slice() // avoid mutating original array
            .sort(sortIncidentsByUpdatedAt)
            .map((incident) => (
              <IncidentCard incident={incident} key={incident.incident_id}>
                {incident.alert_type === "GEOFENCE_VIOLATION" && <MapIcon />}
                {incident.alert_type === "SPEED_VIOLATION" && <GaugeIcon />}
                <AlertTitle className="text-slate-600">
                  <Badge
                    className={`font-xs text-white rounded-full ${
                      incident.alert_type === "SPEED_VIOLATION"
                        ? "bg-orange-50 text-orange-500"
                        : "bg-indigo-50 text-indigo-500"
                    }`}
                  >
                    {incident.taxi_id}
                  </Badge>
                  {incident.alert_type === "GEOFENCE_VIOLATION" && (
                    <span className="font-xs">
                      {" "}
                      is{" "}
                      <span className="font-bold text-slate-950">
                        {incident.distance_km}
                      </span>{" "}
                      km away from city center.
                    </span>
                  )}
                  {incident.alert_type === "SPEED_VIOLATION" && (
                    <span className="font-xs">
                      {" "}
                      is driving at{" "}
                      <span className="font-bold text-slate-950">
                        {incident.speed}
                      </span>{" "}
                      km/h.
                    </span>
                  )}
                </AlertTitle>
                <AlertDescription>
                  <div className="flex items-start text-xs">
                    {formatTimeAgo(incident.updated_at)}
                  </div>
                </AlertDescription>
              </IncidentCard>
            ))}
      </CardContent>
    </Card>
  );
}
