import { useMutation, useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export function useForgotPassword() {
  return useMutation({
    mutationFn: (email: string) =>
      apiRequest<void>('/auth/password/forgot', { method: 'POST', body: { email } }),
  })
}

export function useResetTarget(token: string) {
  return useQuery({
    queryKey: ['password-reset', token],
    queryFn: ({ signal }) =>
      apiRequest<{ email: string }>(`/auth/password/reset/${encodeURIComponent(token)}`, {
        signal,
      }),
    retry: false,
  })
}

export function useResetPassword(token: string) {
  return useMutation({
    mutationFn: (password: string) =>
      apiRequest<void>(`/auth/password/reset/${encodeURIComponent(token)}`, {
        method: 'POST',
        body: { password },
      }),
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      apiRequest<void>('/auth/password/change', { method: 'POST', body }),
  })
}
