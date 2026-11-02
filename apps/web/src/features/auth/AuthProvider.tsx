import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { onSessionExpired, refreshSession } from '../../shared/api/client'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '../../shared/api/tokens'
import { fetchMe, loginRequest, logoutRequest } from './api'
import { AuthContext, type AuthContextValue } from './auth-context'
import type { User } from './types'

type AuthState =
  | { status: 'loading' }
  | { status: 'anonymous'; expired?: boolean }
  | { status: 'authenticated'; user: User }

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [state, setState] = useState<AuthState>({ status: 'loading' })

  useEffect(() => {
    let active = true

    async function restoreSession() {
      // With a stored access token there is no need to rotate on every reload:
      // if it already expired, the client refreshes it on the first 401.
      const hasSession =
        getAccessToken() !== null || (getRefreshToken() !== null && (await refreshSession()))
      if (!hasSession) {
        clearTokens()
        if (active) setState({ status: 'anonymous' })
        return
      }
      try {
        const user = await fetchMe()
        if (active) setState({ status: 'authenticated', user })
      } catch {
        clearTokens()
        // Keep the "expired" flag if the client already reported the expired session.
        if (active) {
          setState((current) =>
            current.status === 'anonymous' ? current : { status: 'anonymous', expired: true },
          )
        }
      }
    }

    void restoreSession()
    const unsubscribe = onSessionExpired(() => {
      queryClient.clear()
      setState({ status: 'anonymous', expired: true })
    })
    return () => {
      active = false
      unsubscribe()
    }
  }, [queryClient])

  const login = useCallback(async (email: string, password: string) => {
    setTokens(await loginRequest(email, password))
    const user = await fetchMe()
    setState({ status: 'authenticated', user })
    return user
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (refreshToken) {
      try {
        await logoutRequest(refreshToken)
      } catch {
        /* the session ends locally even if the server is unreachable */
      }
    }
    clearTokens()
    queryClient.clear()
    setState({ status: 'anonymous' })
  }, [queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({
      status: state.status,
      user: state.status === 'authenticated' ? state.user : null,
      sessionExpired: state.status === 'anonymous' && state.expired === true,
      login,
      logout,
    }),
    [state, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
