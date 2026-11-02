import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export interface Guardian {
  id: number
  full_name: string
  email: string
  kinship: string
  has_access: boolean
  invitation_sent: boolean | null
}

export interface GuardianInput {
  full_name: string
  email: string
  kinship: string
}

const key = (studentId: number) => ['students', studentId, 'guardians']

export function useGuardians(studentId: number, enabled: boolean) {
  return useQuery({
    queryKey: key(studentId),
    queryFn: ({ signal }) => apiRequest<Guardian[]>(`/students/${studentId}/guardians`, { signal }),
    enabled,
  })
}

function useGuardianMutation<TVariables, TResult>(
  studentId: number,
  request: (variables: TVariables) => Promise<TResult>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    // The record header also lists guardians, so the whole student is refreshed.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students', studentId] }),
  })
}

export function useAddGuardian(studentId: number) {
  return useGuardianMutation(studentId, (body: GuardianInput) =>
    apiRequest<Guardian>(`/students/${studentId}/guardians`, { method: 'POST', body }),
  )
}

export function useResendInvitation(studentId: number) {
  return useGuardianMutation(studentId, (guardianId: number) =>
    apiRequest<Guardian>(`/students/${studentId}/guardians/${guardianId}/invitation`, {
      method: 'POST',
    }),
  )
}

export function useUnlinkGuardian(studentId: number) {
  return useGuardianMutation(studentId, (guardianId: number) =>
    apiRequest<void>(`/students/${studentId}/guardians/${guardianId}`, { method: 'DELETE' }),
  )
}
