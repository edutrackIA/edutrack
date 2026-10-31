import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch, apiRequest } from '../../shared/api/client'
import { filenameFrom, saveBlob } from '../../shared/lib/download'
import type { RiskLevel } from '../../shared/lib/risk'
import type { ExitReason } from '../students/types'

export interface PerformanceMetrics {
  true_positives: number
  false_negatives: number
  false_positives: number
  true_negatives: number
  recall: number | null
  precision: number | null
}

export interface DropoutCase {
  student_id: number
  code: string
  full_name: string
  exit_date: string | null
  exit_reason: ExitReason | null
  last_level: RiskLevel
  last_probability: number
  alerted: boolean
}

export interface ModelPerformance {
  window_days: number
  model_versions: string[]
  labeled: number
  dropouts: number
  pending: number
  min_labeled: number
  min_dropouts: number
  metrics: PerformanceMetrics | null
  cases: DropoutCase[]
}

export function useModelPerformance() {
  return useQuery({
    queryKey: ['model-performance'],
    queryFn: ({ signal }) => apiRequest<ModelPerformance>('/model-performance', { signal }),
  })
}

export async function downloadDataset(): Promise<void> {
  const response = await apiFetch('/model-performance/dataset.csv')
  const name = filenameFrom(
    response.headers.get('content-disposition'),
    'edutrack-dataset-anonimizado.csv',
  )
  saveBlob(await response.blob(), name)
}


export interface HoldoutScore {
  cases: number
  dropouts?: number
  recall: number
  precision?: number
  f1?: number
  roc_auc?: number | null
}

export interface ModelVersion {
  version: string
  trained_at: string | null
  active: boolean
  synthetic_samples: number | null
  school_samples: number | null
  school_dropouts: number | null
  school_holdout: HoldoutScore | null
  trained_by: string | null
  activated_by: string | null
  activated_at: string | null
}

export interface ModelsOverview {
  versions: ModelVersion[]
  training: {
    labeled: number
    dropouts: number
    min_labeled: number
    min_dropouts: number
    can_train: boolean
  }
}

export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: ({ signal }) => apiRequest<ModelsOverview>('/models', { signal }),
  })
}

export function useTrainModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiRequest<{ candidate: ModelVersion; active_on_holdout: HoldoutScore | null }>(
        '/models/train',
        { method: 'POST' },
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  })
}

export function useActivateModel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (version: string) =>
      apiRequest<ModelVersion>(`/models/${encodeURIComponent(version)}/activation`, {
        method: 'POST',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  })
}
