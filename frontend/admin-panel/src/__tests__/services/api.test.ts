/**
 * Testes unitários para o cliente HTTP e APIs.
 * 
 * Testa:
 * - Métodos HTTP (GET, POST, PUT, DELETE)
 * - Interceptor de autenticação (JWT token)
 * - Tratamento de erros
 * - APIs específicas (auth, tenants, licenses, devices)
 */

import { authApi, tenantsApi, licensesApi, devicesApi, metricsApi, ApiError } from '../../services/api'

describe('API Client', () => {
  beforeEach(() => {
    // Limpa mocks antes de cada teste
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('Interceptor de Autenticação', () => {
    it('deve incluir token JWT no header Authorization quando disponível', async () => {
      const mockToken = 'mock-jwt-token'
      localStorage.setItem('auth_token', mockToken)

      // Mock do fetch
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], total: 0 }),
      })

      await tenantsApi.list()

      // Verifica que fetch foi chamado
      expect(global.fetch).toHaveBeenCalled()
      
      // Verifica headers manualmente
      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const headers = fetchCall[1]?.headers as Record<string, string>
      expect(headers['Authorization']).toBe(`Bearer ${mockToken}`)
    })

    it('não deve incluir Authorization header quando token não existe', async () => {
      // Sem token no localStorage
      localStorage.removeItem('auth_token')

      // Mock do fetch
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: 'new-token', user: {} }),
      })

      await authApi.login({ email: 'test@test.com', password: 'pass' })

      // Verifica que fetch foi chamado sem Authorization header
      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const headers = fetchCall[1]?.headers as Record<string, string>
      expect(headers['Authorization']).toBeUndefined()
    })
  })

  describe('Tratamento de Erros', () => {
    it('deve lançar ApiError quando resposta não é ok', async () => {
      // Mock de resposta com erro
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Email ou senha incorretos',
            request_id: 'req-123',
          },
        }),
      })

      await expect(
        authApi.login({ email: 'wrong@test.com', password: 'wrong' })
      ).rejects.toThrow(ApiError)

      try {
        await authApi.login({ email: 'wrong@test.com', password: 'wrong' })
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        const apiError = error as ApiError
        expect(apiError.status).toBe(401)
        expect(apiError.code).toBe('INVALID_CREDENTIALS')
        expect(apiError.message).toBe('Email ou senha incorretos')
        expect(apiError.requestId).toBe('req-123')
      }
    })

    it('deve tratar erro quando resposta não tem JSON válido', async () => {
      // Mock de resposta com erro sem JSON
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(
        authApi.login({ email: 'test@test.com', password: 'pass' })
      ).rejects.toThrow(ApiError)

      try {
        await authApi.login({ email: 'test@test.com', password: 'pass' })
      } catch (error) {
        const apiError = error as ApiError
        expect(apiError.code).toBe('UNKNOWN_ERROR')
        expect(apiError.message).toContain('Erro desconhecido')
      }
    })
  })

  describe('authApi', () => {
    it('login: deve fazer POST para /auth/login', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'Bearer',
        user: { id: '1', email: 'admin@test.com', role: 'admin' },
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await authApi.login({
        email: 'admin@test.com',
        password: 'password123',
      })

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'admin@test.com',
            password: 'password123',
          }),
        })
      )
    })

    it('logout: deve fazer POST para /auth/logout', async () => {
      localStorage.setItem('auth_token', 'mock-token')

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })

      await authApi.logout()

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/logout'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })
  })

  describe('tenantsApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('list: deve fazer GET para /admin/tenants com filtros', async () => {
      const mockResponse = {
        items: [{ id: '1', email: 'tenant@test.com', name: 'Test Tenant' }],
        total: 1,
        page: 1,
        page_size: 10,
        total_pages: 1,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await tenantsApi.list({
        status: 'active',
        page: 1,
        page_size: 10,
      })

      expect(result).toEqual(mockResponse)
      
      // Verifica URL com query params
      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const url = fetchCall[0] as string
      expect(url).toContain('/api/admin/tenants')
      expect(url).toContain('status=active')
      expect(url).toContain('page=1')
      expect(url).toContain('page_size=10')
    })

    it('get: deve fazer GET para /admin/tenants/:id', async () => {
      const mockTenant = {
        id: '1',
        email: 'tenant@test.com',
        name: 'Test Tenant',
        plan_type: 'premium',
        status: 'active',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockTenant,
      })

      const result = await tenantsApi.get('1')

      expect(result).toEqual(mockTenant)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/tenants/1'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('create: deve fazer POST para /admin/tenants', async () => {
      const createData = {
        email: 'new@test.com',
        name: 'New Tenant',
        password: 'password123',
        plan_type: 'basic' as const,
      }

      const mockResponse = {
        id: '2',
        ...createData,
        status: 'trial',
        created_at: new Date().toISOString(),
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await tenantsApi.create(createData)

      expect(result.email).toBe(createData.email)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/tenants'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(createData),
        })
      )
    })

    it('suspend: deve fazer POST para /admin/tenants/:id/suspend', async () => {
      const mockResponse = {
        id: '1',
        status: 'suspended',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await tenantsApi.suspend('1')

      expect(result.status).toBe('suspended')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/tenants/1/suspend'),
        expect.objectContaining({ method: 'POST' })
      )
    })

    it('delete: deve fazer DELETE para /admin/tenants/:id', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })

      await tenantsApi.delete('1')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/tenants/1'),
        expect.objectContaining({ method: 'DELETE' })
      )
    })
  })

  describe('licensesApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('list: deve fazer GET para /admin/licenses', async () => {
      const mockResponse = {
        items: [{ id: '1', activation_key: 'XXXX-XXXX-XXXX-XXXX' }],
        total: 1,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await licensesApi.list()

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/licenses'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('create: deve fazer POST para /admin/licenses', async () => {
      const createData = {
        tenant_id: '1',
        plan_type: 'premium' as const,
        device_limit: 5,
        expires_at: '2025-12-31T23:59:59Z',
      }

      const mockResponse = {
        id: '1',
        ...createData,
        activation_key: 'XXXX-XXXX-XXXX-XXXX',
        status: 'pending',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await licensesApi.create(createData)

      expect(result.activation_key).toBeDefined()
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/licenses'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(createData),
        })
      )
    })

    it('revoke: deve fazer PUT para /admin/licenses/:id/revoke', async () => {
      const mockResponse = {
        id: '1',
        status: 'revoked',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await licensesApi.revoke('1')

      expect(result.status).toBe('revoked')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/admin/licenses/1/revoke'),
        expect.objectContaining({ method: 'PUT' })
      )
    })
  })

  describe('devicesApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('list: deve fazer GET para /devices', async () => {
      const mockResponse = {
        items: [{ id: '1', name: 'Device 1', status: 'online' }],
        total: 1,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await devicesApi.list()

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('getStatus: deve fazer GET para /devices/:id/status', async () => {
      const mockDevice = {
        id: '1',
        status: 'online',
        last_seen: new Date().toISOString(),
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDevice,
      })

      const result = await devicesApi.getStatus('1')

      expect(result.status).toBe('online')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/1/status'),
        expect.objectContaining({ method: 'GET' })
      )
    })
  })

  describe('metricsApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('getSystem: deve fazer GET para /metrics', async () => {
      const mockMetrics = {
        total_tenants: 10,
        active_tenants: 8,
        total_devices: 25,
        devices_online: 20,
        total_events_today: 150,
        api_latency_ms: 45,
        cpu_usage_percent: 35.5,
        memory_usage_percent: 60.2,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockMetrics,
      })

      const result = await metricsApi.getSystem()

      expect(result).toEqual(mockMetrics)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metrics'),
        expect.objectContaining({ method: 'GET' })
      )
    })
  })
})
