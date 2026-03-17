/* Statistics.tsx — Tarefa 31: Página de Estatísticas */

import { useEffect, useState } from 'react';
import { BarChart2, Activity, Cpu, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import type { AnomalyRecord, BehaviorPattern, EventStats, PerformanceStats } from '../types';
import { EVENT_LABELS } from '../types';

const PERIODS = [1, 6, 24, 168] as const;
const DAY_LABELS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];

export function Statistics() {
  const [period, setPeriod] = useState<number>(24);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [patterns, setPatterns] = useState<BehaviorPattern[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [perf, setPerf] = useState<PerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getEventStats(period),
      api.getBehaviorPatterns(),
      api.getAnomalies(period),
      api.getPerformanceStats(1),
    ]).then(([s, p, a, pf]) => {
      setStats(s);
      setPatterns(p);
      setAnomalies(a.anomalies);
      setPerf(pf);
    }).finally(() => setLoading(false));
  }, [period]);

  const maxProb = Math.max(...patterns.map((p) => p.presence_probability), 0.01);

  return (
    <div className="page-content">
      <div className="page-header-row">
        <h2 className="page-title">Estatísticas</h2>
        <div className="period-selector">
          {PERIODS.map((h) => (
            <button
              key={h}
              className={`btn btn-sm ${period === h ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setPeriod(h)}
            >
              {h === 1 ? '1h' : h === 6 ? '6h' : h === 24 ? '24h' : '7d'}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-muted">Carregando...</p>}

      {/* Cards de resumo */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <BarChart2 size={20} />
            <div>
              <span className="stat-value">{stats.total_events}</span>
              <span className="stat-label">Eventos</span>
            </div>
          </div>
          <div className="stat-card">
            <Activity size={20} />
            <div>
              <span className="stat-value">{Math.round(stats.avg_confidence * 100)}%</span>
              <span className="stat-label">Confiança Média</span>
            </div>
          </div>
          <div className="stat-card">
            <AlertTriangle size={20} />
            <div>
              <span className="stat-value">{anomalies.length}</span>
              <span className="stat-label">Anomalias</span>
            </div>
          </div>
          {perf && (
            <div className="stat-card">
              <Cpu size={20} />
              <div>
                <span className="stat-value">{perf.avg_total_latency_ms.toFixed(1)}ms</span>
                <span className="stat-label">Latência Média</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Distribuição por tipo */}
      {stats && Object.keys(stats.by_type).length > 0 && (
        <div className="card">
          <h3 className="card-title">Eventos por Tipo</h3>
          <div className="bar-chart">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <div key={type} className="bar-row">
                <span className="bar-label">
                  {EVENT_LABELS[type as keyof typeof EVENT_LABELS] ?? type}
                </span>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${Math.round((count / stats.total_events) * 100)}%` }}
                  />
                </div>
                <span className="bar-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Heatmap de padrões comportamentais */}
      {patterns.length > 0 && (
        <div className="card">
          <h3 className="card-title">Padrões Comportamentais — Probabilidade de Presença</h3>
          <p className="text-muted card-subtitle">Cada célula representa hora × dia da semana</p>
          <div className="heatmap-wrap">
            <div className="heatmap-days">
              {DAY_LABELS.map((d) => <span key={d}>{d}</span>)}
            </div>
            {Array.from({ length: 24 }, (_, h) => (
              <div key={h} className="heatmap-row">
                <span className="heatmap-hour">{String(h).padStart(2, '0')}h</span>
                {Array.from({ length: 7 }, (_, d) => {
                  const p = patterns.find((x) => x.hour_of_day === h && x.day_of_week === d);
                  const intensity = p ? p.presence_probability / maxProb : 0;
                  return (
                    <div
                      key={d}
                      className="heatmap-cell"
                      title={p ? `${Math.round(p.presence_probability * 100)}% presença` : 'Sem dados'}
                      style={{ opacity: 0.15 + intensity * 0.85 }}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Anomalias */}
      {anomalies.length > 0 && (
        <div className="card">
          <h3 className="card-title">Anomalias Detectadas</h3>
          <table className="table">
            <thead>
              <tr><th>Horário</th><th>Tipo</th><th>Confiança</th></tr>
            </thead>
            <tbody>
              {anomalies.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.timestamp).toLocaleString('pt-BR')}</td>
                  <td>{EVENT_LABELS[a.event_type as keyof typeof EVENT_LABELS] ?? a.event_type}</td>
                  <td>{Math.round(a.confidence * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Performance */}
      {perf && perf.samples_count > 0 && (
        <div className="card">
          <h3 className="card-title">Performance do Sistema (última 1h)</h3>
          <div className="perf-grid">
            <div><span>Captura</span><strong>{perf.avg_capture_time_ms.toFixed(2)} ms</strong></div>
            <div><span>Processamento</span><strong>{perf.avg_processing_time_ms.toFixed(2)} ms</strong></div>
            <div><span>Detecção</span><strong>{perf.avg_detection_time_ms.toFixed(2)} ms</strong></div>
            <div><span>Latência total</span><strong>{perf.avg_total_latency_ms.toFixed(2)} ms</strong></div>
            <div><span>Memória</span><strong>{perf.avg_memory_usage_mb.toFixed(1)} MB</strong></div>
            <div><span>CPU</span><strong>{perf.avg_cpu_usage_percent.toFixed(1)}%</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}
