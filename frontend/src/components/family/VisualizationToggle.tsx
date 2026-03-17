/* VisualizationToggle — Seletor dos 3 modos de visualização */

import { useStore, type FamilyViewMode } from '../../store/useStore';

const MODES: { id: FamilyViewMode; label: string; emoji: string }[] = [
  { id: 'pulso',    label: 'Pulso',    emoji: '🔵' },
  { id: 'presenca', label: 'Presença', emoji: '🚶' },
  { id: 'radar',    label: 'Radar',    emoji: '📡' },
];

export function VisualizationToggle() {
  const familyViewMode = useStore((s) => s.familyViewMode);
  const setFamilyViewMode = useStore((s) => s.setFamilyViewMode);

  return (
    <div className="viz-toggle">
      {MODES.map((mode) => (
        <button
          key={mode.id}
          className={`viz-toggle-btn ${familyViewMode === mode.id ? 'active' : ''}`}
          onClick={() => setFamilyViewMode(mode.id)}
        >
          <span className="viz-toggle-emoji">{mode.emoji}</span>
          <span className="viz-toggle-label">{mode.label}</span>
        </button>
      ))}
    </div>
  );
}
