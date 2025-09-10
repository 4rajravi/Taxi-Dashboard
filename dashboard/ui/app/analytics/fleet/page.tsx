"use client";

import { Suspense } from "react";
import { HomeIcon } from "lucide-react";

import { TaxiFleetAnalyticsDashboard } from "@/components/fleet-analytics/analytics-dashboard";
import { Toaster } from "@/components/ui/sonner";

import { useTaxiFleetAnalyticsDataStore } from "@/stores/use-taxi-fleet-analytics-data-store";

function AnalyticsContent() {
  const { clearTaxiFleetAnalyticsData } = useTaxiFleetAnalyticsDataStore();

  const handleHomeClick = () => {
    clearTaxiFleetAnalyticsData();
    window.close();
  };

  return (
    <section className="bg-white mx-auto w-[85vw] min-h-[90vh] p-4 my-4">
      <button onClick={handleHomeClick}>
        <HomeIcon className="text-slate-500 h-5 w-5 mb-2 cursor-pointer" />
      </button>
      <TaxiFleetAnalyticsDashboard/>
    </section>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="flex items-center justify-center">
      <Toaster />
      <Suspense fallback={<div>Loading...</div>}>
        <AnalyticsContent />
      </Suspense>
    </div>
  );
}
