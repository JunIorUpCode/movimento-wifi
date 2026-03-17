/**
 * Componente raiz do painel do cliente WiFiSense.
 * 
 * Gerencia:
 * - Roteamento da aplicação
 * - Autenticação e proteção de rotas
 * - Layout global
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

// Páginas
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import EventsPage from './pages/EventsPage'
import DevicesPage from './pages/DevicesPage'
import NotificationsPage from './pages/NotificationsPage'
import SubscriptionPage from './pages/SubscriptionPage'

// Componentes
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rota pública - Login */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Rotas protegidas - Requerem autenticação */}
        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/subscription" element={<SubscriptionPage />} />
          </Route>
        </Route>
        
        {/* Rota 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
