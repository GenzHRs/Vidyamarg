import { useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { getWsUrl } from "@/services/api";

export const useWebSockets = (clientId: string) => {
  const token = useAuthStore(state => state.token);
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const listeners = useRef<((event: any) => void)[]>([]);

  useEffect(() => {
    if (!clientId || !token) return;

    const WS_URL = getWsUrl();
    const socket = new WebSocket(`${WS_URL}/${encodeURIComponent(clientId)}`);

    socket.onopen = () => {
      socket.send(JSON.stringify({ token }));
      setIsConnected(true);
      console.log("WebSocket connected:", clientId);
    };

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        listeners.current.forEach((cb) => cb(parsed));
      } catch (err) {
        console.error("Failed to parse socket packet:", err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      console.log("WebSocket disconnected:", clientId);
    };

    ws.current = socket;

    return () => {
      socket.close();
    };
  }, [clientId, token]);

  const addMessageListener = (callback: (event: any) => void) => {
    listeners.current.push(callback);
    return () => {
      listeners.current = listeners.current.filter((cb) => cb !== callback);
    };
  };

  const sendMessage = (msg: any) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify(msg));
    }
  };

  return { isConnected, addMessageListener, sendMessage };
};
