/**
 * Componente de proteção de rotas.
 * 
 * Verifica se o usuário está autenticado antes de permitir acesso.
 * Redireciona para login se não autenticado.
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

/**
 * RequireAuth Component
 * 
 * Wrapper para rotas que requerem autenticação.
 * Usa React Router Outlet para renderizar rotas filhas.
 */
export default function RequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Mostra loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    )
  }

  // Redireciona para login se não autenticado
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Renderiza rotas filhas se autenticado
  return <Outlet />
}
