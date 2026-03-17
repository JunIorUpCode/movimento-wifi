/* History — Tarefa 32: Histórico Avançado com filtros */

import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { EVENT_LABELS, EVENT_COLORS, type EventRecord, type EventType } from '../types';
import { RefreshCw, Download } from 'lucide-react';

const EVENT_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'no_presence', label: 'Sem Presença' },
  { value: 'presence_still', label: 'Parado' },
  { value: 'presence_moving', label: 'Movendo' },
  { value: 'fall_suspected', label: 'Queda Suspeita' },
  { value: 'prolonged_inactivity', label: 'Inatividade' },
];

const PAGE_SIZE = 50;

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function History() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [filter, setFilter] = useState('');
  const [minConfidence, setMinConfidence] = useState(0);
  const [periodHours, setPeriodHours] = useState(24);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents(1000, filter || undefined);
      setEvents(data);
      setPage(0);
    } catch (e) {
      console.error('Erro ao buscar eventos:', e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchEvents(); }, [filter]);

  const filtered = events.filter((e) => e.confidence >= minConfidence);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const visible = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleExportCsv = async () => {
    const blob = await api.exportEventsCsv(periodHours);
    downloadBlob(blob, `events_${periodHours}h.csv`);
  };

  const handleExportJson = async () => {
    const blob = await api.exportEventsJson(periodHours);
    downloadBlob(blob, `events_${periodHours}h.json`);
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <h2>Histórico de Eventos</h2>
        <div className="history-actions">
          {/* Filtro por tipo */}
          <select
            className="history-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            {EVENT_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>

          {/* Filtro por confiança mínima */}
          <label className="filter-inline">
            Confiança ≥
            <input
              type="number"
              className="input input-sm"
              min={0} max={1} step={0.1}
              value={minConfidence}
              onChange={(e) => { setMinConfidence(Number(e.target.value)); setPage(0); }}
              style={{ width: 60 }}
            />
          </label>

          {/* Exportação */}
          <select
            className="history-filter"
            value={periodHours}
            onChange={(e) => setPeriodHours(Number(e.target.value))}
          >
            <option value={1}>Exportar: 1h</option>
            <option value={6}>Exportar: 6h</option>
            <option value={24}>Exportar: 24h</option>
            <option value={168}>Exportar: 7d</option>
          </select>
          <button className="btn btn-sm btn-ghost" onClick={handleExportCsv} title="Baixar CSV">
            <Download size={15} /> CSV
          </button>
          <button className="btn btn-sm btn-ghost" onClick={handleExportJson} title="Baixar JSON">
            <Download size={15} /> JSON
          </button>

          <button className="btn btn-icon" onClick={fetchEvents} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      <p className="text-muted" style={{ marginBottom: 8 }}>
        {filtered.length} eventos encontrados
        {totalPages > 1 && ` — página ${page + 1} de ${totalPages}`}
      </p>

      <div className="history-table-wrapper">
        <table className="history-table">
          <thead>
            <tr>
              <th>Data/Hora</th>
              <th>Evento</th>
              <th>Confiança</th>
              <th>Provider</th>
              <th>Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td colSpan={5} className="history-empty">Nenhum evento encontrado.</td>
              </tr>
            ) : (
              visible.map((event) => {
                const color = EVENT_COLORS[event.event_type as EventType] || '#6b7280';
                const label = EVENT_LABELS[event.event_type as EventType] || event.event_type;
                const time = new Date(event.timestamp).toLocaleString('pt-BR');
                let details = '';
                try {
                  const meta = JSON.parse(event.metadata_json);
                  details = Object.entries(meta).map(([k, v]) => `${k}: ${v}`).join(', ');
                } catch { details = event.metadata_json; }

                return (
                  <tr key={event.id}>
                    <td>{time}</td>
                    <td>
                      <span className="event-badge" style={{ backgroundColor: `${color}20`, color }}>
                        {label}
                      </span>
                    </td>
                    <td>{(event.confidence * 100).toFixed(0)}%</td>
                    <td>{event.provider}</td>
                    <td className="history-details">{details}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-sm btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>
            ← Anterior
          </button>
          <span>{page + 1} / {totalPages}</span>
          <button className="btn btn-sm btn-ghost" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>
            Próximo →
          </button>
        </div>
      )}
    </div>
  );
}
