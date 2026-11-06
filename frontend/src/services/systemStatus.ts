import type { AxiosResponse } from 'axios'

import type {
  DatabaseHealthResponse,
  HealthResponse,
  ServiceProbe,
  SystemInfoResponse,
  SystemStatusSnapshot,
} from '../types/system'
import { apiClient, getApiErrorMessage } from './api'

async function probe<T>(
  request: () => Promise<AxiosResponse<T>>,
): Promise<ServiceProbe<T>> {
  const startedAt = performance.now()

  try {
    const response = await request()
    return {
      state: 'online',
      data: response.data,
      latencyMs: Math.round((performance.now() - startedAt) * 100) / 100,
      error: null,
    }
  } catch (error) {
    return {
      state: 'offline',
      data: null,
      latencyMs: Math.round((performance.now() - startedAt) * 100) / 100,
      error: getApiErrorMessage(error),
    }
  }
}

export async function fetchSystemStatus(): Promise<SystemStatusSnapshot> {
  const [health, database, systemInfo] = await Promise.all([
    probe<HealthResponse>(() => apiClient.get('/health')),
    probe<DatabaseHealthResponse>(() => apiClient.get('/health/database')),
    probe<SystemInfoResponse>(() => apiClient.get('/system/info')),
  ])

  return {
    health,
    database,
    systemInfo,
    checkedAt: new Date().toISOString(),
  }
}
