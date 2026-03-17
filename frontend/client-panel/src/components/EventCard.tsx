/**
 * Componente de card de evento individual.
 * 
 * Exibe:
 * - Tipo de evento com ícone
 * - Confidence score
 * - Timestamp
 * - Dispositivo
 * - Ação para marcar falso positivo
 */

import { Activity, UserCheck, AlertTriangle, Clock as ClockIcon, Flag, Check } from 'lucide-react'
import type { Event, EventType } from '../types'
import { formatDateTime } from '../utils/date'
import { useState } from 'react'

interface EventCardProps {
  event: Event
  onMarkFalsePositive?: (eventId: string, notes?: string) => void
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
      return 'Presença Detectada'
    case 'movement':
      return 'Movimento Detectado'
    case 'fall_suspected':
      return 'Queda Suspeita'
    case 'prolonged_inactivity':
      return 'Inatividade Prolongada'
    default:
      return eventType
  }
}

/**
 * EventCard Component
 * 
 * Card detalhado para exibir informações de um evento.
 */
export default function EventCard({ event, onMarkFalsePositive }: EventCardProps) {
  const [showNotes, setShowNotes] = useState(false)
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { icon: Icon, color, bg } = getEventIcon(event.event_type)

  const handleMarkFalsePositive = async () => {
    if (!onMarkFalsePositive) return

    setIsSubmitting(true)
    try {
      await onMarkFalsePositive(event.id, notes || undefined)
      setShowNotes(false)
      setNotes('')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={`card ${event.is_false_positive ? 'opacity-60 border-2 border-gray-300' : ''}`}>
      <div className="flex items-start justify-between">
        {/* Ícone e informações */}
        <div className="flex items-start flex-1">
          <div className={`p-3 rounded-lg ${bg}`}>
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
          <div className="ml-4 flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900">
                {getEventLabel(event.event_type)}
              </h3>
              <span className={`badge ${
                event.confidence >= 0.9 ? 'badge-success' :
                event.confidence >= 0.7 ? 'badge-info' :
                'badge-warning'
              }`}>
                Confiança: {(event.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* Informações do evento */}
            <div className="space-y-1 text-sm text-gray-600">
              <p>
                <span className="font-medium">Dispositivo:</span>{' '}
                {event.device?.name || 'Desconhecido'}
              </p>
              <p>
                <span className="font-medium">Data/Hora:</span>{' '}
                {formatDateTime(event.timestamp)}
              </p>
              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <p>
                  <span className="font-medium">Detalhes:</span>{' '}
                  {JSON.stringify(event.metadata)}
                </p>
              )}
            </div>

            {/* Falso positivo */}
            {event.is_false_positive && (
              <div className="mt-3 p-2 bg-gray-100 rounded flex items-center">
                <Flag className="w-4 h-4 text-gray-600 mr-2" />
                <span className="text-sm text-gray-700">
                  Marcado como falso positivo
                </span>
                {event.user_notes && (
                  <span className="text-sm text-gray-600 ml-2">
                    - {event.user_notes}
                  </span>
                )}
              </div>
            )}

            {/* Formulário para marcar falso positivo */}
            {!event.is_false_positive && showNotes && (
              <div className="mt-3 p-3 bg-gray-50 rounded">
                <label className="label">
                  Notas (opcional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="input resize-none"
                  rows={2}
                  placeholder="Por que este é um falso positivo?"
                  disabled={isSubmitting}
                />
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={handleMarkFalsePositive}
                    disabled={isSubmitting}
                    className="btn btn-primary text-sm"
                  >
                    {isSubmitting ? 'Salvando...' : 'Confirmar'}
                  </button>
                  <button
                    onClick={() => {
                      setShowNotes(false)
                      setNotes('')
                    }}
                    disabled={isSubmitting}
                    className="btn btn-secondary text-sm"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ações */}
      {!event.is_false_positive && !showNotes && onMarkFalsePositive && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => setShowNotes(true)}
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
          >
            <Flag className="w-4 h-4 mr-1" />
            Marcar como falso positivo
          </button>
        </div>
      )}
    </div>
  )
}
