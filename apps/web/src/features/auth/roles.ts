import type { Role } from './types'

export const ROLE_LABELS: Record<Role, string> = {
  DIRECTOR: 'Dirección',
  TEACHER: 'Docente',
  ANALYST: 'Análisis de datos',
  PARENT: 'Familia',
}

const ROLE_HOME: Record<Role, string> = {
  DIRECTOR: '/resumen',
  TEACHER: '/aulas',
  ANALYST: '/evaluaciones',
  PARENT: '/mi-hijo',
}

export function roleHome(role: Role): string {
  return ROLE_HOME[role]
}
