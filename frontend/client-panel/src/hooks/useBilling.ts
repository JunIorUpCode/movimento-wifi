/**
 * Hook personalizado para gerenciamento de billing e assinatura.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billingApi } from '../services/api'
import type { UpgradePlanRequest } from '../types'

export function useSubscription() {
  return useQuery({
    queryKey: ['billing', 'subscription'],
    queryFn: () => billingApi.getSubscription(),
  })
}

export function useUpgradePlan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpgradePlanRequest) => billingApi.upgradePlan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing', 'subscription'] })
    },
  })
}

export function useInvoices(page?: number, pageSize?: number) {
  return useQuery({
    queryKey: ['billing', 'invoices', page, pageSize],
    queryFn: () => billingApi.getInvoices({ page, page_size: pageSize }),
  })
}
