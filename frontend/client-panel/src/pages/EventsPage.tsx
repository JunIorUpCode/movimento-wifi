/**
 * Página de timeline de eventos.
 * 
 * Exibe:
 * - Listagem de eventos com timestamps, tipos, confidence
 * - Filtros por tipo, data, dispositivo
 * - Paginação infinita (scroll)
 * - Ação: marcar falso positivo
 */

import { useState } from 'react'
import { Activity, Filter } from 'lucide-react'
import { useEventsTimeline, useMarkFalsePositive } from '../hooks/useEvents'
import { useDevices } from '../hooks/useDevices'
import EventCard from '../components/EventCard'
import type { EventType } from '../types'

export default function EventsPage() {
  // Estados de filtros
  const [eventType, setEventType] = useState<EventType | ''>('')
  const [deviceId, setDeviceId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Carrega dados
  const { data: events, isLoading, refetch } = useEventsTimeline({
    event_type: eventType || undefined,
    device_id: deviceId || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  })
  const { data: devices } = useDevices()
  const markFalsePositive = useMarkFalsePositive()

  // Handler para marcar falso positivo
  const handleMarkFalsePositive = async (eventId: string, notes?: string) => {
    try {
      await markFalsePositive.mutateAsync({
        id: eventId,
        data: notes ? { user_notes: notes } : undefined,
      })
      refetch()
    } catch (error) {
      console.error('Erro ao marcar falso positivo:', error)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Timeline de Eventos</h1>
        <p className="text-gray-600 mt-1">
          Histórico completo de eventos detectados
        </p>
      </div>

      {/* Filtros */}
      <div className="card mb-6">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Filtros</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Filtro por tipo */}
          <div>
            <label className="label">Tipo de Evento</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value as EventType | '')}
              className="input"
            >
              <option value="">Todos</option>
              <option value="presence">Presença</option>
              <option value="movement">Movimento</option>
              <option value="fall_suspected">Queda Suspeita</option>
              <option value="prolonged_inactivity">Inatividade Prolongada</option>
            </select>
          </div>

          {/* Filtro por dispositivo */}
          <div>
            <label className="label">Dispositivo</label>
            <select
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              className="input"
            >
              <option value="">Todos</option>
              {devices?.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro por data inicial */}
          <div>
            <label className="label">Data Inicial</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="input"
            />
          </div>

          {/* Filtro por data final */}
          <div>
            <label className="label">Data Final</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input"
            />
          </div>
        </div>

        {/* Botão para limpar filtros */}
        {(eventType || deviceId || startDate || endDate) && (
          <div className="mt-4">
            <button
              onClick={() => {
                setEventType('')
                setDeviceId('')
                setStartDate('')
                setEndDate('')
              }}
              className="btn btn-secondary text-sm"
            >
              Limpar Filtros
            </button>
          </div>
        )}
      </div>

      {/* Lista de eventos */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : !events || events.length === 0 ? (
        <div className="card text-center py-12">
          <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum evento encontrado
          </h3>
          <p className="text-gray-600">
            {eventType || deviceId || startDate || endDate
              ? 'Tente ajustar os filtros para ver mais eventos'
              : 'Eventos serão exibidos aqui quando detectados'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              onMarkFalsePositive={handleMarkFalsePositive}
            />
          ))}
        </div>
      )}

      {/* Nota sobre paginação */}
      {events && events.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Exibindo {events.length} eventos</p>
        </div>
      )}
    </div>
  )
}
