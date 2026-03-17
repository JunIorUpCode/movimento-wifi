/* PresenceIndicator — Indicador visual animado de presença */

import { EVENT_COLORS, EVENT_LABELS, type EventType } from '../types';
import { useStore } from '../store/useStore';

export function PresenceIndicator() {
  const currentEvent = useStore((s) => s.currentEvent);
  const color = EVENT_COLORS[currentEvent];
  const label = EVENT_LABELS[currentEvent];
  const isActive = currentEvent !== 'no_presence';
  const isCritical = currentEvent === 'fall_suspected';

  return (
    <div className="presence-indicator">
      <div className="presence-ring-container">
        <div
          className={`presence-ring ${isActive ? 'pulse' : ''} ${isCritical ? 'critical-pulse' : ''}`}
          style={{ borderColor: color, boxShadow: `0 0 20px ${color}40` }}
        >
          <div className="presence-core" style={{ backgroundColor: color }} />
        </div>
      </div>
      <span className="presence-label" style={{ color }}>{label}</span>
    </div>
  );
}
