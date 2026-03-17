/* Store global com Zustand */

import { create } from 'zustand';
import type {
  AppConfig,
  ChartDataPoint,
  EventRecord,
  EventType,
  LiveUpdate,
  SimulationMode,
  WsCalibrationProgress,
  WsAnomalyDetected,
} from '../types';

export type PageId =
  | 'dashboard'
  | 'history'
  | 'calibration'
  | 'statistics'
  | 'notifications'
  | 'zones'
  | 'ml'
  | 'replay'
  | 'pushnotifications'
  | 'settings'
  | 'family';

export type FamilyViewMode = 'pulso' | 'presenca' | 'radar';
export type Theme = 'dark' | 'light';

interface AppState {
  // Status
  isMonitoring: boolean;
  currentEvent: EventType;
  confidence: number;
  simulationMode: SimulationMode;
  uptimeSeconds: number;
  totalEvents: number;

  // Dados de sinal
  signalHistory: ChartDataPoint[];
  lastUpdate: LiveUpdate | null;

  // Alertas
  activeAlert: string | null;
  alertVisible: boolean;

  // Eventos
  events: EventRecord[];

  // Config
  config: AppConfig;

  // Navegação
  activePage: PageId;

  // Calibração (WebSocket)
  calibrationProgress: WsCalibrationProgress['data'] | null;

  // Anomalias recebidas via WS
  recentAnomalies: WsAnomalyDetected['data'][];

  // Notificações push no browser
  pushEnabled: boolean;

  // Painel Família
  familyViewMode: FamilyViewMode;
  theme: Theme;

  // Actions
  setMonitoring: (v: boolean) => void;
  setActivePage: (p: PageId) => void;
  setFamilyViewMode: (m: FamilyViewMode) => void;
  setTheme: (t: Theme) => void;
  setSimulationMode: (m: SimulationMode) => void;
  setConfig: (c: AppConfig) => void;
  setEvents: (e: EventRecord[]) => void;
  pushLiveUpdate: (u: LiveUpdate) => void;
  dismissAlert: () => void;
  setCalibrationProgress: (p: WsCalibrationProgress['data'] | null) => void;
  pushAnomaly: (a: WsAnomalyDetected['data']) => void;
  setPushEnabled: (v: boolean) => void;
  setStatus: (data: {
    is_monitoring: boolean;
    current_event: EventType;
    confidence: number;
    simulation_mode: SimulationMode;
    uptime_seconds: number;
    total_events: number;
  }) => void;
}

const MAX_CHART_POINTS = 60;
const MAX_ANOMALIES = 20;

export const useStore = create<AppState>((set) => ({
  isMonitoring: false,
  currentEvent: 'no_presence',
  confidence: 0,
  simulationMode: 'empty',
  uptimeSeconds: 0,
  totalEvents: 0,
  signalHistory: [],
  lastUpdate: null,
  activeAlert: null,
  alertVisible: false,
  events: [],
  config: {
    movement_sensitivity: 2.0,
    fall_threshold: 12.0,
    inactivity_timeout: 30.0,
    active_provider: 'mock',
    sampling_interval: 0.5,
  },
  activePage: 'dashboard',
  calibrationProgress: null,
  recentAnomalies: [],
  pushEnabled: false,
  familyViewMode: (localStorage.getItem('familyViewMode') as FamilyViewMode) || 'pulso',
  theme: (localStorage.getItem('theme') as Theme) || 'dark',

  setMonitoring: (v) => set({ isMonitoring: v }),
  setActivePage: (p) => set({ activePage: p }),
  setFamilyViewMode: (m) => {
    localStorage.setItem('familyViewMode', m);
    set({ familyViewMode: m });
  },
  setTheme: (t) => {
    localStorage.setItem('theme', t);
    document.documentElement.setAttribute('data-theme', t);
    set({ theme: t });
  },
  setSimulationMode: (m) => set({ simulationMode: m }),
  setConfig: (c) => set({ config: c }),
  setEvents: (e) => set({ events: e }),
  dismissAlert: () => set({ alertVisible: false, activeAlert: null }),
  setCalibrationProgress: (p) => set({ calibrationProgress: p }),
  setPushEnabled: (v) => set({ pushEnabled: v }),
  pushAnomaly: (a) =>
    set((state) => ({
      recentAnomalies: [a, ...state.recentAnomalies].slice(0, MAX_ANOMALIES),
    })),

  setStatus: (data) =>
    set({
      isMonitoring: data.is_monitoring,
      currentEvent: data.current_event,
      confidence: data.confidence,
      simulationMode: data.simulation_mode,
      uptimeSeconds: data.uptime_seconds,
      totalEvents: data.total_events,
    }),

  pushLiveUpdate: (u) =>
    set((state) => {
      const time = new Date(u.timestamp * 1000).toLocaleTimeString('pt-BR');
      const point: ChartDataPoint = {
        time,
        rssi: u.signal.rssi,
        energy: u.features.signal_energy,
        variance: u.features.signal_variance,
        instability: u.features.instability_score,
      };
      const history = [...state.signalHistory, point].slice(-MAX_CHART_POINTS);

      return {
        lastUpdate: u,
        currentEvent: u.event_type,
        confidence: u.confidence,
        signalHistory: history,
        activeAlert: u.alert || state.activeAlert,
        alertVisible: u.alert ? true : state.alertVisible,
      };
    }),
}));
