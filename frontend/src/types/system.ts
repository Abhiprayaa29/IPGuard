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

export interface AuditEventSummary {
  event_id: string
  chain_id: string
  sequence: number
  occurred_at: string
  actor_type: string
  event_type: string
  resource_type: string
  resource_id: string | null
  result: string
  event_hash: string
}

export interface SystemOverviewResponse {
  account_id: string
  authenticated: boolean
  environment: string
  api_status: string
  database_status: string
  database_latency_ms: number | null
  registered_slots: number
  max_slots: number
  current_device_id: string | null
  current_device_name: string | null
  current_device_status: 'ACTIVE' | 'REVOKED' | 'UNREGISTERED' | string
  notes_count: number | null
  assets_count: number | null
  verified_assets_count: number | null
  warnings: string[]
  recent_events: AuditEventSummary[]
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string
    message?: string
  }
}

export type ProbeState = 'online' | 'offline'
export type UiStatus = ProbeState | 'degraded' | 'checking' | 'unknown'

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
  overview: ServiceProbe<SystemOverviewResponse>
  checkedAt: string
}
