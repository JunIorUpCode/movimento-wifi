/**
 * Componente de card de eventos recentes.
 * 
 * Exibe:
 * - Lista dos últimos eventos
 * - Tipo de evento com ícone
 * - Confidence score
 * - Timestamp
 * - Dispositivo
 */

import { Activity, UserCheck, AlertTriangle, Clock as ClockIcon } from 'lucide-react'
import type { Event, EventType } from '../types'
import { formatDistanceToNow } from '../utils/date'

interface RecentEventsCardProps {
  events: Event[]
  isLoading?: boolean
}

/**
 * Retorna ícone e cor para cada tipo de evento
 */
function getEventIcon(eventType: EventType) {
  switch (eventType) {
    case 'presence':
      return { icon: UserCheck, color: 'text-green-600', bg: 'bg-green-100' }
    case 'movement':
      return { icon: Activity, color: 'text-blue-600', bg: 'bg-blue-100' }
    case 'fall_suspected':
      return { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100' }
    case 'prolonged_inactivity':
      return { icon: ClockIcon, color: 'text-orange-600', bg: 'bg-orange-100' }
    default:
      return { icon: Activity, color: 'text-gray-600', bg: 'bg-gray-100' }
  }
}

/**
 * Retorna label em português para tipo de evento
 */
function getEventLabel(eventType: EventType): string {
  switch (eventType) {
    case 'presence':
      return 'Presença'
    case 'movement':
      return 'Movimento'
    case 'fall_suspected':
      return 'Queda Suspeita'
    case 'prolonged_inactivity':
      return 'Inatividade Prolongada'
    default:
      return eventType
  }
}

/**
 * RecentEventsCard Component
 * 
 * Exibe lista de eventos recentes com informações visuais.
 */
export default function RecentEventsCard({ events, isLoading }: RecentEventsCardProps) {
  if (isLoading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Eventos Recentes</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex items-center">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="ml-3 flex-1">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!events || events.length === 0) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Eventos Recentes</h2>
        <div className="text-center py-8">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">Nenhum evento registrado</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Eventos Recentes</h2>
      <div className="space-y-3">
        {events.slice(0, 5).map((event) => {
          const { icon: Icon, color, bg } = getEventIcon(event.event_type)
          
          return (
            <div
              key={event.id}
              className="flex items-start p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className={`p-2 rounded-lg ${bg}`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <div className="ml-3 flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">
                    {getEventLabel(event.event_type)}
                  </p>
                  <span className={`badge ${
                    event.confidence >= 0.9 ? 'badge-success' :
                    event.confidence >= 0.7 ? 'badge-info' :
                    'badge-warning'
                  }`}>
                    {(event.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center mt-1 text-xs text-gray-500">
                  <span>{event.device?.name || 'Dispositivo desconhecido'}</span>
                  <span className="mx-2">•</span>
                  <span>{formatDistanceToNow(event.timestamp)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
