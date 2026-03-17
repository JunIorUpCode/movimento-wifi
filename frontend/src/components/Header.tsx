/* Header — Cabeçalho do sistema */

import { Wifi, Activity } from 'lucide-react';
import { useStore } from '../store/useStore';

export function Header() {
  const isMonitoring = useStore((s) => s.isMonitoring);
  const uptimeSeconds = useStore((s) => s.uptimeSeconds);

  const formatUptime = (s: number) => {
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = Math.floor(s % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <header className="header">
      <div className="header-left">
        <Wifi className="header-icon" size={28} />
        <div>
          <h1 className="header-title">WiFiSense Local</h1>
          <span className="header-subtitle">Monitoramento de Presença & Movimento</span>
        </div>
      </div>
      <div className="header-right">
        <div className={`status-dot ${isMonitoring ? 'active' : 'inactive'}`} />
        <span className="header-status">
          {isMonitoring ? 'Monitorando' : 'Parado'}
        </span>
        {isMonitoring && (
          <span className="header-uptime">
            <Activity size={14} /> {formatUptime(uptimeSeconds)}
          </span>
        )}
      </div>
    </header>
  );
}
