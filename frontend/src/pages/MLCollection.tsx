/* MLCollection.tsx — Tarefa 35: Coleta de Dados ML */

import { useEffect, useState } from 'react';
import { Play, Square, Tag, Download, Cpu, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { MLCollectionStatus } from '../types';

const VALID_LABELS = [
  { value: 'no_presence', label: 'Sem Presença' },
  { value: 'presence_still', label: 'Presença Parada' },
  { value: 'presence_moving', label: 'Presença em Movimento' },
  { value: 'fall_suspected', label: 'Queda Suspeita' },
  { value: 'prolonged_inactivity', label: 'Inatividade Prolongada' },
];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function MLCollection() {
  const [status, setStatus] = useState<MLCollectionStatus | null>(null);
  const [selectedLabel, setSelectedLabel] = useState('presence_still');
  const [windowSecs, setWindowSecs] = useState(10);
  const [trainStatus, setTrainStatus] = useState<{ running: boolean; error: string | null; result: string | null } | null>(null);
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStatus = async () => {
    const s = await api.getMLCollectionStatus();
    setStatus(s);
    const t = await api.getTrainingStatus();
    setTrainStatus(t);
  };

  useEffect(() => {
    loadStatus();
    const iv = setInterval(loadStatus, 3000);
    return () => clearInterval(iv);
  }, []);

  const handleStart = async () => {
    try { await api.startMLCollection(); setMessage({ type: 'ok', text: 'Coleta iniciada.' }); loadStatus(); }
    catch (e: unknown) { setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro.' }); }
  };

  const handleStop = async () => {
    try {
      const r = await api.stopMLCollection();
      setMessage({ type: 'ok', text: `Coleta encerrada. ${r.samples_collected} amostras coletadas.` });
      loadStatus();
    }
    catch (e: unknown) { setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro.' }); }
  };

  const handleLabel = async () => {
    try {
      const r = await api.labelMLEvent(selectedLabel, windowSecs);
      setMessage({ type: 'ok', text: `${r.samples_labeled} amostras rotuladas como '${selectedLabel}'.` });
      loadStatus();
    }
    catch (e: unknown) { setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro ao rotular.' }); }
  };

  const handleExport = async () => {
    try {
      const blob = await api.exportMLDataset();
      downloadBlob(blob, 'training_data.csv');
    }
    catch { setMessage({ type: 'err', text: 'Erro ao exportar dataset.' }); }
  };

  const handleTrain = async () => {
    setLoading(true);
    try {
      const r = await api.triggerTraining();
      setMessage({ type: 'ok', text: r.message });
      setTimeout(loadStatus, 2000);
    }
    catch (e: unknown) { setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro ao iniciar treinamento.' }); }
    finally { setLoading(false); }
  };

  const totalSamples = status?.total_samples ?? 0;
  const distribution = status?.label_distribution ?? {};

  return (
    <div className="page-content">
      <h2 className="page-title">Coleta de Dados ML</h2>
      <p className="page-subtitle">
        Colete amostras rotuladas de sinal Wi-Fi para treinar modelos de detecção personalizados.
      </p>

      {message && (
        <div className={`alert-banner ${message.type === 'ok' ? 'alert-ok' : 'alert-err'}`}>
          {message.type === 'ok' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Status da coleta */}
      <div className="card">
        <div className="card-header-row">
          <h3 className="card-title">Status da Coleta</h3>
          <button className="btn btn-sm btn-ghost" onClick={loadStatus}><RefreshCw size={14} /></button>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{totalSamples}</span>
            <span className="stat-label">Amostras coletadas</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{status?.pending_features ?? 0}</span>
            <span className="stat-label">Features em buffer</span>
          </div>
          <div className="stat-card">
            <span className={`stat-value ${status?.is_collecting ? 'text-green' : 'text-muted'}`}>
              {status?.is_collecting ? 'Ativa' : 'Parada'}
            </span>
            <span className="stat-label">Coleta</span>
          </div>
        </div>

        <div className="form-actions mt-sm">
          {!status?.is_collecting
            ? <button className="btn btn-primary" onClick={handleStart}><Play size={15} /> Iniciar Coleta</button>
            : <button className="btn btn-danger" onClick={handleStop}><Square size={15} /> Parar Coleta</button>
          }
        </div>
      </div>

      {/* Rotulação */}
      {status?.is_collecting && (
        <div className="card">
          <h3 className="card-title">Rotular Evento</h3>
          <p className="text-muted card-subtitle">Rotula as features dos últimos N segundos com o rótulo selecionado.</p>
          <div className="form-row">
            <label>Rótulo</label>
            <select className="input" value={selectedLabel} onChange={(e) => setSelectedLabel(e.target.value)}>
              {VALID_LABELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
          <div className="form-row">
            <label>Janela (segundos)</label>
            <input className="input" type="number" min={1} max={60} value={windowSecs}
              onChange={(e) => setWindowSecs(Number(e.target.value))} style={{ width: 80 }} />
          </div>
          <button className="btn btn-primary" onClick={handleLabel}>
            <Tag size={15} /> Rotular Agora
          </button>
        </div>
      )}

      {/* Distribuição de rótulos */}
      {totalSamples > 0 && (
        <div className="card">
          <h3 className="card-title">Distribuição de Rótulos</h3>
          <div className="bar-chart">
            {Object.entries(distribution).map(([label, count]) => (
              <div key={label} className="bar-row">
                <span className="bar-label">{VALID_LABELS.find((l) => l.value === label)?.label ?? label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${Math.round((count / totalSamples) * 100)}%` }} />
                </div>
                <span className="bar-count">{count}</span>
              </div>
            ))}
          </div>
          <div className="form-actions mt-sm">
            <button className="btn btn-ghost" onClick={handleExport}>
              <Download size={15} /> Exportar Dataset CSV
            </button>
          </div>
        </div>
      )}

      {/* Treinamento */}
      <div className="card">
        <h3 className="card-title">Treinamento do Modelo</h3>
        {trainStatus?.running
          ? <p className="text-muted">Treinamento em andamento...</p>
          : trainStatus?.result
          ? <p className="text-green">{trainStatus.result}</p>
          : trainStatus?.error
          ? <p className="text-danger">{trainStatus.error}</p>
          : null
        }
        <button className="btn btn-primary mt-sm" onClick={handleTrain} disabled={loading || trainStatus?.running}>
          <Cpu size={15} />
          {trainStatus?.running ? 'Treinando...' : 'Iniciar Treinamento'}
        </button>
        <p className="text-muted mt-sm" style={{ fontSize: '0.8rem' }}>
          O modelo será treinado com o dataset exportado. Após o treinamento, ative-o em Configurações → Modelos ML.
        </p>
      </div>
    </div>
  );
}
