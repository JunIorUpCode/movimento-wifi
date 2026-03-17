/**
 * Componente de layout principal do painel do cliente.
 * 
 * Estrutura:
 * - Sidebar com navegação
 * - Header com informações do usuário
 * - Área de conteúdo principal
 */

import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard,
  Activity,
  Smartphone,
  Bell,
  CreditCard,
  LogOut,
  Menu,
  X,
  Wifi,
} from 'lucide-react'
import { useState } from 'react'

/**
 * Layout Component
 * 
 * Fornece estrutura consistente para todas as páginas do client panel.
 */
export default function Layout() {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Links de navegação
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Eventos', href: '/events', icon: Activity },
    { name: 'Dispositivos', href: '/devices', icon: Smartphone },
    { name: 'Notificações', href: '/notifications', icon: Bell },
    { name: 'Assinatura', href: '/subscription', icon: CreditCard },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar para mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 flex flex-col w-64 bg-white">
            <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
              <div className="flex items-center">
                <Wifi className="w-6 h-6 text-primary-600 mr-2" />
                <span className="text-xl font-bold text-primary-600">
                  WiFiSense
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Sidebar para desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 min-h-0 bg-white border-r border-gray-200">
          <div className="flex items-center h-16 px-4 border-b border-gray-200">
            <Wifi className="w-6 h-6 text-primary-600 mr-2" />
            <span className="text-xl font-bold text-primary-600">
              WiFiSense
            </span>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </NavLink>
            ))}
          </nav>
          
          {/* Informações do plano */}
          <div className="p-4 border-t border-gray-200">
            <div className="px-4 py-3 bg-primary-50 rounded-lg">
              <p className="text-xs font-medium text-primary-900">Plano Atual</p>
              <p className="text-sm font-bold text-primary-700 mt-1">
                {user?.plan_type === 'premium' ? 'PREMIUM' : 'BÁSICO'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Área principal */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="sticky top-0 z-10 flex items-center justify-between h-16 px-4 bg-white border-b border-gray-200 lg:px-8">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex items-center ml-auto space-x-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.name || user?.email}</p>
              <p className="text-xs text-gray-500">
                {user?.plan_type === 'premium' ? 'Plano Premium' : 'Plano Básico'}
              </p>
            </div>
            <button
              onClick={logout}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100"
              title="Sair"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Conteúdo */}
        <main className="p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
