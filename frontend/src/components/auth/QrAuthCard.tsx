import {
  AlertCircle,
  CheckCircle2,
  Play,
  RefreshCw,
  Shield,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import { useQrAuth } from '../../hooks/useQrAuth'
import type { SessionType } from '../../types/auth'
import { Button } from '../ui/Button'
import { KeyValueGrid, Panel } from '../ui/DataDisplay'
import { StatusIndicator } from '../ui/Feedback'
import { Tabs } from '../ui/NavigationUi'
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
  } = useQrAuth('AUTHENTICATION', true)

  const handleTabChange = (type: string) => {
    const nextType = type as SessionType
    setActiveTab(nextType)
    startSession(nextType)
  }

  const handleRefresh = () => {
    startSession(activeTab)
  }

  const isApproved = status === 'APPROVED'
  const isRejected = status === 'REJECTED'
  const isInitial = status === 'INITIAL'

  return (
    <Panel
      title="QR Challenge"
      description="ECDSA P-256 hardware keystore verification"
      actions={
        <StatusIndicator
          label={
            isApproved
              ? 'Approved'
              : isRejected
                ? 'Rejected'
                : status === 'SCANNED'
                  ? 'Scanned'
                  : status === 'EXPIRED'
                    ? 'Expired'
                    : status === 'ERROR'
                      ? 'Error'
                      : isInitial
                        ? 'Paused'
                        : 'Waiting for scan'
          }
          tone={
            isApproved
              ? 'success'
              : isRejected || status === 'ERROR'
                ? 'danger'
                : status === 'SCANNED'
                  ? 'accent'
                  : status === 'EXPIRED'
                    ? 'warning'
                    : 'neutral'
          }
        />
      }
    >
      <div className="space-y-5">
        <Tabs
          options={[
            { id: 'AUTHENTICATION', label: 'Mobile Sign-In' },
            { id: 'ENROLLMENT', label: 'Register Device' },
          ]}
          activeId={activeTab}
          onChange={handleTabChange}
        />

        {isInitial ? (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <div className="flex size-11 items-center justify-center rounded-lg border border-ip-border bg-ip-elevated text-zinc-400">
              <Shield size={20} aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">
                Session paused
              </h3>
              <p className="mt-1 text-xs text-zinc-400">
                Start a new challenge when you are ready to scan with IPGuard Authenticator.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={handleRefresh}
              iconLeft={<Play size={14} />}
            >
              Start QR Challenge
            </Button>
          </div>
        ) : isApproved && pollResult ? (
          <div className="space-y-5 py-2">
            <div className="flex flex-col items-center gap-2 text-center">
              <div className="flex size-11 items-center justify-center rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
                <CheckCircle2 size={22} aria-hidden="true" />
              </div>
              <h3 className="text-base font-semibold text-zinc-100">
                Authentication approved
              </h3>
              <p className="text-xs text-zinc-400">
                Hardware Keystore ECDSA signature verified by backend.
              </p>
            </div>

            {pollResult.device && (
              <KeyValueGrid
                columns={2}
                items={[
                  { label: 'Device Name', value: pollResult.device.device_name },
                  {
                    label: 'Model',
                    value: `${pollResult.device.model} (Android ${pollResult.device.android_version})`,
                  },
                  { label: 'Security Level', value: pollResult.device.security_level },
                  {
                    label: 'Public Key Fingerprint',
                    value: pollResult.device.public_key_fingerprint,
                    mono: true,
                  },
                ]}
              />
            )}

            <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-ip-border pt-4">
              <Button variant="secondary" size="sm" onClick={handleRefresh}>
                Start Another Session
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  if (pollResult.access_token && onSuccess) {
                    onSuccess(pollResult.access_token)
                  }
                }}
              >
                Continue to Console
              </Button>
            </div>
          </div>
        ) : isRejected ? (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <div className="flex size-11 items-center justify-center rounded-lg border border-red-500/30 bg-red-500/10 text-red-400">
              <XCircle size={22} aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">
                Authentication rejected
              </h3>
              <p className="mt-1 max-w-sm text-xs text-zinc-400">
                The challenge was declined or biometric verification did not succeed on the mobile device.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={handleRefresh}
              iconLeft={<RefreshCw size={14} />}
            >
              Generate New QR Code
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <QrCodeDisplay
              payload={session?.qr_payload ?? null}
              status={status}
              onRefresh={handleRefresh}
            />

            <div className="flex w-full items-center justify-between gap-3 rounded-lg border border-ip-border bg-ip-elevated/60 px-3.5 py-2.5">
              <QrSessionTimer secondsRemaining={secondsRemaining} />
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={cancelSession}
                  disabled={status === 'CREATING'}
                  aria-label="Cancel session"
                >
                  Cancel
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={status === 'CREATING'}
                  loading={status === 'CREATING'}
                  aria-label="Refresh challenge QR code"
                  iconLeft={
                    status !== 'CREATING' ? <RefreshCw size={13} /> : undefined
                  }
                >
                  Refresh
                </Button>
              </div>
            </div>

            <div className="text-center">
              <p className="text-xs font-medium text-zinc-200">
                {activeTab === 'AUTHENTICATION'
                  ? 'Scan with IPGuard Authenticator to sign in'
                  : 'Scan with IPGuard Authenticator to register your primary device'}
              </p>
              <p className="mt-1 text-xs text-zinc-500">
                One account supports one active registered Android device. Unregister the existing slot in Devices before enrolling a replacement.
              </p>
            </div>

            {errorMessage && (
              <div className="flex w-full items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-400" />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </Panel>
  )
}
