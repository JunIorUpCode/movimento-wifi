/**
 * Testes unitários para o cliente HTTP e APIs.
 * 
 * Testa:
 * - Métodos HTTP (GET, POST, PUT, DELETE)
 * - Interceptor de autenticação (JWT token)
 * - Tratamento de erros
 * - APIs específicas (auth, devices, events, notifications, billing)
 */

import { authApi, devicesApi, eventsApi, notificationsApi, billingApi, ApiError } from '../../services/api'

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('Interceptor de Autenticação', () => {
    it('deve incluir token JWT no header Authorization quando disponível', async () => {
      const mockToken = 'mock-jwt-token'
      
      // Mock do localStorage.getItem para retornar o token
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
        if (key === 'auth_token') return mockToken
        return null
      })

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ([]),
      })

      await devicesApi.list()

      expect(global.fetch).toHaveBeenCalled()
      
      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const headers = fetchCall[1]?.headers as Record<string, string>
      expect(headers['Authorization']).toBe(`Bearer ${mockToken}`)
    })

    it('não deve incluir Authorization header quando token não existe', async () => {
      localStorage.removeItem('auth_token')

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: 'new-token', user: {} }),
      })

      await authApi.login({ email: 'test@test.com', password: 'pass' })

      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const headers = fetchCall[1]?.headers as Record<string, string>
      expect(headers['Authorization']).toBeUndefined()
    })
  })

  describe('Tratamento de Erros', () => {
    it('deve lançar ApiError quando resposta não é ok', async () => {
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
        user: { id: '1', email: 'tenant@test.com', role: 'tenant' },
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await authApi.login({
        email: 'tenant@test.com',
        password: 'password123',
      })

      expect(result).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'tenant@test.com',
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

  describe('devicesApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('list: deve fazer GET para /devices', async () => {
      const mockDevices = [
        { id: '1', name: 'Device 1', status: 'online' },
        { id: '2', name: 'Device 2', status: 'offline' },
      ]

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDevices,
      })

      const result = await devicesApi.list()

      expect(result).toEqual(mockDevices)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('get: deve fazer GET para /devices/:id', async () => {
      const mockDevice = {
        id: '1',
        name: 'Device 1',
        status: 'online',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDevice,
      })

      const result = await devicesApi.get('1')

      expect(result).toEqual(mockDevice)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/1'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('register: deve fazer POST para /devices/register', async () => {
      const registerData = {
        activation_key: 'XXXX-XXXX-XXXX-XXXX',
        name: 'New Device',
      }

      const mockResponse = {
        id: '1',
        ...registerData,
        status: 'online',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await devicesApi.register(registerData)

      expect(result.name).toBe(registerData.name)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(registerData),
        })
      )
    })

    it('update: deve fazer PUT para /devices/:id', async () => {
      const updateData = {
        name: 'Updated Device',
      }

      const mockResponse = {
        id: '1',
        ...updateData,
        status: 'online',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await devicesApi.update('1', updateData)

      expect(result.name).toBe(updateData.name)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('delete: deve fazer DELETE para /devices/:id', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })

      await devicesApi.delete('1')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/1'),
        expect.objectContaining({ method: 'DELETE' })
      )
    })

    it('getStatus: deve fazer GET para /devices/:id/status', async () => {
      const mockStatus = {
        id: '1',
        status: 'online',
        last_seen: new Date().toISOString(),
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockStatus,
      })

      const result = await devicesApi.getStatus('1')

      expect(result.status).toBe('online')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/devices/1/status'),
        expect.objectContaining({ method: 'GET' })
      )
    })
  })

  describe('eventsApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('list: deve fazer GET para /events com filtros', async () => {
      const mockResponse = {
        items: [{ id: '1', type: 'presence_detected' }],
        total: 1,
        page: 1,
        page_size: 10,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await eventsApi.list({
        event_type: 'presence_detected',
        page: 1,
        page_size: 10,
      })

      expect(result).toEqual(mockResponse)
      
      const fetchCall = vi.mocked(global.fetch).mock.calls[0]
      const url = fetchCall[0] as string
      expect(url).toContain('/api/events')
      expect(url).toContain('event_type=presence_detected')
    })

    it('get: deve fazer GET para /events/:id', async () => {
      const mockEvent = {
        id: '1',
        type: 'presence_detected',
        device_id: 'dev-1',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEvent,
      })

      const result = await eventsApi.get('1')

      expect(result).toEqual(mockEvent)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/events/1'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('timeline: deve fazer GET para /events/timeline', async () => {
      const mockEvents = [
        { id: '1', type: 'presence_detected' },
        { id: '2', type: 'movement_detected' },
      ]

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEvents,
      })

      const result = await eventsApi.timeline({ page_size: 5 })

      expect(result).toEqual(mockEvents)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/events/timeline'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('stats: deve fazer GET para /events/stats', async () => {
      const mockStats = {
        events_today: 10,
        events_week: 50,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockStats,
      })

      const result = await eventsApi.stats()

      expect(result).toEqual(mockStats)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/events/stats'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('markFalsePositive: deve fazer POST para /events/:id/feedback', async () => {
      const mockEvent = {
        id: '1',
        is_false_positive: true,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockEvent,
      })

      const result = await eventsApi.markFalsePositive('1', { reason: 'Test' })

      expect(result.is_false_positive).toBe(true)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/events/1/feedback'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('notificationsApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('getConfig: deve fazer GET para /notifications/config', async () => {
      const mockConfig = {
        email_enabled: true,
        email_address: 'test@test.com',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockConfig,
      })

      const result = await notificationsApi.getConfig()

      expect(result).toEqual(mockConfig)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/notifications/config'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('updateConfig: deve fazer PUT para /notifications/config', async () => {
      const updateData = {
        email_enabled: true,
        email_address: 'new@test.com',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => updateData,
      })

      const result = await notificationsApi.updateConfig(updateData)

      expect(result).toEqual(updateData)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/notifications/config'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('test: deve fazer POST para /notifications/test', async () => {
      const testData = {
        channel: 'email' as const,
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })

      await notificationsApi.test(testData)

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/notifications/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(testData),
        })
      )
    })
  })

  describe('billingApi', () => {
    beforeEach(() => {
      localStorage.setItem('auth_token', 'mock-token')
    })

    it('getSubscription: deve fazer GET para /billing/subscription', async () => {
      const mockSubscription = {
        plan_type: 'premium',
        status: 'active',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSubscription,
      })

      const result = await billingApi.getSubscription()

      expect(result).toEqual(mockSubscription)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/billing/subscription'),
        expect.objectContaining({ method: 'GET' })
      )
    })

    it('upgradePlan: deve fazer POST para /billing/upgrade', async () => {
      const upgradeData = {
        plan_type: 'enterprise' as const,
      }

      const mockResponse = {
        plan_type: 'enterprise',
        status: 'active',
      }

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await billingApi.upgradePlan(upgradeData)

      expect(result.plan_type).toBe('enterprise')
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/billing/upgrade'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(upgradeData),
        })
      )
    })
  })
})
