/**
 * Cliente HTTP para comunicação com a API backend.
 * 
 * Funcionalidades:
 * - Interceptors para adicionar token JWT automaticamente
 * - Tratamento de erros centralizado
 * - Métodos helper para GET, POST, PUT, DELETE
 */

import type {
  LoginCredentials,
  AuthResponse,
  Device,
  RegisterDeviceRequest,
  UpdateDeviceRequest,
  Event,
  EventFilters,
  MarkFalsePositiveRequest,
  NotificationConfig,
  UpdateNotificationConfigRequest,
  TestNotificationRequest,
  NotificationLog,
  Subscription,
  Invoice,
  UpgradePlanRequest,
  UpdatePaymentMethodRequest,
  DashboardStats,
  SignalStrengthData,
  PaginatedResponse,
} from '../types'

// URL base da API (configurável via variável de ambiente)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Classe de erro personalizada para erros de API
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public requestId?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Cliente HTTP base com interceptors
 */
class HttpClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  /**
   * Obtém o token JWT do localStorage
   */
  private getToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  /**
   * Constrói headers padrão para requisições
   */
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }

    const token = this.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }

  /**
   * Trata resposta da API
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: {
          code: 'UNKNOWN_ERROR',
          message: 'Erro desconhecido ao processar resposta',
        },
      }))

      throw new ApiError(
        response.status,
        error.error?.code || 'UNKNOWN_ERROR',
        error.error?.message || 'Erro desconhecido',
        error.error?.request_id
      )
    }

    return response.json()
  }

  /**
   * Método GET
   */
  async get<T>(path: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(`${this.baseURL}${path}`, window.location.origin)
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value))
        }
      })
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    })

    return this.handleResponse<T>(response)
  }

  /**
   * Método POST
   */
  async post<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    return this.handleResponse<T>(response)
  }

  /**
   * Método PUT
   */
  async put<T>(path: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })

    return this.handleResponse<T>(response)
  }

  /**
   * Método DELETE
   */
  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })

    return this.handleResponse<T>(response)
  }
}

// Instância do cliente HTTP
const http = new HttpClient(API_BASE_URL)

// ============================================================================
// API de Autenticação
// ============================================================================

export const authApi = {
  /**
   * Realiza login de tenant
   */
  login: (credentials: LoginCredentials) =>
    http.post<AuthResponse>('/auth/login', credentials),

  /**
   * Realiza logout (invalida token)
   */
  logout: () =>
    http.post<void>('/auth/logout'),
}

// ============================================================================
// API de Dispositivos
// ============================================================================

export const devicesApi = {
  /**
   * Lista todos os dispositivos do tenant
   */
  list: () =>
    http.get<Device[]>('/devices'),

  /**
   * Obtém detalhes de um dispositivo específico
   */
  get: (id: string) =>
    http.get<Device>(`/devices/${id}`),

  /**
   * Registra um novo dispositivo com chave de ativação
   */
  register: (data: RegisterDeviceRequest) =>
    http.post<Device>('/devices/register', data),

  /**
   * Atualiza configuração de um dispositivo
   */
  update: (id: string, data: UpdateDeviceRequest) =>
    http.put<Device>(`/devices/${id}`, data),

  /**
   * Desativa um dispositivo
   */
  delete: (id: string) =>
    http.delete<void>(`/devices/${id}`),

  /**
   * Obtém status em tempo real de um dispositivo
   */
  getStatus: (id: string) =>
    http.get<Device>(`/devices/${id}/status`),
}

// ============================================================================
// API de Eventos
// ============================================================================

export const eventsApi = {
  /**
   * Lista eventos do tenant com filtros e paginação
   */
  list: (filters?: EventFilters) =>
    http.get<PaginatedResponse<Event>>('/events', filters),

  /**
   * Obtém detalhes de um evento específico
   */
  get: (id: string) =>
    http.get<Event>(`/events/${id}`),

  /**
   * Obtém timeline de eventos
   */
  timeline: (filters?: EventFilters) =>
    http.get<Event[]>('/events/timeline', filters),

  /**
   * Obtém estatísticas de eventos
   */
  stats: () =>
    http.get<DashboardStats>('/events/stats'),

  /**
   * Marca um evento como falso positivo
   */
  markFalsePositive: (id: string, data?: MarkFalsePositiveRequest) =>
    http.post<Event>(`/events/${id}/feedback`, data),
}

// ============================================================================
// API de Notificações
// ============================================================================

export const notificationsApi = {
  /**
   * Obtém configuração de notificações do tenant
   */
  getConfig: () =>
    http.get<NotificationConfig>('/notifications/config'),

  /**
   * Atualiza configuração de notificações
   */
  updateConfig: (data: UpdateNotificationConfigRequest) =>
    http.put<NotificationConfig>('/notifications/config', data),

  /**
   * Testa um canal de notificação
   */
  test: (data: TestNotificationRequest) =>
    http.post<void>('/notifications/test', data),

  /**
   * Obtém logs de entrega de notificações
   */
  getLogs: (params?: { page?: number; page_size?: number }) =>
    http.get<PaginatedResponse<NotificationLog>>('/notifications/logs', params),
}

// ============================================================================
// API de Billing e Assinatura
// ============================================================================

export const billingApi = {
  /**
   * Obtém assinatura atual do tenant
   */
  getSubscription: () =>
    http.get<Subscription>('/billing/subscription'),

  /**
   * Faz upgrade de plano
   */
  upgradePlan: (data: UpgradePlanRequest) =>
    http.post<Subscription>('/billing/upgrade', data),

  /**
   * Atualiza método de pagamento
   */
  updatePaymentMethod: (data: UpdatePaymentMethodRequest) =>
    http.post<void>('/billing/payment-method', data),

  /**
   * Obtém histórico de faturas
   */
  getInvoices: (params?: { page?: number; page_size?: number }) =>
    http.get<PaginatedResponse<Invoice>>('/billing/invoices', params),

  /**
   * Obtém estatísticas de uso
   */
  getUsage: () =>
    http.get<DashboardStats>('/billing/usage'),
}

// ============================================================================
// API de Dashboard
// ============================================================================

export const dashboardApi = {
  /**
   * Obtém estatísticas do dashboard
   */
  getStats: () =>
    http.get<DashboardStats>('/events/stats'),

  /**
   * Obtém dados de signal strength em tempo real
   */
  getSignalStrength: (deviceId?: string) =>
    http.get<SignalStrengthData[]>('/devices/signal-strength', { device_id: deviceId }),
}

// Exporta cliente HTTP para uso direto se necessário
export { http }
