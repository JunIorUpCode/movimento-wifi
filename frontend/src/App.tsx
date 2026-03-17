/* App.tsx — Layout principal com Sidebar, Header e roteamento por estado */

import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { History } from './pages/History';
import { Settings } from './pages/Settings';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store/useStore';

function App() {
  const activePage = useStore((s) => s.activePage);

  // Conecta WebSocket globalmente
  useWebSocket();

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />;
      case 'history':
        return <History />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
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
