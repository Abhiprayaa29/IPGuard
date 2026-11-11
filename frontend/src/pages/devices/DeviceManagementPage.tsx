import {
  Ban,
  Check,
  Copy,
  History,
  KeyRound,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Smartphone,
  Unlock,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { Button, IconButton } from '../../components/ui/Button'
import { KeyValueGrid, PageHeader, Panel } from '../../components/ui/DataDisplay'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusIndicator,
  useToast,
} from '../../components/ui/Feedback'
import { TextInput } from '../../components/ui/Input'
import { ConfirmationDialog } from '../../components/ui/Modal'
import {
  getDeviceLifecycleSummary,
  restoreDevice,
  revokeDevice,
  unregisterDevice,
} from '../../services/devices'
import type { Device, DeviceLifecycleSummary } from '../../types/devices'

function formatDateTime(value: string | null | undefined): string {
  if (!value) return 'Never'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

export function DeviceManagementPage() {
  const { pushToast } = useToast()
  const [summary, setSummary] = useState<DeviceLifecycleSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const [revokeTarget, setRevokeTarget] = useState<Device | null>(null)
  const [restoreTarget, setRestoreTarget] = useState<Device | null>(null)
  const [unregisterTarget, setUnregisterTarget] = useState<Device | null>(null)
  const [actionReason, setActionReason] = useState('')
  const [recoveryKey, setRecoveryKey] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  const loadSummary = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getDeviceLifecycleSummary()
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load device lifecycle summary.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadSummary()
  }, [loadSummary])

  const copyText = (text: string, id: string) => {
    void navigator.clipboard.writeText(text)
    setCopiedId(id)
    window.setTimeout(() => setCopiedId(null), 1800)
  }

  const closeAllDialogs = () => {
    if (isProcessing) return
    setRevokeTarget(null)
    setRestoreTarget(null)
    setUnregisterTarget(null)
    setActionReason('')
    setRecoveryKey('')
  }

  const handleRevokeConfirm = async () => {
    if (!revokeTarget) return
    setIsProcessing(true)
    setError(null)
    try {
      await revokeDevice(revokeTarget.device_id, actionReason || undefined)
      pushToast(`Access revoked for ${revokeTarget.device_name}.`, 'info')
      setRevokeTarget(null)
      setActionReason('')
      await loadSummary()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device access.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleRestoreConfirm = async () => {
    if (!restoreTarget) return
    setIsProcessing(true)
    setError(null)
    try {
      await restoreDevice(
        restoreTarget.device_id,
        actionReason || undefined,
        recoveryKey || undefined,
      )
      pushToast(`Access restored for ${restoreTarget.device_name}.`, 'success')
      setRestoreTarget(null)
      setActionReason('')
      setRecoveryKey('')
      await loadSummary()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore device access.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleUnregisterConfirm = async () => {
    if (!unregisterTarget) return
    setIsProcessing(true)
    setError(null)
    try {
      await unregisterDevice(unregisterTarget.device_id, actionReason || undefined)
      pushToast(`Device ${unregisterTarget.device_name} unregistered. Slot released (0/1).`, 'info')
      setUnregisterTarget(null)
      setActionReason('')
      await loadSummary()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unregister device.')
    } finally {
      setIsProcessing(false)
    }
  }

  const currentDevice = summary?.current_device ?? null
  const isActive = currentDevice?.status === 'ACTIVE'
  const isRevoked = currentDevice?.status === 'REVOKED'
  const historyDevices = summary?.history ?? []

  return (
    <div className="space-y-6 animate-fade-in">
      <PageHeader
        title="Device Management"
        description="Enforce single-device hardware binding (1 account = maximum 1 registered Android device)."
        breadcrumbs={[{ label: 'Overview', to: '/overview' }, { label: 'Devices' }]}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={() => void loadSummary()}
              loading={loading}
              iconLeft={<RefreshCw size={14} />}
            >
              Refresh
            </Button>
            {!currentDevice && (
              <Link to="/login">
                <Button variant="primary" iconLeft={<Smartphone size={14} />}>
                  Enroll Device
                </Button>
              </Link>
            )}
          </>
        }
      />

      {error && <ErrorState message={error} onDismiss={() => setError(null)} />}

      {loading && !summary ? (
        <LoadingState message="Loading account device binding..." />
      ) : summary ? (
        <>
          {/* Relevant Account Slot Summary (No bloated 4-card metrics) */}
          <Panel title="Account Device Slot">
            <KeyValueGrid
              columns={3}
              items={[
                {
                  label: 'Registered Device',
                  value: `${summary.registered_slots}/${summary.max_slots}`,
                  mono: true,
                },
                {
                  label: 'Registration Status',
                  value: (
                    <StatusIndicator
                      label={currentDevice ? 'REGISTERED' : 'UNREGISTERED'}
                      tone={currentDevice ? 'accent' : 'neutral'}
                    />
                  ),
                },
                {
                  label: 'Device Access Status',
                  value: (
                    <StatusIndicator
                      label={currentDevice ? currentDevice.status : 'NO ACTIVE DEVICE'}
                      tone={
                        isActive ? 'success' : isRevoked ? 'danger' : 'neutral'
                      }
                    />
                  ),
                },
              ]}
            />
          </Panel>

          {/* Primary Single-Device Panel */}
          {!currentDevice ? (
            <Panel title="Registered Authenticator">
              <EmptyState
                icon={<Smartphone size={20} />}
                title="No Android device registered"
                description="Your account slot is open (0/1). Enroll an Android smartphone using QR Authentication to authorize sign-ins and encrypted vaults."
                action={
                  <Link to="/login">
                    <Button variant="primary" iconLeft={<KeyRound size={14} />}>
                      Open QR Enrollment
                    </Button>
                  </Link>
                }
              />
            </Panel>
          ) : (
            <Panel
              title={currentDevice.device_name}
              description={
                isRevoked
                  ? 'Registration slot remains locked (1/1), but authentication access is temporarily revoked.'
                  : 'Hardware-bound ECDSA P-256 authenticator actively authorized for this account.'
              }
              actions={
                <StatusIndicator
                  label={currentDevice.status}
                  tone={isActive ? 'success' : 'danger'}
                />
              }
            >
              {isRevoked && (
                <div
                  role="status"
                  className="mb-5 flex items-start gap-2.5 rounded-lg border border-red-500/35 bg-red-500/10 px-3.5 py-3 text-xs text-red-200"
                >
                  <ShieldAlert size={16} className="mt-0.5 shrink-0 text-red-400" />
                  <div>
                    <p className="font-medium text-red-100">
                      Device registered, authentication access blocked
                    </p>
                    <p className="mt-0.5 text-red-200/80">
                      All bearer sessions have been invalidated and sign-ins are rejected by the server. Restore access with account recovery authorization, or unregister permanently to free the 1/1 slot.
                    </p>
                  </div>
                </div>
              )}

              <KeyValueGrid
                items={[
                  { label: 'Device Identity', value: currentDevice.device_name },
                  {
                    label: 'Hardware & OS',
                    value: `${currentDevice.model} · Android ${currentDevice.android_version}`,
                  },
                  {
                    label: 'Security Level',
                    value: currentDevice.security_level,
                    mono: true,
                  },
                  {
                    label: 'Registered Date',
                    value: formatDateTime(currentDevice.enrolled_at),
                  },
                  {
                    label: 'Last Authentication',
                    value: formatDateTime(currentDevice.last_used_at),
                  },
                  {
                    label: 'Device ID',
                    value: (
                      <span className="inline-flex items-center gap-1.5">
                        <span className="break-all">{currentDevice.device_id}</span>
                        <IconButton
                          label="Copy device ID"
                          onClick={() => copyText(currentDevice.device_id, 'dev-id')}
                        >
                          {copiedId === 'dev-id' ? (
                            <Check size={13} className="text-emerald-400" />
                          ) : (
                            <Copy size={13} />
                          )}
                        </IconButton>
                      </span>
                    ),
                    mono: true,
                  },
                ]}
              />

              <div className="mt-4 border-t border-ip-border pt-4">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-zinc-500">
                    Public Key SHA-256 Fingerprint
                  </span>
                  <IconButton
                    label="Copy public key fingerprint"
                    onClick={() =>
                      copyText(currentDevice.public_key_fingerprint, 'pub-fp')
                    }
                  >
                    {copiedId === 'pub-fp' ? (
                      <Check size={13} className="text-emerald-400" />
                    ) : (
                      <Copy size={13} />
                    )}
                  </IconButton>
                </div>
                <p className="mt-1 break-all rounded-md border border-ip-border bg-ip-bg px-3 py-2 font-mono text-xs text-zinc-300">
                  {currentDevice.public_key_fingerprint}
                </p>
              </div>

              {/* Exact State -> Actions Mapping */}
              <div className="mt-5 flex flex-wrap items-center justify-end gap-2.5 border-t border-ip-border pt-4">
                {isActive && (
                  <>
                    <Button
                      variant="secondary"
                      iconLeft={<Ban size={14} />}
                      onClick={() => setRevokeTarget(currentDevice)}
                    >
                      Revoke Access
                    </Button>
                    <Button
                      variant="danger"
                      iconLeft={<Unlock size={14} />}
                      onClick={() => setUnregisterTarget(currentDevice)}
                    >
                      Unregister Device
                    </Button>
                  </>
                )}

                {isRevoked && (
                  <>
                    <Button
                      variant="primary"
                      iconLeft={<RotateCcw size={14} />}
                      onClick={() => setRestoreTarget(currentDevice)}
                    >
                      Restore Access
                    </Button>
                    <Button
                      variant="danger"
                      iconLeft={<Unlock size={14} />}
                      onClick={() => setUnregisterTarget(currentDevice)}
                    >
                      Unregister Device
                    </Button>
                  </>
                )}
              </div>
            </Panel>
          )}

          {/* Separated Device History Section (UNREGISTERED records only) */}
          <Panel
            title="Device History"
            description="Previously unregistered devices preserved for auditability. These devices hold 0 registration slots and cannot authenticate."
            actions={<History size={15} className="text-zinc-500" />}
            noPadding
          >
            {historyDevices.length === 0 ? (
              <div className="px-5 py-8 text-center text-xs text-zinc-500">
                No unregistered device history for this account.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-ip-border bg-ip-bg/60 text-zinc-400">
                    <tr>
                      <th className="px-4 py-2.5 font-medium">Device</th>
                      <th className="px-4 py-2.5 font-medium">Device ID</th>
                      <th className="px-4 py-2.5 font-medium">Status</th>
                      <th className="px-4 py-2.5 font-medium">Enrolled</th>
                      <th className="px-4 py-2.5 font-medium text-right">Unregistered</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ip-border">
                    {historyDevices.map((d) => (
                      <tr key={d.id} className="hover:bg-ip-elevated/40">
                        <td className="px-4 py-3">
                          <span className="font-medium text-zinc-200">{d.device_name}</span>
                          <span className="block text-[11px] text-zinc-500">
                            {d.model} · Android {d.android_version}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-[11px] text-zinc-400">
                          {d.device_id}
                        </td>
                        <td className="px-4 py-3">
                          <StatusIndicator label="UNREGISTERED" tone="neutral" />
                        </td>
                        <td className="px-4 py-3 tabular-nums text-zinc-400">
                          {formatDateTime(d.enrolled_at)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-zinc-400">
                          {formatDateTime(d.unregistered_at)}
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

      {/* Confirmation Dialog: Revoke Access */}
      <ConfirmationDialog
        open={Boolean(revokeTarget)}
        onClose={closeAllDialogs}
        onConfirm={() => void handleRevokeConfirm()}
        title="Revoke device access?"
        description="This device will no longer be able to authenticate. Its registration will remain reserved and can be restored later."
        confirmLabel="Revoke Access"
        confirmVariant="danger"
        isProcessing={isProcessing}
      >
        <TextInput
          id="revoke-reason"
          label="Audit reason (optional)"
          value={actionReason}
          onChange={(e) => setActionReason(e.target.value)}
          placeholder="e.g., Lost device or temporary suspension"
        />
      </ConfirmationDialog>

      {/* Confirmation Dialog: Restore Access */}
      <ConfirmationDialog
        open={Boolean(restoreTarget)}
        onClose={closeAllDialogs}
        onConfirm={() => void handleRestoreConfirm()}
        title="Restore device access?"
        description="This will restore authentication access for the previously registered device."
        confirmLabel="Restore Access"
        confirmVariant="primary"
        isProcessing={isProcessing}
      >
        <TextInput
          id="restore-recovery-key"
          label="Account recovery authorization key"
          type="password"
          value={recoveryKey}
          onChange={(e) => setRecoveryKey(e.target.value)}
          placeholder="Leave blank in dev or enter recovery key"
          hint="Verified out-of-band on the server; the blocked device cannot restore itself."
        />
        <TextInput
          id="restore-reason"
          label="Audit reason (optional)"
          value={actionReason}
          onChange={(e) => setActionReason(e.target.value)}
          placeholder="e.g., Device recovered by owner"
        />
      </ConfirmationDialog>

      {/* Confirmation Dialog: Unregister Device */}
      <ConfirmationDialog
        open={Boolean(unregisterTarget)}
        onClose={closeAllDialogs}
        onConfirm={() => void handleUnregisterConfirm()}
        title="Unregister this device?"
        description="This permanently ends the current device registration and releases the account's device slot. A new device must complete enrollment."
        confirmLabel="Unregister Device"
        confirmVariant="danger"
        isProcessing={isProcessing}
      >
        <TextInput
          id="unregister-reason"
          label="Audit reason (optional)"
          value={actionReason}
          onChange={(e) => setActionReason(e.target.value)}
          placeholder="e.g., Upgrading to a new Android phone"
        />
      </ConfirmationDialog>
    </div>
  )
}
