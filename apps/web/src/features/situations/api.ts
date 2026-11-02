import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export type SituationGroup = 'MESSAGE' | 'TEAM'

export interface SituationKindInfo {
  kind: string
  label: string
  group: SituationGroup
  description: string
}

export interface Situation {
  id: number
  student_id: number
  kind: string
  label: string
  group: SituationGroup
  note: string | null
  started_on: string
  resolved_on: string | null
  created_at: string
}

export interface Checkin {
  classroom_id: number
  week_start: string
  deadline: string
  editable: boolean
  completed: boolean
  completed_at: string | null
}

export function useSituationCatalog() {
  return useQuery({
    queryKey: ['situations', 'catalog'],
    queryFn: ({ signal }) => apiRequest<SituationKindInfo[]>('/situations/catalog', { signal }),
    staleTime: Infinity,
  })
}

export function useClassroomSituations(classroomId: number) {
  return useQuery({
    queryKey: ['situations', 'classroom', classroomId],
    queryFn: ({ signal }) =>
      apiRequest<Situation[]>(`/classrooms/${classroomId}/situations`, { signal }),
  })
}

export function useStudentSituations(studentId: number) {
  return useQuery({
    queryKey: ['situations', 'student', studentId],
    queryFn: ({ signal }) =>
      apiRequest<Situation[]>(`/students/${studentId}/situations`, { signal }),
  })
}

export function useCheckin(classroomId: number) {
  return useQuery({
    queryKey: ['checkins', classroomId],
    queryFn: ({ signal }) =>
      apiRequest<Checkin>(`/classrooms/${classroomId}/checkins/current`, { signal }),
  })
}

export function useCompleteCheckin(classroomId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiRequest<Checkin>(`/classrooms/${classroomId}/checkins/current/complete`, {
        method: 'POST',
      }),
    onSuccess: (checkin) => queryClient.setQueryData(['checkins', classroomId], checkin),
  })
}

function useSituationMutation<TVariables>(request: (variables: TVariables) => Promise<Situation>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['situations'] }),
  })
}

export interface NewSituation {
  studentId: number
  kind: string
  note: string
  startedOn: string
}

export function useCreateSituation() {
  return useSituationMutation(({ studentId, kind, note, startedOn }: NewSituation) =>
    apiRequest<Situation>(`/students/${studentId}/situations`, {
      method: 'POST',
      body: { kind, note: note || null, started_on: startedOn || null },
    }),
  )
}

export function useUpdateSituation() {
  return useSituationMutation(
    ({ id, ...changes }: { id: number; note?: string; resolved?: boolean }) =>
      apiRequest<Situation>(`/situations/${id}`, { method: 'PATCH', body: changes }),
  )
}
