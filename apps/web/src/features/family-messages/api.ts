import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { ClassroomStudent } from '../classrooms/api'

export interface FamilyMessage {
  id: number
  student: ClassroomStudent
  kind: string
  kind_label: string
  reference_date: string
  status: 'SENT' | 'HELD' | 'FAILED' | 'DISCARDED'
  subject: string
  intro: string
  rows: [string, string][]
  hold_reason: string | null
  created_at: string
  sent_at: string | null
}

export function useHeldMessages() {
  return useQuery({
    queryKey: ['family-messages', 'held'],
    queryFn: ({ signal }) => apiRequest<FamilyMessage[]>('/family-messages/held', { signal }),
  })
}

export function useReviewMessage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'release' | 'discard' }) =>
      apiRequest<FamilyMessage>(`/family-messages/${id}/${action}`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-messages'] }),
  })
}
