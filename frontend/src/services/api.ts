/* API service — fetch wrapper para o backend */

import type {
  AppConfig,
  AnomalyRecord,
  BehaviorPattern,
  CalibrationProfile,
  CalibrationProgress,
  EventRecord,
  EventStats,
  HealthStatus,
  MLCollectionStatus,
  NotificationLog,
  PerformanceStats,
  SystemStatus,
  Zone,
} from '../types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function requestBlob(path: string): Promise<Blob> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.blob();
}

export const api = {
  /* ── sistema ────────────────────────────────────────────────── */
  getHealth: () => request<HealthStatus>('/health'),
  getStatus: () => request<SystemStatus>('/status'),
  startMonitor: () => request<{ status: string }>('/monitor/start', { method: 'POST' }),
  stopMonitor: () => request<{ status: string }>('/monitor/stop', { method: 'POST' }),

  /* ── eventos ────────────────────────────────────────────────── */
  getEvents: (limit = 100, eventType?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (eventType) params.set('event_type', eventType);
    return request<EventRecord[]>(`/events?${params}`);
  },

  /* ── config ─────────────────────────────────────────────────── */
  getConfig: () => request<AppConfig>('/config'),
  updateConfig: (data: Partial<AppConfig>) =>
    request<AppConfig>('/config', { method: 'POST', body: JSON.stringify(data) }),
  listConfigProfiles: () => request<{ profiles: string[] }>('/config/profiles'),
  saveConfigProfile: (name: string) => request<AppConfig>(`/config/profiles/${name}`, { method: 'POST' }),
  activateConfigProfile: (name: string) => request<AppConfig>(`/config/profiles/${name}/activate`, { method: 'POST' }),
  deleteConfigProfile: (name: string) => request<void>(`/config/profiles/${name}`, { method: 'DELETE' }),

  /* ── simulação e power save ─────────────────────────────────── */
  setSimulationMode: (mode: string) =>
    request<{ status: string; mode: string }>('/simulation/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  getSimulationModes: () =>
    request<{ modes: { value: string; description: string }[]; current_mode: string }>('/simulation/modes'),
  enablePowerSave: () => request<{ status: string; sampling_interval: number }>('/power-save/enable', { method: 'POST' }),
  disablePowerSave: () => request<{ status: string; sampling_interval: number }>('/power-save/disable', { method: 'POST' }),
  getPowerSaveStatus: () => request<{ active: boolean; sampling_interval: number }>('/power-save/status'),

  /* ── calibração ─────────────────────────────────────────────── */
  startCalibration: (profileName: string, durationSeconds: number) =>
    request<{ status: string; profile_name: string }>('/calibration/start', {
      method: 'POST',
      body: JSON.stringify({ profile_name: profileName, duration_seconds: durationSeconds }),
    }),
  stopCalibration: () => request<{ status: string }>('/calibration/stop', { method: 'POST' }),
  getCalibrationProgress: () => request<CalibrationProgress>('/calibration/progress'),
  listCalibrationProfiles: () => request<CalibrationProfile[]>('/calibration/profiles'),
  activateCalibrationProfile: (name: string) =>
    request<{ status: string; profile_name: string }>(`/calibration/profiles/${name}/activate`, { method: 'POST' }),
  deleteCalibrationProfile: (name: string) =>
    request<void>(`/calibration/profiles/${name}`, { method: 'DELETE' }),

  /* ── zonas ──────────────────────────────────────────────────── */
  listZones: () => request<Zone[]>('/zones'),
  createZone: (data: { name: string; rssi_min: number; rssi_max: number; alert_config_json?: string }) =>
    request<Zone>('/zones', { method: 'POST', body: JSON.stringify(data) }),
  updateZone: (id: number, data: { name: string; rssi_min: number; rssi_max: number; alert_config_json?: string }) =>
    request<Zone>(`/zones/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteZone: (id: number) => request<void>(`/zones/${id}`, { method: 'DELETE' }),
  getCurrentZone: () => request<{ current_zone: Zone | null; rssi: number | null; message: string }>('/zones/current'),

  /* ── estatísticas ───────────────────────────────────────────── */
  getEventStats: (periodHours = 24) =>
    request<EventStats>(`/stats?period_hours=${periodHours}`),
  getBehaviorPatterns: () => request<BehaviorPattern[]>('/stats/patterns'),
  getAnomalies: (periodHours = 24) =>
    request<{ period_hours: number; total: number; anomalies: AnomalyRecord[] }>(`/stats/anomalies?period_hours=${periodHours}`),
  getPerformanceStats: (periodHours = 1) =>
    request<PerformanceStats>(`/stats/performance?period_hours=${periodHours}`),

  /* ── exportação ─────────────────────────────────────────────── */
  exportEventsCsv: (periodHours = 24) => requestBlob(`/export/events.csv?period_hours=${periodHours}`),
  exportEventsJson: (periodHours = 24) => requestBlob(`/export/events.json?period_hours=${periodHours}`),
  exportBackup: (periodHours = 168) => requestBlob(`/export/backup?period_hours=${periodHours}`),

  /* ── ML ─────────────────────────────────────────────────────── */
  startMLCollection: () => request<{ status: string }>('/ml/data-collection/start', { method: 'POST' }),
  stopMLCollection: () => request<{ status: string; samples_collected: number }>('/ml/data-collection/stop', { method: 'POST' }),
  getMLCollectionStatus: () => request<MLCollectionStatus>('/ml/data-collection/status'),
  labelMLEvent: (label: string, windowSeconds = 10) =>
    request<{ status: string; samples_labeled: number; total_samples: number }>('/ml/label', {
      method: 'POST',
      body: JSON.stringify({ label, window_seconds: windowSeconds }),
    }),
  exportMLDataset: () => requestBlob('/ml/export'),
  triggerTraining: () => request<{ status: string; message: string }>('/ml/train', { method: 'POST' }),
  getTrainingStatus: () => request<{ running: boolean; error: string | null; result: string | null }>('/ml/train/status'),

  /* ── notificações ───────────────────────────────────────────── */
  getNotificationLogs: (limit = 50) => request<NotificationLog[]>(`/notifications/logs?limit=${limit}`),
  getNotificationConfig: () => request<Record<string, unknown>>('/notifications/config'),
  testNotification: (channel: string, message?: string) =>
    request<{ status: string }>('/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ channel, message: message ?? 'Teste de notificação WiFiSense' }),
    }),
};
