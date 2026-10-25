import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type {
  Commitment,
  FamilySurvey,
  Grade,
  Recommendation,
  RiskAssessment,
  StudentDetail,
  StudentSummary,
} from './types'

function useStudentResource<T>(studentId: number, resource: string) {
  return useQuery({
    queryKey: ['students', studentId, resource],
    queryFn: ({ signal }) => apiRequest<T>(`/students/${studentId}/${resource}`, { signal }),
  })
}

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
  return useStudentResource<Recommendation[]>(studentId, 'recommendations')
}

export function useStudentGrades(studentId: number) {
  return useStudentResource<Grade[]>(studentId, 'grades')
}

export function useStudentRiskHistory(studentId: number) {
  return useStudentResource<RiskAssessment[]>(studentId, 'risk')
}

export function useStudentCommitments(studentId: number) {
  return useStudentResource<Commitment[]>(studentId, 'commitments')
}

export function useStudentSurveys(studentId: number) {
  return useStudentResource<FamilySurvey[]>(studentId, 'surveys')
}
