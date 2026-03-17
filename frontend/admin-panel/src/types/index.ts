/**
 * Definições de tipos TypeScript para o painel administrativo.
 * 
 * Tipos principais:
 * - Tenant: Cliente da plataforma
 * - License: Licença de ativação
 * - Device: Dispositivo registrado
 * - Event: Evento detectado
 * - AuditLog: Log de auditoria
 */

// ============================================================================
// Tipos de Autenticação
// ============================================================================

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  role: 'admin' | 'tenant'
  name?: string
}

// ============================================================================
// Tipos de Tenant
// ============================================================================

export type TenantStatus = 'trial' | 'active' | 'suspended' | 'expired'
export type PlanType = 'basic' | 'premium'

export interface Tenant {
  id: string
  email: string
  name: string
  plan_type: PlanType
  status: TenantStatus
  trial_ends_at: string | null
  created_at: string
  updated_at: string
  
  // Campos calculados
  devices_count?: number
  active_licenses_count?: number
}

export interface CreateTenantRequest {
  email: string
  name: string
  password: string
  plan_type: PlanType
}

export interface UpdateTenantRequest {
  name?: string
  plan_type?: PlanType
  status?: TenantStatus
}

// ============================================================================
// Tipos de Licença
// ============================================================================

export type LicenseStatus = 'pending' | 'activated' | 'revoked' | 'expired'

export interface License {
  id: string
  tenant_id: string
  activation_key: string
  plan_type: PlanType
  device_limit: number
  expires_at: string
  activated_at: string | null
  device_id: string | null
  status: LicenseStatus
  created_at: string
  
  // Campos relacionados
  tenant?: Tenant
  device?: Device
}

export interface CreateLicenseRequest {
  tenant_id: string
  plan_type: PlanType
  device_limit: number
  expires_at: string
}

export interface ExtendLicenseRequest {
  expires_at: string
}

// ============================================================================
// Tipos de Dispositivo
// ============================================================================

export type DeviceStatus = 'online' | 'offline' | 'error'
export type HardwareType = 'raspberry_pi' | 'windows' | 'linux'

export interface Device {
  id: string
  tenant_id: string
  name: string
  hardware_type: HardwareType
  status: DeviceStatus
  last_seen: string
  registered_at: string
  hardware_info: HardwareInfo
  config: DeviceConfig
  
  // Campos relacionados
  tenant?: Tenant
  license?: License
  health?: DeviceHealth
}

export interface HardwareInfo {
  os: string
  csi_capable: boolean
  wifi_adapter: string
  cpu_model?: string
  memory_mb?: number
}

export interface DeviceConfig {
  sampling_interval: number
  detection_thresholds: {
    presence: number
    movement: number
    fall?: number
  }
  enabled_events: string[]
}

export interface DeviceHealth {
  cpu_percent: number
  memory_mb: number
  disk_percent: number
  timestamp: string
}

// ============================================================================
// Tipos de Evento
// ============================================================================

export type EventType = 'presence' | 'movement' | 'fall_suspected' | 'prolonged_inactivity'

export interface Event {
  id: string
  tenant_id: string
  device_id: string
  event_type: EventType
  confidence: number
  timestamp: string
  metadata: Record<string, any>
  is_false_positive: boolean
  user_notes: string | null
  
  // Campos relacionados
  device?: Device
}

// ============================================================================
// Tipos de Log de Auditoria
// ============================================================================

export interface AuditLog {
  id: string
  tenant_id: string | null
  admin_id: string | null
  action: string
  resource_type: string
  resource_id: string
  before_state: Record<string, any> | null
  after_state: Record<string, any> | null
  ip_address: string
  timestamp: string
  
  // Campos relacionados
  admin?: User
  tenant?: Tenant
}

// ============================================================================
// Tipos de Métricas
// ============================================================================

export interface SystemMetrics {
  total_tenants: number
  active_tenants: number
  total_devices: number
  devices_online: number
  total_events_today: number
  api_latency_ms: number
  cpu_usage_percent: number
  memory_usage_percent: number
}

export interface TenantMetrics {
  tenant_id: string
  devices_count: number
  events_count_today: number
  events_count_week: number
  last_event_at: string | null
}

// ============================================================================
// Tipos de Paginação e Filtros
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface TenantFilters extends PaginationParams {
  status?: TenantStatus
  plan_type?: PlanType
  search?: string
}

export interface LicenseFilters extends PaginationParams {
  tenant_id?: string
  status?: LicenseStatus
  plan_type?: PlanType
}

export interface DeviceFilters extends PaginationParams {
  tenant_id?: string
  status?: DeviceStatus
  plan_type?: PlanType
}

export interface AuditLogFilters extends PaginationParams {
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}

// ============================================================================
// Tipos de Resposta de API
// ============================================================================

export interface ApiError {
  error: {
    code: string
    message: string
    request_id?: string
  }
}

export interface ApiSuccess<T = any> {
  data: T
  message?: string
}
