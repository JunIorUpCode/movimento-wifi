/* History — Página de histórico de eventos */

import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { EVENT_LABELS, EVENT_COLORS, type EventRecord, type EventType } from '../types';
import { RefreshCw } from 'lucide-react';

const EVENT_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'no_presence', label: 'Sem Presença' },
  { value: 'presence_still', label: 'Parado' },
  { value: 'presence_moving', label: 'Movendo' },
  { value: 'fall_suspected', label: 'Queda Suspeita' },
  { value: 'prolonged_inactivity', label: 'Inatividade' },
];

export function History() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents(200, filter || undefined);
      setEvents(data);
    } catch (e) {
      console.error('Erro ao buscar eventos:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchEvents();
  }, [filter]);

  return (
    <div className="history-page">
      <div className="history-header">
        <h2>Histórico de Eventos</h2>
        <div className="history-actions">
          <select
            className="history-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            {EVENT_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
          <button className="btn btn-icon" onClick={fetchEvents} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

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
            {events.length === 0 ? (
              <tr>
                <td colSpan={5} className="history-empty">
                  Nenhum evento encontrado.
                </td>
              </tr>
            ) : (
              events.map((event) => {
                const color = EVENT_COLORS[event.event_type as EventType] || '#6b7280';
                const label = EVENT_LABELS[event.event_type as EventType] || event.event_type;
                const time = new Date(event.timestamp).toLocaleString('pt-BR');

                let details = '';
                try {
                  const meta = JSON.parse(event.metadata_json);
                  details = Object.entries(meta)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ');
                } catch {
                  details = event.metadata_json;
                }

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
    </div>
  );
}
