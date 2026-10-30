import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export interface Period {
  id: number
  year: number
  bimester: number
  start_date: string
  end_date: string
  label: string
  has_grades: boolean
}

/** Most recent period with grades: the one that can be evaluated or reviewed. */
export function latestWithGrades(periods: Period[] | undefined): Period | undefined {
  const withGrades = periods?.filter((period) => period.has_grades) ?? []
  return withGrades[withGrades.length - 1] ?? periods?.[periods.length - 1]
}

export function periodOptionLabel(period: Period): string {
  return period.has_grades ? period.label : `${period.label} (sin notas)`
}

export function usePeriods() {
  return useQuery({
    queryKey: ['periods'],
    queryFn: ({ signal }) => apiRequest<Period[]>('/periods', { signal }),
    staleTime: 10 * 60_000,
  })
}
