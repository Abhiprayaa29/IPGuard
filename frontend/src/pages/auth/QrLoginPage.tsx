import { ArrowRight, CheckCircle2, FileText, FolderLock, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { QrAuthCard } from '../../components/auth/QrAuthCard'
import { Button } from '../../components/ui/Button'
import { PageHeader, Panel } from '../../components/ui/DataDisplay'
import { StatusIndicator } from '../../components/ui/Feedback'
import { InfoRow } from '../../components/ui/InfoRow'
import { clearStoredSessionToken, getStoredSessionToken, saveSessionToken } from '../../utils/session'

export function QrLoginPage() {
  const [authenticatedToken, setAuthenticatedToken] = useState<string | null>(() =>
    getStoredSessionToken(),
  )

  const handleAuthSuccess = (token: string) => {
    saveSessionToken(token)
    setAuthenticatedToken(token)
  }

  const handleSignOut = () => {
    clearStoredSessionToken()
    setAuthenticatedToken(null)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="QR Authentication"
        description="Authenticate browser sessions or enroll your primary Android device using hardware-backed ECDSA signatures."
        breadcrumbs={[
          { label: 'Overview', to: '/overview' },
          { label: 'QR Authentication' },
        ]}
        actions={
          authenticatedToken ? (
            <StatusIndicator label="Authenticated session active" tone="success" />
          ) : (
            <StatusIndicator label="Awaiting verification" tone="neutral" />
          )
        }
      />

      {authenticatedToken ? (
        <Panel
          title="Browser session active"
          description="Your browser holds a verified bearer token issued after ECDSA challenge confirmation."
        >
          <div className="space-y-5">
            <div className="flex items-start gap-3 rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4">
              <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-emerald-400" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-zinc-100">Access granted</p>
                <p className="mt-0.5 text-xs text-zinc-400">
                  Signed in with Android Keystore verification. You can manage your device, notes, assets, and watermarks from this console.
                </p>
              </div>
            </div>

            <div className="rounded-lg border border-ip-border bg-ip-elevated/60 p-3.5">
              <p className="text-[11px] font-medium text-zinc-500">
                Session Access Token
              </p>
              <p className="mt-1 break-all font-mono text-xs text-zinc-200">
                {authenticatedToken}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <Link to="/overview">
                <Button variant="primary" size="sm" iconRight={<ArrowRight size={14} />}>
                  Go to Overview
                </Button>
              </Link>
              <Link to="/notes">
                <Button variant="secondary" size="sm" iconLeft={<FileText size={14} />}>
                  Secure Notes
                </Button>
              </Link>
              <Link to="/assets">
                <Button variant="secondary" size="sm" iconLeft={<FolderLock size={14} />}>
                  Asset Vault
                </Button>
              </Link>
              <Link to="/devices">
                <Button variant="secondary" size="sm" iconLeft={<Smartphone size={14} />}>
                  Devices
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                Sign Out
              </Button>
            </div>
          </div>
        </Panel>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 lg:items-start">
          <div className="lg:col-span-7">
            <QrAuthCard onSuccess={handleAuthSuccess} />
          </div>

          <div className="space-y-4 lg:col-span-5">
            <Panel
              title="Security Guarantees"
              description="Protocol constraints enforced on every challenge."
            >
              <dl>
                <InfoRow
                  label="Challenge Transport (SEC-02)"
                  value="Browser memory only"
                />
                <InfoRow
                  label="Key Isolation"
                  value="ECDSA P-256 (Keystore / TEE)"
                />
                <InfoRow
                  label="Replay Protection (SEC-01)"
                  value="PostgreSQL FOR UPDATE lock"
                />
                <InfoRow
                  label="Device Slot Policy"
                  value="1 device per account"
                />
              </dl>
            </Panel>

            <Panel title="Need to replace a device?">
              <p className="text-xs leading-5 text-zinc-400">
                Revoking a device preserves its 1/1 slot so access can be restored later with your recovery key. Unregistering releases the 0/1 slot for new device enrollment.
              </p>
              <div className="mt-3">
                <Link
                  to="/devices"
                  className="inline-flex items-center gap-1.5 text-xs font-medium text-ip-accent-400 hover:text-ip-accent-300"
                >
                  Open Device Management
                  <ArrowRight size={13} />
                </Link>
              </div>
            </Panel>
          </div>
        </div>
      )}
    </div>
  )
}
