/* MonitorControls — Controles de monitoramento e simulação */

import { Play, Square } from 'lucide-react';
import { useStore } from '../store/useStore';
import { api } from '../services/api';
import { SIMULATION_LABELS, type SimulationMode } from '../types';

const MODES: SimulationMode[] = [
  'empty',
  'still',
  'moving',
  'fall',
  'post_fall_inactivity',
  'random',
];

export function MonitorControls() {
  const isMonitoring = useStore((s) => s.isMonitoring);
  const simulationMode = useStore((s) => s.simulationMode);
  const setMonitoring = useStore((s) => s.setMonitoring);
  const setSimulationMode = useStore((s) => s.setSimulationMode);

  const handleStart = async () => {
    await api.startMonitor();
    setMonitoring(true);
  };

  const handleStop = async () => {
    await api.stopMonitor();
    setMonitoring(false);
  };

  const handleModeChange = async (mode: SimulationMode) => {
    await api.setSimulationMode(mode);
    setSimulationMode(mode);
  };

  return (
    <div className="controls-container">
      <div className="controls-buttons">
        {!isMonitoring ? (
          <button className="btn btn-start" onClick={handleStart}>
            <Play size={18} />
            Iniciar Monitoramento
          </button>
        ) : (
          <button className="btn btn-stop" onClick={handleStop}>
            <Square size={18} />
            Parar Monitoramento
          </button>
        )}
      </div>

      <div className="controls-modes">
        <label className="controls-label">Modo de Simulação</label>
        <div className="mode-grid">
          {MODES.map((mode) => (
            <button
              key={mode}
              className={`mode-btn ${simulationMode === mode ? 'active' : ''}`}
              onClick={() => handleModeChange(mode)}
            >
              {SIMULATION_LABELS[mode]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
