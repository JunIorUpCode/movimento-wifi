/* Hook de WebSocket com auto-reconnect */

import { useEffect, useRef } from 'react';
import type { LiveUpdate } from '../types';
import { useStore } from '../store/useStore';

export function useWebSocket() {
  const pushLiveUpdate = useStore((s) => s.pushLiveUpdate);
  const isMonitoring = useStore((s) => s.isMonitoring);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const host = window.location.host;
      const ws = new WebSocket(`${protocol}://${host}/ws/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Conectado');
      };

      ws.onmessage = (event) => {
        try {
          const data: LiveUpdate = JSON.parse(event.data);
          if (data.event_type) {
            pushLiveUpdate(data);
          }
        } catch {
          // Ignora mensagens inválidas
        }
      };

      ws.onclose = () => {
        console.log('[WS] Desconectado, reconectando em 2s...');
        reconnectTimer.current = setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [pushLiveUpdate]);

  return wsRef;
}
