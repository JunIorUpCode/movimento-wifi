/* PulsoView — Modo "Pulso": ícone SVG animado por estado */

import type { EventType } from '../../types';

interface Props {
  eventType: EventType;
}

const CONFIG: Record<EventType, { color: string; animation: string; label: string }> = {
  no_presence:          { color: '#6b7280', animation: 'pulso-idle',     label: 'Ambiente vazio' },
  presence_still:       { color: '#3b82f6', animation: 'pulso-calm',     label: 'Em repouso' },
  presence_moving:      { color: '#10b981', animation: 'pulso-active',   label: 'Em movimento' },
  fall_suspected:       { color: '#ef4444', animation: 'pulso-critical',  label: 'QUEDA' },
  prolonged_inactivity: { color: '#f59e0b', animation: 'pulso-slow',     label: 'Sem movimento' },
};

function HouseIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M60 15 L100 55 L90 55 L90 100 L70 100 L70 75 L50 75 L50 100 L30 100 L30 55 L20 55 Z"
        fill={color} opacity="0.3" stroke={color} strokeWidth="3" strokeLinejoin="round" />
      <circle cx="60" cy="45" r="6" fill={color} opacity="0.5" />
    </svg>
  );
}

function SittingIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Cabeça */}
      <circle cx="60" cy="28" r="14" fill={color} />
      {/* Corpo */}
      <path d="M50 42 Q50 65 48 72 L72 72 Q70 65 70 42 Z" fill={color} />
      {/* Pernas dobradas */}
      <path d="M48 72 L38 90 L52 90 L58 72" fill={color} />
      <path d="M72 72 L82 90 L68 90 L62 72" fill={color} />
      {/* Assento */}
      <rect x="30" y="88" width="60" height="8" rx="4" fill={color} opacity="0.4" />
    </svg>
  );
}

function WalkingIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Cabeça */}
      <circle cx="62" cy="22" r="13" fill={color} />
      {/* Corpo */}
      <path d="M55 35 L58 65" stroke={color} strokeWidth="8" strokeLinecap="round" />
      {/* Braço frente */}
      <path d="M57 48 L40 58" stroke={color} strokeWidth="6" strokeLinecap="round" />
      {/* Braço trás */}
      <path d="M59 45 L76 38" stroke={color} strokeWidth="6" strokeLinecap="round" />
      {/* Perna frente */}
      <path d="M58 65 L48 85 L36 95" stroke={color} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
      {/* Perna trás */}
      <path d="M60 65 L70 82 L80 90" stroke={color} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
      {/* Trilha de movimento */}
      <circle cx="26" cy="100" r="3" fill={color} opacity="0.3" />
      <circle cx="18" cy="100" r="2" fill={color} opacity="0.2" />
      <circle cx="12" cy="100" r="1.5" fill={color} opacity="0.1" />
    </svg>
  );
}

function FallingIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Cabeça */}
      <circle cx="88" cy="38" r="13" fill={color} />
      {/* Corpo inclinado */}
      <path d="M82 50 L45 75" stroke={color} strokeWidth="9" strokeLinecap="round" />
      {/* Braços abertos */}
      <path d="M70 58 L88 45" stroke={color} strokeWidth="6" strokeLinecap="round" />
      <path d="M62 63 L50 48" stroke={color} strokeWidth="6" strokeLinecap="round" />
      {/* Pernas */}
      <path d="M45 75 L28 65" stroke={color} strokeWidth="7" strokeLinecap="round" />
      <path d="M50 78 L35 92" stroke={color} strokeWidth="7" strokeLinecap="round" />
      {/* Impacto */}
      <path d="M25 96 Q40 100 60 96 Q80 100 95 96" stroke={color} strokeWidth="2" strokeDasharray="4 3" opacity="0.5" />
      {/* Linhas de choque */}
      <path d="M15 85 L22 78" stroke={color} strokeWidth="2" opacity="0.6" />
      <path d="M12 92 L20 90" stroke={color} strokeWidth="2" opacity="0.6" />
      <path d="M14 99 L22 96" stroke={color} strokeWidth="2" opacity="0.6" />
    </svg>
  );
}

function SleepingIcon({ color }: { color: string }) {
  return (
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Corpo deitado */}
      <rect x="15" y="68" width="90" height="18" rx="9" fill={color} opacity="0.3" />
      {/* Cabeça */}
      <circle cx="95" cy="62" r="14" fill={color} />
      {/* Corpo */}
      <rect x="20" y="68" width="72" height="14" rx="7" fill={color} />
      {/* Zzzs */}
      <text x="68" y="50" fontSize="14" fill={color} opacity="0.7" fontWeight="bold">z</text>
      <text x="78" y="38" fontSize="18" fill={color} opacity="0.5" fontWeight="bold">z</text>
      <text x="90" y="24" fontSize="22" fill={color} opacity="0.3" fontWeight="bold">z</text>
    </svg>
  );
}

const ICONS: Record<EventType, React.FC<{ color: string }>> = {
  no_presence:          HouseIcon,
  presence_still:       SittingIcon,
  presence_moving:      WalkingIcon,
  fall_suspected:       FallingIcon,
  prolonged_inactivity: SleepingIcon,
};

export function PulsoView({ eventType }: Props) {
  const { color, animation } = CONFIG[eventType];
  const Icon = ICONS[eventType];

  return (
    <div className="pulso-view" style={{ '--pulso-color': color } as React.CSSProperties}>
      <div className={`pulso-ring ${animation}`}>
        <div className="pulso-icon-wrap">
          <Icon color={color} />
        </div>
      </div>
    </div>
  );
}
