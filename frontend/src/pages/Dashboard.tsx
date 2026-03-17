/* Dashboard — Página principal */

import { useEffect } from 'react';
import { StatusCard } from '../components/StatusCard';
import { PresenceIndicator } from '../components/PresenceIndicator';
import { SignalChart } from '../components/SignalChart';
import { EventTimeline } from '../components/EventTimeline';
import { ConfidenceScore } from '../components/ConfidenceScore';
import { MonitorControls } from '../components/MonitorControls';
import { AlertBanner } from '../components/AlertBanner';
import { WifiRadar } from '../components/WifiRadar';
import { WifiSonar } from '../components/WifiSonar';
import { useStore } from '../store/useStore';
import { api } from '../services/api';

export function Dashboard() {
  const setStatus = useStore((s) => s.setStatus);
  const setEvents = useStore((s) => s.setEvents);

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [status, events] = await Promise.all([
          api.getStatus(),
          api.getEvents(15),
        ]);
        setStatus(status);
        setEvents(events);
      } catch (e) {
        console.error('Erro ao carregar dados iniciais:', e);
      }
    };
    fetchInitial();

    // Polling de eventos a cada 3s
    const interval = setInterval(async () => {
      try {
        const events = await api.getEvents(15);
        setEvents(events);
      } catch {
        // silencioso
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [setStatus, setEvents]);

  return (
    <div className="dashboard">
      <AlertBanner />

      <div className="dashboard-top">
        <StatusCard />
        <PresenceIndicator />
        <ConfidenceScore />
      </div>

      <MonitorControls />

      <div className="dashboard-charts">
        <SignalChart />
        <WifiRadar />
      </div>

      <WifiSonar />

      <EventTimeline />
    </div>
  );
}
