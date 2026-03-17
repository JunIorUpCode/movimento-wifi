/* AlertBanner — Banner de alerta para eventos críticos */

import { useStore } from '../store/useStore';
import { AlertTriangle, X } from 'lucide-react';

export function AlertBanner() {
  const activeAlert = useStore((s) => s.activeAlert);
  const alertVisible = useStore((s) => s.alertVisible);
  const dismissAlert = useStore((s) => s.dismissAlert);

  if (!alertVisible || !activeAlert) return null;

  return (
    <div className="alert-banner">
      <div className="alert-content">
        <AlertTriangle size={22} />
        <span>{activeAlert}</span>
      </div>
      <button className="alert-dismiss" onClick={dismissAlert}>
        <X size={18} />
      </button>
    </div>
  );
}
