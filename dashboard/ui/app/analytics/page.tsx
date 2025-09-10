"use client";

import { useSearchParams, redirect } from "next/navigation";
import { Suspense } from "react";
import { HomeIcon } from "lucide-react";

import { TaxiAnalyticsDashboard } from "@/components/analytics/analytics-dashboard";
import { Toaster } from "@/components/ui/sonner";

import { useTaxiAnalyticsDataStore } from "@/stores/use-taxi-analytics-data-store";

function AnalyticsContent() {
  const searchParams = useSearchParams();

  const { clearTaxiAnalyticsData } = useTaxiAnalyticsDataStore();

  const taxiId = searchParams.get("taxi_id");
  const taxiIdNumber = taxiId ? parseInt(taxiId, 10) : NaN;

  if (!taxiId || isNaN(taxiIdNumber) || taxiIdNumber <= 0) {
    redirect("/home");
  }

  const handleHomeClick = () => {
    clearTaxiAnalyticsData(taxiId);
    window.close();
  };

  return (
    <section className="bg-white mx-auto w-[85vw] min-h-[90vh] p-4 my-4">
      <button onClick={handleHomeClick}>
        <HomeIcon className="text-slate-500 h-5 w-5 mb-2 cursor-pointer" />
      </button>
      <TaxiAnalyticsDashboard taxi_id={taxiIdNumber} />
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
