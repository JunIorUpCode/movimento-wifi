/**
 * Componente raiz do painel administrativo WiFiSense.
 * 
 * Gerencia:
 * - Roteamento da aplicação
 * - Autenticação e proteção de rotas
 * - Layout global
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'

// Páginas
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TenantsPage from './pages/TenantsPage'
import LicensesPage from './pages/LicensesPage'
import DevicesPage from './pages/DevicesPage'
import AuditLogsPage from './pages/AuditLogsPage'

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
            <Route path="/tenants" element={<TenantsPage />} />
            <Route path="/licenses" element={<LicensesPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
          </Route>
        </Route>
        
        {/* Rota 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
