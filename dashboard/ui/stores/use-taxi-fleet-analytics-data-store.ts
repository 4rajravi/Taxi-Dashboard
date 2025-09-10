import { create } from "zustand";

type FleetMetricsTrend = {
  time: string;
  active_taxis_count: number;
  in_transit_taxis_count: number;
  trip_ended_taxis_count: number;
};

type FleetEventLatencyTrendMetric = {
    latency_in_seconds: number;
    change_from_last_5s_percent: number;
}

type FleetEventLatencyTrend = {
  max: FleetEventLatencyTrendMetric;
  min: FleetEventLatencyTrendMetric;
  mean: FleetEventLatencyTrendMetric;
};

type FleetIncidentsTrend = {
  time: string;
  geofence_violation_count: number;
  speed_violation_count: number;
  total_violation_count: number;
};

type TaxiFleetAnalyticsData = {
  fleet_metrics_trend: FleetMetricsTrend[];
  fleet_event_latency_trend: FleetEventLatencyTrend;
  fleet_incidents_trend: FleetIncidentsTrend[];
  };

type TaxiFleetAnalyticsDataStore = {
    taxiFleetAnalyticsData: TaxiFleetAnalyticsData | null;
    setTaxiFleetAnalyticsData: (taxiFleetAnalyticsData: TaxiFleetAnalyticsData) => void;
    clearTaxiFleetAnalyticsData: () => void;
};

export const useTaxiFleetAnalyticsDataStore = create<TaxiFleetAnalyticsDataStore>((set) => ({
    taxiFleetAnalyticsData: null,
    setTaxiFleetAnalyticsData: (taxiFleetAnalyticsData) =>
        set({ taxiFleetAnalyticsData }),
    clearTaxiFleetAnalyticsData: () =>
        set({ taxiFleetAnalyticsData: null }),
}));
