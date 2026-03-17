/* ConfidenceScore — Barra visual de confiança */

import { useStore } from '../store/useStore';
import { EVENT_COLORS } from '../types';
import { ShieldCheck } from 'lucide-react';

export function ConfidenceScore() {
  const confidence = useStore((s) => s.confidence);
  const currentEvent = useStore((s) => s.currentEvent);
  const color = EVENT_COLORS[currentEvent];
  const pct = (confidence * 100).toFixed(0);

  return (
    <div className="confidence-card">
      <div className="confidence-card-header">
        <ShieldCheck size={20} color={color} />
        <h3>Score de Confiança</h3>
      </div>
      <div className="confidence-gauge">
        <svg viewBox="0 0 120 60" className="confidence-svg">
          <path
            d="M 10 55 A 50 50 0 0 1 110 55"
            fill="none"
            stroke="#2a2d3a"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path
            d="M 10 55 A 50 50 0 0 1 110 55"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${confidence * 157} 157`}
            className="confidence-arc"
          />
        </svg>
        <span className="confidence-value" style={{ color }}>{pct}%</span>
      </div>
    </div>
  );
}
