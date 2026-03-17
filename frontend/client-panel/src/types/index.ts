/**
 * Definições de tipos TypeScript para o painel do cliente.
 * 
 * Tipos principais:
 * - Device: Dispositivo registrado
 * - Event: Evento detectado
 * - NotificationConfig: Configuração de notificações
 * - Subscription: Assinatura e billing
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
  plan_type?: PlanType
}

// ============================================================================
// Tipos de Plano
// ============================================================================

export type PlanType = 'basic' | 'premium'
export type TenantStatus = 'trial' | 'active' | 'suspended' | 'expired'

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

export interface RegisterDeviceRequest {
  activation_key: string
  name: string
}

export interface UpdateDeviceRequest {
  name?: string
  config?: Partial<DeviceConfig>
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
  device?: Device
}

export interface EventFilters {
  device_id?: string
  event_type?: EventType
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface MarkFalsePositiveRequest {
  user_notes?: string
}

// ============================================================================
// Tipos de Notificação
// ============================================================================

export type NotificationChannel = 'telegram' | 'email' | 'webhook'

export interface NotificationConfig {
  id: string
  tenant_id: string
  enabled: boolean
  channels: NotificationChannel[]
  min_confidence: number
  cooldown_seconds: number
  quiet_hours: QuietHours | null
  
  // Telegram
  telegram_bot_token?: string
  telegram_chat_ids?: string[]
  
  // Email
  email_recipients?: string[]
  
  // Webhook
  webhook_urls?: string[]
  webhook_secret?: string
  
  updated_at: string
}

export interface QuietHours {
  start: string  // HH:MM formato 24h
  end: string    // HH:MM formato 24h
}

export interface UpdateNotificationConfigRequest {
  enabled?: boolean
  channels?: NotificationChannel[]
  min_confidence?: number
  cooldown_seconds?: number
  quiet_hours?: QuietHours | null
  telegram_bot_token?: string
  telegram_chat_ids?: string[]
  email_recipients?: string[]
  webhook_urls?: string[]
  webhook_secret?: string
}

export interface TestNotificationRequest {
  channel: NotificationChannel
}

export interface NotificationLog {
  id: string
  tenant_id: string
  event_id: string
  channel: NotificationChannel
  recipient: string
  success: boolean
  error_message: string | null
  timestamp: string
}

// ============================================================================
// Tipos de Assinatura e Billing
// ============================================================================

export interface Subscription {
  tenant_id: string
  plan_type: PlanType
  status: TenantStatus
  trial_ends_at: string | null
  next_billing_date: string | null
  monthly_amount: number
  devices_count: number
  device_limit: number
}

export interface Invoice {
  id: string
  tenant_id: string
  amount: number
  status: 'pending' | 'paid' | 'failed' | 'refunded'
  due_date: string
  paid_at: string | null
  line_items: InvoiceLineItem[]
  created_at: string
}

export interface InvoiceLineItem {
  description: string
  quantity: number
  unit_price: number
  total: number
}

export interface UpgradePlanRequest {
  plan_type: PlanType
}

export interface UpdatePaymentMethodRequest {
  payment_method_id: string
}

// ============================================================================
// Tipos de Dashboard
// ============================================================================

export interface DashboardStats {
  devices_online: number
  devices_total: number
  events_today: number
  events_week: number
  last_event_at: string | null
}

export interface SignalStrengthData {
  timestamp: string
  device_id: string
  device_name: string
  rssi: number
  signal_quality: number
}

// ============================================================================
// Tipos de WebSocket
// ============================================================================

export interface WebSocketMessage {
  type: 'event' | 'device_status' | 'notification'
  data: any
}

export interface EventWebSocketData {
  event_id: string
  device_id: string
  event_type: EventType
  confidence: number
  timestamp: string
}

export interface DeviceStatusWebSocketData {
  device_id: string
  status: DeviceStatus
  last_seen: string
}

// ============================================================================
// Tipos de Paginação
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
