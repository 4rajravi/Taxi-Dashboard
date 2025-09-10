"use client";

import { toast } from "sonner";
import { useEffect, useState } from "react";

import { CircleCheckIcon } from "lucide-react";
import { Label } from "@radix-ui/react-label";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { useLoadAllIncidents } from "@/hooks/use-fetch-all-incidents";
import { useIncidentsDataStore } from "@/stores/use-incidents-data-store";

export default function IncidentHistory() {
  const [refreshFlag, setRefreshFlag] = useState(false);
  const { fetchSucceeded } = useLoadAllIncidents(refreshFlag);

  const handleRefresh = () => {
    setRefreshFlag((prev) => !prev);
  };

  const allIncidents = useIncidentsDataStore((state) => state.allIncidents);

  useEffect(() => {
    if (fetchSucceeded) {
      toast.dismiss(); // Hide any existing toasts
      toast(
        <div className="flex flex-row">
          <CircleCheckIcon className="text-green-500 w-5 h-5 mr-2" />
          Latest Incident Data Fetched Successfully!
        </div>,
        {
          duration: 2000,
          position: "top-center",
        }
      );
    }
  }, [fetchSucceeded]);

  return (
    <div className="py-4">
      {!fetchSucceeded && <div>Loading incidents...</div>}
      {fetchSucceeded && (
        <>
          {Object.entries(allIncidents).length > 0 && (
            <div>
              <div className="py-4 mb-4 flex items-center justify-between">
                <div>
                  <Label className="text-slate-500 text-lg mr-4">
                    Total Incidents:
                    <span className="text-slate-950 font-semibold ml-1">
                      {Object.entries(allIncidents).length}
                    </span>
                  </Label>
                  <Label className="text-slate-500 text-lg mr-4">
                    Geofence Violations:
                    <span className="text-slate-950 font-semibold ml-1">
                      {
                        Object.values(allIncidents).filter(
                          (incident) =>
                            incident.alert_type === "GEOFENCE_VIOLATION"
                        ).length
                      }
                    </span>
                  </Label>
                  <Label className="text-slate-500 text-lg mr-4">
                    Speed Violations:
                    <span className="text-slate-950 font-semibold ml-1">
                      {
                        Object.values(allIncidents).filter(
                          (incident) =>
                            incident.alert_type === "SPEED_VIOLATION"
                        ).length
                      }
                    </span>
                  </Label>
                </div>
                <Button className="cursor-pointer" onClick={handleRefresh}>
                  Refresh Incidents
                </Button>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[72px]">Taxi ID</TableHead>
                    <TableHead className="w-[36%]">Event</TableHead>
                    <TableHead className="whitespace-nowrap">
                      Timestamp
                    </TableHead>
                    <TableHead className="whitespace-nowrap">
                      Actual Event Time
                    </TableHead>
                    <TableHead className="whitespace-nowrap">
                      Current Coordinates [Lat, Lng]
                    </TableHead>
                    <TableHead className="whitespace-nowrap">
                      Taxi Status
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {allIncidents &&
                    Object.entries(allIncidents).map(([key, incident]) => (
                      <TableRow key={key} className="h-12">
                        <TableCell className="w-[72px] font-medium">
                          <span className="font-normal text-xs bg-slate-950 px-2 text-white rounded-2xl">
                            {incident.taxi_id}
                          </span>
                        </TableCell>
                        <TableCell className="w-[36%]">
                          {incident.alert_type == "GEOFENCE_VIOLATION" && (
                            <>
                              <span className="font-normal text-xs bg-indigo-50 text-indigo-500 px-2 py-1 mr-1 rounded-full">
                                geofence_violation
                              </span>
                              <span>
                                Taxi is{" "}
                                <span className="font-bold">
                                  {incident.distance_km}
                                </span>{" "}
                                km away from city center.
                              </span>
                            </>
                          )}
                          {incident.alert_type == "SPEED_VIOLATION" && (
                            <>
                              <span className="font-normal text-xs bg-orange-50 text-orange-500 px-2 py-1 mr-1 rounded-full">
                                speed_violation
                              </span>
                              <span>
                                Taxi is driving at{" "}
                                <span className="font-bold">
                                  {incident.speed}
                                </span>{" "}
                                km/h.
                              </span>
                            </>
                          )}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {incident.updated_at}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {incident.timestamp}
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          <span className="font-normal text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                            {incident.longitude}
                          </span>
                          <span className="font-normal text-xs bg-gray-100 text-gray-700 px-2 py-1 ml-1 rounded-full">
                            {incident.latitude}
                          </span>
                        </TableCell>
                        <TableCell className="whitespace-nowrap">
                          {incident.trip_status}
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </div>
          )}
          {Object.entries(allIncidents).length == 0 && (
            <div>No Incidents Found.</div>
          )}
        </>
      )}
    </div>
  );
}
