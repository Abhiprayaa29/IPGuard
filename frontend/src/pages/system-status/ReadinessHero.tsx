import { Clock3 } from 'lucide-react'
import { PageHeader, Panel } from '../../components/ui/DataDisplay'
import { RefreshButton } from '../../components/ui/RefreshButton'
import { StatusBadge } from '../../components/ui/StatusBadge'
import type { SystemStatusSnapshot, UiStatus } from '../../types/system'
import { formatClock } from '../../utils/format'
import { getOverallLabel } from '../../utils/status'

interface ReadinessHeroProps {
  status: UiStatus
  snapshot: SystemStatusSnapshot | undefined
  isRefreshing: boolean
  isInitialLoading: boolean
  onRefresh: () => void
}

const summaryCopy: Record<UiStatus, string> = {
  online: 'All live service probes responded within expected boundaries.',
  degraded:
    'The API control plane responded, but one or more downstream subsystems reported issues.',
  offline: 'Backend API probe failed or could not be reached.',
  checking: 'Querying live health endpoints...',
  unknown: 'No completed readiness probe is available yet.',
}

export function ReadinessHero({
  status,
  snapshot,
  isRefreshing,
  isInitialLoading,
  onRefresh,
}: ReadinessHeroProps) {
  return (
    <div className="space-y-4">
      <PageHeader
        title="System Status"
        description="Live readiness telemetry probed directly from the API server and PostgreSQL database."
        breadcrumbs={[
          { label: 'Overview', to: '/overview' },
          { label: 'System Status' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={status} />
            <RefreshButton
              onClick={onRefresh}
              isRefreshing={isRefreshing}
              disabled={isInitialLoading}
              busyLabel={isInitialLoading ? 'Checking...' : 'Refreshing...'}
            />
          </div>
        }
      />

      <Panel>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-zinc-100">
              Overall status: {getOverallLabel(status)}
            </p>
            <p className="mt-0.5 text-xs text-zinc-400">{summaryCopy[status]}</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Clock3 size={14} aria-hidden="true" />
            <span>
              Last verified{' '}
              <span className="font-mono text-zinc-200 tabular-nums">
                {formatClock(snapshot?.checkedAt)}
              </span>
            </span>
          </div>
        </div>
      </Panel>
    </div>
  )
}
