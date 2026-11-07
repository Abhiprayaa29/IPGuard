import {
  CheckCircle2,
  KeyRound,
  Play,
  RefreshCw,
  Shield,
  ShieldAlert,
  Smartphone,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import { useQrAuth } from '../../hooks/useQrAuth'
import type { SessionType } from '../../types/auth'
import { QrCodeDisplay } from './QrCodeDisplay'
import { QrSessionTimer } from './QrSessionTimer'

interface QrAuthCardProps {
  onSuccess?: (accessToken: string) => void
}

export function QrAuthCard({ onSuccess }: QrAuthCardProps) {
  const [activeTab, setActiveTab] = useState<SessionType>('AUTHENTICATION')
  const {
    status,
    session,
    pollResult,
    secondsRemaining,
    errorMessage,
    startSession,
    cancelSession,
  } = useQrAuth(activeTab, true)

  const handleTabChange = (type: SessionType) => {
    setActiveTab(type)
    startSession(type)
  }

  const handleRefresh = () => {
    startSession(activeTab)
  }

  const isApproved = status === 'APPROVED'
  const isRejected = status === 'REJECTED'
  const isInitial = status === 'INITIAL'

  return (
    <div className="relative mx-auto w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 bg-slate-900/60 p-6 shadow-2xl backdrop-blur-2xl sm:p-8 animate-fade-up">
      {/* Glow Effects */}
      <div
        className="pointer-events-none absolute -top-24 -left-24 size-64 rounded-full bg-ip-teal-500/10 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-24 -right-24 size-64 rounded-full bg-ip-gold-500/10 blur-3xl"
        aria-hidden="true"
      />

      {/* Card Header & Security Badges */}
      <div className="relative z-10 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="grid size-9 place-items-center rounded-xl border border-ip-teal-400/20 bg-ip-teal-400/10 text-ip-teal-300">
              <Shield size={18} />
            </span>
            <div>
              <h2 className="font-display text-lg font-bold text-white">
                Hardware-Backed QR Auth
              </h2>
              <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
                ECDSA NIST P-256 • Keystore Protected
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="rounded-full border border-ip-teal-400/20 bg-ip-teal-400/5 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-ip-teal-300">
              Anti QR-Jacking
            </span>
          </div>
        </div>

        {/* Tab Switcher: Sign In vs Device Enrollment */}
        <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-950/60 p-1 border border-white/5">
          <button
            type="button"
            onClick={() => handleTabChange('AUTHENTICATION')}
            className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition ${
              activeTab === 'AUTHENTICATION'
                ? 'bg-ip-teal-400/15 text-ip-teal-300 border border-ip-teal-400/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Smartphone size={14} />
            Mobile Sign-In
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('ENROLLMENT')}
            className={`flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition ${
              activeTab === 'ENROLLMENT'
                ? 'bg-ip-gold-400/15 text-ip-gold-300 border border-ip-gold-400/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <KeyRound size={14} />
            Register Device
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="relative z-10 mt-6 flex flex-col items-center">
        {/* Initial / Canceled State */}
        {isInitial ? (
          <div className="flex w-full flex-col items-center gap-4 py-8 text-center animate-fade-in">
            <div className="grid size-14 place-items-center rounded-2xl border border-white/10 bg-slate-950/60 text-slate-400">
              <Shield size={28} />
            </div>
            <div>
              <h3 className="font-display text-base font-bold text-white">
                Session Paused
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                Click below to generate a new secure QR challenge.
              </p>
            </div>
            <button
              type="button"
              onClick={handleRefresh}
              className="mt-2 inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 px-6 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/25"
            >
              <Play size={14} />
              Start QR Authentication
            </button>
          </div>
        ) : isApproved && pollResult ? (
          /* Approved Success State */
          <div className="flex w-full flex-col items-center gap-5 py-4 text-center animate-fade-in">
            <div className="grid size-16 place-items-center rounded-3xl border border-emerald-400/30 bg-emerald-400/10 text-emerald-400 shadow-[0_0_30px_rgba(52,211,153,0.2)]">
              <CheckCircle2 size={36} />
            </div>

            <div>
              <h3 className="font-display text-xl font-bold text-white">
                Authentication Approved
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                Hardware Keystore signature successfully verified by PostgreSQL backend.
              </p>
            </div>

            {pollResult.device && (
              <div className="w-full rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-left">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Authenticated Device Credentials
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">Device Name:</span>
                    <p className="font-medium text-white truncate">
                      {pollResult.device.device_name}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Model:</span>
                    <p className="font-medium text-white truncate">
                      {pollResult.device.model} (Android {pollResult.device.android_version})
                    </p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-500">Security Level:</span>
                    <p className="font-medium text-ip-teal-300">
                      {pollResult.device.security_level} (Hardware Isolated)
                    </p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-slate-500">Fingerprint:</span>
                    <p className="font-mono text-[11px] text-slate-300 truncate">
                      {pollResult.device.public_key_fingerprint}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="flex w-full flex-col gap-2.5">
              <button
                type="button"
                onClick={() => {
                  if (pollResult.access_token && onSuccess) {
                    onSuccess(pollResult.access_token)
                  }
                }}
                className="w-full rounded-xl border border-emerald-400/30 bg-emerald-500/20 py-2.5 text-xs font-semibold text-emerald-200 transition hover:bg-emerald-500/30 hover:border-emerald-400/50"
              >
                Proceed to Protected Dashboard
              </button>
              <button
                type="button"
                onClick={handleRefresh}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-2 text-xs font-medium text-slate-400 transition hover:bg-white/10 hover:text-white"
              >
                Start Another Session
              </button>
            </div>
          </div>
        ) : isRejected ? (
          /* Rejected State */
          <div className="flex w-full flex-col items-center gap-5 py-6 text-center animate-fade-in">
            <div className="grid size-16 place-items-center rounded-3xl border border-rose-500/30 bg-rose-500/10 text-rose-400 shadow-[0_0_30px_rgba(244,63,94,0.2)]">
              <XCircle size={36} />
            </div>

            <div>
              <h3 className="font-display text-xl font-bold text-white">
                Authentication Rejected
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                The authentication challenge was denied or biometric verification failed on the mobile device.
              </p>
            </div>

            <button
              type="button"
              onClick={handleRefresh}
              className="mt-2 inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/10 px-6 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/20"
            >
              <RefreshCw size={14} />
              Generate New QR Code
            </button>
          </div>
        ) : (
          /* Active QR State */
          <div className="flex w-full flex-col items-center gap-5">
            <QrCodeDisplay
              payload={session?.qr_payload ?? null}
              status={status}
              onRefresh={handleRefresh}
            />

            {/* Countdown Timer & Actions */}
            <div className="flex w-full items-center justify-between rounded-2xl border border-white/5 bg-slate-950/40 px-4 py-3">
              <QrSessionTimer secondsRemaining={secondsRemaining} />
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={cancelSession}
                  disabled={status === 'CREATING'}
                  aria-label="Cancel session"
                  className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRefresh}
                  disabled={status === 'CREATING'}
                  aria-label="Refresh challenge QR code"
                  className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
                >
                  <RefreshCw size={12} className={status === 'CREATING' ? 'animate-spin' : ''} />
                  Refresh
                </button>
              </div>
            </div>

            {/* User Instructions */}
            <div className="w-full text-center">
              <p className="text-xs text-slate-300 font-medium">
                {activeTab === 'AUTHENTICATION'
                  ? 'Scan with IPGuard Authenticator on Samsung A54'
                  : 'Enroll new Android Authenticator device'}
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Approve via Biometrics or Device Screen Lock. Nonce and origin are bound to this session.
              </p>
            </div>

            {/* Error Message if Present */}
            {errorMessage && (
              <div className="flex w-full items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
                <ShieldAlert size={16} className="flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Card Footer: Security Guarantee */}
      <div className="relative z-10 mt-6 border-t border-white/5 pt-4 text-center">
        <p className="text-[10px] text-slate-500">
          Protected by RFC 6454 Origin Binding, Row-Level Lock, & In-Memory Polling Authorization (SEC-02).
        </p>
      </div>
    </div>
  )
}
