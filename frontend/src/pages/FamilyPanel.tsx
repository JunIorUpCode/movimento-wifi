/* FamilyPanel — Painel Família: interface simplificada para familiares */

import { useEffect, useState } from 'react';
import { Home, Clock, Bell, Settings, ArrowLeft, Sun, Moon, Wifi } from 'lucide-react';
import { useStore } from '../store/useStore';
import { api } from '../services/api';
import { PulsoView } from '../components/family/PulsoView';
import { PresencaView } from '../components/family/PresencaView';
import { RadarView } from '../components/family/RadarView';
import { VisualizationToggle } from '../components/family/VisualizationToggle';
import { FamilyHistory } from '../components/family/FamilyHistory';
import { FamilyNotifications } from '../components/family/FamilyNotifications';
import type { EventType } from '../types';

type FamilyTab = 'live' | 'history' | 'notifications' | 'settings';

const HUMAN_STATUS: Record<EventType, string> = {
  no_presence:          'Ninguém detectado no ambiente',
  presence_still:       'Pessoa em repouso',
  presence_moving:      'Movimento normal detectado',
  fall_suspected:       '⚠️ QUEDA DETECTADA',
  prolonged_inactivity: 'Sem movimento há muito tempo',
};

const STATUS_COLOR: Record<EventType, string> = {
  no_presence:          '#6b7280',
  presence_still:       '#3b82f6',
  presence_moving:      '#10b981',
  fall_suspected:       '#ef4444',
  prolonged_inactivity: '#f59e0b',
};

function formatUptime(s: number) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}min`;
  return `${m}min`;
}

/* Mini heatmap do dia — hora a hora */
function DayHeatmap() {
  const events = useStore((s) => s.events);
  const hours = Array.from({ length: 24 }, (_, h) => {
    const count = events.filter((e) => new Date(e.timestamp).getHours() === h).length;
    return count;
  });
  const max = Math.max(...hours, 1);
  const currentHour = new Date().getHours();

  return (
    <div className="family-heatmap">
      <span className="family-heatmap-label">0h</span>
      <div className="family-heatmap-bars">
        {hours.map((count, h) => (
          <div
            key={h}
            className={`family-heatmap-bar ${h === currentHour ? 'current' : ''}`}
            style={{ height: `${Math.max(10, (count / max) * 100)}%` }}
            title={`${h}h: ${count} eventos`}
          />
        ))}
      </div>
      <span className="family-heatmap-label">23h</span>
    </div>
  );
}

/* Configurações do painel família */
function FamilySettings() {
  const familyViewMode = useStore((s) => s.familyViewMode);
  const setFamilyViewMode = useStore((s) => s.setFamilyViewMode);
  const theme = useStore((s) => s.theme);
  const setTheme = useStore((s) => s.setTheme);

  return (
    <div className="family-settings-tab">
      <h3 className="family-section-title">Preferências</h3>

      <div className="family-settings-group">
        <label className="family-settings-label">Modo de visualização padrão</label>
        <VisualizationToggle />
        <p className="family-settings-desc">
          Modo atual: <strong>
            {familyViewMode === 'pulso' ? 'Pulso' : familyViewMode === 'presenca' ? 'Presença' : 'Radar'}
          </strong>
        </p>
      </div>

      <div className="family-settings-group">
        <label className="family-settings-label">Tema</label>
        <div className="family-theme-toggle">
          <button
            className={`family-theme-btn ${theme === 'dark' ? 'active' : ''}`}
            onClick={() => setTheme('dark')}
          >
            <Moon size={16} /> Escuro
          </button>
          <button
            className={`family-theme-btn ${theme === 'light' ? 'active' : ''}`}
            onClick={() => setTheme('light')}
          >
            <Sun size={16} /> Claro
          </button>
        </div>
      </div>
    </div>
  );
}

export function FamilyPanel() {
  const [activeTab, setActiveTab] = useState<FamilyTab>('live');
  const currentEvent = useStore((s) => s.currentEvent);
  const isMonitoring = useStore((s) => s.isMonitoring);
  const uptimeSeconds = useStore((s) => s.uptimeSeconds);
  const familyViewMode = useStore((s) => s.familyViewMode);
  const theme = useStore((s) => s.theme);
  const setActivePage = useStore((s) => s.setActivePage);
  const setStatus = useStore((s) => s.setStatus);
  const setTheme = useStore((s) => s.setTheme);

  /* Aplica tema salvo ao montar */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  /* Polling de status */
  useEffect(() => {
    const poll = async () => {
      try {
        const status = await api.getStatus();
        setStatus(status);
      } catch { /* silencioso */ }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, [setStatus]);

  const statusColor = STATUS_COLOR[currentEvent];
  const isFall = currentEvent === 'fall_suspected';

  const TABS: { id: FamilyTab; label: string; icon: React.ElementType }[] = [
    { id: 'live',          label: 'Ao Vivo',       icon: Home },
    { id: 'history',       label: 'Histórico',      icon: Clock },
    { id: 'notifications', label: 'Notificações',   icon: Bell },
    { id: 'settings',      label: 'Config',         icon: Settings },
  ];

  return (
    <div className={`family-panel ${isFall ? 'family-panel-alert' : ''}`}>
      {/* Header */}
      <header className="family-header">
        <div className="family-header-left">
          <Wifi size={20} className="family-logo-icon" />
          <span className="family-header-title">WiFiSense</span>
          <span className="family-header-sep">•</span>
          <span className="family-header-location">Residência Principal</span>
        </div>
        <div className="family-header-right">
          <button
            className="family-theme-icon-btn"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Alternar tema"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            className="family-back-btn"
            onClick={() => setActivePage('dashboard')}
            title="Voltar ao painel admin"
          >
            <ArrowLeft size={16} />
            <span>Admin</span>
          </button>
        </div>
      </header>

      {/* Layout: sidebar (desktop) + conteúdo */}
      <div className="family-body">
        {/* Sidebar — só desktop */}
        <nav className="family-sidebar">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`family-nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={20} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* Conteúdo principal */}
        <main className="family-main">
          {activeTab === 'live' && (
            <div className="family-live">
              {/* Status bar */}
              <div className="family-status-bar">
                <div className="family-status-dot-wrap">
                  <span
                    className={`family-status-dot ${isMonitoring ? 'active' : ''}`}
                    style={{ backgroundColor: isMonitoring ? statusColor : '#4b5563' }}
                  />
                  <span className="family-status-live">{isMonitoring ? 'Ao vivo' : 'Offline'}</span>
                </div>
                {isMonitoring && (
                  <span className="family-uptime">
                    Ativo há {formatUptime(uptimeSeconds)}
                  </span>
                )}
              </div>

              {/* Alerta de queda */}
              {isFall && (
                <div className="family-fall-alert">
                  🚨 QUEDA DETECTADA — Verifique imediatamente!
                </div>
              )}

              {/* Visualização central */}
              <div className="family-visualization">
                {familyViewMode === 'pulso'    && <PulsoView eventType={currentEvent} />}
                {familyViewMode === 'presenca' && <PresencaView eventType={currentEvent} />}
                {familyViewMode === 'radar'    && <RadarView eventType={currentEvent} />}
              </div>

              {/* Status em texto */}
              <div className="family-status-text" style={{ color: statusColor }}>
                {HUMAN_STATUS[currentEvent]}
              </div>

              {/* Toggle de modos */}
              <VisualizationToggle />

              {/* Heatmap do dia */}
              <div className="family-heatmap-section">
                <span className="family-section-subtitle">Atividade de hoje</span>
                <DayHeatmap />
              </div>
            </div>
          )}

          {activeTab === 'history'       && <FamilyHistory />}
          {activeTab === 'notifications' && <FamilyNotifications />}
          {activeTab === 'settings'      && <FamilySettings />}
        </main>
      </div>

      {/* Tab bar — mobile */}
      <nav className="family-tabbar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`family-tabbar-item ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={22} />
            <span>{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
