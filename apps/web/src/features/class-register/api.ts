import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export type AttendanceStatus = 'PRESENT' | 'ABSENT' | 'LATE' | 'JUSTIFIED'

export interface TeachingCourse {
  classroom_id: number
  classroom: string
  year: number
  subject_id: number
  subject: string
}

export interface TeachingClassroom {
  classroom_id: number
  classroom: string
  year: number
  is_tutor: boolean
}

interface RegisterStudent {
  student_id: number
  code: string
  full_name: string
}

export interface Gradebook {
  classroom_id: number
  subject_id: number
  period_id: number
  rows: (RegisterStudent & { score: number | null })[]
}

export interface AttendanceSheet {
  classroom_id: number
  date: string
  period_id: number | null
  rows: (RegisterStudent & { status: AttendanceStatus | null })[]
}

export interface BehaviorSheet {
  classroom_id: number
  period_id: number
  rows: (RegisterStudent & { rating: number | null; notes: string | null })[]
}

export function useMyTeaching() {
  return useQuery({
    queryKey: ['me', 'teaching'],
    queryFn: ({ signal }) =>
      apiRequest<{ courses: TeachingCourse[]; classrooms: TeachingClassroom[] }>('/me/teaching', {
        signal,
      }),
  })
}

export interface GradebookKey {
  classroomId: number
  subjectId: number
  periodId: number
}

export function useGradebook(key: GradebookKey | null) {
  return useQuery({
    queryKey: ['gradebook', key],
    queryFn: ({ signal }) =>
      apiRequest<Gradebook>(
        `/gradebook?classroom_id=${key!.classroomId}&subject_id=${key!.subjectId}&period_id=${key!.periodId}`,
        { signal },
      ),
    enabled: key !== null,
  })
}

/** Saving a sheet returns it updated; it becomes the cached version right away. */
function useSaveSheet<TBody, TSheet>(
  request: (body: TBody) => Promise<TSheet>,
  cacheKey: (sheet: TSheet) => unknown[],
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: (sheet) => {
      queryClient.setQueryData(cacheKey(sheet), sheet)
      // Grades, attendance and conduct feed summaries and risk elsewhere.
      void queryClient.invalidateQueries({ queryKey: ['students'] })
    },
  })
}

export function useSaveGrades() {
  return useSaveSheet(
    (body: {
      classroom_id: number
      subject_id: number
      period_id: number
      scores: { student_id: number; score: number | null }[]
    }) => apiRequest<Gradebook>('/gradebook', { method: 'PUT', body }),
    (sheet) => [
      'gradebook',
      { classroomId: sheet.classroom_id, subjectId: sheet.subject_id, periodId: sheet.period_id },
    ],
  )
}

export function useAttendanceSheet(classroomId: number | null, day: string) {
  return useQuery({
    queryKey: ['attendance', classroomId, day],
    queryFn: ({ signal }) =>
      apiRequest<AttendanceSheet>(`/classrooms/${classroomId}/attendance?date=${day}`, { signal }),
    enabled: classroomId !== null && day !== '',
  })
}

export function useSaveAttendance(classroomId: number) {
  return useSaveSheet(
    (body: { date: string; records: { student_id: number; status: AttendanceStatus }[] }) =>
      apiRequest<AttendanceSheet>(`/classrooms/${classroomId}/attendance`, {
        method: 'PUT',
        body,
      }),
    (sheet) => ['attendance', sheet.classroom_id, sheet.date],
  )
}

export function useBehaviorSheet(classroomId: number | null, periodId: number | null) {
  return useQuery({
    queryKey: ['behavior', classroomId, periodId],
    queryFn: ({ signal }) =>
      apiRequest<BehaviorSheet>(`/classrooms/${classroomId}/behavior?period_id=${periodId}`, {
        signal,
      }),
    enabled: classroomId !== null && periodId !== null,
  })
}

export function useSaveBehavior(classroomId: number) {
  return useSaveSheet(
    (body: {
      period_id: number
      ratings: { student_id: number; rating: number | null; notes: string | null }[]
    }) =>
      apiRequest<BehaviorSheet>(`/classrooms/${classroomId}/behavior`, { method: 'PUT', body }),
    (sheet) => ['behavior', sheet.classroom_id, sheet.period_id],
  )
}

/** Local date as YYYY-MM-DD (not UTC, which would be tomorrow in the evening in Peru). */
export function todayValue(): string {
  const now = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** The period that contains a date, or the latest one when none does. */
export function periodFor<T extends { id: number; start_date: string; end_date: string }>(
  periods: T[] | undefined,
  day: string,
): T | undefined {
  return (
    periods?.find((period) => period.start_date <= day && day <= period.end_date) ??
    periods?.[periods.length - 1]
  )
}
