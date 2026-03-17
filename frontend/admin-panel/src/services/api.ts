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
  Tenant,
  CreateTenantRequest,
  UpdateTenantRequest,
  License,
  CreateLicenseRequest,
  ExtendLicenseRequest,
  Device,
  AuditLog,
  SystemMetrics,
  PaginatedResponse,
  TenantFilters,
  LicenseFilters,
  DeviceFilters,
  AuditLogFilters,
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
   * Realiza login de administrador
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
// API de Tenants
// ============================================================================

export const tenantsApi = {
  /**
   * Lista todos os tenants com filtros e paginação
   */
  list: (filters?: TenantFilters) =>
    http.get<PaginatedResponse<Tenant>>('/admin/tenants', filters),

  /**
   * Obtém detalhes de um tenant específico
   */
  get: (id: string) =>
    http.get<Tenant>(`/admin/tenants/${id}`),

  /**
   * Cria um novo tenant
   */
  create: (data: CreateTenantRequest) =>
    http.post<Tenant>('/admin/tenants', data),

  /**
   * Atualiza um tenant existente
   */
  update: (id: string, data: UpdateTenantRequest) =>
    http.put<Tenant>(`/admin/tenants/${id}`, data),

  /**
   * Deleta um tenant (cascade)
   */
  delete: (id: string) =>
    http.delete<void>(`/admin/tenants/${id}`),

  /**
   * Suspende um tenant
   */
  suspend: (id: string) =>
    http.post<Tenant>(`/admin/tenants/${id}/suspend`),

  /**
   * Ativa um tenant suspenso
   */
  activate: (id: string) =>
    http.post<Tenant>(`/admin/tenants/${id}/activate`),
}

// ============================================================================
// API de Licenças
// ============================================================================

export const licensesApi = {
  /**
   * Lista todas as licenças com filtros e paginação
   */
  list: (filters?: LicenseFilters) =>
    http.get<PaginatedResponse<License>>('/admin/licenses', filters),

  /**
   * Obtém detalhes de uma licença específica
   */
  get: (id: string) =>
    http.get<License>(`/admin/licenses/${id}`),

  /**
   * Gera uma nova licença
   */
  create: (data: CreateLicenseRequest) =>
    http.post<License>('/admin/licenses', data),

  /**
   * Revoga uma licença
   */
  revoke: (id: string) =>
    http.put<License>(`/admin/licenses/${id}/revoke`),

  /**
   * Estende a expiração de uma licença
   */
  extend: (id: string, data: ExtendLicenseRequest) =>
    http.put<License>(`/admin/licenses/${id}/extend`, data),
}

// ============================================================================
// API de Dispositivos
// ============================================================================

export const devicesApi = {
  /**
   * Lista todos os dispositivos com filtros e paginação
   */
  list: (filters?: DeviceFilters) =>
    http.get<PaginatedResponse<Device>>('/devices', filters),

  /**
   * Obtém detalhes de um dispositivo específico
   */
  get: (id: string) =>
    http.get<Device>(`/devices/${id}`),

  /**
   * Obtém status em tempo real de um dispositivo
   */
  getStatus: (id: string) =>
    http.get<Device>(`/devices/${id}/status`),
}

// ============================================================================
// API de Logs de Auditoria
// ============================================================================

export const auditLogsApi = {
  /**
   * Lista logs de auditoria com filtros e paginação
   */
  list: (filters?: AuditLogFilters) =>
    http.get<PaginatedResponse<AuditLog>>('/audit-logs', filters),
}

// ============================================================================
// API de Métricas
// ============================================================================

export const metricsApi = {
  /**
   * Obtém métricas globais do sistema
   */
  getSystem: () =>
    http.get<SystemMetrics>('/metrics'),
}

// Exporta cliente HTTP para uso direto se necessário
export { http }
