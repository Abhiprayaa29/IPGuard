import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  
  Copy,
  
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
  
  Unlock,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listDevices, revokeDevice, unregisterDevice } from '../../services/devices'
import type { Device } from '../../types/devices'


export function DeviceManagementPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [copiedFingerprint, setCopiedFingerprint] = useState<string | null>(null)

  // Confirmation modal states
  const [revokeTarget, setRevokeTarget] = useState<Device | null>(null)
  const [unregisterTarget, setUnregisterTarget] = useState<Device | null>(null)
  const [actionReason, setActionReason] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // session token handled in service

  const loadDevices = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listDevices()
      setDevices(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load device list.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDevices()
  }, [loadDevices])

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedFingerprint(id)
    setTimeout(() => setCopiedFingerprint(null), 2000)
  }

  const handleRevokeConfirm = async () => {
    if (!revokeTarget) return
    setIsProcessing(true)
    setError(null)
    try {
      await revokeDevice(revokeTarget.device_id, actionReason)
      setSuccessMessage(`Access for device "${revokeTarget.device_name}" has been REVOKED.`)
      setRevokeTarget(null)
      setActionReason('')
      await loadDevices()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke device.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleUnregisterConfirm = async () => {
    if (!unregisterTarget) return
    setIsProcessing(true)
    setError(null)
    try {
      await unregisterDevice(unregisterTarget.device_id, actionReason)
      setSuccessMessage(
        `Device "${unregisterTarget.device_name}" is now UNREGISTERED. Its registration slot is released.`
      )
      setUnregisterTarget(null)
      setActionReason('')
      await loadDevices()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unregister device.')
    } finally {
      setIsProcessing(false)
    }
  }

  const filteredDevices = devices.filter((d) => {
    const q = searchQuery.toLowerCase()
    return (
      d.device_name.toLowerCase().includes(q) ||
      d.device_id.toLowerCase().includes(q) ||
      d.model.toLowerCase().includes(q) ||
      d.public_key_fingerprint.toLowerCase().includes(q)
    )
  })

  const activeCount = devices.filter((d) => d.status === 'ACTIVE').length
  const revokedCount = devices.filter((d) => d.status === 'REVOKED').length
  const unregisteredCount = devices.filter((d) => d.status === 'UNREGISTERED').length

  return (
    <div className="flex flex-col gap-8 pb-12 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-ip-teal-400/25 bg-ip-teal-400/10 px-3 py-1 text-xs font-semibold text-ip-teal-300 shadow-sm mb-2">
            <Shield size={13} />
            Hardware Authenticator Registry
          </div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Device Management
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Control trusted hardware authenticators, enforce one-time enrollment, and manage access lifecycles.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={loadDevices}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/60 px-4 py-2.5 text-xs font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 px-4 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/25"
          >
            <Smartphone size={14} />
            QR Sign-In
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-4 backdrop-blur-xl">
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            Total Devices
          </span>
          <p className="mt-1 text-2xl font-bold text-white">{devices.length}</p>
        </div>
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.04] p-4 backdrop-blur-xl">
          <span className="text-[11px] font-medium uppercase tracking-wider text-emerald-400">
            Active Authenticators
          </span>
          <p className="mt-1 text-2xl font-bold text-emerald-300">{activeCount}</p>
        </div>
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/[0.04] p-4 backdrop-blur-xl">
          <span className="text-[11px] font-medium uppercase tracking-wider text-rose-400">
            Revoked (Locked)
          </span>
          <p className="mt-1 text-2xl font-bold text-rose-300">{revokedCount}</p>
        </div>
        <div className="rounded-2xl border border-slate-500/20 bg-slate-500/[0.04] p-4 backdrop-blur-xl">
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
            Unregistered Slots
          </span>
          <p className="mt-1 text-2xl font-bold text-slate-300">{unregisteredCount}</p>
        </div>
      </div>

      {/* Success / Error Banners */}
      {successMessage && (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{successMessage}</span>
          </div>
          <button type="button" onClick={() => setSuccessMessage(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-xs text-rose-300">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
          <button type="button" onClick={() => setError(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search
          size={16}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by device name, device ID, hardware model, or fingerprint..."
          className="w-full rounded-xl border border-white/10 bg-slate-900/60 pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-ip-teal-400 focus:outline-none focus:ring-1 focus:ring-ip-teal-400"
        />
      </div>

      {/* Device List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400">
          <RefreshCw size={28} className="animate-spin text-ip-teal-400 mb-3" />
          <p className="text-xs">Loading registered devices...</p>
        </div>
      ) : filteredDevices.length === 0 ? (
        <div className="rounded-3xl border border-white/10 bg-slate-900/30 p-12 text-center backdrop-blur-xl">
          <Smartphone size={36} className="mx-auto text-slate-600 mb-3" />
          <h3 className="text-sm font-semibold text-white">No devices found</h3>
          <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
            {searchQuery
              ? 'No registered device matches your search filter.'
              : 'No hardware authenticator is currently registered. Scan the QR code to enroll your Android phone.'}
          </p>
          <div className="mt-5">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/10 px-4 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/20"
            >
              Go to QR Enrollment
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDevices.map((device) => {
            // isRegistered inferred from status
            const isAccessActive = device.status === 'ACTIVE'
            const isRevoked = device.status === 'REVOKED'
            const isUnregistered = device.status === 'UNREGISTERED'

            return (
              <div
                key={device.id}
                className="group relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/50 p-5 backdrop-blur-xl transition hover:border-white/20 shadow-lg"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  {/* Left: Device Info */}
                  <div className="flex items-start gap-3.5">
                    <div
                      className={`grid size-11 flex-shrink-0 place-items-center rounded-2xl border ${
                        isAccessActive
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                          : isRevoked
                          ? 'border-rose-500/30 bg-rose-500/10 text-rose-400'
                          : 'border-slate-500/30 bg-slate-500/10 text-slate-400'
                      }`}
                    >
                      <Smartphone size={22} />
                    </div>

                    <div className="flex flex-col gap-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-display text-sm font-bold text-white">
                          {device.device_name}
                        </h3>
                        <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                          {device.model} • Android {device.android_version}
                        </span>

                        {/* Status Badges */}
                        {isAccessActive && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                            <ShieldCheck size={11} />
                            ACTIVE
                          </span>
                        )}
                        {isRevoked && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-rose-400/30 bg-rose-400/10 px-2.5 py-0.5 text-[10px] font-semibold text-rose-300">
                            <ShieldAlert size={11} />
                            REVOKED (LOCKED)
                          </span>
                        )}
                        {isUnregistered && (
                          <span className="inline-flex items-center gap-1 rounded-full border border-slate-500/30 bg-slate-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-slate-400">
                            <Unlock size={11} />
                            UNREGISTERED
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-400">
                        <span>
                          <strong className="text-slate-500 font-medium">Device ID:</strong>{' '}
                          <code className="font-mono text-slate-300">{device.device_id}</code>
                        </span>
                        <span>
                          <strong className="text-slate-500 font-medium">Security:</strong>{' '}
                          <span className="text-ip-teal-300 font-mono">{device.security_level}</span>
                        </span>
                      </div>

                      {/* Fingerprint snippet */}
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-[10px] text-slate-500">Public Key Fingerprint:</span>
                        <code className="font-mono text-[10px] text-ip-gold-300 break-all bg-black/30 px-2 py-0.5 rounded border border-white/5">
                          {device.public_key_fingerprint}
                        </code>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(device.public_key_fingerprint, device.id)}
                          className="text-slate-400 hover:text-white"
                          title="Copy fingerprint"
                        >
                          <Copy size={12} />
                        </button>
                        {copiedFingerprint === device.id && (
                          <span className="text-[10px] text-emerald-400">Copied!</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Middle / Timestamps */}
                  <div className="flex flex-wrap gap-4 text-[11px] text-slate-400 border-t border-white/5 pt-3 lg:border-t-0 lg:pt-0">
                    <div className="flex flex-col">
                      <span className="text-[10px] uppercase font-semibold text-slate-500">
                        Enrolled At
                      </span>
                      <span className="font-mono text-slate-300">
                        {new Date(device.enrolled_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[10px] uppercase font-semibold text-slate-500">
                        Last Authentication
                      </span>
                      <span className="font-mono text-slate-300">
                        {device.last_used_at
                          ? new Date(device.last_used_at).toLocaleString()
                          : 'Never'}
                      </span>
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center gap-2">
                    {/* Revoke Action */}
                    {isAccessActive && (
                      <button
                        type="button"
                        onClick={() => setRevokeTarget(device)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-300 transition hover:bg-rose-500/20"
                        title="Cut access and prevent future sign-ins without releasing registration"
                      >
                        <Ban size={13} />
                        Revoke Access
                      </button>
                    )}

                    {/* Unregister Action */}
                    {!isUnregistered && (
                      <button
                        type="button"
                        onClick={() => setUnregisterTarget(device)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-semibold text-amber-300 transition hover:bg-amber-500/20"
                        title="Release registration binding so device can re-enroll"
                      >
                        <Unlock size={13} />
                        Unregister Device
                      </button>
                    )}

                    {isUnregistered && (
                      <span className="text-[11px] font-medium text-slate-500 italic">
                        Slot released (ready for re-enrollment)
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Revoke Confirmation Modal */}
      {revokeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-3xl border border-rose-500/30 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400 mb-3">
              <ShieldAlert size={24} />
              <h3 className="font-display text-lg font-bold text-white">Revoke Device Access</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to revoke access for{' '}
              <strong className="text-white">{revokeTarget.device_name}</strong> (
              <code className="text-rose-300">{revokeTarget.device_id}</code>)?
            </p>
            <div className="mt-3 rounded-xl border border-white/5 bg-slate-950/60 p-3 text-[11px] text-slate-400">
              <p>• Immediate revocation of all active sessions.</p>
              <p>• Prevents any future Sign In from this device.</p>
              <p>• <strong>Registration remains LOCKED</strong>: device cannot re-register without explicit unregistration.</p>
            </div>
            <div className="mt-4">
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Reason (Optional):
              </label>
              <input
                type="text"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Lost device, suspicious activity"
                className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-600 focus:border-rose-400 focus:outline-none"
              />
            </div>
            <div className="mt-6 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={() => {
                  setRevokeTarget(null)
                  setActionReason('')
                }}
                disabled={isProcessing}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRevokeConfirm}
                disabled={isProcessing}
                className="inline-flex items-center gap-2 rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-rose-500 disabled:opacity-50"
              >
                {isProcessing && <RefreshCw size={12} className="animate-spin" />}
                Confirm Revoke
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Unregister Confirmation Modal */}
      {unregisterTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-3xl border border-amber-500/30 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-amber-400 mb-3">
              <Unlock size={24} />
              <h3 className="font-display text-lg font-bold text-white">Unregister Device</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to unregister{' '}
              <strong className="text-white">{unregisterTarget.device_name}</strong>?
            </p>
            <div className="mt-3 rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-3 text-[11px] text-amber-200/90 space-y-1">
              <p>• <strong>Releases the enrollment binding</strong> so a device can register again.</p>
              <p>• Terminates all active sessions bound to this device.</p>
              <p>• <strong>Safe & Non-Destructive:</strong> Secure Notes and audit logs are <strong>NEVER deleted</strong>.</p>
            </div>
            <div className="mt-4">
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Reason (Optional):
              </label>
              <input
                type="text"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="e.g. Device replacement, re-installing authenticator"
                className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-600 focus:border-amber-400 focus:outline-none"
              />
            </div>
            <div className="mt-6 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={() => {
                  setUnregisterTarget(null)
                  setActionReason('')
                }}
                disabled={isProcessing}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUnregisterConfirm}
                disabled={isProcessing}
                className="inline-flex items-center gap-2 rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-amber-500 disabled:opacity-50"
              >
                {isProcessing && <RefreshCw size={12} className="animate-spin" />}
                Confirm Unregister
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
