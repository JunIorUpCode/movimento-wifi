/* Replay.tsx — Tarefa 37: Replay de Eventos */

import { useEffect, useRef, useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { EVENT_COLORS, EVENT_LABELS, type EventRecord, type EventType } from '../types';

const SPEED_OPTIONS = [0.5, 1, 2, 4];

export function Replay() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [filter, setFilter] = useState('');
  const [periodHours, setPeriodHours] = useState(24);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const loadEvents = async () => {
    const data = await api.getEvents(500, filter || undefined);
    // Ordena do mais antigo ao mais recente para replay cronológico
    setEvents([...data].reverse());
    setIndex(0);
    setPlaying(false);
  };

  useEffect(() => { loadEvents(); }, [filter, periodHours]);

  // Controle de reprodução automática
  useEffect(() => {
    if (playing) {
      timerRef.current = setInterval(() => {
        setIndex((prev) => {
          if (prev >= events.length - 1) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, Math.round(1000 / speed));
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [playing, speed, events.length]);

  const current = events[index] ?? null;

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIndex(Number(e.target.value));
    setPlaying(false);
  };

  return (
    <div className="page-content">
      <h2 className="page-title">Replay de Eventos</h2>
      <p className="page-subtitle">Reproduza o histórico de eventos detectados em ordem cronológica.</p>

      {/* Controles de filtro */}
      <div className="card">
        <div className="form-row-2">
          <div className="form-row">
            <label>Tipo de evento</label>
            <select className="input" value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">Todos</option>
              <option value="fall_suspected">Queda Suspeita</option>
              <option value="prolonged_inactivity">Inatividade Prolongada</option>
              <option value="presence_moving">Presença Movendo</option>
              <option value="presence_still">Presença Parada</option>
              <option value="no_presence">Sem Presença</option>
            </select>
          </div>
          <div className="form-row">
            <label>Período</label>
            <select className="input" value={periodHours} onChange={(e) => setPeriodHours(Number(e.target.value))}>
              <option value={1}>Última 1h</option>
              <option value={6}>Últimas 6h</option>
              <option value={24}>Últimas 24h</option>
              <option value={168}>Últimos 7 dias</option>
            </select>
          </div>
        </div>
        <button className="btn btn-ghost mt-sm" onClick={loadEvents}>
          <RefreshCw size={14} /> Recarregar
        </button>
      </div>

      {events.length === 0 ? (
        <div className="card"><p className="text-muted">Nenhum evento encontrado para os filtros selecionados.</p></div>
      ) : (
        <>
          {/* Visualização do evento atual */}
          {current && (
            <div className="card replay-current">
              {(() => {
                const color = EVENT_COLORS[current.event_type as EventType] || '#6b7280';
                const label = EVENT_LABELS[current.event_type as EventType] || current.event_type;
                return (
                  <>
                    <div className="replay-event-badge" style={{ backgroundColor: `${color}20`, borderColor: color, color }}>
                      {label}
                    </div>
                    <div className="replay-meta">
                      <div><span>Horário</span><strong>{new Date(current.timestamp).toLocaleString('pt-BR')}</strong></div>
                      <div><span>Confiança</span><strong>{Math.round(current.confidence * 100)}%</strong></div>
                      <div><span>Provider</span><strong>{current.provider}</strong></div>
                      <div><span>Evento</span><strong>{index + 1} / {events.length}</strong></div>
                    </div>
                    {/* Barra de confiança */}
                    <div className="replay-confidence-bar">
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${Math.round(current.confidence * 100)}%`, backgroundColor: color }} />
                      </div>
                      <span>{Math.round(current.confidence * 100)}%</span>
                    </div>
                  </>
                );
              })()}
            </div>
          )}

          {/* Scrubber */}
          <div className="card">
            <input
              type="range"
              className="replay-scrubber"
              min={0}
              max={events.length - 1}
              value={index}
              onChange={handleSeek}
            />
            <div className="replay-timestamps">
              <span>{events[0] ? new Date(events[0].timestamp).toLocaleString('pt-BR') : ''}</span>
              <span>{events[events.length - 1] ? new Date(events[events.length - 1].timestamp).toLocaleString('pt-BR') : ''}</span>
            </div>

            {/* Controles de reprodução */}
            <div className="replay-controls">
              <button className="btn btn-icon" onClick={() => { setIndex(0); setPlaying(false); }} title="Início">
                <SkipBack size={18} />
              </button>
              <button
                className="btn btn-primary"
                onClick={() => setPlaying(!playing)}
              >
                {playing ? <><Pause size={16} /> Pausar</> : <><Play size={16} /> Reproduzir</>}
              </button>
              <button className="btn btn-icon" onClick={() => { setIndex(events.length - 1); setPlaying(false); }} title="Final">
                <SkipForward size={18} />
              </button>

              {/* Velocidade */}
              <div className="speed-selector">
                {SPEED_OPTIONS.map((s) => (
                  <button
                    key={s}
                    className={`btn btn-sm ${speed === s ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setSpeed(s)}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Mini timeline dos últimos 20 eventos */}
          <div className="card">
            <h3 className="card-title">Timeline</h3>
            <div className="replay-timeline">
              {events.slice(Math.max(0, index - 10), index + 10).map((e, i) => {
                const realIdx = Math.max(0, index - 10) + i;
                const color = EVENT_COLORS[e.event_type as EventType] || '#6b7280';
                return (
                  <div
                    key={e.id}
                    className={`timeline-dot ${realIdx === index ? 'active' : ''}`}
                    style={{ backgroundColor: color }}
                    title={`${EVENT_LABELS[e.event_type as EventType] ?? e.event_type} — ${new Date(e.timestamp).toLocaleTimeString('pt-BR')}`}
                    onClick={() => { setIndex(realIdx); setPlaying(false); }}
                  />
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
