import { useQuery } from '@tanstack/react-query'

import { fetchSystemStatus } from '../services/systemStatus'

export function useSystemStatus() {
  return useQuery({
    queryKey: ['system-status'],
    queryFn: fetchSystemStatus,
    staleTime: 10_000,
    retry: 1,
    refetchOnWindowFocus: false,
  })
}
