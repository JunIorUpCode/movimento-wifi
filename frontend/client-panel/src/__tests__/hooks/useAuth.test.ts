/**
 * Testes unitários para o hook useAuth.
 * 
 * Testa:
 * - Login com credenciais válidas
 * - Login com credenciais inválidas
 * - Logout
 * - Carregamento de autenticação do localStorage
 * - Verificação de role tenant
 */

import { renderHook, waitFor } from '@testing-library/react'
import { useAuth } from '../../hooks/useAuth'
import { authApi } from '../../services/api'
import { BrowserRouter } from 'react-router-dom'
import { ReactNode } from 'react'

// Mock do módulo de API
vi.mock('../../services/api', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

// Mock do react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

/**
 * Wrapper para fornecer Router ao hook
 */
function wrapper({ children }: { children: ReactNode }) {
  return <BrowserRouter>{children}</BrowserRouter>
}

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Inicialização', () => {
    it('deve iniciar com isLoading=true e depois false quando não há token', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })

      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()
    })

    it('deve carregar autenticação do localStorage se token válido existe', async () => {
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
        name: 'Tenant Test',
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.token).toBe(mockToken)
    })

    it('deve limpar localStorage se usuário não é tenant', async () => {
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
    })
  })

  describe('Login', () => {
    it('deve fazer login com credenciais válidas de tenant', async () => {
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
        name: 'Tenant Test',
      }
      const mockToken = 'mock-jwt-token'

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: mockToken,
        token_type: 'Bearer',
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await result.current.login({
        email: 'tenant@test.com',
        password: 'password123',
      })

      expect(authApi.login).toHaveBeenCalledWith({
        email: 'tenant@test.com',
        password: 'password123',
      })

      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.token).toBe(mockToken)

      expect(localStorage.getItem('auth_token')).toBe(mockToken)
      expect(localStorage.getItem('auth_user')).toBe(JSON.stringify(mockUser))

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })

    it('deve rejeitar login de usuário não-tenant', async () => {
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
      }

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'mock-token',
        token_type: 'Bearer',
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await expect(
        result.current.login({
          email: 'admin@test.com',
          password: 'password123',
        })
      ).rejects.toThrow('Acesso negado. Apenas clientes podem acessar este painel.')

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
    })

    it('deve limpar dados em caso de erro de login', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('Credenciais inválidas'))

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      await expect(
        result.current.login({
          email: 'tenant@test.com',
          password: 'wrong-password',
        })
      ).rejects.toThrow('Credenciais inválidas')

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })

  describe('Logout', () => {
    it('deve fazer logout e limpar dados', async () => {
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      vi.mocked(authApi.logout).mockResolvedValue(undefined)

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
      })

      await result.current.logout()

      expect(authApi.logout).toHaveBeenCalled()

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()

      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })

    it('deve limpar dados locais mesmo se API de logout falhar', async () => {
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      vi.mocked(authApi.logout).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useAuth(), { wrapper })

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
      })

      await result.current.logout()

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })
})
