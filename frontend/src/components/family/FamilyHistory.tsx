/* FamilyHistory — Histórico simplificado em linguagem humana */

import { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../services/api';
import type { EventType } from '../../types';

const HUMAN_LABEL: Record<EventType, string> = {
  no_presence:          'Ninguém no ambiente',
  presence_still:       'Pessoa em repouso',
  presence_moving:      'Movimento detectado',
  fall_suspected:       '⚠️ Queda detectada',
  prolonged_inactivity: 'Sem movimento por muito tempo',
};

const EVENT_ICON: Record<EventType, string> = {
  no_presence:          '🏠',
  presence_still:       '🧘',
  presence_moving:      '🚶',
  fall_suspected:       '🚨',
  prolonged_inactivity: '😴',
};

const EVENT_DOT_COLOR: Record<EventType, string> = {
  no_presence:          '#6b7280',
  presence_still:       '#3b82f6',
  presence_moving:      '#10b981',
  fall_suspected:       '#ef4444',
  prolonged_inactivity: '#f59e0b',
};

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function formatRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'agora';
  if (m < 60) return `há ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `há ${h}h`;
  return `há ${Math.floor(h / 24)} dia(s)`;
}

export function FamilyHistory() {
  const events = useStore((s) => s.events);
  const setEvents = useStore((s) => s.setEvents);

  useEffect(() => {
    api.getEvents(30).then(setEvents).catch(() => {});
  }, [setEvents]);

  if (events.length === 0) {
    return (
      <div className="family-history-empty">
        <span>📋</span>
        <p>Nenhum evento registrado hoje.</p>
      </div>
    );
  }

  return (
    <div className="family-history">
      <h3 className="family-section-title">Atividade recente</h3>
      <div className="family-timeline">
        {events.map((ev) => (
          <div key={ev.id} className="family-timeline-item">
            <div
              className="family-timeline-dot"
              style={{ backgroundColor: EVENT_DOT_COLOR[ev.event_type] }}
            />
            <div className="family-timeline-content">
              <div className="family-timeline-row">
                <span className="family-timeline-icon">{EVENT_ICON[ev.event_type]}</span>
                <span className="family-timeline-label">{HUMAN_LABEL[ev.event_type]}</span>
              </div>
              <div className="family-timeline-meta">
                <span>{formatTime(ev.timestamp)}</span>
                <span className="family-timeline-relative">{formatRelative(ev.timestamp)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
