"use client";

import { CircleCheckIcon, RefreshCwIcon } from "lucide-react";
import { toast } from "sonner";

import { useState, useEffect, useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import TaxiEventLatencyTrendChart from "./charts/taxi-event-latency-trend-chart";
import TaxiSpeedTrendChart from "./charts/taxi-speed-trend-chart";
import TaxiAverageSpeedTrendChart from "./charts/taxi-average-speed-trend-chart";
import TaxiIncidentsTrendChart from "./charts/taxi-incidents-trend-chart";

import { useTaxiAnalyticsDataStore } from "@/stores/use-taxi-analytics-data-store";

import { useLoadTaxiAnalyticsData } from "@/hooks/use-fetch-taxi-analytics-data";

export function TaxiAnalyticsDashboard({ taxi_id }: { taxi_id: number }) {
  const [refreshFlag, setRefreshFlag] = useState(false);

  // Fetch analytics data for the given taxi_id
  const { loadingTaxis, fetchSucceeded } = useLoadTaxiAnalyticsData(
    String(taxi_id),
    refreshFlag
  );

  useEffect(() => {
    if (fetchSucceeded) {
      toast.dismiss(); // Hide any existing toasts
      toast(
        <div className="flex flex-row">
          <CircleCheckIcon className="text-green-500 w-5 h-5 mr-2" />
          Taxi Trends Data Fetched Successfully!
        </div>,
        {
          duration: 2000,
          position: "top-center",
        }
      );
    }
  }, [fetchSucceeded]);

  // Get analytics data from the Zustand store
  const taxiAnalyticsData = useTaxiAnalyticsDataStore(
    (state) => state.taxiAnalyticsDataById[String(taxi_id)]
  );

  const taxiEventLatencyTrendChartData = useMemo(
    () => taxiAnalyticsData?.event_latency_trend || [],
    [taxiAnalyticsData?.event_latency_trend]
  );

  const taxiSpeedTrendChartData = useMemo(
    () => taxiAnalyticsData?.speed_trend || [],
    [taxiAnalyticsData?.speed_trend]
  );

  const taxiAverageSpeedTrendChartData = useMemo(
    () => taxiAnalyticsData?.average_speed_trend || [],
    [taxiAnalyticsData?.average_speed_trend]
  );

  const taxiIncidentTrendChartData = useMemo(() => {
    const incidentsTrend = taxiAnalyticsData?.incidents_trend || [];
    return incidentsTrend.sort(
      (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
    );
  }, [taxiAnalyticsData?.incidents_trend]);

  const handleRefresh = () => {
    setRefreshFlag((prev) => !prev);
  };

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">
        Taxi Trends Analytics Dashboard
      </h1>
      <Label className="text-gray-300 mb-4 font-light text-s">
        Explore various taxi trends including event latency, speed, average
        speed, and more to gain valuable insights into taxi performance and
        operations.
      </Label>
      <div className="flex items-center justify-between py-4 mb-4">
        <Label className="text-md font-light text-slate-500">
          Taxi{" "}
          <Badge className="rounded-full font-normal px-2">{taxi_id}</Badge>
        </Label>
        <Button
          variant="outline"
          className="cursor-pointer flex items-center"
          onClick={handleRefresh}
        >
          <RefreshCwIcon /> Refresh Data
        </Button>
      </div>
      <div className="flex flex-col gap-4">
        {loadingTaxis && (
          <div className="text-slate-400 flex justify-center items-center">
            Loading taxi trends analytics data...
          </div>
        )}
        {!loadingTaxis && !fetchSucceeded && (
          <div className="text-slate-400 flex justify-center items-center">
            Failed to fetch taxi trends analytics data.
          </div>
        )}
        {!loadingTaxis && fetchSucceeded && (
          <>
            <TaxiEventLatencyTrendChart
              taxiId={taxi_id}
              taxiEventLatencyTrendChartData={taxiEventLatencyTrendChartData}
            />
            <div className="grid grid-cols-2 gap-4">
              <TaxiSpeedTrendChart
                taxiId={taxi_id}
                taxiSpeedTrendChartData={taxiSpeedTrendChartData}
              />
              <TaxiAverageSpeedTrendChart
                taxiId={taxi_id}
                taxiAverageSpeedTrendChartData={taxiAverageSpeedTrendChartData}
              />
            </div>
            <TaxiIncidentsTrendChart
              taxiId={taxi_id}
              taxiIncidentTrendChartData={taxiIncidentTrendChartData}
            />
          </>
        )}
      </div>
    </div>
  );
}
