/**
 * Testes unitários para o hook useAuth.
 * 
 * Testa:
 * - Login com credenciais válidas
 * - Login com credenciais inválidas
 * - Logout
 * - Carregamento de autenticação do localStorage
 * - Verificação de role admin
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
    // Limpa localStorage antes de cada teste
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Inicialização', () => {
    it('deve iniciar com isLoading=true e depois false quando não há token', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper })

      // Inicialmente está carregando
      expect(result.current.isLoading).toBe(true)

      // Aguarda finalizar carregamento
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Não está autenticado
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()
    })

    it('deve carregar autenticação do localStorage se token válido existe', async () => {
      // Simula token e usuário no localStorage
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
        name: 'Admin Test',
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda carregar do localStorage
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Deve estar autenticado
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.token).toBe(mockToken)
    })

    it('deve limpar localStorage se usuário não é admin', async () => {
      // Simula usuário não-admin no localStorage
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda processamento
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Não deve estar autenticado
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      
      // Deve ter limpado localStorage
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
    })
  })

  describe('Login', () => {
    it('deve fazer login com credenciais válidas de admin', async () => {
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
        name: 'Admin Test',
      }
      const mockToken = 'mock-jwt-token'

      // Mock da resposta da API
      vi.mocked(authApi.login).mockResolvedValue({
        access_token: mockToken,
        token_type: 'Bearer',
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda inicialização
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Executa login
      await result.current.login({
        email: 'admin@test.com',
        password: 'password123',
      })

      // Verifica que API foi chamada
      expect(authApi.login).toHaveBeenCalledWith({
        email: 'admin@test.com',
        password: 'password123',
      })

      // Verifica estado atualizado
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.token).toBe(mockToken)

      // Verifica localStorage
      expect(localStorage.getItem('auth_token')).toBe(mockToken)
      expect(localStorage.getItem('auth_user')).toBe(JSON.stringify(mockUser))

      // Verifica navegação para dashboard
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })

    it('deve rejeitar login de usuário não-admin', async () => {
      const mockUser = {
        id: '1',
        email: 'tenant@test.com',
        role: 'tenant' as const,
      }

      // Mock da resposta da API
      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'mock-token',
        token_type: 'Bearer',
        user: mockUser,
      })

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda inicialização
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Tenta fazer login
      await expect(
        result.current.login({
          email: 'tenant@test.com',
          password: 'password123',
        })
      ).rejects.toThrow('Acesso negado. Apenas administradores podem acessar este painel.')

      // Não deve estar autenticado
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()

      // localStorage deve estar limpo
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
    })

    it('deve limpar dados em caso de erro de login', async () => {
      // Mock de erro da API
      vi.mocked(authApi.login).mockRejectedValue(new Error('Credenciais inválidas'))

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda inicialização
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Tenta fazer login
      await expect(
        result.current.login({
          email: 'admin@test.com',
          password: 'wrong-password',
        })
      ).rejects.toThrow('Credenciais inválidas')

      // Não deve estar autenticado
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
    })
  })

  describe('Logout', () => {
    it('deve fazer logout e limpar dados', async () => {
      // Configura estado autenticado
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      // Mock da API de logout
      vi.mocked(authApi.logout).mockResolvedValue(undefined)

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda carregar autenticação
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
      })

      // Executa logout
      await result.current.logout()

      // Verifica que API foi chamada
      expect(authApi.logout).toHaveBeenCalled()

      // Verifica estado limpo
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(result.current.token).toBeNull()

      // Verifica localStorage limpo
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()

      // Verifica navegação para login
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })

    it('deve limpar dados locais mesmo se API de logout falhar', async () => {
      // Configura estado autenticado
      const mockUser = {
        id: '1',
        email: 'admin@test.com',
        role: 'admin' as const,
      }
      const mockToken = 'mock-jwt-token'

      localStorage.setItem('auth_token', mockToken)
      localStorage.setItem('auth_user', JSON.stringify(mockUser))

      // Mock de erro na API de logout
      vi.mocked(authApi.logout).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useAuth(), { wrapper })

      // Aguarda carregar autenticação
      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true)
      })

      // Executa logout
      await result.current.logout()

      // Mesmo com erro, deve limpar dados locais
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBeNull()
      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(localStorage.getItem('auth_user')).toBeNull()
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })
})
