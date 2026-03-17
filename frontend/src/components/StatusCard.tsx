/* StatusCard — Card com estado atual */

import { EVENT_LABELS, EVENT_COLORS, type EventType } from '../types';
import { useStore } from '../store/useStore';
import {
  UserCheck,
  UserX,
  PersonStanding,
  AlertTriangle,
  Clock,
} from 'lucide-react';

const EVENT_ICONS: Record<EventType, typeof UserCheck> = {
  no_presence: UserX,
  presence_still: PersonStanding,
  presence_moving: UserCheck,
  fall_suspected: AlertTriangle,
  prolonged_inactivity: Clock,
};

export function StatusCard() {
  const currentEvent = useStore((s) => s.currentEvent);
  const confidence = useStore((s) => s.confidence);
  const simulationMode = useStore((s) => s.simulationMode);

  const Icon = EVENT_ICONS[currentEvent] || UserX;
  const color = EVENT_COLORS[currentEvent];
  const label = EVENT_LABELS[currentEvent];
  const isCritical = currentEvent === 'fall_suspected' || currentEvent === 'prolonged_inactivity';

  return (
    <div className={`status-card ${isCritical ? 'critical' : ''}`} style={{ borderColor: color }}>
      <div className="status-card-header">
        <Icon size={32} color={color} />
        <div>
          <h3 className="status-card-title">Estado Atual</h3>
          <p className="status-card-event" style={{ color }}>{label}</p>
        </div>
      </div>
      <div className="status-card-footer">
        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={{ width: `${confidence * 100}%`, backgroundColor: color }}
          />
        </div>
        <span className="confidence-text">{(confidence * 100).toFixed(0)}% confiança</span>
      </div>
    </div>
  );
}
