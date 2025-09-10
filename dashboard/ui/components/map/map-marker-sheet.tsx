"use client";

import {
  GaugeIcon,
  RouteIcon,
  CarTaxiFrontIcon,
  MapPinnedIcon,
  RadiusIcon,
  ChartNoAxesCombined,
  ClockIcon,
  ArrowRightIcon,
} from "lucide-react";
import Link from "next/link";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

import { Taxi } from "@/stores/use-taxi-data-store";
import {
  getTripStatusBadgeTheme,
  getTaxiSpeedTheme,
  getDistanceFromCityCenterTheme,
} from "@/lib/utils";

type MapTaxiSheetProps = {
  taxi: Taxi | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onClose?: () => void;
};

export function MapTaxiSheet({
  taxi,
  open,
  onOpenChange,
  onClose,
}: MapTaxiSheetProps) {
  if (!taxi) return null;

  // Check if object has latitude and longitude properties
  const hasCoordinates = (
    obj: unknown
  ): obj is { latitude: number; longitude: number } =>
    !!obj &&
    typeof obj === "object" &&
    obj !== null &&
    "latitude" in obj &&
    typeof (obj as { latitude: unknown }).latitude === "number" &&
    "longitude" in obj &&
    typeof (obj as { longitude: unknown }).longitude === "number";

  // Check if object has timestamp property
  const hasTimestamp = (obj: unknown): obj is { timestamp: string } =>
    !!obj &&
    typeof obj === "object" &&
    "timestamp" in obj &&
    typeof (obj as { timestamp: unknown }).timestamp === "string";

  // Check if object has trip_status property
  const hasTripStatus = (obj: unknown): obj is { trip_status: string } =>
    !!obj &&
    typeof obj === "object" &&
    "trip_status" in obj &&
    typeof (obj as { trip_status: unknown }).trip_status === "string";

  // Check if object has speed property
  const hasSpeed = (obj: unknown): obj is { speed: number } =>
    !!obj &&
    typeof obj === "object" &&
    "speed" in obj &&
    typeof (obj as { speed: unknown }).speed === "number";

  // Check if object has speed property
  const hasDistanceFromCityCenter = (
    obj: unknown
  ): obj is { distance_from_forbidden_city_km: number } =>
    !!obj &&
    typeof obj === "object" &&
    "distance_from_forbidden_city_km" in obj &&
    typeof (obj as { distance_from_forbidden_city_km: unknown })
      .distance_from_forbidden_city_km === "number";

  // Check if object has avg_speed property
  const hasAverageSpeed = (obj: unknown): obj is { avg_speed: number } =>
    !!obj &&
    typeof obj === "object" &&
    "avg_speed" in obj &&
    typeof (obj as { avg_speed: unknown }).avg_speed === "number";

  // Check if object has total_distance_km property
  const hasTotalDistance = (
    obj: unknown
  ): obj is { total_distance_km: number } =>
    !!obj &&
    typeof obj === "object" &&
    obj !== null &&
    "total_distance_km" in obj &&
    typeof (obj as { total_distance_km: unknown }).total_distance_km ===
      "number";

  // Check if object has speed property
  const hasMsgSentUtcTimestamp = (
    obj: unknown
  ): obj is { sent_at_utc_ms: number } =>
    !!obj &&
    typeof obj === "object" &&
    "sent_at_utc_ms" in obj &&
    typeof (obj as { sent_at_utc_ms: unknown }).sent_at_utc_ms === "number";

  // Extract coordinates from taxi if available, otherwise default to (0, 0)
  const coordinates = hasCoordinates(taxi)
    ? { latitude: taxi.latitude, longitude: taxi.longitude }
    : { latitude: 0, longitude: 0 };

  // Get badge label and theme for trip status
  const { statusBadgeLabel, statusBadgeTheme } = getTripStatusBadgeTheme(
    hasTripStatus(taxi) ? taxi.trip_status : "N/A",
    hasSpeed(taxi) ? taxi.speed : 0.0
  );

  // Get theme for taxi speed display
  const { taxiSpeedTheme } = getTaxiSpeedTheme(
    hasTripStatus(taxi) ? taxi.trip_status : "N/A",
    hasSpeed(taxi) ? taxi.speed : 0.0
  );

  // Get theme for taxi distance from city center
  const { distanceFromCityCenterTheme } = getDistanceFromCityCenterTheme(
    hasDistanceFromCityCenter(taxi) ? taxi.distance_from_forbidden_city_km : 0.0
  );

  const taxiInfoBaseClass = "border border-slate-200 rounded-2xl p-4";
  const taxiInfoLabelClass =
    "flex flex-row space-x-2 text-slate-500 text-xs font-normal";
  const taxiInfoValueClass =
    "scroll-m-20 text-xl font-semibold tracking-tight mt-1";

  // Formats a UTC timestamp into a relative time string (e.g., "5 minutes ago")
  function formatTimeAgo(sent_at_utc_ms: number): React.ReactNode {
    const now = Date.now();
    const diffMs = now - sent_at_utc_ms;
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) return `${diffSec} seconds ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin} minutes ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr} hours ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay} days ago`;

    return new Date(sent_at_utc_ms).toLocaleString();
  }

  // Formats a UTC timestamp (in milliseconds) into a human-readable date-time string
  function formatUtcTimestamp(time_ms: number): React.ReactNode {
    if (!time_ms) return "N/A";
    const date = new Date(time_ms);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(
      2,
      "0"
    )}-${String(date.getDate()).padStart(2, "0")} ${String(
      date.getHours()
    ).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}:${String(
      date.getSeconds()
    ).padStart(2, "0")}`;
  }

  function calculateTimeDifferenceInSeconds(
    timestamp_b: number,
    timestamp_a: number
  ): React.ReactNode {
    if (!timestamp_b || !timestamp_a) return "N/A";
    const differenceInSeconds = (timestamp_b - timestamp_a) / 1000;
    return differenceInSeconds >= 0
      ? `${differenceInSeconds.toFixed(3)}s`
      : "Invalid timestamps";
  }

  return (
    <Sheet
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen && onClose) {
          onClose();
        }
      }}
    >
      <SheetContent
        aria-describedby="Taxi Details"
        aria-description="Taxi Details"
        side="right"
        className="w-[400px] sm:w-[400px]"
      >
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <CarTaxiFrontIcon className="text-2xl" />
            Taxi{" "}
            <Badge className="bg-slate-950 rounded-full">{taxi.taxi_id}</Badge>
            <Badge className={statusBadgeTheme}>{statusBadgeLabel}</Badge>
          </SheetTitle>
          <SheetDescription></SheetDescription>
        </SheetHeader>
        {hasMsgSentUtcTimestamp(taxi) && (
          <label className="text-slate-400 text-xs font-normal px-4">
            Lastest Update: {formatTimeAgo(taxi.processed_at_utc_ms)}
          </label>
        )}
        <div className="flex flex-col space-y-2 rounded-xl px-4">
          {/* Current or last location */}
          <div className={`${taxiInfoBaseClass}`}>
            <div className={`${taxiInfoLabelClass}`}>
              <MapPinnedIcon className="mr-1 text-slate-800" size={18} />
              {hasTripStatus(taxi) &&
              (taxi.trip_status === "inactive" || taxi.trip_status === "end")
                ? "Last Location"
                : "Current Location"}
            </div>
            <h4 className={`${taxiInfoValueClass} text-slate-800`}>
              {coordinates.latitude}, {coordinates.longitude}
            </h4>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {/* Current speed */}
            <div className={`${taxiInfoBaseClass}`}>
              <div className={`${taxiInfoLabelClass}`}>
                <GaugeIcon className="mr-1 text-slate-800" size={18} /> Current
                Speed
              </div>
              <h4 className={`${taxiSpeedTheme} ${taxiInfoValueClass}`}>
                {hasAverageSpeed(taxi) &&
                hasTripStatus(taxi) &&
                hasSpeed(taxi) &&
                taxi.trip_status === "active"
                  ? `${taxi.speed} km/h`
                  : "N/A"}
              </h4>
            </div>
            {/* Average speed */}
            <div className={`${taxiInfoBaseClass}`}>
              <div className={`${taxiInfoLabelClass}`}>
                <ChartNoAxesCombined
                  className="mr-1 text-slate-800"
                  size={18}
                />{" "}
                Average Speed
              </div>
              <h4 className={`${taxiInfoValueClass} text-slate-800`}>
                {hasAverageSpeed(taxi) &&
                hasTripStatus(taxi) &&
                taxi.trip_status === "active"
                  ? `${taxi.avg_speed} km/h`
                  : "N/A"}
              </h4>
            </div>
          </div>
          {/* Total distance */}
          <div className={`${taxiInfoBaseClass}`}>
            <div className={`${taxiInfoLabelClass}`}>
              <RouteIcon className="mr-1 text-slate-800" size={16} /> Distance
              Run
            </div>
            <h4 className={`${taxiInfoValueClass} text-slate-800`}>
              {hasTotalDistance(taxi) ? `${taxi.total_distance_km} km` : "N/A"}
            </h4>
          </div>
          {/* Distance from city center */}
          <div className={`${taxiInfoBaseClass}`}>
            <div className={`${taxiInfoLabelClass}`}>
              <RadiusIcon className="mr-1 text-slate-800" size={18} /> Distance
              from City Center
            </div>
            <h4
              className={`${distanceFromCityCenterTheme} ${taxiInfoValueClass}`}
            >
              {hasDistanceFromCityCenter(taxi)
                ? `${taxi.distance_from_forbidden_city_km} km`
                : "N/A"}
            </h4>
          </div>
        </div>
        <div className="px-4">
          <div className={`${taxiInfoBaseClass}`}>
            <div className={`${taxiInfoLabelClass} mb-2`}>
              <ClockIcon className="mr-1 text-slate-800" size={18} />
              Timestamps and Latency Details
            </div>
            <div className="py-2">
              <div className="text-slate-800 text-xs font-semibold mb-4">
                Actual Event Time:{" "}
                <span className="bg-gray-100 text-slate-600 px-2 py-1 font-normal rounded-full">
                  {hasTimestamp(taxi) ? taxi.timestamp : "N/A"}
                </span>
              </div>
              <div className="text-slate-800 text-xs font-normal mb-2">
                Event Published to Kafka Time:{" "}
                <span className="bg-gray-100 text-slate-600 px-2 py-1 rounded-full">
                  {hasTimestamp(taxi)
                    ? formatUtcTimestamp(taxi.sent_at_utc_ms)
                    : "N/A"}
                </span>
              </div>
              <div className="text-slate-800 text-xs font-normal mb-2">
                Event Processed by Flink Time:{" "}
                <span className="bg-gray-100 text-slate-600 px-2 py-1 rounded-full">
                  {hasTimestamp(taxi)
                    ? formatUtcTimestamp(taxi.processed_at_utc_ms)
                    : "N/A"}
                </span>
              </div>
            </div>
            <Label className="font-light text-md mb-2">
              Event Latency:
              <span className="font-semibold">
                <span className="font-bold">
                  {calculateTimeDifferenceInSeconds(
                    taxi.processed_at_utc_ms,
                    taxi.sent_at_utc_ms
                  )}
                </span>
              </span>
            </Label>
            <Label className="text-xs text-slate-500 font-normal mb-1">
              Latency = T2 - T1
            </Label>
            <Label className="text-xs text-slate-400 font-light">
              T2: Message Processed and Sent by Flink Time
            </Label>
            <Label className="text-xs text-slate-400 font-light">
              T1: Message Published to Kafka Time
            </Label>
          </div>
          <Link
            href={{
              pathname: "/analytics",
              query: { taxi_id: taxi.taxi_id },
            }}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button
              variant="link"
              className="text-indigo-500 cursor-pointer mt-4"
            >
              View Taxi Trends Analytics
              <ArrowRightIcon />
            </Button>
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  );
}
