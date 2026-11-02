import { createContext, useContext } from 'react'
import type { User } from './types'

export interface AuthContextValue {
  status: 'loading' | 'anonymous' | 'authenticated'
  user: User | null
  /** True when the session ended on its own (expired), not by logging out. */
  sessionExpired: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (value === null) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
