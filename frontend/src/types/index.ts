/* Tipos TypeScript espelhando os schemas do backend */

export type EventType =
  | 'no_presence'
  | 'presence_still'
  | 'presence_moving'
  | 'fall_suspected'
  | 'prolonged_inactivity';

export type SimulationMode =
  | 'empty'
  | 'still'
  | 'moving'
  | 'fall'
  | 'post_fall_inactivity'
  | 'random';

export interface EventRecord {
  id: number;
  timestamp: string;
  event_type: EventType;
  confidence: number;
  provider: string;
  metadata_json: string;
}

export interface SystemStatus {
  is_monitoring: boolean;
  current_event: EventType;
  confidence: number;
  simulation_mode: SimulationMode;
  provider: string;
  uptime_seconds: number;
  total_events: number;
  signal_data: SignalData | null;
  features: FeatureData | null;
}

export interface SignalData {
  rssi: number;
  csi_mean: number;
  timestamp: number;
}

export interface FeatureData {
  rssi_normalized: number;
  rssi_smoothed: number;
  signal_energy: number;
  signal_variance: number;
  rate_of_change: number;
  instability_score: number;
  csi_mean_amplitude: number;
}

export interface LiveUpdate {
  event_type: EventType;
  confidence: number;
  timestamp: number;
  signal: SignalData;
  features: FeatureData;
  alert: string | null;
}

export interface AppConfig {
  movement_sensitivity: number;
  fall_threshold: number;
  inactivity_timeout: number;
  active_provider: string;
  sampling_interval: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  uptime_seconds: number;
}

/* Dados para gráficos */
export interface ChartDataPoint {
  time: string;
  rssi: number;
  energy: number;
  variance: number;
  instability: number;
}

/* Labels amigáveis */
export const EVENT_LABELS: Record<EventType, string> = {
  no_presence: 'Sem Presença',
  presence_still: 'Presença (Parado)',
  presence_moving: 'Presença (Movendo)',
  fall_suspected: '⚠️ Queda Suspeita',
  prolonged_inactivity: '⏳ Inatividade Prolongada',
};

export const EVENT_COLORS: Record<EventType, string> = {
  no_presence: '#6b7280',
  presence_still: '#3b82f6',
  presence_moving: '#10b981',
  fall_suspected: '#ef4444',
  prolonged_inactivity: '#f59e0b',
};

export const SIMULATION_LABELS: Record<SimulationMode, string> = {
  empty: 'Ambiente Vazio',
  still: 'Pessoa Parada',
  moving: 'Pessoa Andando',
  fall: 'Queda Simulada',
  post_fall_inactivity: 'Imobilidade Pós-Queda',
  random: 'Aleatório',
};

/* Calibração */
export interface CalibrationProfile {
  id: number;
  name: string;
  baseline_json: string;
  created_at: string;
  updated_at: string | null;
  is_active: boolean;
}

export interface CalibrationProgress {
  running: boolean;
  profile_name: string | null;
  duration_seconds: number;
  elapsed_seconds: number | null;
  error: string | null;
  result: {
    mean_rssi: number;
    std_rssi: number;
    mean_variance: number;
    noise_floor: number;
    samples_count: number;
  } | null;
}

/* Zonas */
export interface Zone {
  id: number;
  name: string;
  rssi_min: number;
  rssi_max: number;
  alert_config_json: string;
  created_at: string;
}

/* Estatísticas */
export interface EventStats {
  total_events: number;
  by_type: Record<string, number>;
  avg_confidence: number;
  period_hours: number;
}

export interface BehaviorPattern {
  id: number;
  hour_of_day: number;
  day_of_week: number;
  presence_probability: number;
  avg_movement_level: number;
  sample_count: number;
  last_updated: string;
}

export interface PerformanceStats {
  avg_total_latency_ms: number;
  avg_capture_time_ms: number;
  avg_processing_time_ms: number;
  avg_detection_time_ms: number;
  avg_memory_usage_mb: number;
  avg_cpu_usage_percent: number;
  samples_count: number;
}

export interface AnomalyRecord {
  id: number;
  timestamp: string;
  event_type: string;
  confidence: number;
  provider: string;
}

/* ML */
export interface MLCollectionStatus {
  is_collecting: boolean;
  total_samples: number;
  pending_features: number;
  label_distribution: Record<string, number>;
  models_dir: string;
}

/* Notificações */
export interface NotificationLog {
  id: number;
  timestamp: string;
  channel: string;
  event_type: string;
  confidence: number;
  recipient: string;
  success: boolean;
  error_message: string | null;
  alert_data: string;
}

/* WebSocket — novos tipos de evento */
export interface WsCalibrationProgress {
  type: 'calibration_progress';
  data: {
    profile_name: string;
    elapsed_seconds: number;
    duration_seconds: number;
    progress_percent: number;
    phase: 'collecting' | 'calculating' | 'done' | 'error';
  };
}

export interface WsNotificationSent {
  type: 'notification_sent';
  data: {
    channel: string;
    event_type: string;
    confidence: number;
    success: boolean;
    recipient: string;
  };
}

export interface WsAnomalyDetected {
  type: 'anomaly_detected';
  data: {
    event_type: string;
    confidence: number;
    timestamp: number;
    details: Record<string, unknown>;
  };
}

export type WsMessage =
  | (LiveUpdate & { type?: undefined })
  | WsCalibrationProgress
  | WsNotificationSent
  | WsAnomalyDetected;
