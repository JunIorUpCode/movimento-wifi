/* PushNotifications.tsx — Tarefa 36: Notificações Push no browser */

import { useEffect, useState } from 'react';
import { Bell, BellOff, AlertTriangle, CheckCircle } from 'lucide-react';
import { useStore } from '../store/useStore';

type PermissionState = 'default' | 'granted' | 'denied' | 'unsupported';

export function PushNotifications() {
  const pushEnabled = useStore((s) => s.pushEnabled);
  const setPushEnabled = useStore((s) => s.setPushEnabled);
  const recentAnomalies = useStore((s) => s.recentAnomalies);

  const [permission, setPermission] = useState<PermissionState>('default');

  useEffect(() => {
    if (!('Notification' in window)) {
      setPermission('unsupported');
      return;
    }
    setPermission(Notification.permission as PermissionState);
  }, []);

  const requestPermission = async () => {
    if (!('Notification' in window)) return;
    const result = await Notification.requestPermission();
    setPermission(result as PermissionState);
    if (result === 'granted') {
      setPushEnabled(true);
      new Notification('WiFiSense', {
        body: 'Notificações push ativadas com sucesso!',
        icon: '/vite.svg',
      });
    }
  };

  const togglePush = () => {
    if (!pushEnabled && permission !== 'granted') {
      requestPermission();
    } else {
      setPushEnabled(!pushEnabled);
    }
  };

  const EVENT_LABELS: Record<string, string> = {
    fall_suspected: 'Queda Suspeita',
    prolonged_inactivity: 'Inatividade Prolongada',
  };

  return (
    <div className="page-content">
      <h2 className="page-title">Notificações Push</h2>
      <p className="page-subtitle">
        Receba alertas diretamente no browser quando anomalias críticas forem detectadas.
      </p>

      {/* Status */}
      <div className="card">
        <h3 className="card-title">Status das Notificações</h3>

        {permission === 'unsupported' && (
          <div className="alert-banner alert-err">
            <BellOff size={16} />
            <span>Este browser não suporta notificações push.</span>
          </div>
        )}

        {permission === 'denied' && (
          <div className="alert-banner alert-err">
            <BellOff size={16} />
            <span>
              Permissão bloqueada. Habilite notificações nas configurações do browser para este site.
            </span>
          </div>
        )}

        {permission === 'granted' && (
          <div className="alert-banner alert-ok">
            <CheckCircle size={16} />
            <span>Permissão concedida. Notificações estão disponíveis.</span>
          </div>
        )}

        <div className="push-toggle-row">
          <div>
            <strong>Notificações de anomalias</strong>
            <p className="text-muted">Alertas de queda e inatividade prolongada (confiança ≥ 85%)</p>
          </div>
          <button
            className={`btn ${pushEnabled ? 'btn-danger' : 'btn-primary'}`}
            onClick={togglePush}
            disabled={permission === 'denied' || permission === 'unsupported'}
          >
            {pushEnabled ? <><BellOff size={15} /> Desativar</> : <><Bell size={15} /> Ativar</>}
          </button>
        </div>

        {permission === 'default' && (
          <button className="btn btn-ghost mt-sm" onClick={requestPermission}>
            Solicitar Permissão do Browser
          </button>
        )}
      </div>

      {/* Anomalias recentes (recebidas via WebSocket) */}
      <div className="card">
        <h3 className="card-title">Anomalias Recentes (sessão atual)</h3>
        {recentAnomalies.length === 0 ? (
          <p className="text-muted">Nenhuma anomalia detectada nesta sessão.</p>
        ) : (
          <div className="anomaly-list">
            {recentAnomalies.map((a, i) => (
              <div key={i} className="anomaly-item">
                <AlertTriangle size={16} className="text-danger" />
                <div>
                  <strong>{EVENT_LABELS[a.event_type] ?? a.event_type}</strong>
                  <span className="text-muted">
                    {' — '}{Math.round(a.confidence * 100)}% confiança
                    {' — '}{new Date(a.timestamp * 1000).toLocaleTimeString('pt-BR')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Informações */}
      <div className="card">
        <h3 className="card-title">Como Funciona</h3>
        <ul className="info-list">
          <li>As notificações são enviadas pelo browser quando o WiFiSense detecta eventos críticos.</li>
          <li>Apenas eventos com confiança ≥ 85% geram notificações push.</li>
          <li>Tipos de evento: <strong>Queda Suspeita</strong> e <strong>Inatividade Prolongada</strong>.</li>
          <li>A aba do browser precisa estar aberta para receber alertas.</li>
          <li>Para notificações remotas (quando aba fechada), configure Telegram ou Webhook.</li>
        </ul>
      </div>
    </div>
  );
}
