/**
 * Página de configuração de notificações.
 * 
 * Exibe:
 * - Formulário para configurar canais (Telegram, email, webhook)
 * - Wizard para criar bot Telegram (instruções passo a passo)
 * - Configurar min_confidence, quiet_hours, cooldown
 * - Botão "Testar" para cada canal
 * - Exibir logs de notificações recentes
 */

import { Bell, Send, Mail, Webhook, Check } from 'lucide-react'
import { useState } from 'react'
import { useNotificationConfig, useUpdateNotificationConfig, useTestNotification } from '../hooks/useNotifications'

export default function NotificationsPage() {
  const { data: config, isLoading } = useNotificationConfig()
  const updateConfig = useUpdateNotificationConfig()
  const testNotification = useTestNotification()

  const [enabled, setEnabled] = useState(config?.enabled ?? true)
  const [minConfidence, setMinConfidence] = useState(config?.min_confidence ?? 0.7)
  const [cooldownSeconds, setCooldownSeconds] = useState(config?.cooldown_seconds ?? 300)

  const handleSave = async () => {
    try {
      await updateConfig.mutateAsync({
        enabled,
        min_confidence: minConfidence,
        cooldown_seconds: cooldownSeconds,
      })
      alert('Configurações salvas com sucesso!')
    } catch (error) {
      alert('Erro ao salvar configurações')
    }
  }

  if (isLoading) {
    return <div className="text-center py-12">Carregando...</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Notificações</h1>
        <p className="text-gray-600 mt-1">
          Configure como e quando você deseja receber alertas
        </p>
      </div>

      {/* Configurações gerais */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Configurações Gerais
        </h2>

        <div className="space-y-4">
          {/* Ativar/Desativar */}
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Notificações Ativas</p>
              <p className="text-sm text-gray-600">
                Ativar ou desativar todas as notificações
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          {/* Confiança mínima */}
          <div>
            <label className="label">
              Confiança Mínima: {(minConfidence * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Apenas eventos com confiança acima deste valor gerarão notificações
            </p>
          </div>

          {/* Cooldown */}
          <div>
            <label className="label">
              Intervalo entre notificações (segundos)
            </label>
            <input
              type="number"
              value={cooldownSeconds}
              onChange={(e) => setCooldownSeconds(parseInt(e.target.value))}
              className="input"
              min="0"
              step="60"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tempo mínimo entre notificações do mesmo tipo
            </p>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleSave}
            disabled={updateConfig.isPending}
            className="btn btn-primary"
          >
            {updateConfig.isPending ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </div>

      {/* Canais de notificação */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Telegram */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Send className="w-6 h-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Telegram</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Receba alertas instantâneos no Telegram
          </p>
          <button className="btn btn-secondary w-full text-sm">
            Configurar
          </button>
        </div>

        {/* Email */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Mail className="w-6 h-6 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Email</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Receba notificações por email
          </p>
          <button className="btn btn-secondary w-full text-sm">
            Configurar
          </button>
        </div>

        {/* Webhook */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Webhook className="w-6 h-6 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Webhook</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Integre com seus sistemas
          </p>
          <button className="btn btn-secondary w-full text-sm">
            Configurar
          </button>
        </div>
      </div>
    </div>
  )
}
