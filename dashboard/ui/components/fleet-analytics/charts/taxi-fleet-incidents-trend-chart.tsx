"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

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
  "An interactive stacked bar chart with legend for taxi fleet incidents trend";

const chartConfig = {
  geofence_violation_count: {
    label: "Geofence Violations",
    color: "var(--chart-6)",
  },
  speed_violation_count: {
    label: "Speed Violations",
    color: "var(--chart-5)",
  },
} satisfies ChartConfig;

export default function TaxiFleetIncidentsTrendChart({
  taxiFleetIncidentTrendChartData,
}: {
  taxiFleetIncidentTrendChartData: Array<{
    time: string;
    geofence_violation_count: number;
    speed_violation_count: number;
  }>;
}) {
  return (
    <Card className="py-4">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1">
          <CardTitle className="text-md">Taxi Incidents Trend</CardTitle>
          <CardDescription className="text-xs">
            Taxi Fleet incidents trend over time
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig}>
          <BarChart
            accessibilityLayer
            data={taxiFleetIncidentTrendChartData}
            barCategoryGap="20%"
            maxBarSize={40}
            layout="horizontal"
            width={40}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="time"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
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
              tickMargin={8}
              tickFormatter={(value) => `${value}`}
            />
            <ChartTooltip
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
            <ChartLegend content={<ChartLegendContent />} />
            <Bar
              dataKey="geofence_violation_count"
              stackId="a"
              fill="var(--color-geofence_violation_count)"
              radius={[0, 0, 4, 4]}
            />
            <Bar
              dataKey="speed_violation_count"
              stackId="a"
              fill="var(--color-speed_violation_count)"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
