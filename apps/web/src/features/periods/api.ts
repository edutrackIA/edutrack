import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '../../shared/api/client'

export interface Period {
  id: number
  year: number
  bimester: number
  start_date: string
  end_date: string
  label: string
}

export function usePeriods() {
  return useQuery({
    queryKey: ['periods'],
    queryFn: ({ signal }) => apiRequest<Period[]>('/periods', { signal }),
    staleTime: 10 * 60_000,
  })
}
