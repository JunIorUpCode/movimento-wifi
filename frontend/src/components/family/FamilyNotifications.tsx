/* FamilyNotifications — Configuração de notificações no Painel Família */

import { useEffect, useState } from 'react';
import { api } from '../../services/api';

interface NotifConfig {
  enabled: boolean;
  telegram_configured: boolean;
  telegram_chat_count: number;
  whatsapp_configured: boolean;
  min_confidence: number;
  cooldown_seconds: number;
}

export function FamilyNotifications() {
  const [config, setConfig] = useState<NotifConfig | null>(null);
  const [testMsg, setTestMsg] = useState('Teste de notificação WiFiSense');
  const [feedback, setFeedback] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getNotificationConfig()
      .then((c) => setConfig(c as NotifConfig))
      .catch(() => {});
  }, []);

  const handleTest = async () => {
    setLoading(true);
    setFeedback(null);
    try {
      await api.testNotification('telegram', testMsg);
      setFeedback({ type: 'ok', text: '✓ Mensagem enviada para o Telegram!' });
    } catch {
      setFeedback({ type: 'err', text: 'Falha ao enviar. Verifique as configurações.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="family-notifications">
      <h3 className="family-section-title">Canais de notificação</h3>

      {/* Telegram */}
      <div className={`family-notif-card ${config?.telegram_configured ? 'configured' : ''}`}>
        <div className="family-notif-header">
          <span className="family-notif-icon">✈️</span>
          <div>
            <span className="family-notif-name">Telegram</span>
            <span className={`family-notif-badge ${config?.telegram_configured ? 'active' : 'inactive'}`}>
              {config?.telegram_configured ? 'Configurado' : 'Não configurado'}
            </span>
          </div>
        </div>
        {config?.telegram_configured && (
          <p className="family-notif-info">
            {config.telegram_chat_count} destinatário(s) cadastrado(s)
          </p>
        )}
        {config?.telegram_configured && (
          <div className="family-notif-test">
            <input
              className="family-notif-input"
              value={testMsg}
              onChange={(e) => setTestMsg(e.target.value)}
              placeholder="Mensagem de teste..."
            />
            <button
              className="family-btn family-btn-primary"
              onClick={handleTest}
              disabled={loading}
            >
              {loading ? 'Enviando…' : 'Testar'}
            </button>
          </div>
        )}
        {!config?.telegram_configured && (
          <p className="family-notif-info text-muted">
            Configure o bot do Telegram nas configurações avançadas.
          </p>
        )}
      </div>

      {/* WhatsApp — em breve */}
      <div className="family-notif-card coming-soon">
        <div className="family-notif-header">
          <span className="family-notif-icon">💬</span>
          <div>
            <span className="family-notif-name">WhatsApp</span>
            <span className="family-notif-badge coming">Em breve</span>
          </div>
        </div>
        <p className="family-notif-info text-muted">
          Notificações via WhatsApp estarão disponíveis em uma próxima atualização.
        </p>
      </div>

      {/* Feedback */}
      {feedback && (
        <div className={`family-feedback ${feedback.type === 'ok' ? 'ok' : 'err'}`}>
          {feedback.text}
        </div>
      )}

      {/* Info de configuração */}
      {config && (
        <div className="family-notif-settings">
          <h4>Configuração atual</h4>
          <div className="family-notif-settings-row">
            <span>Confiança mínima</span>
            <span>{Math.round(config.min_confidence * 100)}%</span>
          </div>
          <div className="family-notif-settings-row">
            <span>Intervalo entre alertas</span>
            <span>{Math.round(config.cooldown_seconds / 60)} min</span>
          </div>
        </div>
      )}
    </div>
  );
}
