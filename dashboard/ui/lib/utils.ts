import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Combines class names and merges Tailwind classes to avoid conflicts
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(...inputs));
}

// Formats a number as a distance in km, using K, M, or B suffixes
export function formatKmDistance(value: number): string {
  if (value < 1_000) return `${value}`; // Less than 1,000: show as is
  if (value < 1_000_000) return `${(value / 1_000).toFixed(1)}K`; // Thousands
  if (value < 1_000_000_000) return `${(value / 1_000_000).toFixed(1)}M`; // Millions
  return `${(value / 1_000_000_000).toFixed(1)}B`; // Billions
}

interface TripStatusBadgeTheme {
  statusBadgeLabel: string;
  statusBadgeTheme: string;
}

// Returns label and theme classes for a trip status badge
export function getTripStatusBadgeTheme(
  trip_status?: string,
  speed?: number
): TripStatusBadgeTheme {
  switch (trip_status) {
    case "active":
      let label = "Connected";
      if (speed !== undefined && speed === 0) {
        return {
          statusBadgeLabel: label,
          statusBadgeTheme:
            "bg-emerald-50 text-emerald-400 rounded-2xl px-4 py-1 font-normal",
        };
      }
      if (speed !== undefined && speed > 0) {
        label = "In Transit";
        return {
          statusBadgeLabel: label,
          statusBadgeTheme:
            "bg-blue-50 text-blue-400 rounded-2xl px-4 py-1 font-normal",
        };
      }
    case "inactive":
      return {
        statusBadgeLabel: "Reconnecting...",
        statusBadgeTheme:
          "bg-blue-50 text-blue-400 rounded-2xl px-4 py-1 font-normal",
      };
    case "end":
      return {
        statusBadgeLabel: "Trip Complete",
        statusBadgeTheme:
          "bg-gray-100 text-slate-400 rounded-2xl px-4 py-1 font-normal",
      };
    default:
      return {
        statusBadgeLabel: "Status Unknown",
        statusBadgeTheme:
          "bg-gray-100 text-neutral-400 rounded-2xl px-4 py-1 font-normal",
      };
  }
}

interface TaxiSpeedTheme {
  taxiSpeedTheme: string;
}

// Returns theme classes for taxi speed based on validity and trip status
export function getTaxiSpeedTheme(
  trip_status?: string,
  speed?: number
): TaxiSpeedTheme {
  // If trip is inactive, ended, or not available, use neutral color
  if (
    trip_status === "inactive" ||
    trip_status === "end" ||
    trip_status === "N/A"
  ) {
    return { taxiSpeedTheme: "" };
  }

  // Color based on speed value
  if (speed !== undefined && speed > 0 && speed <= 50) {
    return { taxiSpeedTheme: "text-emerald-500" }; // Speed in safe range > 0 & <= 50
  } else if (speed !== undefined && speed > 50) {
    return { taxiSpeedTheme: "text-red-500" }; // Speed too high > 0
  } else {
    return { taxiSpeedTheme: "text-slate-800" }; // Zero or undefined
  }
}

interface DistanceFromCityCenterTheme {
  distanceFromCityCenterTheme: string;
}

// Returns theme classes for taxi speed based on validity and trip status
export function getDistanceFromCityCenterTheme(
  distance_from_forbidden_city_km?: number
): DistanceFromCityCenterTheme {
  // Color based on distance_from_forbidden_city_km value
  if (
    distance_from_forbidden_city_km !== undefined &&
    distance_from_forbidden_city_km > 10 &&
    distance_from_forbidden_city_km <= 15
  ) {
    return { distanceFromCityCenterTheme: "text-yellow-500" }; // distance_from_forbidden_city_km in safe range <=10
  } else if (
    distance_from_forbidden_city_km !== undefined &&
    distance_from_forbidden_city_km > 15
  ) {
    return { distanceFromCityCenterTheme: "text-orange-500" }; // distance_from_forbidden_city_km in safe range <=10
  } else {
    return { distanceFromCityCenterTheme: "text-slate-800" }; // Zero or undefined
  }
}
