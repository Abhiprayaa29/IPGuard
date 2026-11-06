import { LockKeyhole } from 'lucide-react'

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
  const environment = snapshot?.systemInfo.data?.environment
  const apiVersion = snapshot?.systemInfo.data?.api_version
  const databaseEngine =
    snapshot?.systemInfo.data?.database_engine ??
    snapshot?.database.data?.database

  return (
    <section
      aria-labelledby="environment-heading"
      className="grid gap-8 rounded-[1.75rem] border border-white/[0.07] bg-white/[0.02] p-6 backdrop-blur-sm sm:p-8 lg:grid-cols-[0.75fr_1.25fr]"
    >
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-ip-gold-400/80">
          Environment
        </p>
        <h2
          id="environment-heading"
          className="mt-2 font-display text-2xl font-semibold tracking-[-0.02em] text-white"
        >
          Connection details
        </h2>
        <p className="mt-3 max-w-sm text-sm leading-6 text-slate-500">
          Non-sensitive runtime metadata returned by the API, including the
          endpoint this browser is currently using.
        </p>

        <div className="mt-6 flex gap-3 rounded-2xl border border-ip-teal-400/15 bg-ip-teal-400/[0.04] p-4">
          <LockKeyhole
            size={16}
            strokeWidth={1.8}
            className="mt-0.5 shrink-0 text-ip-teal-300"
            aria-hidden="true"
          />
          <p className="text-xs leading-5 text-slate-400">
            This view does not expose credentials, connection strings, or
            environment secrets. Database access remains server-side.
          </p>
        </div>
      </div>

      <dl className="rounded-2xl border border-white/[0.06] bg-ip-navy-950/35 px-5 py-2">
        <InfoRow label="API base URL" value={apiBaseUrl} mono />
        <InfoRow
          label="Service"
          value={
            isLoading
              ? pendingValue
              : (snapshot?.health.data?.service ?? 'Unavailable')
          }
          mono
        />
        <InfoRow
          label="Application version"
          value={isLoading ? pendingValue : (appVersion ?? 'Unavailable')}
        />
        <InfoRow
          label="Environment"
          value={isLoading ? pendingValue : (environment ?? 'Unavailable')}
        />
        <InfoRow
          label="API version"
          value={isLoading ? pendingValue : (apiVersion ?? 'Unavailable')}
        />
        <InfoRow
          label="Database engine"
          value={
            isLoading ? pendingValue : (databaseEngine ?? 'Unavailable')
          }
        />
        <InfoRow
          label="Last verification"
          value={formatClock(snapshot?.checkedAt)}
        />
      </dl>
    </section>
  )
}
