import {
  Activity,
  ArrowRight,
  FileText,
  FolderLock,
  QrCode,
  RefreshCw,
  ShieldAlert,
  Smartphone,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '../../components/ui/Button'
import { KeyValueGrid, PageHeader, Panel } from '../../components/ui/DataDisplay'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusIndicator,
} from '../../components/ui/Feedback'
import { fetchSystemOverview } from '../../services/systemStatus'
import type { SystemOverviewResponse } from '../../types/system'

function formatTimestamp(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export function OverviewPage() {
  const [overview, setOverview] = useState<SystemOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadOverview = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSystemOverview()
      setOverview(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load security overview.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  const deviceStatusTone = (() => {
    if (!overview) return 'neutral' as const
    if (overview.current_device_status === 'ACTIVE') return 'success' as const
    if (overview.current_device_status === 'REVOKED') return 'danger' as const
    return 'neutral' as const
  })()

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Security Overview"
        description="Account device binding, authentication posture, encrypted vault access, and live audit events."
        breadcrumbs={[{ label: 'Overview' }]}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={() => void loadOverview()}
              loading={loading}
              iconLeft={<RefreshCw size={14} />}
            >
              Refresh
            </Button>
            {!overview?.authenticated && (
              <Link to="/login">
                <Button variant="primary" iconLeft={<QrCode size={14} />}>
                  Sign In with QR
                </Button>
              </Link>
            )}
          </>
        }
      />

      {error && <ErrorState message={error} onRetry={() => void loadOverview()} />}

      {loading && !overview ? (
        <LoadingState message="Loading live security posture..." />
      ) : overview ? (
        <>
          {/* Relevant Security Warnings */}
          {overview.warnings.length > 0 && (
            <div className="space-y-2">
              {overview.warnings.map((warning, idx) => (
                <div
                  key={`${warning}-${idx}`}
                  role="status"
                  className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-[13px] text-amber-200"
                >
                  <ShieldAlert size={16} className="mt-0.5 shrink-0 text-amber-400" />
                  <span>{warning}</span>
                </div>
              ))}
            </div>
          )}

          {/* Core Summary Row */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel
              title="Device Binding"
              description="One account is bound to at most one registered Android device."
              actions={
                <StatusIndicator label={overview.current_device_status} tone={deviceStatusTone} />
              }
            >
              <KeyValueGrid
                items={[
                  {
                    label: 'Registered Device Slot',
                    value: `${overview.registered_slots}/${overview.max_slots}`,
                    mono: true,
                  },
                  {
                    label: 'Active Device Name',
                    value: overview.current_device_name ?? 'None registered',
                  },
                  {
                    label: 'Account Identifier',
                    value: overview.account_id,
                    mono: true,
                  },
                  {
                    label: 'Device Identifier',
                    value: overview.current_device_id ?? 'Not assigned',
                    mono: true,
                  },
                ]}
              />
              <div className="mt-4 flex items-center justify-between border-t border-ip-border pt-3">
                <span className="text-xs text-zinc-400">
                  Manage revocation, restoration, or slot release
                </span>
                <Link
                  to="/devices"
                  className="inline-flex items-center gap-1 text-xs font-medium text-ip-accent-hover hover:underline"
                >
                  Open Devices
                  <ArrowRight size={13} />
                </Link>
              </div>
            </Panel>

            <Panel
              title="System Health"
              description="Live infrastructure connectivity measured on the backend."
              actions={
                <StatusIndicator
                  label={
                    overview.database_status === 'ok' ? 'Operational' : 'Degraded'
                  }
                  tone={overview.database_status === 'ok' ? 'success' : 'warning'}
                />
              }
            >
              <KeyValueGrid
                items={[
                  {
                    label: 'API Service',
                    value: overview.api_status === 'ok' ? 'Operational' : 'Unavailable',
                  },
                  {
                    label: 'PostgreSQL 17',
                    value:
                      overview.database_status === 'ok'
                        ? `Operational (${overview.database_latency_ms ?? 0} ms)`
                        : 'Unavailable',
                    mono: true,
                  },
                  {
                    label: 'Environment',
                    value: overview.environment,
                    mono: true,
                  },
                  {
                    label: 'Console Session',
                    value: overview.authenticated ? 'Authenticated' : 'Unauthenticated',
                  },
                ]}
              />
              <div className="mt-4 flex items-center justify-between border-t border-ip-border pt-3">
                <span className="text-xs text-zinc-400">Inspect individual service probes</span>
                <Link
                  to="/system-status"
                  className="inline-flex items-center gap-1 text-xs font-medium text-ip-accent-hover hover:underline"
                >
                  System Status
                  <ArrowRight size={13} />
                </Link>
              </div>
            </Panel>
          </div>

          {/* Encrypted Vault Overviews */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Panel
              title="Secure Notes"
              description="AES-256-GCM super-encrypted notes isolated per owner."
              actions={<FileText size={16} className="text-zinc-400" />}
            >
              {overview.authenticated ? (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-zinc-400">Encrypted notes stored</p>
                    <p className="mt-0.5 text-lg font-semibold tabular-nums text-zinc-100">
                      {overview.notes_count ?? 0}
                    </p>
                  </div>
                  <Link to="/notes">
                    <Button variant="secondary" size="sm" iconRight={<ArrowRight size={13} />}>
                      Open Notes
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-zinc-400">
                    Sign in with your hardware authenticator to inspect your encrypted notes.
                  </p>
                  <Link to="/login">
                    <Button variant="secondary" size="sm">
                      Sign In
                    </Button>
                  </Link>
                </div>
              )}
            </Panel>

            <Panel
              title="Asset Vault"
              description="XChaCha20-Poly1305 AEAD files and SHA-256 integrity records."
              actions={<FolderLock size={16} className="text-zinc-400" />}
            >
              {overview.authenticated ? (
                <div className="flex items-center justify-between">
                  <div className="flex gap-6">
                    <div>
                      <p className="text-xs text-zinc-400">Encrypted assets</p>
                      <p className="mt-0.5 text-lg font-semibold tabular-nums text-zinc-100">
                        {overview.assets_count ?? 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-zinc-400">Integrity verified</p>
                      <p className="mt-0.5 text-lg font-semibold tabular-nums text-emerald-300">
                        {overview.verified_assets_count ?? 0}
                      </p>
                    </div>
                  </div>
                  <Link to="/assets">
                    <Button variant="secondary" size="sm" iconRight={<ArrowRight size={13} />}>
                      Open Vault
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-zinc-400">
                    Sign in with your hardware authenticator to access encrypted files and watermarks.
                  </p>
                  <Link to="/login">
                    <Button variant="secondary" size="sm">
                      Sign In
                    </Button>
                  </Link>
                </div>
              )}
            </Panel>
          </div>

          {/* Recent Security Events Table */}
          <Panel
            title="Recent Security Events"
            description="Tamper-evident append-only audit chain records for this account's device."
            noPadding
          >
            {overview.recent_events.length === 0 ? (
              <div className="p-5">
                <EmptyState
                  icon={<Activity size={18} />}
                  title="No security events recorded"
                  description="Device enrollment, authentication, revocation, and asset integrity events appear here."
                  action={
                    <Link to="/login">
                      <Button variant="secondary" size="sm" iconLeft={<Smartphone size={13} />}>
                        Start QR Authentication
                      </Button>
                    </Link>
                  }
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-ip-border bg-ip-bg/60 text-zinc-400">
                    <tr>
                      <th className="px-4 py-2.5 font-medium">Event</th>
                      <th className="px-4 py-2.5 font-medium">Resource</th>
                      <th className="px-4 py-2.5 font-medium">Outcome</th>
                      <th className="px-4 py-2.5 font-medium">Chain Hash</th>
                      <th className="px-4 py-2.5 font-medium text-right">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ip-border">
                    {overview.recent_events.map((evt) => (
                      <tr key={evt.event_id} className="hover:bg-ip-elevated/40">
                        <td className="px-4 py-3 font-medium text-zinc-100">{evt.event_type}</td>
                        <td className="px-4 py-3 font-mono text-[11px] text-zinc-400">
                          {evt.resource_type}
                          {evt.resource_id ? ` · ${evt.resource_id.slice(0, 12)}` : ''}
                        </td>
                        <td className="px-4 py-3">
                          <StatusIndicator
                            label={evt.result}
                            tone={
                              evt.result === 'ACTIVE' ||
                              evt.result === 'APPROVED' ||
                              evt.result === 'VERIFIED' ||
                              evt.result === 'SUCCESS'
                                ? 'success'
                                : evt.result === 'REVOKED'
                                  ? 'danger'
                                  : 'neutral'
                            }
                          />
                        </td>
                        <td className="px-4 py-3 font-mono text-[11px] text-zinc-400">
                          {evt.event_hash.slice(0, 14)}...
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-zinc-400">
                          {formatTimestamp(evt.occurred_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </>
      ) : null}
    </div>
  )
}
