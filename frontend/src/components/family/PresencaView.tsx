/* PresencaView — Modo "Presença": silhueta humana SVG com poses */

import type { EventType } from '../../types';

interface Props {
  eventType: EventType;
}

const GRADIENT_COLORS: Record<EventType, [string, string]> = {
  no_presence:          ['#1a1d2e', '#0f1117'],
  presence_still:       ['#1e3a5f', '#1a1d2e'],
  presence_moving:      ['#14432a', '#1a1d2e'],
  fall_suspected:       ['#5f1e1e', '#2a1010'],
  prolonged_inactivity: ['#4a3800', '#1a1d2e'],
};

const SILHOUETTE_COLOR: Record<EventType, string> = {
  no_presence:          '#4b5563',
  presence_still:       '#3b82f6',
  presence_moving:      '#10b981',
  fall_suspected:       '#ef4444',
  prolonged_inactivity: '#f59e0b',
};

const ANIMATION_CLASS: Record<EventType, string> = {
  no_presence:          'presenca-absent',
  presence_still:       'presenca-still',
  presence_moving:      'presenca-moving',
  fall_suspected:       'presenca-fall',
  prolonged_inactivity: 'presenca-inactive',
};

/* SVG silhueta — standing */
function Silhouette({ color, pose }: { color: string; pose: EventType }) {
  if (pose === 'no_presence') {
    return (
      <svg viewBox="0 0 100 140" fill="none" xmlns="http://www.w3.org/2000/svg" opacity="0.25">
        <circle cx="50" cy="25" r="18" stroke={color} strokeWidth="3" strokeDasharray="6 4" />
        <path d="M36 43 Q50 55 64 43 L66 95 L50 100 L34 95 Z" stroke={color} strokeWidth="3" strokeDasharray="6 4" fill="none" />
        <path d="M34 95 L26 130" stroke={color} strokeWidth="3" strokeDasharray="6 4" />
        <path d="M66 95 L74 130" stroke={color} strokeWidth="3" strokeDasharray="6 4" />
      </svg>
    );
  }

  if (pose === 'presence_still') {
    return (
      <svg viewBox="0 0 100 140" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="22" r="17" fill={color} />
        <path d="M36 39 Q36 80 38 90 L62 90 Q64 80 64 39 Z" fill={color} />
        <path d="M36 52 L20 68" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M64 52 L80 68" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M38 90 L32 125" stroke={color} strokeWidth="8" strokeLinecap="round" />
        <path d="M62 90 L68 125" stroke={color} strokeWidth="8" strokeLinecap="round" />
      </svg>
    );
  }

  if (pose === 'presence_moving') {
    return (
      <svg viewBox="0 0 100 140" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="55" cy="20" r="16" fill={color} />
        <path d="M48 36 L52 78" stroke={color} strokeWidth="10" strokeLinecap="round" />
        <path d="M50 52 L28 44" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M51 50 L72 38" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M52 78 L40 108 L28 122" stroke={color} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M53 78 L66 105 L78 118" stroke={color} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (pose === 'fall_suspected') {
    return (
      <svg viewBox="0 0 130 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="105" cy="25" r="16" fill={color} />
        <path d="M96 40 L45 68" stroke={color} strokeWidth="10" strokeLinecap="round" />
        <path d="M78 50 L95 35" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M70 55 L58 38" stroke={color} strokeWidth="7" strokeLinecap="round" />
        <path d="M45 68 L22 58" stroke={color} strokeWidth="8" strokeLinecap="round" />
        <path d="M48 72 L34 88" stroke={color} strokeWidth="8" strokeLinecap="round" />
        <path d="M15 92 Q65 98 115 92" stroke={color} strokeWidth="3" strokeDasharray="5 3" opacity="0.5" />
      </svg>
    );
  }

  /* prolonged_inactivity — deitado */
  return (
    <svg viewBox="0 0 160 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="130" cy="28" r="17" fill={color} />
      <path d="M120 44 L30 44" stroke={color} strokeWidth="14" strokeLinecap="round" />
      <path d="M30 44 L16 36" stroke={color} strokeWidth="8" strokeLinecap="round" />
      <path d="M30 44 L20 58" stroke={color} strokeWidth="8" strokeLinecap="round" />
      <path d="M10 68 L150 68" stroke={color} strokeWidth="4" strokeLinecap="round" opacity="0.3" />
      <text x="88" y="22" fontSize="12" fill={color} opacity="0.7" fontWeight="bold">z</text>
      <text x="100" y="12" fontSize="16" fill={color} opacity="0.4" fontWeight="bold">z</text>
    </svg>
  );
}

export function PresencaView({ eventType }: Props) {
  const [gradStart, gradEnd] = GRADIENT_COLORS[eventType];
  const color = SILHOUETTE_COLOR[eventType];
  const animClass = ANIMATION_CLASS[eventType];

  return (
    <div
      className={`presenca-view ${animClass}`}
      style={{
        background: `radial-gradient(ellipse at center, ${gradStart} 0%, ${gradEnd} 100%)`,
      }}
    >
      <div className="presenca-silhouette">
        <Silhouette color={color} pose={eventType} />
      </div>
      <div className="presenca-glow" style={{ backgroundColor: color }} />
    </div>
  );
}
