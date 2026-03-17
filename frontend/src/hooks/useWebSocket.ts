/* Hook de WebSocket com auto-reconnect e suporte a novos tipos de evento */

import { useEffect, useRef } from 'react';
import type { LiveUpdate, WsMessage } from '../types';
import { useStore } from '../store/useStore';

export function useWebSocket() {
  const pushLiveUpdate = useStore((s) => s.pushLiveUpdate);
  const setCalibrationProgress = useStore((s) => s.setCalibrationProgress);
  const pushAnomaly = useStore((s) => s.pushAnomaly);
  const pushEnabled = useStore((s) => s.pushEnabled);
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
          const msg: WsMessage = JSON.parse(event.data);

          // Evento de detecção (estrutura antiga — sem campo 'type')
          if (!msg.type && 'event_type' in msg) {
            pushLiveUpdate(msg as LiveUpdate);
            return;
          }

          switch (msg.type) {
            case 'calibration_progress':
              setCalibrationProgress(msg.data);
              break;

            case 'anomaly_detected':
              pushAnomaly(msg.data);
              // Notificação push no browser (se habilitada)
              if (pushEnabled && 'Notification' in window && Notification.permission === 'granted') {
                new Notification('WiFiSense — Anomalia detectada', {
                  body: `${msg.data.event_type} — confiança ${Math.round(msg.data.confidence * 100)}%`,
                  icon: '/vite.svg',
                });
              }
              break;

            case 'notification_sent':
              // Disponível para subscribers futuros; sem ação global por enquanto
              console.log('[WS] Notificação enviada:', msg.data);
              break;

            default:
              // Evento de detecção com campo 'type' não reconhecido — tenta como LiveUpdate
              if ('event_type' in msg) {
                pushLiveUpdate(msg as unknown as LiveUpdate);
              }
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
  }, [pushLiveUpdate, setCalibrationProgress, pushAnomaly, pushEnabled]);

  return wsRef;
}
