/* Settings — Página de configurações */

import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import type { AppConfig } from '../types';
import { Save, RotateCcw } from 'lucide-react';

interface ProvidersAvailability {
  csi: boolean;
  rssi_windows: boolean;
  rssi_linux: boolean;
  mock: boolean;
}

export function Settings() {
  const config = useStore((s) => s.config);
  const setConfig = useStore((s) => s.setConfig);
  const [local, setLocal] = useState<AppConfig>(config);
  const [saved, setSaved] = useState(false);
  const [providers, setProviders] = useState<ProvidersAvailability>({
    csi: false, rssi_windows: false, rssi_linux: false, mock: true,
  });

  useEffect(() => {
    api.getConfig().then((c) => {
      setConfig(c);
      setLocal(c);
    });
    // Detecta OS para habilitar providers disponíveis
    // RssiWindowsProvider.is_available() sempre retorna True no Windows
    const isWindows = navigator.platform.toLowerCase().includes('win')
      || navigator.userAgent.toLowerCase().includes('windows');
    setProviders({
      csi: false,         // CSI requer hardware especial
      rssi_windows: isWindows,
      rssi_linux: !isWindows,
      mock: true,
    });
  }, [setConfig]);

  const handleSave = async () => {
    try {
      const updated = await api.updateConfig(local);
      setConfig(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      console.error('Erro ao salvar config:', e);
    }
  };

  const handleReset = () => {
    const defaults: AppConfig = {
      movement_sensitivity: 2.0,
      fall_threshold: 12.0,
      inactivity_timeout: 30.0,
      active_provider: 'mock',
      sampling_interval: 0.5,
    };
    setLocal(defaults);
  };

  return (
    <div className="settings-page">
      <h2>Configurações</h2>

      <div className="settings-grid">
        <div className="setting-group">
          <label>Sensibilidade de Movimento</label>
          <input
            type="range"
            min="0.5"
            max="10"
            step="0.5"
            value={local.movement_sensitivity}
            onChange={(e) =>
              setLocal({ ...local, movement_sensitivity: Number(e.target.value) })
            }
          />
          <span className="setting-value">{local.movement_sensitivity}</span>
          <p className="setting-desc">Limiar de variância para detectar movimento. Menor = mais sensível.</p>
        </div>

        <div className="setting-group">
          <label>Limiar de Queda</label>
          <input
            type="range"
            min="3"
            max="30"
            step="1"
            value={local.fall_threshold}
            onChange={(e) =>
              setLocal({ ...local, fall_threshold: Number(e.target.value) })
            }
          />
          <span className="setting-value">{local.fall_threshold}</span>
          <p className="setting-desc">Taxa de variação para detectar queda. Menor = mais sensível.</p>
        </div>

        <div className="setting-group">
          <label>Tempo de Inatividade (s)</label>
          <input
            type="range"
            min="10"
            max="120"
            step="5"
            value={local.inactivity_timeout}
            onChange={(e) =>
              setLocal({ ...local, inactivity_timeout: Number(e.target.value) })
            }
          />
          <span className="setting-value">{local.inactivity_timeout}s</span>
          <p className="setting-desc">Segundos sem movimento para considerar inatividade prolongada.</p>
        </div>

        <div className="setting-group">
          <label>Intervalo de Amostragem (s)</label>
          <input
            type="range"
            min="0.1"
            max="2"
            step="0.1"
            value={local.sampling_interval}
            onChange={(e) =>
              setLocal({ ...local, sampling_interval: Number(e.target.value) })
            }
          />
          <span className="setting-value">{local.sampling_interval}s</span>
          <p className="setting-desc">Frequência de leitura do sinal. Menor = mais amostras por segundo.</p>
        </div>

        <div className="setting-group">
          <label>Provider Ativo</label>
          <select
            className="setting-select"
            value={local.active_provider}
            onChange={(e) => setLocal({ ...local, active_provider: e.target.value })}
          >
            <option value="mock">Simulador (Mock)</option>
            {(providers.rssi_windows || providers.rssi_linux) && (
              <option value="rssi_windows">
                RSSI Real {providers.rssi_windows ? '(Windows — disponível)' : '(Linux — disponível)'}
              </option>
            )}
            {providers.csi && (
              <option value="csi">CSI Real (disponível)</option>
            )}
            {!providers.rssi_windows && !providers.rssi_linux && (
              <option value="rssi" disabled>RSSI Real (não detectado)</option>
            )}
            {!providers.csi && (
              <option value="csi_placeholder" disabled>CSI Real (hardware não conectado)</option>
            )}
          </select>
          <p className="setting-desc">Fonte de dados de sinal Wi-Fi. Após salvar, reinicie o monitor.</p>
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn btn-secondary" onClick={handleReset}>
          <RotateCcw size={16} />
          Restaurar Padrão
        </button>
        <button className="btn btn-primary" onClick={handleSave}>
          <Save size={16} />
          {saved ? '✓ Salvo!' : 'Salvar Configurações'}
        </button>
      </div>
    </div>
  );
}
