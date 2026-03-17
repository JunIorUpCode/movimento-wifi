/**
 * Hook personalizado para gerenciamento de autenticação.
 * 
 * Funcionalidades:
 * - Login e logout
 * - Armazenamento de token JWT no localStorage
 * - Verificação de autenticação
 * - Informações do usuário autenticado
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import type { User, LoginCredentials } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

/**
 * Hook useAuth
 * 
 * Gerencia o estado de autenticação do usuário administrador.
 * Persiste o token JWT no localStorage para manter sessão entre reloads.
 */
export function useAuth() {
  const navigate = useNavigate()
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  /**
   * Carrega dados de autenticação do localStorage na inicialização
   */
  useEffect(() => {
    const loadAuth = () => {
      try {
        const token = localStorage.getItem('auth_token')
        const userStr = localStorage.getItem('auth_user')

        if (token && userStr) {
          const user = JSON.parse(userStr) as User
          
          // Verifica se o usuário é admin
          if (user.role !== 'admin') {
            // Limpa dados se não for admin
            localStorage.removeItem('auth_token')
            localStorage.removeItem('auth_user')
            setState({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
            })
            return
          }

          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } else {
          setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      } catch (error) {
        console.error('Erro ao carregar autenticação:', error)
        setState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        })
      }
    }

    loadAuth()
  }, [])

  /**
   * Realiza login do administrador
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      const response = await authApi.login(credentials)

      // Verifica se o usuário é admin
      if (response.user.role !== 'admin') {
        throw new Error('Acesso negado. Apenas administradores podem acessar este painel.')
      }

      // Armazena token e dados do usuário
      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('auth_user', JSON.stringify(response.user))

      setState({
        user: response.user,
        token: response.access_token,
        isAuthenticated: true,
        isLoading: false,
      })

      // Redireciona para dashboard
      navigate('/dashboard')
    } catch (error) {
      // Limpa qualquer dado de autenticação em caso de erro
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      
      setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      })

      throw error
    }
  }, [navigate])

  /**
   * Realiza logout do administrador
   */
  const logout = useCallback(async () => {
    try {
      // Tenta invalidar token no backend
      await authApi.logout()
    } catch (error) {
      // Ignora erros de logout no backend
      console.error('Erro ao fazer logout no backend:', error)
    } finally {
      // Sempre limpa dados locais
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')

      setState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      })

      // Redireciona para login
      navigate('/login')
    }
  }, [navigate])

  return {
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    login,
    logout,
  }
}
