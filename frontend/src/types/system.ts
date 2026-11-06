export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface DatabaseHealthResponse {
  status: string
  database: string
  latency_ms: number
}

export interface SystemInfoResponse {
  name: string
  version: string
  environment: string
  api_version: string
  database_engine: string
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string
    message?: string
  }
}

export type ProbeState = 'online' | 'offline'
export type UiStatus = ProbeState | 'degraded' | 'checking'

export interface ServiceProbe<T> {
  state: ProbeState
  data: T | null
  latencyMs: number
  error: string | null
}

export interface SystemStatusSnapshot {
  health: ServiceProbe<HealthResponse>
  database: ServiceProbe<DatabaseHealthResponse>
  systemInfo: ServiceProbe<SystemInfoResponse>
  checkedAt: string
}
