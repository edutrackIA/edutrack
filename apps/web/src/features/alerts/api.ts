import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { RiskLevel } from '../../shared/lib/risk'
import type { ClassroomStudent } from '../classrooms/api'

export interface Alert {
  id: number
  student: ClassroomStudent
  level: RiskLevel
  is_read: boolean
  created_at: string
}

interface AlertsPage {
  total: number
  items: Alert[]
}

export function useAlerts(unreadOnly: boolean) {
  return useQuery({
    queryKey: ['alerts', 'list', unreadOnly],
    queryFn: ({ signal }) =>
      apiRequest<AlertsPage>(`/alerts?size=100${unreadOnly ? '&unread=true' : ''}`, { signal }),
    placeholderData: (previous) => previous,
  })
}

export function useUnreadAlertsCount(enabled: boolean) {
  return useQuery({
    queryKey: ['alerts', 'unread-count'],
    queryFn: async ({ signal }) =>
      (await apiRequest<AlertsPage>('/alerts?unread=true&size=1', { signal })).total,
    enabled,
    refetchInterval: 60_000,
  })
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (alertId: number) =>
      apiRequest<Alert>(`/alerts/${alertId}`, { method: 'PATCH', body: { is_read: true } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })
}
