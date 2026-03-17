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
