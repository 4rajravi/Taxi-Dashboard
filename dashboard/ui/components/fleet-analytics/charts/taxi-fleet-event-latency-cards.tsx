import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

interface LatencyData {
  latency_in_seconds: number;
  change_from_last_5s_percent: number;
}

interface TaxiFleetEventLatencyCardsProps {
  taxiFleetEventLatencyTrend: {
    max: LatencyData;
    min: LatencyData;
    mean: LatencyData;
  };
}

export default function TaxiFleetEventLatencyCards({
  taxiFleetEventLatencyTrend,
}: TaxiFleetEventLatencyCardsProps) {
  const formatLatency = (seconds: number | null) => {
    if (seconds === null) {
      return "N/A";
    }
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(0)}ms`;
    }
    return `${seconds.toFixed(2)}s`;
  };

  const formatPercentage = (percent: number | null) => {
    if (percent === null || percent === undefined) {
      return "0.0%";
    }
    const sign = percent > 0 ? "+" : "";
    return `${sign}${percent.toFixed(1)}%`;
  };

  const getTrendIcon = (percent: number) => {
    if (percent > 0) {
      return (
        <span className="bg-red-50 px-2 rounded-full py-1">
          <TrendingUp className="h-4 w-4 text-red-500" />
        </span>
      );
    } else if (percent < 0) {
      return (
        <span className="bg-green-50 px-2 rounded-full py-1">
          <TrendingDown className="h-4 w-4 text-green-500" />
        </span>
      );
    }
    return (
      <span className="bg-slate-50 px-2 rounded-full py-1">
        <span className="text-slate-500 bg-gray-50 px-2 py-1 text-xs">N/A</span>
      </span>
    );
  };

  const getTrendColor = (percent: number) => {
    if (percent > 0) return "text-red-500";
    if (percent < 0) return "text-green-500";
    return "text-slate-500";
  };

  const cards = [
    {
      title: "Max Latency",
      description: "Highest Event Processing Latency in Seconds",
      data: taxiFleetEventLatencyTrend.max,
    },
    {
      title: "Min Latency",
      description: "Lowest Event Processing Latency in Seconds",
      data: taxiFleetEventLatencyTrend.min,
    },
    {
      title: "Average Latency",
      description: "Average Event Processing Latency in Seconds",
      data: taxiFleetEventLatencyTrend.mean,
    },
  ];

  return (
    <div className="border rounded-xl p-6">
      <div className="mb-4">
      <h4 className="font-semibold">Taxi Fleet Event Latency Trends</h4>
      <span className="text-xs text-gray-500">Taxi fleet event processing latency trends over the last 5 minutes</span>
      </div>
      <div className="grid gap-4 md:grid-cols-3 grid-cols-1">
        {cards.map((card, index) => (
          <Card key={index} className="py-4">
            <CardContent>
              <div className="flex flex-row items-center justify-between space-y-0 pb-2">
                <h4 className="text-sm font-medium">{card.title}</h4>
                {getTrendIcon(card.data.change_from_last_5s_percent)}
              </div>
              <div className="text-2xl font-bold">
                {formatLatency(card.data.latency_in_seconds)}
              </div>
              <p className="text-xs text-muted-foreground">
                {card.description}
              </p>
              <div className="flex items-center pt-1">
                <span
                  className={`text-xs font-medium ${getTrendColor(
                    card.data.change_from_last_5s_percent
                  )}`}
                >
                  {formatPercentage(card.data.change_from_last_5s_percent)}
                </span>
                <span className="text-xs text-muted-foreground ml-1">
                  from last 5s
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
