/* App.tsx — Layout principal com Sidebar, Header e roteamento por estado */

import { useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { History } from './pages/History';
import { Settings } from './pages/Settings';
import { Calibration } from './pages/Calibration';
import { Statistics } from './pages/Statistics';
import { Notifications } from './pages/Notifications';
import { Zones } from './pages/Zones';
import { MLCollection } from './pages/MLCollection';
import { PushNotifications } from './pages/PushNotifications';
import { Replay } from './pages/Replay';
import { FamilyPanel } from './pages/FamilyPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store/useStore';

function App() {
  const activePage = useStore((s) => s.activePage);
  const theme = useStore((s) => s.theme);

  // Conecta WebSocket globalmente
  useWebSocket();

  // Aplica tema salvo no localStorage ao iniciar
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Painel Família: layout próprio, sem Header/Sidebar admin
  if (activePage === 'family') {
    return <FamilyPanel />;
  }

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':         return <Dashboard />;
      case 'history':           return <History />;
      case 'calibration':       return <Calibration />;
      case 'statistics':        return <Statistics />;
      case 'notifications':     return <Notifications />;
      case 'zones':             return <Zones />;
      case 'ml':                return <MLCollection />;
      case 'pushnotifications': return <PushNotifications />;
      case 'replay':            return <Replay />;
      case 'settings':          return <Settings />;
      default:                  return <Dashboard />;
    }
  };

  return (
    <div className="app-layout">
      <Header />
      <div className="app-body">
        <Sidebar />
        <main className="app-main">{renderPage()}</main>
      </div>
    </div>
  );
}

export default App;
