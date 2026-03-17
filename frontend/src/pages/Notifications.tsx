/* Notifications.tsx — Tarefa 33: Configuração e logs de notificações */

import { useEffect, useState } from 'react';
import { Bell, Send, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { NotificationLog } from '../types';

export function Notifications() {
  const [logs, setLogs] = useState<NotificationLog[]>([]);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [testChannel, setTestChannel] = useState('telegram');
  const [testMsg, setTestMsg] = useState('Teste de notificação WiFiSense');
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    const [l, c] = await Promise.all([
      api.getNotificationLogs(100),
      api.getNotificationConfig(),
    ]);
    setLogs(l);
    setConfig(c);
  };

  useEffect(() => { loadLogs(); }, []);

  const handleTest = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await api.testNotification(testChannel, testMsg);
      setMessage({ type: 'ok', text: `Notificação de teste enviada para '${testChannel}'.` });
    } catch (e: unknown) {
      setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro ao enviar teste.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-content">
      <h2 className="page-title">Notificações</h2>

      {message && (
        <div className={`alert-banner ${message.type === 'ok' ? 'alert-ok' : 'alert-err'}`}>
          {message.type === 'ok' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Status de configuração */}
      {config && (
        <div className="card">
          <h3 className="card-title">Status dos Canais</h3>
          <div className="channels-grid">
            <div className={`channel-card ${(config.telegram_configured as boolean) ? 'configured' : ''}`}>
              <Bell size={20} />
              <div>
                <strong>Telegram</strong>
                <span>{(config.telegram_configured as boolean) ? `${config.telegram_chat_count} chat(s)` : 'Não configurado'}</span>
              </div>
            </div>
            <div className={`channel-card ${(config.whatsapp_configured as boolean) ? 'configured' : ''}`}>
              <Bell size={20} />
              <div>
                <strong>WhatsApp</strong>
                <span>{(config.whatsapp_configured as boolean) ? `${config.whatsapp_recipient_count} destinatário(s)` : 'Não configurado'}</span>
              </div>
            </div>
            <div className={`channel-card ${(config.webhook_configured as boolean) ? 'configured' : ''}`}>
              <Bell size={20} />
              <div>
                <strong>Webhook</strong>
                <span>{(config.webhook_configured as boolean) ? `${config.webhook_url_count} URL(s)` : 'Não configurado'}</span>
              </div>
            </div>
          </div>
          <div className="config-meta">
            <span>Habilitado: <strong>{(config.enabled as boolean) ? 'Sim' : 'Não'}</strong></span>
            <span>Confiança mínima: <strong>{Math.round((config.min_confidence as number) * 100)}%</strong></span>
            <span>Cooldown: <strong>{config.cooldown_seconds}s</strong></span>
          </div>
          <p className="text-muted mt-sm">
            Para alterar credenciais de canais, use <code>PUT /api/notifications/config</code>.
          </p>
        </div>
      )}

      {/* Enviar teste */}
      <div className="card">
        <h3 className="card-title">Enviar Notificação de Teste</h3>
        <div className="form-row">
          <label>Canal</label>
          <select className="input" value={testChannel} onChange={(e) => setTestChannel(e.target.value)}>
            <option value="telegram">Telegram</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="webhook">Webhook</option>
          </select>
        </div>
        <div className="form-row">
          <label>Mensagem</label>
          <input className="input" value={testMsg} onChange={(e) => setTestMsg(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={handleTest} disabled={loading}>
          <Send size={15} /> Enviar Teste
        </button>
      </div>

      {/* Logs */}
      <div className="card">
        <div className="card-header-row">
          <h3 className="card-title">Histórico de Envios</h3>
          <button className="btn btn-sm btn-ghost" onClick={loadLogs}>
            <RefreshCw size={14} /> Atualizar
          </button>
        </div>
        {logs.length === 0 ? (
          <p className="text-muted">Nenhuma notificação enviada ainda.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Horário</th><th>Canal</th><th>Evento</th><th>Confiança</th><th>Status</th></tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{new Date(l.timestamp).toLocaleString('pt-BR')}</td>
                  <td>{l.channel}</td>
                  <td>{l.event_type}</td>
                  <td>{Math.round(l.confidence * 100)}%</td>
                  <td>
                    {l.success
                      ? <span className="badge badge-green">OK</span>
                      : <span className="badge badge-red" title={l.error_message ?? ''}>Falha</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
