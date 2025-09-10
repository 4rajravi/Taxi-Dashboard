import { create } from "zustand";

type EventLatency = {
  time: string;
  event_latency_in_seconds: number;
};

type SpeedTrend = {
  time: string;
  speed_in_km_per_hour: number;
};

type AverageSpeedTrend = {
  time: string;
  average_speed_in_km_per_hour: number;
};

type IncidentsTrend = {
  time: string;
  geofence_violation_count: number;
  speed_violation_count: number;
};

type TaxiAnalyticsData = {
  event_latency_trend: EventLatency[];
  speed_trend: SpeedTrend[];
  average_speed_trend: AverageSpeedTrend[];
  incidents_trend: IncidentsTrend[];
};

type TaxiAnalyticsDataStore = {
  taxiAnalyticsDataById: Record<string, TaxiAnalyticsData | null>;
  setTaxiAnalyticsData: (taxiId: string, taxiAnalyticsData: TaxiAnalyticsData) => void;
  clearTaxiAnalyticsData: (taxiId: string) => void;
};

export const useTaxiAnalyticsDataStore = create<TaxiAnalyticsDataStore>(
  (set) => ({
    taxiAnalyticsDataById: {},
    setTaxiAnalyticsData: (taxiId, taxiAnalyticsData) =>
      set((state) => ({
        taxiAnalyticsDataById: {
          ...state.taxiAnalyticsDataById,
          [taxiId]: taxiAnalyticsData,
        },
      })),
    clearTaxiAnalyticsData: (taxiId) =>
      set((state) => {
        const { [taxiId]: _, ...rest } = state.taxiAnalyticsDataById;
        return { taxiAnalyticsDataById: rest };
      }),
  })
);
