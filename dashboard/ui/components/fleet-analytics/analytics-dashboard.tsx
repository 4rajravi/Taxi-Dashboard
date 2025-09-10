"use client";

import { CircleCheckIcon, RefreshCwIcon } from "lucide-react";
import { toast } from "sonner";

import { useState, useEffect, useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import TaxiFleetMetricsTrendChart from "./charts/taxi-fleet-metrics-trend-chart";

import { useTaxiFleetAnalyticsDataStore } from "@/stores/use-taxi-fleet-analytics-data-store";
import { useLoadTaxiFleetAnalyticsData } from "@/hooks/use-fetch-taxi-fleet-analytics-data";
import TaxiFleetEventLatencyCards from "./charts/taxi-fleet-event-latency-cards";
import TaxiFleetIncidentsTrendChart from "./charts/taxi-fleet-incidents-trend-chart";

export function TaxiFleetAnalyticsDashboard() {
  const [refreshFlag, setRefreshFlag] = useState(false);

  // Fetch analytics data for the given taxi_id
  const { loadingTaxis, fetchSucceeded } =
    useLoadTaxiFleetAnalyticsData(refreshFlag);

  useEffect(() => {
    if (fetchSucceeded) {
      toast.dismiss(); // Hide any existing toasts
      toast(
        <div className="flex flex-row">
          <CircleCheckIcon className="text-green-500 w-5 h-5 mr-2" />
          Taxi Fleet Trends Data Fetched Successfully!
        </div>,
        {
          duration: 2000,
          position: "top-center",
        }
      );
    }
  }, [fetchSucceeded]);

  // Get analytics data from the Zustand store
  const taxiFleetAnalyticsData = useTaxiFleetAnalyticsDataStore(
    (state) => state.taxiFleetAnalyticsData
  );

  const taxiFleetMetricsTrendChartData = useMemo(
    () => taxiFleetAnalyticsData?.fleet_metrics_trend || [],
    [taxiFleetAnalyticsData?.fleet_metrics_trend]
  );

  const taxiFleetEventLatencyTrend = useMemo(
    () =>
      taxiFleetAnalyticsData?.fleet_event_latency_trend || {
        max: { latency_in_seconds: 0, change_from_last_5s_percent: 0 },
        min: { latency_in_seconds: 0, change_from_last_5s_percent: 0 },
        mean: { latency_in_seconds: 0, change_from_last_5s_percent: 0 },
      },
    [taxiFleetAnalyticsData?.fleet_event_latency_trend]
  );

  const taxiFleetIncidentsTrendChartData = useMemo(() => {
    const incidentsTrend = taxiFleetAnalyticsData?.fleet_incidents_trend || [];
    return incidentsTrend.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
  }, [taxiFleetAnalyticsData?.fleet_incidents_trend]);


  const handleRefresh = () => {
    setRefreshFlag((prev) => !prev);
  };

  console.log("Taxi Fleet Analytics Data:", taxiFleetAnalyticsData);

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">
        Taxi Fleet Trends Analytics Dashboard
      </h1>
      <Label className="text-gray-300 mb-4 font-light text-s">
        Explore various taxi fleet trends to gain valuable insights into taxi
        fleet performance and operations.
      </Label>
      <div className="flex items-center justify-between py-4 mb-4">
        {/* <Label className="text-md font-light text-slate-500">
          Taxi{" "}
          <Badge className="rounded-full font-normal px-2">{taxi_id}</Badge>
        </Label> */}
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
            Loading taxi fleet trends analytics data...
          </div>
        )}
        {!loadingTaxis && !fetchSucceeded && (
          <div className="text-slate-400 flex justify-center items-center">
            Failed to fetch taxi fleet trends analytics data.
          </div>
        )}
        {!loadingTaxis && fetchSucceeded && (
          <>
            {taxiFleetMetricsTrendChartData &&
            taxiFleetMetricsTrendChartData.length > 0 ? (
              <TaxiFleetMetricsTrendChart
                taxiFleetMetricsTrendChartData={taxiFleetMetricsTrendChartData}
              />
            ) : (
              <div className="text-slate-400 flex justify-center items-center">
                No taxi fleet metrics trend data available.
              </div>
            )}
            {taxiFleetEventLatencyTrend &&
            Object.keys(taxiFleetEventLatencyTrend).length > 0 ? (
              <TaxiFleetEventLatencyCards
                taxiFleetEventLatencyTrend={taxiFleetEventLatencyTrend}
              />
            ) : (
              <div className="text-slate-400 flex justify-center items-center">
                No taxi fleet event latency data available.
              </div>
            )}
            {taxiFleetIncidentsTrendChartData &&
            taxiFleetIncidentsTrendChartData.length > 0 ? (
              <TaxiFleetIncidentsTrendChart
                taxiFleetIncidentTrendChartData={
                  taxiFleetIncidentsTrendChartData
                }
              />
            ) : (
              <div className="text-slate-400 flex justify-center items-center">
                No taxi fleet incidents trend data available.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
