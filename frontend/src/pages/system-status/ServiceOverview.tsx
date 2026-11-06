import { Database, MonitorSmartphone, Server } from 'lucide-react'

import { StatusCard } from '../../components/ui/StatusCard'
import type { SystemStatusSnapshot, UiStatus } from '../../types/system'
import { formatLatency } from '../../utils/format'

interface ServiceOverviewProps {
  snapshot: SystemStatusSnapshot | undefined
  isLoading: boolean
}

function resolveStatus(
  isLoading: boolean,
  state: 'online' | 'offline' | undefined,
): UiStatus {
  if (isLoading) {
    return 'checking'
  }

  return state ?? 'offline'
}

export function ServiceOverview({
  snapshot,
  isLoading,
}: ServiceOverviewProps) {
  const backendStatus = resolveStatus(isLoading, snapshot?.health.state)
  const databaseStatus = resolveStatus(isLoading, snapshot?.database.state)

  return (
    <section aria-labelledby="service-probes-heading">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-ip-gold-400/80">
            Service probes
          </p>
          <h2
            id="service-probes-heading"
            className="mt-2 font-display text-2xl font-semibold tracking-[-0.02em] text-white"
          >
            Core readiness layers
          </h2>
        </div>
        <p className="max-w-md text-xs leading-5 text-slate-500 sm:text-right">
          Each layer is checked independently so a database issue cannot hide a
          healthy API or client application.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatusCard
          icon={MonitorSmartphone}
          eyebrow="Client layer"
          title="Frontend"
          description="The React application is loaded, routed, and able to reach its local API configuration."
          status="online"
          metrics={[
            { label: 'Runtime', value: 'React + Vite' },
            { label: 'Route', value: '/system-status' },
          ]}
          style={{ animationDelay: '80ms' }}
        />
        <StatusCard
          icon={Server}
          eyebrow="Control layer"
          title="Backend API"
          description="FastAPI health metadata confirms that the API process is available on the configured endpoint."
          status={backendStatus}
          note={
            !isLoading && backendStatus === 'offline'
              ? (snapshot?.health.error ?? 'The API did not respond.')
              : null
          }
          metrics={[
            {
              label: 'Service',
              value: snapshot?.health.data?.service ?? 'ipguard-api',
            },
            {
              label: 'Latency',
              value:
                backendStatus === 'online'
                  ? formatLatency(snapshot?.health.latencyMs)
                  : 'Not available',
            },
          ]}
          style={{ animationDelay: '160ms' }}
        />
        <StatusCard
          icon={Database}
          eyebrow="Persistence layer"
          title="PostgreSQL"
          description="The backend executes a real database query and reports the measured round-trip response."
          status={databaseStatus}
          note={
            !isLoading && databaseStatus === 'offline'
              ? (snapshot?.database.error ??
                'PostgreSQL did not respond to the health probe.')
              : null
          }
          metrics={[
            {
              label: 'Engine',
              value: snapshot?.database.data?.database ?? 'PostgreSQL',
            },
            {
              label: 'Latency',
              value:
                databaseStatus === 'online'
                  ? formatLatency(snapshot?.database.latencyMs)
                  : 'Not available',
            },
          ]}
          style={{ animationDelay: '240ms' }}
        />
      </div>
    </section>
  )
}
