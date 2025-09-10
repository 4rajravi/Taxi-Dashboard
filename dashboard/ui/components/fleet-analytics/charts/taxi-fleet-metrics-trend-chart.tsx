import React from "react";

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

export const description =
  "An interactive area chart for taxi fleet metrics trends";

export default function TaxiFleetMetricsTrendChart({
  taxiFleetMetricsTrendChartData,
}: {
  taxiFleetMetricsTrendChartData: Array<{
    time: string;
    active_taxis_count: number;
    in_transit_taxis_count: number;
    trip_ended_taxis_count: number;
  }>;
}) {
  const taxiFleetMetricsTrendChartConfig = {
    active_taxis_count: {
      label: "Active Taxis",
      color: "var(--chart-2)",
    },
    in_transit_taxis_count: {
      label: "In Transit Taxis",
      color: "var(--chart-3)",
    },
    trip_ended_taxis_count: {
      label: "Trip Ended Taxis",
      color: "var(--chart-4)",
    },
  } satisfies ChartConfig;

  return (
    <Card className="pt-0 pb-4">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle className="text-md">
            Taxi Fleet Metrics Trends
          </CardTitle>
          <CardDescription className="text-xs">
            Taxi fleet metrics trends over time, including active taxis, in transit taxis, and trip ended taxis.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-2 sm:pt-4">
        <ChartContainer
          config={taxiFleetMetricsTrendChartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart accessibilityLayer data={taxiFleetMetricsTrendChartData}>
            <defs>
              <linearGradient id="fillActiveTaxisCount" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-active_taxis_count)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-active_taxis_count)"
                  stopOpacity={0.1}
                />
              </linearGradient>
              <linearGradient id="fillInTransitTaxisCount" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-in_transit_taxis_count)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-in_transit_taxis_count)"
                  stopOpacity={0.1}
                />
              </linearGradient>
              <linearGradient id="fillTripEndedTaxisCount" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-trip_ended_taxis_count)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-trip_ended_taxis_count)"
                  stopOpacity={0.1}
                />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="time"
              tickLine={false}
              axisLine={false}
              tickMargin={2}
              minTickGap={8}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                });
              }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={2}
              tickFormatter={(value) => `${value}`}
            />

            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value, payload) => {
                    const timestamp = payload?.[0]?.payload?.time;
                    return new Date(timestamp)
                      .toLocaleString("en-US", {
                        year: "numeric",
                        month: "2-digit",
                        day: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                        timeZoneName: "short",
                      })
                      .replace(",", "")
                      .replace(/(\d{2})\/(\d{2})\/(\d{4})/, "$3-$1-$2");
                  }}
                  indicator="dot"
                />
              }
            />
            <Area
              dataKey="active_taxis_count"
              type="natural"
              fill="url(#fillActiveTaxisCount)"
              stroke="var(--color-active_taxis_count)"
              strokeWidth={1}
              fillOpacity={0.5}
            />
            <Area
              dataKey="in_transit_taxis_count"
              type="natural"
              fill="url(#fillInTransitTaxisCount)"
              stroke="var(--color-in_transit_taxis_count)"
              strokeWidth={1}
              fillOpacity={0.5}
            />
            <Area
              dataKey="trip_ended_taxis_count"
              type="natural"
              fill="url(#fillTripEndedTaxisCount)"
              stroke="var(--color-trip_ended_taxis_count)"
              strokeWidth={1}
              fillOpacity={0.5}
            />
            <ChartLegend content={<ChartLegendContent />} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
