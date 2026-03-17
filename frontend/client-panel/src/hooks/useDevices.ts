/**
 * Hook personalizado para gerenciamento de dispositivos.
 * 
 * Funcionalidades:
 * - Listar dispositivos do tenant
 * - Obter detalhes de um dispositivo
 * - Registrar novo dispositivo
 * - Atualizar dispositivo
 * - Deletar dispositivo
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { devicesApi } from '../services/api'
import type { Device, RegisterDeviceRequest, UpdateDeviceRequest } from '../types'

/**
 * Hook para listar todos os dispositivos do tenant
 */
export function useDevices() {
  return useQuery({
    queryKey: ['devices'],
    queryFn: () => devicesApi.list(),
  })
}

/**
 * Hook para obter detalhes de um dispositivo específico
 */
export function useDevice(id: string) {
  return useQuery({
    queryKey: ['devices', id],
    queryFn: () => devicesApi.get(id),
    enabled: !!id,
  })
}

/**
 * Hook para registrar um novo dispositivo
 */
export function useRegisterDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: RegisterDeviceRequest) => devicesApi.register(data),
    onSuccess: () => {
      // Invalida cache de dispositivos para recarregar lista
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })
}

/**
 * Hook para atualizar um dispositivo
 */
export function useUpdateDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateDeviceRequest }) =>
      devicesApi.update(id, data),
    onSuccess: (_, variables) => {
      // Invalida cache do dispositivo específico e da lista
      queryClient.invalidateQueries({ queryKey: ['devices', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })
}

/**
 * Hook para deletar um dispositivo
 */
export function useDeleteDevice() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => devicesApi.delete(id),
    onSuccess: () => {
      // Invalida cache de dispositivos para recarregar lista
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })
}
