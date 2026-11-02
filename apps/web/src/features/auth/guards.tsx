import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { EmptyState, FullPageLoader } from '../../shared/ui/Feedback'
import { useAuth } from './auth-context'
import type { Role } from './types'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageLoader />
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}

export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth()

  if (!user || !roles.includes(user.role)) {
    return (
      <EmptyState
        title="No tienes acceso a esta sección"
        description="Si crees que deberías verla, pide a la dirección de tu colegio que revise tu rol."
      />
    )
  }
  return <>{children}</>
}
