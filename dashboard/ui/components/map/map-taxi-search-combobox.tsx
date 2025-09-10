"use client";

import * as React from "react";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

import { CheckIcon, XIcon, ChevronsUpDown } from "lucide-react";

import {
  Taxi,
  useAllTaxiIdsStore,
  useTaxiDataStore,
} from "@/stores/use-taxi-data-store";

import { cn } from "@/lib/utils";
import { useFetchTaxiIds } from "@/hooks/use-fetch-taxi-ids";

type MapTaxiSearchComboboxProps = {
  //taxis: Taxi[]; // Replace `TaxiType` with the correct type if available
  selectedTaxiMarker: Taxi | null;
  onSelectTaxi: (taxi: Taxi | null) => void;
};

// Taxi selection combobox component
export function MapTaxiSearchCombobox({
  //taxis,
  selectedTaxiMarker,
  onSelectTaxi,
}: MapTaxiSearchComboboxProps) {
  const { loadingTaxiIds, fetchSucceeded: taxiIdsFetchSucceeded } =
    useFetchTaxiIds();

  // Get taxis as an object keyed by taxi_id from the store
  const taxisById = useTaxiDataStore((state) => state.taxis);

  // Get all taxi IDs from the store
  const taxiIds = useAllTaxiIdsStore((state) => state.allTaxiIds);

  // Extract taxi IDs as an array of numbers
  // const taxiIds = React.useMemo(() => {
  //   const validIds = new Set(taxis.map((taxi: Taxi) => Number(taxi.taxi_id)));
  //   return Object.keys(taxisById)
  //     .map(Number)
  //     .filter((id) => validIds.has(id));
  // }, [taxisById, taxis]);

  // State for popover open/close
  const [open, setOpen] = React.useState(false);

  // State for selected taxi ID (null if none selected)
  const [, setSelectedTaxiID] = React.useState<number | null>(null);

  // Handle taxi selection
  const handleSelect = (taxiId: number) => {
    setSelectedTaxiID(taxiId);
    const selected = taxisById[taxiId];
    if (selected) {
      onSelectTaxi(selected);
    }
    setOpen(false);
  };

  // Handle clearing the selection
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedTaxiID(null);
    onSelectTaxi(null);
  };

  return (
    <div className="absolute top-3 right-2 z-[9999]">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          {/* Trigger button for popover */}
          <div
            onClick={() => setOpen(true)}
            className="w-[200px] text-sm border rounded-full px-3 py-2 cursor-pointer text-left bg-white flex shadow-sm items-center justify-between"
          >
            <span>
              {selectedTaxiMarker?.taxi_id
                ? `Taxi ${selectedTaxiMarker?.taxi_id}`
                : "Select Taxi to View"}
            </span>
            {/* Show clear icon if taxi is selected, else show dropdown icon */}
            {selectedTaxiMarker?.taxi_id ? (
              <XIcon
                onClick={handleClear}
                className="w-4 h-4 text-muted-foreground hover:text-foreground"
              />
            ) : (
              <ChevronsUpDown className="w-4 h-4 text-muted-foreground hover:text-foreground" />
            )}
          </div>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0">
          <Command>
            {/* Search input */}
            <CommandInput placeholder="Search taxi by ID..." />
            <CommandEmpty>No taxi found.</CommandEmpty>
            {/* List of taxis */}
            <CommandGroup className="max-h-[250px] overflow-y-auto">
              {loadingTaxiIds ? (
                <div className="text-center py-2 text-sm text-muted-foreground">
                  Loading Taxi IDs...
                </div>
              ) : taxiIdsFetchSucceeded ? (
                [...taxiIds]
                  .sort((taxiOne, taxiTwo) => {
                    if (taxiOne === selectedTaxiMarker?.taxi_id) return -1;
                    if (taxiTwo === selectedTaxiMarker?.taxi_id) return 1;
                    return 0;
                  })
                  .map((taxiId) => (
                    <CommandItem
                      key={taxiId}
                      onSelect={() => handleSelect(taxiId)}
                      className="cursor-pointer"
                    >
                      <CheckIcon
                        className={cn(
                          "mr-2 h-4 w-4",
                          selectedTaxiMarker?.taxi_id === taxiId
                            ? "opacity-100"
                            : "opacity-0"
                        )}
                      />
                      Taxi ID
                      <span className="font-normal text-xs bg-slate-200 px-2 rounded-2xl">
                        {taxiId}
                      </span>
                    </CommandItem>
                  ))
              ) : (
                <div className="text-center py-2 text-sm text-muted-foreground">
                  Failed to Fetch Taxi IDs.
                </div>
              )}
            </CommandGroup>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
