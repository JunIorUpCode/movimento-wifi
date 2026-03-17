/* API service — fetch wrapper para o backend */

import type { AppConfig, EventRecord, HealthStatus, SystemStatus } from '../types';

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

export const api = {
  getHealth: () => request<HealthStatus>('/health'),

  getStatus: () => request<SystemStatus>('/status'),

  getEvents: (limit = 100, eventType?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (eventType) params.set('event_type', eventType);
    return request<EventRecord[]>(`/events?${params}`);
  },

  getConfig: () => request<AppConfig>('/config'),

  updateConfig: (data: Partial<AppConfig>) =>
    request<AppConfig>('/config', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  setSimulationMode: (mode: string) =>
    request<{ status: string; mode: string }>('/simulation/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),

  startMonitor: () =>
    request<{ status: string }>('/monitor/start', { method: 'POST' }),

  stopMonitor: () =>
    request<{ status: string }>('/monitor/stop', { method: 'POST' }),
};
