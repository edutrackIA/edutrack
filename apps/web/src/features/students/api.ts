import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { Recommendation, StudentDetail, StudentSummary } from './types'

export function useStudent(studentId: number) {
  return useQuery({
    queryKey: ['students', studentId],
    queryFn: ({ signal }) => apiRequest<StudentDetail>(`/students/${studentId}`, { signal }),
  })
}

export function useStudentSummary(studentId: number, periodId: number | null) {
  const query = periodId === null ? '' : `?period_id=${periodId}`
  return useQuery({
    queryKey: ['students', studentId, 'summary', periodId],
    queryFn: ({ signal }) =>
      apiRequest<StudentSummary>(`/students/${studentId}/summary${query}`, { signal }),
  })
}

export function useStudentRecommendations(studentId: number) {
  return useQuery({
    queryKey: ['students', studentId, 'recommendations'],
    queryFn: ({ signal }) =>
      apiRequest<Recommendation[]>(`/students/${studentId}/recommendations`, { signal }),
  })
}
