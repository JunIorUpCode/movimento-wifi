/* RadarView — Modo "Radar": blob de calor animado */

import { useStore } from '../../store/useStore';
import type { EventType } from '../../types';

interface Props {
  eventType: EventType;
}

const BLOB_COLOR: Record<EventType, string> = {
  no_presence:          '#4b5563',
  presence_still:       '#3b82f6',
  presence_moving:      '#10b981',
  fall_suspected:       '#ef4444',
  prolonged_inactivity: '#f59e0b',
};

const BLOB_ANIMATION: Record<EventType, string> = {
  no_presence:          'radar-idle',
  presence_still:       'radar-calm',
  presence_moving:      'radar-pulse',
  fall_suspected:       'radar-critical',
  prolonged_inactivity: 'radar-slow',
};

const RING_OPACITY: Record<EventType, number> = {
  no_presence:          0.06,
  presence_still:       0.12,
  presence_moving:      0.20,
  fall_suspected:       0.30,
  prolonged_inactivity: 0.08,
};

export function RadarView({ eventType }: Props) {
  const lastUpdate = useStore((s) => s.lastUpdate);
  const instability = lastUpdate?.features?.instability_score ?? 0;
  const blobScale = 0.7 + Math.min(instability * 1.5, 0.6);

  const color = BLOB_COLOR[eventType];
  const animClass = BLOB_ANIMATION[eventType];
  const ringOpacity = RING_OPACITY[eventType];

  return (
    <div className="radar-view">
      {/* Rings concêntricos */}
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="radar-ring"
          style={{
            width: `${i * 22}%`,
            height: `${i * 22}%`,
            borderColor: color,
            opacity: ringOpacity * (5 - i),
          }}
        />
      ))}

      {/* Cruz central */}
      <div className="radar-cross" style={{ opacity: ringOpacity * 2 }}>
        <div className="radar-cross-h" style={{ backgroundColor: color }} />
        <div className="radar-cross-v" style={{ backgroundColor: color }} />
      </div>

      {/* Blob principal */}
      <div
        className={`radar-blob ${animClass}`}
        style={{
          backgroundColor: color,
          transform: `scale(${blobScale})`,
          boxShadow: `0 0 40px 15px ${color}55, 0 0 80px 30px ${color}22`,
        }}
      />

      {/* Scan line (só quando monitorando) */}
      {eventType !== 'no_presence' && (
        <div className="radar-scan" style={{ borderTopColor: color }} />
      )}
    </div>
  );
}
