/* Calibration.tsx — Tarefa 30: Página de Calibração */

import { useEffect, useState } from 'react';
import { Play, Square, Trash2, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import type { CalibrationProfile, CalibrationProgress } from '../types';

export function Calibration() {
  const calibrationProgress = useStore((s) => s.calibrationProgress);

  const [profiles, setProfiles] = useState<CalibrationProfile[]>([]);
  const [progress, setProgress] = useState<CalibrationProgress | null>(null);
  const [profileName, setProfileName] = useState('default');
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const loadData = async () => {
    const [profs, prog] = await Promise.all([
      api.listCalibrationProfiles(),
      api.getCalibrationProgress(),
    ]);
    setProfiles(profs);
    setProgress(prog);
  };

  useEffect(() => {
    loadData();
    const iv = setInterval(() => {
      api.getCalibrationProgress().then(setProgress);
    }, 3000);
    return () => clearInterval(iv);
  }, []);

  // Atualiza barra de progresso quando WS emite calibration_progress
  useEffect(() => {
    if (calibrationProgress?.phase === 'done') {
      loadData();
      setMessage({ type: 'ok', text: 'Calibração concluída com sucesso!' });
    } else if (calibrationProgress?.phase === 'error') {
      loadData();
    }
  }, [calibrationProgress]);

  const handleStart = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await api.startCalibration(profileName, duration);
      setMessage({ type: 'ok', text: `Calibração iniciada. Mantenha o ambiente vazio por ${duration}s.` });
      setTimeout(loadData, 1000);
    } catch (e: unknown) {
      setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro ao iniciar calibração.' });
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      await api.stopCalibration();
      setMessage({ type: 'ok', text: 'Calibração cancelada.' });
      loadData();
    } catch (e: unknown) {
      setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro.' });
    }
  };

  const handleActivate = async (name: string) => {
    try {
      await api.activateCalibrationProfile(name);
      setMessage({ type: 'ok', text: `Perfil '${name}' ativado.` });
      loadData();
    } catch {
      setMessage({ type: 'err', text: `Erro ao ativar perfil '${name}'.` });
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Remover perfil '${name}'?`)) return;
    try {
      await api.deleteCalibrationProfile(name);
      loadData();
    } catch {
      setMessage({ type: 'err', text: `Erro ao remover perfil '${name}'.` });
    }
  };

  const wsProgress = calibrationProgress ?? (progress?.running ? {
    profile_name: progress.profile_name ?? '',
    elapsed_seconds: progress.elapsed_seconds ?? 0,
    duration_seconds: progress.duration_seconds,
    progress_percent: progress.elapsed_seconds
      ? Math.min(100, Math.round((progress.elapsed_seconds / progress.duration_seconds) * 100))
      : 0,
    phase: 'collecting' as const,
  } : null);

  return (
    <div className="page-content">
      <h2 className="page-title">Calibração</h2>
      <p className="page-subtitle">
        Calibre o ambiente para que o sistema saiba como é a "linha de base" sem pessoas.
      </p>

      {message && (
        <div className={`alert-banner ${message.type === 'ok' ? 'alert-ok' : 'alert-err'}`}>
          {message.type === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Formulário de início */}
      {!wsProgress && (
        <div className="card">
          <h3 className="card-title">Nova Calibração</h3>
          <div className="form-row">
            <label>Nome do perfil</label>
            <input
              className="input"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="ex: sala-de-estar"
            />
          </div>
          <div className="form-row">
            <label>Duração (segundos)</label>
            <input
              className="input"
              type="number"
              min={10}
              max={300}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
            />
          </div>
          <button className="btn btn-primary" onClick={handleStart} disabled={loading}>
            {loading ? <Loader size={16} className="spin" /> : <Play size={16} />}
            Iniciar Calibração
          </button>
        </div>
      )}

      {/* Progresso */}
      {wsProgress && (
        <div className="card">
          <div className="card-header-row">
            <h3 className="card-title">
              {wsProgress.phase === 'done' ? 'Calibração Concluída' : 'Calibração em Andamento'}
            </h3>
            {wsProgress.phase !== 'done' && wsProgress.phase !== 'error' && (
              <button className="btn btn-danger btn-sm" onClick={handleStop}>
                <Square size={14} /> Cancelar
              </button>
            )}
          </div>
          <p className="text-muted">Perfil: <strong>{wsProgress.profile_name}</strong></p>
          <div className="progress-bar-wrap">
            <div
              className="progress-bar-fill"
              style={{ width: `${wsProgress.progress_percent}%` }}
            />
          </div>
          <p className="progress-label">
            {wsProgress.phase === 'collecting'
              ? `${Math.round(wsProgress.elapsed_seconds)}s / ${wsProgress.duration_seconds}s — coletando amostras...`
              : wsProgress.phase === 'calculating'
              ? 'Calculando baseline...'
              : wsProgress.phase === 'done'
              ? 'Concluído!'
              : 'Erro na calibração.'}
          </p>
          {progress?.error && <p className="text-danger">{progress.error}</p>}
          {progress?.result && (
            <div className="result-grid">
              <div><span>RSSI médio</span><strong>{progress.result.mean_rssi} dBm</strong></div>
              <div><span>Desvio padrão</span><strong>{progress.result.std_rssi}</strong></div>
              <div><span>Noise floor</span><strong>{progress.result.noise_floor} dBm</strong></div>
              <div><span>Amostras</span><strong>{progress.result.samples_count}</strong></div>
            </div>
          )}
        </div>
      )}

      {/* Perfis salvos */}
      <div className="card">
        <h3 className="card-title">Perfis Salvos</h3>
        {profiles.length === 0 ? (
          <p className="text-muted">Nenhum perfil salvo ainda. Execute uma calibração para criar um.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Criado em</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{new Date(p.created_at).toLocaleString('pt-BR')}</td>
                  <td>
                    {p.is_active
                      ? <span className="badge badge-green">Ativo</span>
                      : <span className="badge badge-gray">Inativo</span>}
                  </td>
                  <td className="actions-cell">
                    {!p.is_active && (
                      <button className="btn btn-sm btn-primary" onClick={() => handleActivate(p.name)}>
                        <CheckCircle size={13} /> Ativar
                      </button>
                    )}
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(p.name)}>
                      <Trash2 size={13} /> Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
