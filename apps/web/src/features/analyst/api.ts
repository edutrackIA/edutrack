import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiRequest } from '../../shared/api/client'
import { filenameFrom, saveBlob } from '../../shared/lib/download'
import type { RiskLevel } from '../../shared/lib/risk'

export type ImportKind = 'STUDENTS' | 'GRADES' | 'ATTENDANCE'

export interface ImportJob {
  /** Null for a preview, which is not stored. */
  id: number | null
  kind: ImportKind
  filename: string
  status: 'PENDING' | 'DONE' | 'FAILED'
  rows_ok: number
  rows_failed: number
  errors: { row: number | null; column: string | null; message: string }[]
  created_at: string | null
  preview: boolean
}

export interface AssessmentRun {
  evaluated: number
  skipped: number
  model_version: string | null
  by_level: Record<RiskLevel, number>
  skipped_students: { student_id: number; code: string; full_name: string; reason: string }[]
}

export interface Thresholds {
  medium_from: number
  high_from: number
}

export function useImportFile() {
  return useMutation({
    mutationFn: ({
      kind,
      file,
      periodId,
      preview,
    }: {
      kind: ImportKind
      file: File
      periodId?: number
      /** Validate only: the server checks every row and saves nothing. */
      preview: boolean
    }) => {
      const form = new FormData()
      form.append('kind', kind)
      form.append('file', file)
      if (periodId !== undefined) form.append('period_id', String(periodId))
      if (preview) form.append('dry_run', 'true')
      return apiRequest<ImportJob>('/imports', { method: 'POST', body: form })
    },
  })
}

export async function downloadTemplate(kind: ImportKind): Promise<void> {
  const response = await apiFetch(`/imports/templates/${kind}`)
  const fallback = `${kind.toLowerCase()}.csv`
  saveBlob(await response.blob(), filenameFrom(response.headers.get('content-disposition'), fallback))
}

/** Runs the model for a period; everything derived from risk must be reloaded. */
export function useRunAssessment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (periodId: number) =>
      apiRequest<AssessmentRun>('/risk-assessments/run', {
        method: 'POST',
        body: { period_id: periodId },
      }),
    onSuccess: () => queryClient.invalidateQueries(),
  })
}

export function useThresholds() {
  return useQuery({
    queryKey: ['settings', 'risk-thresholds'],
    queryFn: ({ signal }) => apiRequest<Thresholds>('/settings/risk-thresholds', { signal }),
  })
}

export function useUpdateThresholds() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: Thresholds) =>
      apiRequest<Thresholds>('/settings/risk-thresholds', { method: 'PUT', body }),
    onSuccess: (data) => queryClient.setQueryData(['settings', 'risk-thresholds'], data),
  })
}
