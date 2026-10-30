import { useMutation, useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'
import type { Classroom } from '../classrooms/api'
import type { Period } from '../periods/api'

export type StaffRole = 'DIRECTOR' | 'TEACHER' | 'ANALYST'

export const STAFF_ROLE_LABELS: Record<StaffRole, string> = {
  DIRECTOR: 'Dirección',
  TEACHER: 'Docente',
  ANALYST: 'Análisis de datos',
}

export interface Subject {
  id: number
  name: string
}

export interface StaffMember {
  id: number
  full_name: string
  email: string
  role: StaffRole
  is_active: boolean
  has_access: boolean
  invitation_sent: boolean | null
}

export interface Assignment {
  id: number
  classroom_id: number
  classroom: string
  subject_id: number
  subject: string
  teacher_id: number
  teacher: string
}

/** Mutation that refreshes the given lists when it succeeds. */
function useSetupMutation<TVariables, TResult>(
  request: (variables: TVariables) => Promise<TResult>,
  ...keys: QueryKey[]
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: () =>
      Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey }))),
  })
}

// --- Bimestres ---------------------------------------------------------------------

export function useCreatePeriod() {
  return useSetupMutation(
    (body: { year: number; bimester: number; start_date: string; end_date: string }) =>
      apiRequest<Period>('/periods', { method: 'POST', body }),
    ['periods'],
  )
}

export function useUpdatePeriod() {
  return useSetupMutation(
    ({ id, ...body }: { id: number; start_date: string; end_date: string }) =>
      apiRequest<Period>(`/periods/${id}`, { method: 'PATCH', body }),
    ['periods'],
  )
}

// --- Cursos ------------------------------------------------------------------------

export function useSubjects() {
  return useQuery({
    queryKey: ['subjects'],
    queryFn: ({ signal }) => apiRequest<Subject[]>('/subjects', { signal }),
  })
}

export function useCreateSubject() {
  return useSetupMutation(
    (name: string) => apiRequest<Subject>('/subjects', { method: 'POST', body: { name } }),
    ['subjects'],
  )
}

export function useRenameSubject() {
  return useSetupMutation(
    ({ id, name }: { id: number; name: string }) =>
      apiRequest<Subject>(`/subjects/${id}`, { method: 'PATCH', body: { name } }),
    ['subjects'],
    ['course-assignments'],
  )
}

// --- Aulas -------------------------------------------------------------------------

export function useCreateClassroom() {
  return useSetupMutation(
    (body: { year: number; grade: number; section: string }) =>
      apiRequest<Classroom>('/classrooms', { method: 'POST', body }),
    ['classrooms'],
  )
}

export function useSetTutor() {
  return useSetupMutation(
    ({ id, tutor_id }: { id: number; tutor_id: number | null }) =>
      apiRequest<Classroom>(`/classrooms/${id}`, { method: 'PATCH', body: { tutor_id } }),
    ['classrooms'],
  )
}

// --- Personal ------------------------------------------------------------------------

export function useStaff() {
  return useQuery({
    queryKey: ['staff'],
    queryFn: ({ signal }) => apiRequest<StaffMember[]>('/staff', { signal }),
  })
}

export function useInviteStaff() {
  return useSetupMutation(
    (body: { full_name: string; email: string; role: StaffRole }) =>
      apiRequest<StaffMember>('/staff', { method: 'POST', body }),
    ['staff'],
  )
}

export function useResendStaffInvitation() {
  return useSetupMutation(
    (id: number) => apiRequest<StaffMember>(`/staff/${id}/invitation`, { method: 'POST' }),
    ['staff'],
  )
}

export function useSetStaffActive() {
  return useSetupMutation(
    ({ id, is_active }: { id: number; is_active: boolean }) =>
      apiRequest<StaffMember>(`/staff/${id}`, { method: 'PATCH', body: { is_active } }),
    ['staff'],
    ['classrooms'],
  )
}

// --- Asignaciones --------------------------------------------------------------------

export function useAssignments(classroomId: number | null) {
  return useQuery({
    queryKey: ['course-assignments', classroomId],
    queryFn: ({ signal }) =>
      apiRequest<Assignment[]>(`/course-assignments?classroom_id=${classroomId}`, { signal }),
    enabled: classroomId !== null,
  })
}

export function useAssignCourse() {
  return useSetupMutation(
    (body: { classroom_id: number; subject_id: number; teacher_id: number }) =>
      apiRequest<Assignment>('/course-assignments', { method: 'POST', body }),
    ['course-assignments'],
  )
}

export function useUnassignCourse() {
  return useSetupMutation(
    (id: number) => apiRequest<void>(`/course-assignments/${id}`, { method: 'DELETE' }),
    ['course-assignments'],
  )
}
