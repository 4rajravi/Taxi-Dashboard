"use client";

import "leaflet/dist/leaflet.css";
import "react-leaflet-markercluster/styles";

import { useEffect, useState, useMemo, useCallback } from "react";
import { Circle, MapContainer, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-markercluster";

import { MapMarker } from "@/components/map/map-marker";
import { MapSetView } from "@/components/map/map-set-view";
import { MapResize } from "@/components/map/map-resize";
import { MapTaxiSearchCombobox } from "@/components/map/map-taxi-search-combobox";
import { MapSettings } from "@/components/map/map-settings";
import { MapTaxiSheet } from "@/components/map/map-marker-sheet";

import { Taxi, useTaxiDataStore } from "@/stores/use-taxi-data-store";

import { useLoadTaxis } from "@/hooks/use-fetch-taxis";
import { useTaxisWebSocket } from "@/hooks/use-taxis-websocket";

export default function MapContainerWrapper() {
  const { loadingTaxis, fetchSucceeded } = useLoadTaxis();

  const selectedTaxi = useTaxiDataStore((state) => state.selectedTaxi);
  const setSelectedTaxi = useTaxiDataStore((state) => state.setSelectedTaxi);

  const selectedCoordinates = useTaxiDataStore(
    (state) => state.selectedCoordinates
  );
  const setSelectedCoordinates = useTaxiDataStore(
    (state) => state.setSelectedCoordinates
  );

  const zoomScale = useTaxiDataStore((state) => state.zoomScale);
  const setZoomScale = useTaxiDataStore((state) => state.setZoomScale);

  useTaxisWebSocket(fetchSucceeded && !loadingTaxis);
  const taxis = Object.values(useTaxiDataStore((state) => state.taxis));

  const selectedTaxiData =
    taxis.find((t) => t.taxi_id === selectedTaxi?.taxi_id) ?? null;

  const [mapSettings, setMapSettings] = useState({
    viewStationaryTaxis: true,
    viewInTransitTaxis: true,
    viewTripEndedTaxis: true,
    viewOutsideGeofence: false,
    viewGeofence10km: false,
    viewGeofence15km: false,
  });

  const handleMapSettings = (newSettings: typeof mapSettings) => {
    setMapSettings(newSettings);
  };

  useEffect(() => {
    if (selectedTaxiData) {
      setSelectedCoordinates([
        selectedTaxiData.latitude,
        selectedTaxiData.longitude,
      ]);
    }
  }, [selectedTaxiData, setSelectedCoordinates]);

  type MapSettings = {
    viewStationaryTaxis: boolean;
    viewInTransitTaxis: boolean;
    viewTripEndedTaxis: boolean;
    viewOutsideGeofence: boolean;
    viewGeofence10km: boolean;
    viewGeofence15km: boolean;
  };

  const [sheetOpen, setSheetOpen] = useState(false);

  useEffect(() => {
    setSheetOpen(!!selectedTaxi);
  }, [selectedTaxi]);

  const shouldDisplayTaxi = useCallback(
    (taxi: Taxi, mapSettings: MapSettings): boolean => {
      if (!taxi.is_valid_speed) return false;

      if (!mapSettings.viewTripEndedTaxis && taxi.trip_status === "end") {
        return false;
      }

      if (
        (!mapSettings.viewStationaryTaxis &&
          taxi.trip_status === "active" &&
          taxi.speed <= 0) ||
        (!mapSettings.viewInTransitTaxis &&
          taxi.trip_status === "active" &&
          taxi.speed > 0)
      ) {
        return false;
      }

      if (
        !mapSettings.viewOutsideGeofence &&
        taxi.distance_from_forbidden_city_km > 15
      ) {
        return false;
      }

      return true;
    },
    []
  );

  const filteredTaxis = useMemo(() => {
    return taxis.filter((taxi) => shouldDisplayTaxi(taxi, mapSettings));
  }, [taxis, mapSettings, shouldDisplayTaxi]);

  // Memoize your marker click handler (to keep a stable function reference)
  const handleMarkerClick = useCallback(
    (taxi: Taxi) => {
      setSelectedTaxi(null); // reset first to force update
      setTimeout(() => setSelectedTaxi(taxi), 0);
      setSelectedCoordinates([taxi.latitude, taxi.longitude]);
      setZoomScale(20);
    },
    [setSelectedTaxi, setSelectedCoordinates, setZoomScale]
  );

  // Memoize the array of MapMarker components
  const memoizedMarkers = useMemo(() => {
    if (loadingTaxis) return null;

    return filteredTaxis.map((taxi) => (
      <MapMarker
        key={taxi.taxi_id}
        taxi={taxi}
        onClick={() => handleMarkerClick(taxi)}
        isSelected={selectedTaxi?.taxi_id === taxi.taxi_id}
      />
    ));
    // Only depend on filteredTaxis array and selection state to avoid unnecessary remounts
  }, [loadingTaxis, filteredTaxis, selectedTaxi?.taxi_id, handleMarkerClick]);

  return (
    <div className="relative h-full w-full">
      <div id="map-container" className="h-full w-full rounded-xl">
        {/* Leaflet ap container */}
        <MapContainer
          center={[39.9168, 116.3972]} // Default map center (Beijing)
          zoom={zoomScale}
          minZoom={10}
          scrollWheelZoom={true}
          className="h-full w-full rounded-xl"
          // maxBounds={[[17.0, 73.0], [54.0, 135.0]]} // Southwest and Northeast corners of China
          // maxBoundsViscosity={1.0} // Prevents panning outside bounds
        >
          {/* Base map tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          {/* 10km and 15km circles from city center */}
          {mapSettings.viewGeofence10km && (
            <Circle
              center={[39.9168, 116.3972]}
              radius={10000}
              pathOptions={{
                color: "#a3a3a3",
                fill: false,
                weight: 1,
                dashArray: "3 3",
              }}
            />
          )}
          {mapSettings.viewGeofence15km && (
            <Circle
              center={[39.9168, 116.3972]}
              radius={15000}
              pathOptions={{
                color: "#d4d4d4",
                fill: false,
                weight: 1,
                dashArray: "3 3",
              }}
            />
          )}
          <MarkerClusterGroup
            showCoverageOnHover={false}
            spiderfyOnMaxZoom={false}
            disableClusteringAtZoom={15}
            removeOutsideVisibleBounds={true}
            maxClusterRadius={120}
            chunkedLoading={true}
          >
            {memoizedMarkers}
          </MarkerClusterGroup>
          {/* Ensures map resizes correctly */}
          <MapResize />
          {/* Dynamically set map view */}
          <MapSetView
            coordinates={selectedCoordinates}
            zoom={zoomScale}
            onZoomConsumed={() => setZoomScale(undefined)}
          />
        </MapContainer>
        <MapTaxiSheet
          taxi={selectedTaxiData}
          open={sheetOpen}
          onOpenChange={setSheetOpen}
        />
        <MapSettings onSave={handleMapSettings} />
        <MapTaxiSearchCombobox
          // taxis={taxis.filter((taxi) => shouldDisplayTaxi(taxi, mapSettings))}
          selectedTaxiMarker={selectedTaxi}
          onSelectTaxi={(taxi) => {
            if (taxi) {
              setSelectedTaxi(taxi);
              setSelectedCoordinates([taxi.latitude, taxi.longitude]);
              setZoomScale(20);
            } else {
              setSelectedTaxi(null);
              setSelectedCoordinates(null);
              setZoomScale(10);
            }
          }}
        />
      </div>
    </div>
  );
}
