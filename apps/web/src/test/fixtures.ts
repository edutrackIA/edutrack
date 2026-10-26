import type { User } from '../features/auth/types'

export const TEACHER_USER: User = {
  id: 2,
  email: 'docente@edutrack.dev',
  full_name: 'Luis Quispe',
  role: 'TEACHER',
  institution_id: 1,
}

export const DIRECTOR_USER: User = {
  id: 1,
  email: 'director@edutrack.dev',
  full_name: 'Carmen Rojas',
  role: 'DIRECTOR',
  institution_id: 1,
}

export const ANALYST_USER: User = {
  id: 5,
  email: 'analista@edutrack.dev',
  full_name: 'Ana Torres',
  role: 'ANALYST',
  institution_id: 1,
}
