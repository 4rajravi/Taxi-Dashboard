"use client";

import Image from "next/image";

import { AppSidebar } from "@/components/incidents/incident-sidebar";
import { Label } from "@/components/ui/label";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";

import { useTaxiFleetMetricsStore } from "@/stores/use-taxi-fleet-metrics-store";
import { ChartNoAxesCombined } from "lucide-react";
import Link from "next/link";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const totalTaxiFleetSize = useTaxiFleetMetricsStore(
    (state) => state.totalTaxiFleetSize
  );

  const dataReplayMode = useTaxiFleetMetricsStore(
    (state) => state.dataReplayMode
  );
  const dataReplaySpeed = useTaxiFleetMetricsStore(
    (state) => state.dataReplaySpeed
  );

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "23rem",
          "--sidebar-width-mobile": "23rem",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <div className="flex flex-col h-screen w-full">
        <div className="h-12 flex items-center justify-between px-4 bg-white shrink-0">
          <div className="flex items-center gap-2">
            <SidebarTrigger className="text-slate-500 h-5 w-5" />
            <h5 className="text-m font-semibold">
              Real-Time Traffic Monitoring
            </h5>
            <Label className="text-xs font-normal hidden sm:flex flex-row items-center gap-1">
              <span>
                Taxi Fleet Size{" "}
                <span className="bg-indigo-500 text-white rounded-full py-1 px-2">
                  {totalTaxiFleetSize}
                </span>
              </span>
              <span>
                Replay Mode{" "}
                <span className="bg-gray-900 text-white rounded-full py-1 px-2">
                  {dataReplayMode.charAt(0).toUpperCase() +
                    dataReplayMode.slice(1)}
                </span>
              </span>
              <span>
                Replay Speed{" "}
                <span className="bg-gray-900 text-white rounded-full py-1 px-2">
                  {dataReplaySpeed}x
                </span>
              </span>
            </Label>
          </div>
          <div className="flex flex-row gap-2 items-center hidden sm:flex">
            <Tooltip>
              <TooltipTrigger asChild>
                <Link
                  href="/analytics/fleet/"
                  passHref
                  target="_blank"
                  className="flex flex-row items-center gap-1 text-xs font-normal text-slate-950 cursor-pointer"
                  style={{
                  display: "flex",
                  alignItems: "center",
                  }}
                >
                  <ChartNoAxesCombined
                  height={20}
                  width={20}
                  />
                  Fleet Analytics
                </Link>
              </TooltipTrigger>
              <TooltipContent>Taxi Fleet Analytics</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex flex-row gap-1 text-xs font-normal text</svg>-slate-950 cursor-pointer">
                  <a
                    href="http://localhost:8088/"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      cursor: "pointer",
                      textDecoration: "none",
                      color: "inherit",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    <Image
                      src="/apache-kafka-icon.png"
                      alt="Apache Kafka Icon"
                      width={25}
                      height={25}
                    />
                    Kafka UI
                  </a>
                </div>
              </TooltipTrigger>
              <TooltipContent>Kafka UI Dashboard</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex flex-row gap-1 text-xs font-normal text-slate-950 cursor-pointer">
                  <a
                    href="http://localhost:8081/"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      cursor: "pointer",
                      textDecoration: "none",
                      color: "inherit",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.3rem",
                    }}
                  >
                    <Image
                      src="/apache-flink-icon.png"
                      alt="Apache Flink Icon"
                      width={19}
                      height={19}
                    />
                    Flink UI
                  </a>
                </div>
              </TooltipTrigger>
              <TooltipContent>Apache Flink UI Dashboard</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex flex-row gap-1 text-xs font-normal text-slate-950 cursor-pointer">
                  {/* <ChartNoAxesColumnDecreasing className="h-4 w-4" /> */}
                  <a
                    href="http://localhost:8086/"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      cursor: "pointer",
                      textDecoration: "none",
                      color: "inherit",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.3rem",
                    }}
                  >
                    <Image
                      src="/influxdb-icon.png"
                      alt="InfluxDB Icon"
                      width={19}
                      height={19}
                    />
                    InfluxDB
                  </a>
                </div>
              </TooltipTrigger>
              <TooltipContent>InfluxDB Dashboard</TooltipContent>
            </Tooltip>
          </div>
        </div>
        <Label className="text-xs font-normal block sm:hidden px-4 mb-2">
          <span>
            Fleet Size{" "}
            <span className="bg-indigo-500 text-white rounded-full py-1 px-2">
              {totalTaxiFleetSize}
            </span>
          </span>
          <span>
            {" "}
            Mode{" "}
            <span className="bg-gray-900 text-white rounded-full py-1 px-2">
              {dataReplayMode.charAt(0).toUpperCase() + dataReplayMode.slice(1)}
            </span>
          </span>
          <span>
            {" "}
            Speed{" "}
            <span className="bg-gray-900 text-white rounded-full py-1 px-2">
              {dataReplaySpeed}x
            </span>
          </span>
        </Label>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </SidebarProvider>
  );
}
