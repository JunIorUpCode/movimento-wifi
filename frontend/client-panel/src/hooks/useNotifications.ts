/**
 * Hook personalizado para gerenciamento de notificações.
 * 
 * Funcionalidades:
 * - Obter configuração de notificações
 * - Atualizar configuração
 * - Testar canal de notificação
 * - Obter logs de notificações
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../services/api'
import type { UpdateNotificationConfigRequest, TestNotificationRequest } from '../types'

/**
 * Hook para obter configuração de notificações
 */
export function useNotificationConfig() {
  return useQuery({
    queryKey: ['notifications', 'config'],
    queryFn: () => notificationsApi.getConfig(),
  })
}

/**
 * Hook para atualizar configuração de notificações
 */
export function useUpdateNotificationConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateNotificationConfigRequest) =>
      notificationsApi.updateConfig(data),
    onSuccess: () => {
      // Invalida cache de configuração
      queryClient.invalidateQueries({ queryKey: ['notifications', 'config'] })
    },
  })
}

/**
 * Hook para testar canal de notificação
 */
export function useTestNotification() {
  return useMutation({
    mutationFn: (data: TestNotificationRequest) =>
      notificationsApi.test(data),
  })
}

/**
 * Hook para obter logs de notificações
 */
export function useNotificationLogs(page?: number, pageSize?: number) {
  return useQuery({
    queryKey: ['notifications', 'logs', page, pageSize],
    queryFn: () => notificationsApi.getLogs({ page, page_size: pageSize }),
  })
}
