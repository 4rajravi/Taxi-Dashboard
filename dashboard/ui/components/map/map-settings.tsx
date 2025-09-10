"use client";

import * as React from "react";

import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetClose,
  SheetDescription,
  SheetFooter,
  SheetTitle,
} from "@/components/ui/sheet";
import { Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

type MapSettingsProps = {
  onSave: (settings: {
    viewStationaryTaxis: boolean;
    viewInTransitTaxis: boolean;
    viewTripEndedTaxis: boolean;
    viewOutsideGeofence: boolean;
    viewGeofence10km: boolean;
    viewGeofence15km: boolean;
  }) => void;
};

export function MapSettings({ onSave }: MapSettingsProps) {
  const [viewStationaryTaxis, setViewStationaryTaxis] = React.useState(true);
  const [viewInTransitTaxis, setViewInTransitTaxis] = React.useState(true);
  const [viewTripEndedTaxis, setViewTripEndedTaxis] = React.useState(true);
  const [viewOutsideGeofence, setViewOutsideGeofence] = React.useState(false);
  const [viewGeofence10km, setViewGeofence10km] = React.useState(false);
  const [viewGeofence15km, setViewGeofence15km] = React.useState(false);

  const handleSave = () => {
    const settings = {
      viewStationaryTaxis,
      viewInTransitTaxis,
      viewOutsideGeofence,
      viewTripEndedTaxis,
      viewGeofence10km,
      viewGeofence15km,
    };
    onSave(settings);
  };

  const handleGeofenceToggle = (checked: boolean) => {
    setViewOutsideGeofence(checked);
    if (checked) {
      if (!viewStationaryTaxis && !viewInTransitTaxis && !viewTripEndedTaxis) {
        setViewStationaryTaxis(true);
        setViewInTransitTaxis(true);
        setViewTripEndedTaxis(true);
      }
    }
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <button className="absolute top-20 left-3 z-[9999] rounded-none bg-white p-2 text-s shadow-sm hover:bg-gray-100 cursor-pointer">
          <Settings className="h-3.5 w-3.5" />
        </button>
      </SheetTrigger>
      <SheetContent className="w-[360px] sm:w-[360px]">
        <SheetHeader>
          <SheetTitle>Configure Map Settings</SheetTitle>
          <SheetDescription>
            Manage different taxi markers on the map.
          </SheetDescription>
        </SheetHeader>

        <div className="grid gap-4 p-4 rounded-md">
          <div className="flex items-center justify-between">
            <Label htmlFor="viewActiveTaxis" className="font-normal">
              View Stationary Taxis
            </Label>
            <Switch
              className="cursor-pointer"
              id="viewActiveTaxis"
              checked={viewStationaryTaxis}
              onCheckedChange={setViewStationaryTaxis}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="viewInTransitTaxis" className="font-normal">
              View In Transit Taxis
            </Label>
            <Switch
              className="cursor-pointer"
              id="viewInTransitTaxis"
              checked={viewInTransitTaxis}
              onCheckedChange={setViewInTransitTaxis}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="viewTripEndedTaxis" className="font-normal">
              View Trip Completed Taxis
            </Label>
            <Switch
              className="cursor-pointer"
              id="viewTripEndedTaxis"
              checked={viewTripEndedTaxis}
              onCheckedChange={setViewTripEndedTaxis}
            />
          </div>
          <div className="mt-4">
            <div className="flex items-center justify-between mb-4">
              <Label htmlFor="viewOutsideGeofence" className="font-normal">
                View Taxis Outside 15km City Radius
              </Label>
              <Switch
                className="cursor-pointer"
                id="viewOutsideGeofence"
                checked={viewOutsideGeofence}
                onCheckedChange={handleGeofenceToggle}
              />
            </div>

            <div className="flex items-center justify-between mb-4">
              <Label htmlFor="viewGeofence10km" className="font-normal">
                Show 10 km Geofence Around City Center
              </Label>
              <Switch
                className="cursor-pointer"
                id="viewGeofence10km"
                checked={viewGeofence10km}
                onCheckedChange={setViewGeofence10km}
              />
            </div>

            <div className="flex items-center justify-between mb-4">
              <Label htmlFor="viewGeofence15km" className="font-normal">
                Show 15 km Geofence Around City Center
              </Label>
              <Switch
                className="cursor-pointer"
                id="viewGeofence15km"
                checked={viewGeofence15km}
                onCheckedChange={setViewGeofence15km}
              />
            </div>
          </div>
        </div>

        <SheetFooter className="mt-2">
          <SheetClose asChild>
            <Button
              className="cursor-pointer"
              type="submit"
              onClick={handleSave}
            >
              Save changes
            </Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
