/**
 * Página de visualização de plano e billing.
 * 
 * Exibe:
 * - Plano atual (BÁSICO/PREMIUM)
 * - Próxima data de cobrança e valor
 * - Botão para upgrade de plano
 * - Histórico de faturas
 */

import { CreditCard, Calendar, DollarSign, TrendingUp, FileText } from 'lucide-react'
import { useSubscription, useInvoices, useUpgradePlan } from '../hooks/useBilling'
import { formatDate } from '../utils/date'

export default function SubscriptionPage() {
  const { data: subscription, isLoading: subLoading } = useSubscription()
  const { data: invoicesData, isLoading: invoicesLoading } = useInvoices(1, 10)
  const upgradePlan = useUpgradePlan()

  const handleUpgrade = async () => {
    if (!confirm('Deseja fazer upgrade para o plano PREMIUM?')) return

    try {
      await upgradePlan.mutateAsync({ plan_type: 'premium' })
      alert('Upgrade realizado com sucesso!')
    } catch (error) {
      alert('Erro ao fazer upgrade')
    }
  }

  if (subLoading) {
    return <div className="text-center py-12">Carregando...</div>
  }

  const isPremium = subscription?.plan_type === 'premium'

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Assinatura</h1>
        <p className="text-gray-600 mt-1">
          Gerencie seu plano e pagamentos
        </p>
      </div>

      {/* Plano atual */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Plano Atual
            </h2>
            <div className="flex items-center">
              <span className={`text-3xl font-bold ${
                isPremium ? 'text-purple-600' : 'text-green-600'
              }`}>
                {isPremium ? 'PREMIUM' : 'BÁSICO'}
              </span>
              <span className={`ml-3 badge ${
                subscription?.status === 'active' ? 'badge-success' :
                subscription?.status === 'trial' ? 'badge-info' :
                'badge-warning'
              }`}>
                {subscription?.status === 'active' ? 'Ativo' :
                 subscription?.status === 'trial' ? 'Trial' :
                 'Suspenso'}
              </span>
            </div>
          </div>
          {!isPremium && (
            <button
              onClick={handleUpgrade}
              disabled={upgradePlan.isPending}
              className="btn btn-primary flex items-center"
            >
              <TrendingUp className="w-5 h-5 mr-2" />
              {upgradePlan.isPending ? 'Processando...' : 'Fazer Upgrade'}
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start">
            <DollarSign className="w-5 h-5 text-gray-600 mr-3 mt-0.5" />
            <div>
              <p className="text-sm text-gray-600">Valor Mensal</p>
              <p className="text-lg font-semibold text-gray-900">
                R$ {subscription?.monthly_amount.toFixed(2)}
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <Calendar className="w-5 h-5 text-gray-600 mr-3 mt-0.5" />
            <div>
              <p className="text-sm text-gray-600">Próxima Cobrança</p>
              <p className="text-lg font-semibold text-gray-900">
                {subscription?.next_billing_date
                  ? formatDate(subscription.next_billing_date)
                  : 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <CreditCard className="w-5 h-5 text-gray-600 mr-3 mt-0.5" />
            <div>
              <p className="text-sm text-gray-600">Dispositivos</p>
              <p className="text-lg font-semibold text-gray-900">
                {subscription?.devices_count} / {subscription?.device_limit}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Histórico de faturas */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Histórico de Faturas
        </h2>

        {invoicesLoading ? (
          <div className="text-center py-8">Carregando...</div>
        ) : !invoicesData?.items || invoicesData.items.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">Nenhuma fatura encontrada</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                    Data
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                    Valor
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                    Status
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {invoicesData.items.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-gray-100">
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {formatDate(invoice.created_at)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900">
                      R$ {invoice.amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge ${
                        invoice.status === 'paid' ? 'badge-success' :
                        invoice.status === 'pending' ? 'badge-warning' :
                        'badge-danger'
                      }`}>
                        {invoice.status === 'paid' ? 'Pago' :
                         invoice.status === 'pending' ? 'Pendente' :
                         'Falhou'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button className="text-sm text-primary-600 hover:text-primary-700">
                        Ver Detalhes
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
