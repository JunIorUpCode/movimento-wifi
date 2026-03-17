/**
 * Página de dashboard administrativo.
 * 
 * Exibe:
 * - Métricas globais (tenants, dispositivos, receita)
 * - Gráficos de eventos por hora
 * - Métricas de sistema (latência, CPU, memória)
 * - Atualização em tempo real via polling (30s)
 */

import { useQuery } from '@tanstack/react-query'
import { metricsApi } from '../services/api'
import {
  Users,
  Smartphone,
  Activity,
  TrendingUp,
  Cpu,
  HardDrive,
  Clock,
} from 'lucide-react'

/**
 * DashboardPage Component
 * 
 * Dashboard principal com métricas e estatísticas do sistema.
 */
export default function DashboardPage() {
  // Busca métricas do sistema com polling a cada 30 segundos
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: () => metricsApi.getSystem(),
    refetchInterval: 30000, // 30 segundos
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando métricas...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Erro ao carregar métricas do sistema</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Visão geral da plataforma WiFiSense SaaS
        </p>
      </div>

      {/* Cards de métricas principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total de Tenants */}
        <MetricCard
          title="Total de Tenants"
          value={metrics?.total_tenants || 0}
          subtitle={`${metrics?.active_tenants || 0} ativos`}
          icon={Users}
          color="blue"
        />

        {/* Dispositivos Online */}
        <MetricCard
          title="Dispositivos"
          value={metrics?.devices_online || 0}
          subtitle={`de ${metrics?.total_devices || 0} total`}
          icon={Smartphone}
          color="green"
        />

        {/* Eventos Hoje */}
        <MetricCard
          title="Eventos Hoje"
          value={metrics?.total_events_today || 0}
          icon={Activity}
          color="purple"
        />

        {/* Latência API */}
        <MetricCard
          title="Latência API"
          value={`${metrics?.api_latency_ms || 0}ms`}
          icon={Clock}
          color="orange"
        />
      </div>

      {/* Métricas de sistema */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU Usage */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Uso de CPU</h3>
            <Cpu className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Utilização</span>
              <span className="font-medium text-gray-900">
                {metrics?.cpu_usage_percent?.toFixed(1) || 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  (metrics?.cpu_usage_percent || 0) > 80
                    ? 'bg-red-500'
                    : (metrics?.cpu_usage_percent || 0) > 60
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${metrics?.cpu_usage_percent || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Uso de Memória</h3>
            <HardDrive className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Utilização</span>
              <span className="font-medium text-gray-900">
                {metrics?.memory_usage_percent?.toFixed(1) || 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  (metrics?.memory_usage_percent || 0) > 80
                    ? 'bg-red-500'
                    : (metrics?.memory_usage_percent || 0) > 60
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${metrics?.memory_usage_percent || 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder para gráficos */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Eventos por Hora (Últimas 24h)
        </h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
          <p className="text-gray-500">Gráfico será implementado com Recharts</p>
        </div>
      </div>
    </div>
  )
}

/**
 * Componente de card de métrica
 */
interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  color?: 'blue' | 'green' | 'purple' | 'orange'
}

function MetricCard({ title, value, subtitle, icon: Icon, color = 'blue' }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}
