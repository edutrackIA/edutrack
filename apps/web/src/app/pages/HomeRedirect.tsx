import { Navigate } from 'react-router-dom'
import { useAuth } from '../../features/auth/auth-context'
import { roleHome } from '../../features/auth/roles'

export function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? roleHome(user.role) : '/login'} replace />
}
