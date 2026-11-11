import type { AxiosResponse } from 'axios'

import type {
  DatabaseHealthResponse,
  HealthResponse,
  ServiceProbe,
  SystemInfoResponse,
  SystemOverviewResponse,
  SystemStatusSnapshot,
} from '../types/system'
import { getStoredSessionToken } from '../utils/session'
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

export async function fetchSystemOverview(): Promise<SystemOverviewResponse> {
  try {
    const token = getStoredSessionToken()
    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    const response = await apiClient.get<SystemOverviewResponse>('/system/overview', {
      headers,
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function fetchSystemStatus(): Promise<SystemStatusSnapshot> {
  const token = getStoredSessionToken()
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}

  const [health, database, systemInfo, overview] = await Promise.all([
    probe<HealthResponse>(() => apiClient.get('/health')),
    probe<DatabaseHealthResponse>(() => apiClient.get('/health/database')),
    probe<SystemInfoResponse>(() => apiClient.get('/system/info')),
    probe<SystemOverviewResponse>(() => apiClient.get('/system/overview', { headers })),
  ])

  return {
    health,
    database,
    systemInfo,
    overview,
    checkedAt: new Date().toISOString(),
  }
}
