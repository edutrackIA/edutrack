import type { Role } from '../features/auth/types'

export interface NavItem {
  to: string
  label: string
}

export const NAV_ITEMS: Record<Role, NavItem[]> = {
  DIRECTOR: [
    { to: '/resumen', label: 'Resumen' },
    { to: '/aulas', label: 'Aulas' },
    { to: '/recomendaciones', label: 'Recomendaciones' },
    { to: '/modelo', label: 'Modelo' },
    { to: '/solicitudes-de-datos', label: 'Solicitudes de datos' },
    { to: '/configuracion', label: 'Configuración' },
  ],
  TEACHER: [
    { to: '/registro', label: 'Registro' },
    { to: '/aulas', label: 'Mis aulas' },
    { to: '/alertas', label: 'Alertas' },
    { to: '/recomendaciones', label: 'Recomendaciones' },
    { to: '/seguimiento', label: 'Seguimiento semanal' },
  ],
  ANALYST: [
    { to: '/evaluaciones', label: 'Evaluaciones' },
    { to: '/carga-de-datos', label: 'Carga de datos' },
    { to: '/umbrales', label: 'Umbrales de riesgo' },
    { to: '/modelo', label: 'Modelo' },
    { to: '/aulas', label: 'Aulas' },
  ],
  PARENT: [{ to: '/mi-hijo', label: 'Mi hijo' }],
}
