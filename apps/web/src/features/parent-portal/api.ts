import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { ClassroomStudent } from '../classrooms/api'
import type { FamilySurvey } from '../students/types'

export type FamilyMood = 'GOOD' | 'OK' | 'WORRIED'
export type HomeChange =
  | 'MOVING'
  | 'HEALTH'
  | 'PARENTS_WORK'
  | 'CARING_FAMILY'
  | 'ECONOMIC'
  | 'OTHER'

export interface FamilyCheckin {
  id: number
  student: ClassroomStudent
  month: string
  mood: FamilyMood
  mood_label: string
  home_changes: HomeChange[]
  home_change_labels: string[]
  peer_concern: boolean
  comment: string | null
  submitted_at: string
  reviewed_at: string | null
}

export interface FamilyCheckinInput {
  mood: FamilyMood
  home_changes: HomeChange[]
  peer_concern: boolean
  comment: string | null
}

export type SurveyInput = Omit<FamilySurvey, 'id' | 'submitted_at'>

export function useChildren() {
  return useQuery({
    queryKey: ['me', 'children'],
    queryFn: ({ signal }) => apiRequest<ClassroomStudent[]>('/me/children', { signal }),
  })
}

export function useCurrentCheckin(studentId: number) {
  return useQuery({
    queryKey: ['family-checkins', studentId],
    queryFn: ({ signal }) =>
      apiRequest<{ month: string; checkin: FamilyCheckin | null }>(
        `/students/${studentId}/family-checkins/current`,
        { signal },
      ),
  })
}

export function useSubmitCheckin(studentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: FamilyCheckinInput) =>
      apiRequest<FamilyCheckin>(`/students/${studentId}/family-checkins/current`, {
        method: 'PUT',
        body,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-checkins', studentId] }),
  })
}

export function useSubmitSurvey(studentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SurveyInput) =>
      apiRequest<FamilySurvey>(`/students/${studentId}/surveys`, { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students', studentId] }),
  })
}

export function usePendingFamilyReports() {
  return useQuery({
    queryKey: ['family-checkins', 'pending'],
    queryFn: ({ signal }) => apiRequest<FamilyCheckin[]>('/family-checkins/pending', { signal }),
  })
}

export function useReviewFamilyReport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiRequest<FamilyCheckin>(`/family-checkins/${id}/review`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-checkins'] }),
  })
}

/** "Flores Ruiz, Lucía" → "Lucía". */
export function firstName(fullName: string): string {
  return fullName.split(',')[1]?.trim() || fullName
}
