export type Role = 'DIRECTOR' | 'TEACHER' | 'PARENT' | 'ANALYST'

export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  institution_id: number
}
