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
  "An interactive area chart for taxi average speed trends";

export default function TaxiAverageSpeedTrendChart({
  taxiId,
  taxiAverageSpeedTrendChartData,
}: {
  taxiId: number;
  taxiAverageSpeedTrendChartData: Array<{
    time: string;
    average_speed_in_km_per_hour: number;
  }>;
}) {
  const taxiAverageSpeedTrendChartConfig = {
    average_speed_in_km_per_hour: {
      label: "Average Speed (km/h)",
      color: "var(--chart-2)",
    },
  } satisfies ChartConfig;

  return (
    <Card className="pt-0 pb-4">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle className="text-md">
            Average Speed Trends
          </CardTitle>
          <CardDescription className="text-xs">
            Taxi <span className="font-semibold text-slate-900">{taxiId}</span> average speed trends over time
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-2 sm:pt-4">
        <ChartContainer
          config={taxiAverageSpeedTrendChartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart accessibilityLayer data={taxiAverageSpeedTrendChartData}>
            <defs>
              <linearGradient id="fillAverageSpeed" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor="var(--color-average_speed_in_km_per_hour)"
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor="var(--color-average_speed_in_km_per_hour)"
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
              dataKey="average_speed_in_km_per_hour"
              tickLine={false}
              axisLine={false}
              tickMargin={2}
              tickFormatter={(value) => `${value} km/h`}
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
              dataKey="average_speed_in_km_per_hour"
              type="natural"
              fill="url(#fillAverageSpeed)"
              stroke="var(--color-average_speed_in_km_per_hour)"
              stackId="a"
            />
            <ChartLegend content={<ChartLegendContent />} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
