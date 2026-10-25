import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { ClassroomStudent } from '../classrooms/api'
import type { RecommendationStatus } from '../students/types'

export interface ReviewItem {
  id: number
  student: ClassroomStudent
  period_id: number
  status: RecommendationStatus
  parent_items: string[]
  teacher_items: string[]
  reviewed_at: string | null
  sent_at: string | null
  created_at: string
}

export function useRecommendationQueue(status: RecommendationStatus) {
  return useQuery({
    queryKey: ['recommendations', 'queue', status],
    queryFn: ({ signal }) =>
      apiRequest<ReviewItem[]>(`/recommendations?status=${status}`, { signal }),
    placeholderData: (previous) => previous,
  })
}

function useRecommendationAction<TVariables>(
  request: (variables: TVariables) => Promise<ReviewItem>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: (item) => {
      void queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      void queryClient.invalidateQueries({ queryKey: ['students', item.student.id] })
    },
  })
}

/** Saves the family's text (if edited) and then approves, which emails the family. */
export function useApproveRecommendation() {
  return useRecommendationAction(async ({ id, items }: { id: number; items?: string[] }) => {
    if (items) {
      await apiRequest<ReviewItem>(`/recommendations/${id}`, {
        method: 'PATCH',
        body: { parent_items: items },
      })
    }
    return apiRequest<ReviewItem>(`/recommendations/${id}/approve`, { method: 'POST' })
  })
}

export function useSaveRecommendation() {
  return useRecommendationAction(({ id, items }: { id: number; items: string[] }) =>
    apiRequest<ReviewItem>(`/recommendations/${id}`, {
      method: 'PATCH',
      body: { parent_items: items },
    }),
  )
}

export function useDiscardRecommendation() {
  return useRecommendationAction((id: number) =>
    apiRequest<ReviewItem>(`/recommendations/${id}/discard`, { method: 'POST' }),
  )
}

export function useResendRecommendation() {
  return useRecommendationAction((id: number) =>
    apiRequest<ReviewItem>(`/recommendations/${id}/send`, { method: 'POST' }),
  )
}
