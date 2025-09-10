import { useEffect, useRef } from "react";

import { useIncidentsDataStore } from "@/stores/use-incidents-data-store";

const WS_API_URL = "ws://localhost:8000/ws/incidents";
const PING_INTERVAL_MS = 15000;
const MAX_RECONNECT_DELAY = 30000;
const INITIAL_RECONNECT_DELAY = 1000;

export function useIncidentsWebSocket(wsEnabled: boolean) {
  // Get actions from the incident data store
  const setIncidents = useIncidentsDataStore((state) => state.setIncidents);

  // WebSocket Refs to persist values across renders
  const wsRef = useRef<WebSocket | null>(null);
  const wsReconnectAttempt = useRef(0);
  const wsPingInterval = useRef<NodeJS.Timeout | null>(null);
  const wsReconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  // Clear ping interval
  const clearPing = () => {
    if (wsPingInterval.current) {
      clearInterval(wsPingInterval.current);
      wsPingInterval.current = null;
    }
  };

  // Helper: Clear reconnect timeout
  const clearReconnect = () => {
    if (wsReconnectTimeout.current) {
      clearTimeout(wsReconnectTimeout.current);
      wsReconnectTimeout.current = null;
    }
  };

  // Helper: Cleanup WebSocket and timers
  const cleanup = () => {
    clearPing();
    clearReconnect();
    wsRef.current?.close();
    wsRef.current = null;
  };

  useEffect(() => {
    if (!wsEnabled) {
      // If WebSocket is disabled, cleanup and exit
      cleanup();
      return;
    }

    // Establish WebSocket connection
    function connect() {
      wsRef.current = new WebSocket(WS_API_URL);

      wsRef.current.onopen = () => {
        // console.log(`Connected to WebSocket API ${WS_API_URL}.`);
        wsReconnectAttempt.current = 0;
        clearPing();

        // Start keep-alive ping interval
        wsPingInterval.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "ping" }));
          }
        }, PING_INTERVAL_MS);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setIncidents(data.incidents);
        } catch (err) {
          console.error("Invalid WebSocket Message:", err);
        }
      };

      wsRef.current.onerror = (err) => {
        console.error("WebSocket Error:", err);
        wsRef.current?.close();
      };

      wsRef.current.onclose = (event) => {
        console.log(`WebSocket Connection Closed. Code: ${event.code}`);
        clearPing();

        // Exponential backoff for reconnection
        const delay = Math.min(
          MAX_RECONNECT_DELAY,
          INITIAL_RECONNECT_DELAY * 2 ** wsReconnectAttempt.current
        );
        // console.log(
        //   `Reconnecting WebSocket API ${WS_API_URL} in ${delay} ms...`
        // );

        wsReconnectTimeout.current = setTimeout(() => {
          wsReconnectAttempt.current += 1;
          connect();
        }, delay);
      };
    }

    connect();

    // Cleanup on unmount or wsEnabled change
    return cleanup;
  }, [setIncidents, wsEnabled]);
}
