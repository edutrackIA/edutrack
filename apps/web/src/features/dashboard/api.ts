import { useQuery } from '@tanstack/react-query'
import { apiFetch, apiRequest } from '../../shared/api/client'
import { filenameFrom, saveBlob } from '../../shared/lib/download'
import type { DashboardSummary } from './types'

function withPeriod(path: string, periodId: number | null): string {
  return periodId === null ? path : `${path}?period_id=${periodId}`
}

export function useDashboardSummary(periodId: number | null) {
  return useQuery({
    queryKey: ['dashboard', 'summary', periodId],
    queryFn: ({ signal }) =>
      apiRequest<DashboardSummary>(withPeriod('/dashboard/summary', periodId), { signal }),
    // Keep showing the previous period while the new one loads.
    placeholderData: (previous) => previous,
  })
}

export async function downloadRiskReport(periodId: number | null): Promise<void> {
  const response = await apiFetch(withPeriod('/reports/risk', periodId))
  const filename = filenameFrom(response.headers.get('content-disposition'), 'reporte-riesgo.pdf')
  saveBlob(await response.blob(), filename)
}
