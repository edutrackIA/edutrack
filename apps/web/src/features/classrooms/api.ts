import { useQuery } from '@tanstack/react-query'
import type { User } from '../auth/types'
import { apiRequest } from '../../shared/api/client'
import type { RiskLevel } from '../../shared/lib/risk'

export interface Classroom {
  id: number
  year: number
  grade: number
  section: string
  tutor: User | null
  student_count: number
}

export interface ClassroomStudent {
  id: number
  code: string
  full_name: string
  classroom: string
  risk_level: RiskLevel | null
  probability: number | null
}

export function classroomLabel(classroom: Pick<Classroom, 'grade' | 'section'>): string {
  return `${classroom.grade}° ${classroom.section}`
}

export function useClassrooms() {
  return useQuery({
    queryKey: ['classrooms'],
    queryFn: ({ signal }) => apiRequest<Classroom[]>('/classrooms', { signal }),
  })
}

export function useClassroomStudents(classroomId: number | null, level: RiskLevel | null) {
  const query = level ? `?level=${level}` : ''
  return useQuery({
    queryKey: ['classrooms', classroomId, 'students', level],
    queryFn: ({ signal }) =>
      apiRequest<ClassroomStudent[]>(`/classrooms/${classroomId}/students${query}`, { signal }),
    enabled: classroomId !== null,
    placeholderData: (previous) => previous,
  })
}
