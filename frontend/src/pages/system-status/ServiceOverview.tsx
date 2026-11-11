import { Database, Lock, MonitorSmartphone, Server, ShieldCheck } from 'lucide-react'
import { StatusCard } from '../../components/ui/StatusCard'
import type { ProbeState, SystemStatusSnapshot, UiStatus } from '../../types/system'
import { formatLatency } from '../../utils/format'

interface ServiceOverviewProps {
  snapshot: SystemStatusSnapshot | undefined
  isLoading: boolean
}

function resolveProbeStatus(
  isLoading: boolean,
  snapshot: SystemStatusSnapshot | undefined,
  state: ProbeState | undefined,
): UiStatus {
  if (isLoading) return 'checking'
  if (!snapshot || !state) return 'unknown'
  return state
}

function resolveCompositeServiceStatus(
  isLoading: boolean,
  snapshot: SystemStatusSnapshot | undefined,
): UiStatus {
  if (isLoading) return 'checking'
  if (!snapshot) return 'unknown'
  if (snapshot.health.state === 'offline') return 'offline'
  if (snapshot.database.state === 'offline' || snapshot.overview.state === 'offline') {
    return 'degraded'
  }
  return 'online'
}

export function ServiceOverview({
  snapshot,
  isLoading,
}: ServiceOverviewProps) {
  const apiStatus = resolveProbeStatus(isLoading, snapshot, snapshot?.health.state)
  const dbStatus = resolveProbeStatus(isLoading, snapshot, snapshot?.database.state)
  const overviewStatus = resolveProbeStatus(
    isLoading,
    snapshot,
    snapshot?.overview.state,
  )
  const vaultServiceStatus = resolveCompositeServiceStatus(isLoading, snapshot)

  return (
    <section aria-labelledby="service-probes-heading" className="space-y-3">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <h2
          id="service-probes-heading"
          className="text-sm font-semibold text-zinc-100"
        >
          Service Probes
        </h2>
        <p className="text-xs text-zinc-500">
          Statuses reflect live HTTP and PostgreSQL probe responses only.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <StatusCard
          icon={Server}
          eyebrow="Control Plane"
          title="Backend API"
          description="FastAPI HTTP process readiness endpoint (/health)."
          status={apiStatus}
          note={
            !isLoading && apiStatus === 'offline'
              ? (snapshot?.health.error ?? 'Backend API did not respond.')
              : null
          }
          metrics={[
            {
              label: 'Service ID',
              value: snapshot?.health.data?.service ?? 'Unknown',
            },
            {
              label: 'Round-trip',
              value:
                apiStatus === 'online'
                  ? formatLatency(snapshot?.health.latencyMs)
                  : 'Unavailable',
            },
          ]}
        />

        <StatusCard
          icon={Database}
          eyebrow="Persistence"
          title="PostgreSQL"
          description="Live database connection and SQL query health probe (/health/db)."
          status={dbStatus}
          note={
            !isLoading && dbStatus === 'offline'
              ? (snapshot?.database.error ?? 'PostgreSQL probe failed.')
              : null
          }
          metrics={[
            {
              label: 'Engine',
              value: snapshot?.database.data?.database ?? 'Unknown',
            },
            {
              label: 'Query Latency',
              value:
                dbStatus === 'online'
                  ? formatLatency(snapshot?.database.latencyMs)
                  : 'Unavailable',
            },
          ]}
        />

        <StatusCard
          icon={ShieldCheck}
          eyebrow="Identity & Lifecycle"
          title="Authentication & Device Service"
          description="Account slot tracking, QR challenge sessions, and audit chain summary (/api/v1/system/overview)."
          status={overviewStatus}
          note={
            !isLoading && overviewStatus === 'offline'
              ? (snapshot?.overview.error ?? 'Overview endpoint unavailable.')
              : null
          }
          metrics={[
            {
              label: 'Device Slot',
              value: snapshot?.overview.data
                ? `${snapshot.overview.data.registered_slots}/${snapshot.overview.data.max_slots} (${snapshot.overview.data.current_device_status})`
                : 'Unknown',
            },
            {
              label: 'Latency',
              value:
                overviewStatus === 'online'
                  ? formatLatency(snapshot?.overview.latencyMs)
                  : 'Unavailable',
            },
          ]}
        />

        <StatusCard
          icon={Lock}
          eyebrow="Cryptographic Storage"
          title="Asset & Steganography Service"
          description="Encrypted Asset Vault, Secure Notes, and LSB watermark pipeline availability."
          status={vaultServiceStatus}
          note={
            !isLoading && vaultServiceStatus === 'degraded'
              ? 'Database or overview telemetry reported degraded connectivity.'
              : null
          }
          metrics={[
            {
              label: 'Cipher Suite',
              value: 'AES-256-GCM / XChaCha20-Poly1305',
            },
            {
              label: 'Watermark Signature',
              value: 'ECDSA P-256 + SHA-256 LSB',
            },
          ]}
        />
      </div>

      <StatusCard
        icon={MonitorSmartphone}
        eyebrow="Web Client"
        title="Browser Console"
        description="React 19 + TypeScript single-page console running in the current browser session."
        status="online"
        metrics={[
          { label: 'Runtime', value: 'React 19 + Vite' },
          { label: 'Active Probe Route', value: '/system-status' },
        ]}
      />
    </section>
  )
}
