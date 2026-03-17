/* EventTimeline — Timeline vertical de eventos recentes */

import { EVENT_LABELS, EVENT_COLORS, type EventRecord } from '../types';
import { useStore } from '../store/useStore';
import { Circle } from 'lucide-react';

export function EventTimeline() {
  const events = useStore((s) => s.events);
  const recent = events.slice(0, 15);

  if (recent.length === 0) {
    return (
      <div className="timeline-container">
        <h3 className="chart-title">Eventos Recentes</h3>
        <p className="timeline-empty">Nenhum evento registrado ainda.</p>
      </div>
    );
  }

  return (
    <div className="timeline-container">
      <h3 className="chart-title">Eventos Recentes</h3>
      <div className="timeline">
        {recent.map((event) => (
          <TimelineItem key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}

function TimelineItem({ event }: { event: EventRecord }) {
  const color = EVENT_COLORS[event.event_type] || '#6b7280';
  const label = EVENT_LABELS[event.event_type] || event.event_type;
  const time = new Date(event.timestamp).toLocaleTimeString('pt-BR');
  const date = new Date(event.timestamp).toLocaleDateString('pt-BR');

  return (
    <div className="timeline-item">
      <div className="timeline-dot">
        <Circle size={10} fill={color} color={color} />
      </div>
      <div className="timeline-content">
        <span className="timeline-event" style={{ color }}>{label}</span>
        <span className="timeline-time">{date} {time}</span>
        <span className="timeline-confidence">
          {(event.confidence * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
