/**
 * Hook personalizado para gerenciamento de eventos.
 * 
 * Funcionalidades:
 * - Listar eventos com filtros
 * - Obter timeline de eventos
 * - Obter estatísticas
 * - Marcar falso positivo
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '../services/api'
import type { EventFilters, MarkFalsePositiveRequest } from '../types'

/**
 * Hook para listar eventos com filtros
 */
export function useEvents(filters?: EventFilters) {
  return useQuery({
    queryKey: ['events', filters],
    queryFn: () => eventsApi.list(filters),
  })
}

/**
 * Hook para obter timeline de eventos
 */
export function useEventsTimeline(filters?: EventFilters) {
  return useQuery({
    queryKey: ['events', 'timeline', filters],
    queryFn: () => eventsApi.timeline(filters),
  })
}

/**
 * Hook para obter estatísticas de eventos
 */
export function useEventsStats() {
  return useQuery({
    queryKey: ['events', 'stats'],
    queryFn: () => eventsApi.stats(),
    refetchInterval: 30000, // Atualiza a cada 30 segundos
  })
}

/**
 * Hook para marcar evento como falso positivo
 */
export function useMarkFalsePositive() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: MarkFalsePositiveRequest }) =>
      eventsApi.markFalsePositive(id, data),
    onSuccess: () => {
      // Invalida cache de eventos para recarregar
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}
