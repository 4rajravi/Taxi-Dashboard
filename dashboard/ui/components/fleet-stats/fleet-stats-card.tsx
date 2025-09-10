import { TrendingUp, TrendingDown } from "lucide-react";
import CountUp from "react-countup";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { formatKmDistance } from "@/lib/utils";

// Props type for StatsCard
type Stats = {
  label: string;
  previousValue: number;
  currentValue: number;
  trend: string | number;
  trendPositive: boolean;
  cardTheme: string;
};

// StatsCard displays a stat with trend indicator and label
export default function FleetStatsCard({
  label,
  previousValue,
  currentValue,
  trend,
  trendPositive,
  cardTheme,
}: Stats) {
  // Set icon and badge color based on trend
  const TrendIcon =
    trend == "0%" ? () => null : trendPositive ? TrendingUp : TrendingDown;
  const badgeColor =
    trend == "0%"
      ? "text-slate-800 group-hover:text-white p-0"
      : trendPositive
      ? "text-green-500 p-0"
      : "text-red-500 p-0";

  return (
    <Card
      className={`w-full ${cardTheme} border border-slate-200 hover:bg-slate-950 hover:text-white fleet-stats-card group transition-transform duration-750 ease-in-out transform hover:scale-103`}
    >
      <CardContent className="p-4">
        {/* Stat label */}
        <div className="text-xs mb-1 fleet-stats-card-label">{label}</div>
        {/* Stat value */}
        <div className="text-4xl font-bold pb-2 w-full">
          {label === "Total Distance Run (km)" ? (
            <CountUp
              start={previousValue}
              end={currentValue}
              decimals={2}
              formattingFn={formatKmDistance}
            >
              {({ countUpRef }) => (
                <div>
                  <span ref={countUpRef} />
                </div>
              )}
            </CountUp>
          ) : (
            <CountUp start={previousValue} end={currentValue} delay={0}>
              {({ countUpRef }) => (
                <div>
                  <span ref={countUpRef} />
                </div>
              )}
            </CountUp>
          )}
        </div>
        {/* Trend badge with icon */}
        <Badge
          variant={trendPositive ? "default" : "destructive"}
          className={`rounded-xl ${badgeColor} bg-tansparent font-bold`}
        >
          <TrendIcon className="w-4 h-4" />
          {trend}
        </Badge>
        {/* Time reference */}
        <span className="text-xs ml-2 fleet-stats-card-label">
          from last 5 seconds
        </span>
      </CardContent>
    </Card>
  );
}
