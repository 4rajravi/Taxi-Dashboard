import { create } from "zustand";

// Types for each metric
type MetricWithChange = {
  count: number;
  change_from_last_hour: number | null;
};

type TotalDistanceMetric = {
  distance: number;
  change_from_last_hour: number;
};

type FleetAvgSpeedMetric = {
  avg_speed: number;
};

type TaxiFleetMetrics = {
  active_taxis: MetricWithChange;
  in_transit_taxis: MetricWithChange;
  trip_ended_taxis: MetricWithChange;
  total_distance: TotalDistanceMetric;
  fleet_avg_speed: FleetAvgSpeedMetric;
  current_taxi_fleet_size: number;
};

type TaxiFleetMetricsStore = {
  taxiFleetMetrics: TaxiFleetMetrics | null;
  totalTaxiFleetSize: number;
  dataReplayMode: string;
  dataReplaySpeed: string;

  setTaxiFleetMetrics: (metrics: TaxiFleetMetrics) => void;
  setTotalTaxiFleetSize: (size: number) => void;
  setDataReplayMode: (size: string) => void;
  setDataReplaySpeed: (size: string) => void;

  clearTaxiFleetMetrics: () => void;
  clearTotalTaxiFleetSize: () => void;
  clearDataReplayMode: () => void;
  clearDataReplaySpeed: () => void;
};

export const useTaxiFleetMetricsStore = create<TaxiFleetMetricsStore>(
  (set) => ({
    taxiFleetMetrics: null,
    totalTaxiFleetSize: 0,
    dataReplayMode: "actual",
    dataReplaySpeed: "1.0",

    setTaxiFleetMetrics: (metrics) => set({ taxiFleetMetrics: metrics }),
    setTotalTaxiFleetSize: (total_taxi_fleet_size) =>
      set({ totalTaxiFleetSize: total_taxi_fleet_size }),
    setDataReplayMode: (data_replay_mode) =>
      set({ dataReplayMode: data_replay_mode }),
    setDataReplaySpeed: (data_replay_speed) =>
      set({ dataReplaySpeed: data_replay_speed }),

    clearTaxiFleetMetrics: () => set({ taxiFleetMetrics: null }),
    clearTotalTaxiFleetSize: () => set({ totalTaxiFleetSize: 0 }),
    clearDataReplayMode: () => set({ totalTaxiFleetSize: 0 }),
    clearDataReplaySpeed: () => set({ totalTaxiFleetSize: 0 }),
  })
);
