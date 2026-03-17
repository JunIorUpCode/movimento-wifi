/**
 * Página de login do painel administrativo.
 * 
 * Funcionalidades:
 * - Formulário de login com email e senha
 * - Validação de campos
 * - Tratamento de erros
 * - Redirecionamento após login bem-sucedido
 */

import { useState, FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Lock, Mail, AlertCircle } from 'lucide-react'
import { ApiError } from '../services/api'

/**
 * LoginPage Component
 * 
 * Página de autenticação para administradores.
 * Redireciona para dashboard se já autenticado.
 */
export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // Redireciona se já autenticado
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  /**
   * Manipula submissão do formulário de login
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    // Validação básica
    if (!email || !password) {
      setError('Por favor, preencha todos os campos')
      return
    }

    setIsLoading(true)

    try {
      await login({ email, password })
    } catch (err) {
      if (err instanceof ApiError) {
        // Mensagens de erro específicas baseadas no código
        switch (err.code) {
          case 'INVALID_CREDENTIALS':
            setError('Email ou senha incorretos')
            break
          case 'ACCOUNT_LOCKED':
            setError('Conta bloqueada. Tente novamente mais tarde.')
            break
          case 'ACCOUNT_SUSPENDED':
            setError('Conta suspensa. Entre em contato com o suporte.')
            break
          default:
            setError(err.message || 'Erro ao fazer login')
        }
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Erro desconhecido ao fazer login')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <div className="max-w-md w-full">
        {/* Card de login */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Logo e título */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <Lock className="w-8 h-8 text-primary-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Painel Administrativo
            </h1>
            <p className="text-gray-600 mt-2">
              WiFiSense SaaS Platform
            </p>
          </div>

          {/* Mensagem de erro */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Formulário */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Campo de email */}
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input pl-10"
                  placeholder="admin@wifisense.com"
                  disabled={isLoading}
                  autoComplete="email"
                  autoFocus
                />
              </div>
            </div>

            {/* Campo de senha */}
            <div>
              <label htmlFor="password" className="label">
                Senha
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-10"
                  placeholder="••••••••"
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>
            </div>

            {/* Botão de submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Entrando...
                </span>
              ) : (
                'Entrar'
              )}
            </button>
          </form>

          {/* Informações adicionais */}
          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Acesso restrito a administradores</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>© 2024 WiFiSense. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  )
}
