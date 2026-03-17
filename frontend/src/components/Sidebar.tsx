/* Sidebar — Navegação lateral */

import {
  LayoutDashboard,
  History,
  Settings,
  SlidersHorizontal,
  BarChart2,
  Bell,
  MapPin,
  Brain,
  BellRing,
  Play,
  Users,
} from 'lucide-react';
import { useStore, type PageId } from '../store/useStore';

const NAV_ITEMS: { id: PageId; label: string; icon: React.ElementType; group?: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'history', label: 'Histórico', icon: History },
  { id: 'replay', label: 'Replay', icon: Play },
  { id: 'statistics', label: 'Estatísticas', icon: BarChart2, group: 'Análise' },
  { id: 'calibration', label: 'Calibração', icon: SlidersHorizontal },
  { id: 'zones', label: 'Zonas', icon: MapPin },
  { id: 'ml', label: 'Coleta ML', icon: Brain, group: 'ML' },
  { id: 'notifications', label: 'Notificações', icon: Bell, group: 'Alertas' },
  { id: 'pushnotifications', label: 'Push Browser', icon: BellRing },
  { id: 'settings', label: 'Configurações', icon: Settings, group: 'Sistema' },
];

export function Sidebar() {
  const activePage = useStore((s) => s.activePage);
  const setActivePage = useStore((s) => s.setActivePage);

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => setActivePage(item.id as PageId)}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button
          className="sidebar-family-btn"
          onClick={() => setActivePage('family')}
          title="Abrir Painel Família"
        >
          <Users size={16} />
          <span>Painel Família</span>
        </button>
        <span className="sidebar-version">v1.0.0</span>
      </div>
    </aside>
  );
}
