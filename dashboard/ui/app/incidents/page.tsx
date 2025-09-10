"use client";

import { HomeIcon } from "lucide-react";

import IncidentHistory from "@/components/incidents/incident-history";
import { Toaster } from "@/components/ui/sonner";

import { useTaxiDataStore } from "@/stores/use-taxi-data-store";
import { useIncidentsDataStore } from "@/stores/use-incidents-data-store";

export default function IncidentsPage() {
  const setSelectedTaxi = useTaxiDataStore((state) => state.setSelectedTaxi);
  const setSelectedCoordinates = useTaxiDataStore(
    (state) => state.setSelectedCoordinates
  );
  const setZoomScale = useTaxiDataStore((state) => state.setZoomScale);
  const { clearAllIncidents } = useIncidentsDataStore();

  const handleHomeClick = () => {
    setSelectedTaxi(null);
    setSelectedCoordinates([39.9168, 116.3972]);
    setZoomScale(10);
    clearAllIncidents();
    window.close();
  };

  return (
    <div className="flex items-center justify-center">
      <Toaster />
      <section className="bg-white mx-auto w-[85vw] min-h-[90vh] p-4 my-4">
        <button onClick={handleHomeClick}>
          <HomeIcon className="text-slate-500 h-5 w-5 mb-2 cursor-pointer" />
        </button>
        <h1 className="text-2xl font-semibold">Incidents</h1>
        <IncidentHistory />
      </section>
    </div>
  );
}
