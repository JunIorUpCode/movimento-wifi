/**
 * Página de dashboard do cliente.
 * 
 * Exibe:
 * - Status de todos os dispositivos
 * - Gráficos de signal strength em tempo real
 * - Indicadores visuais de eventos recentes
 * - Atualização em tempo real via WebSocket
 */

import { Smartphone, Activity, AlertTriangle, TrendingUp } from 'lucide-react'
import { useDevices } from '../hooks/useDevices'
import { useEventsStats, useEventsTimeline } from '../hooks/useEvents'
import StatsCard from '../components/StatsCard'
import DeviceStatusCard from '../components/DeviceStatusCard'
import RecentEventsCard from '../components/RecentEventsCard'

export default function DashboardPage() {
  // Carrega dados
  const { data: devices, isLoading: devicesLoading } = useDevices()
  const { data: stats, isLoading: statsLoading } = useEventsStats()
  const { data: recentEvents, isLoading: eventsLoading } = useEventsTimeline({
    page_size: 5,
  })

  // Calcula estatísticas de dispositivos
  const devicesOnline = devices?.filter(d => d.status === 'online').length || 0
  const devicesTotal = devices?.length || 0

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Visão geral dos seus dispositivos e eventos
        </p>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={Smartphone}
          label="Dispositivos Online"
          value={`${devicesOnline}/${devicesTotal}`}
          color="green"
          isLoading={devicesLoading}
        />
        <StatsCard
          icon={Activity}
          label="Eventos Hoje"
          value={stats?.events_today || 0}
          color="blue"
          isLoading={statsLoading}
        />
        <StatsCard
          icon={TrendingUp}
          label="Eventos Esta Semana"
          value={stats?.events_week || 0}
          color="purple"
          isLoading={statsLoading}
        />
        <StatsCard
          icon={AlertTriangle}
          label="Alertas Críticos"
          value={0}
          color="red"
          isLoading={statsLoading}
        />
      </div>

      {/* Grid de conteúdo */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna esquerda - Dispositivos */}
        <div className="lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Meus Dispositivos
          </h2>
          
          {devicesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <div key={i} className="card animate-pulse">
                  <div className="h-32 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
          ) : !devices || devices.length === 0 ? (
            <div className="card text-center py-12">
              <Smartphone className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhum dispositivo registrado
              </h3>
              <p className="text-gray-600 mb-4">
                Registre seu primeiro dispositivo para começar a monitorar
              </p>
              <button className="btn btn-primary">
                Registrar Dispositivo
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {devices.map((device) => (
                <DeviceStatusCard key={device.id} device={device} />
              ))}
            </div>
          )}
        </div>

        {/* Coluna direita - Eventos recentes */}
        <div>
          <RecentEventsCard
            events={recentEvents || []}
            isLoading={eventsLoading}
          />
        </div>
      </div>

      {/* Nota sobre WebSocket */}
      {devicesOnline > 0 && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <Activity className="w-5 h-5 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Atualização em tempo real ativa.</span>
                {' '}
                Os dados são atualizados automaticamente via WebSocket.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
