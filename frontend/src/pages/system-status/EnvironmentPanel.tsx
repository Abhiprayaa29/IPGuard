import { LockKeyhole } from 'lucide-react'
import { Panel } from '../../components/ui/DataDisplay'
import { InfoRow } from '../../components/ui/InfoRow'
import { apiBaseUrl } from '../../services/api'
import type { SystemStatusSnapshot } from '../../types/system'
import { formatClock } from '../../utils/format'

interface EnvironmentPanelProps {
  snapshot: SystemStatusSnapshot | undefined
  isLoading: boolean
}

const pendingValue = 'Checking...'

export function EnvironmentPanel({
  snapshot,
  isLoading,
}: EnvironmentPanelProps) {
  const appVersion =
    snapshot?.systemInfo.data?.version ?? snapshot?.health.data?.version
  const environment =
    snapshot?.systemInfo.data?.environment ??
    snapshot?.overview.data?.environment
  const apiVersion = snapshot?.systemInfo.data?.api_version
  const databaseEngine =
    snapshot?.systemInfo.data?.database_engine ??
    snapshot?.database.data?.database

  return (
    <Panel
      title="Environment & Runtime Metadata"
      description="Non-sensitive runtime configuration reported by the API server."
    >
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="flex items-start gap-3 rounded-lg border border-ip-border bg-ip-elevated/60 p-4">
            <LockKeyhole
              size={16}
              className="mt-0.5 shrink-0 text-ip-accent-400"
              aria-hidden="true"
            />
            <p className="text-xs leading-5 text-zinc-400">
              Only non-sensitive runtime identifiers are exposed here. Secrets,
              recovery keys, and database credentials remain strictly server-side.
            </p>
          </div>
        </div>

        <dl className="lg:col-span-7">
          <InfoRow label="API Base URL" value={apiBaseUrl} mono />
          <InfoRow
            label="Service Name"
            value={
              isLoading
                ? pendingValue
                : (snapshot?.health.data?.service ?? 'Unavailable')
            }
            mono
          />
          <InfoRow
            label="Application Version"
            value={isLoading ? pendingValue : (appVersion ?? 'Unavailable')}
          />
          <InfoRow
            label="Environment"
            value={isLoading ? pendingValue : (environment ?? 'Unavailable')}
          />
          <InfoRow
            label="API Version"
            value={isLoading ? pendingValue : (apiVersion ?? 'Unavailable')}
          />
          <InfoRow
            label="Database Engine"
            value={
              isLoading ? pendingValue : (databaseEngine ?? 'Unavailable')
            }
          />
          <InfoRow
            label="Last Verification"
            value={formatClock(snapshot?.checkedAt)}
          />
        </dl>
      </div>
    </Panel>
  )
}
