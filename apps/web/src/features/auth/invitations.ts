import { useMutation, useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export interface InvitationInfo {
  full_name: string
  email: string
}

export function useInvitation(token: string) {
  return useQuery({
    queryKey: ['invitations', token],
    queryFn: ({ signal }) =>
      apiRequest<InvitationInfo>(`/invitations/${encodeURIComponent(token)}`, { signal }),
    retry: false,
  })
}

export function useAcceptInvitation(token: string) {
  return useMutation({
    mutationFn: (password: string) =>
      apiRequest<void>(`/invitations/${encodeURIComponent(token)}/accept`, {
        method: 'POST',
        body: { password },
      }),
  })
}

/** Same rules as the server, checked live so people see what is missing while typing. */
export function passwordChecks(password: string, confirmation: string) {
  return [
    { label: 'Al menos 8 caracteres', ok: password.length >= 8 },
    { label: 'Al menos una letra', ok: /\p{L}/u.test(password) },
    { label: 'Al menos un número', ok: /\d/.test(password) },
    { label: 'Ambas contraseñas coinciden', ok: password.length > 0 && password === confirmation },
  ]
}

export function isValidNewPassword(password: string, confirmation: string): boolean {
  return passwordChecks(password, confirmation).every((check) => check.ok)
}
