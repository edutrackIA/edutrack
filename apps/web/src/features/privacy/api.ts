import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiRequest } from '../../shared/api/client'
import { filenameFrom, saveBlob } from '../../shared/lib/download'

export type DataRequestKind = 'ACCESS' | 'RECTIFICATION' | 'CANCELLATION' | 'OPPOSITION'
export type DataRequestStatus = 'PENDING' | 'RESOLVED' | 'REJECTED'

export const KIND_LABELS: Record<DataRequestKind, { label: string; help: string }> = {
  ACCESS: { label: 'Acceso', help: 'Recibir una copia de los datos que el colegio guarda.' },
  RECTIFICATION: { label: 'Rectificación', help: 'Corregir un dato inexacto o incompleto.' },
  CANCELLATION: {
    label: 'Cancelación',
    help: 'Pedir que se eliminen datos que ya no sean necesarios.',
  },
  OPPOSITION: { label: 'Oposición', help: 'Oponerse a un uso concreto de los datos.' },
}

export const STATUS_LABELS: Record<DataRequestStatus, string> = {
  PENDING: 'Pendiente',
  RESOLVED: 'Atendida',
  REJECTED: 'Rechazada',
}

export interface DataRequest {
  id: number
  student_id: number
  student_name: string
  requester_name: string
  kind: DataRequestKind
  details: string
  status: DataRequestStatus
  response: string | null
  created_at: string
  due_date: string
  resolved_at: string | null
}

export function usePrivacyStatus(enabled: boolean) {
  return useQuery({
    queryKey: ['privacy'],
    queryFn: ({ signal }) =>
      apiRequest<{ version: string; accepted_at: string | null }>('/me/privacy', { signal }),
    enabled,
    staleTime: Infinity,
  })
}

export function useAcceptPrivacy() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (version: string) =>
      apiRequest<{ version: string; accepted_at: string }>('/me/privacy/acceptance', {
        method: 'POST',
        body: { version },
      }),
    onSuccess: (status) => queryClient.setQueryData(['privacy'], status),
  })
}

export function useDataRequests() {
  return useQuery({
    queryKey: ['data-requests'],
    queryFn: ({ signal }) => apiRequest<DataRequest[]>('/data-requests', { signal }),
  })
}

export function useCreateDataRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { student_id: number; kind: DataRequestKind; details: string }) =>
      apiRequest<DataRequest>('/data-requests', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['data-requests'] }),
  })
}

export function useResolveDataRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...body
    }: {
      id: number
      status: Exclude<DataRequestStatus, 'PENDING'>
      response: string
    }) => apiRequest<DataRequest>(`/data-requests/${id}/resolution`, { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['data-requests'] }),
  })
}

export async function downloadStudentExport(studentId: number): Promise<void> {
  const response = await apiFetch(`/students/${studentId}/data-export`)
  const name = filenameFrom(response.headers.get('content-disposition'), 'expediente.json')
  saveBlob(await response.blob(), name)
}
