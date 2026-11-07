import { ArrowRight, CheckCircle2, Lock, Shield, Smartphone } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { QrAuthCard } from '../../components/auth/QrAuthCard'

export function QrLoginPage() {
  const [authenticatedToken, setAuthenticatedToken] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-10">
      {/* Top Banner / Hero */}
      <div className="mx-auto max-w-2xl text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-ip-teal-400/25 bg-ip-teal-400/10 px-3.5 py-1 text-xs font-semibold text-ip-teal-300 shadow-sm mb-4">
          <Shield size={13} />
          Milestone 2.4-C • Web QR Authentication
        </div>
        <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Passwordless Hardware Verification
        </h1>
        <p className="mt-3 text-sm text-slate-400">
          Sign in securely using your registered Android device. No passwords, no SMS OTPs.
          Authenticated with ECDSA NIST P-256 signatures generated inside Android Keystore.
        </p>
      </div>

      {authenticatedToken ? (
        <div className="mx-auto w-full max-w-lg rounded-3xl border border-emerald-400/30 bg-slate-900/80 p-8 text-center backdrop-blur-2xl shadow-2xl animate-fade-in">
          <div className="mx-auto grid size-16 place-items-center rounded-3xl border border-emerald-400/30 bg-emerald-400/10 text-emerald-400 mb-4">
            <CheckCircle2 size={36} />
          </div>
          <h2 className="font-display text-2xl font-bold text-white">
            Access Granted
          </h2>
          <p className="mt-2 text-xs text-slate-400">
            Session authorization established via verified ECDSA P-256 hardware signature.
          </p>
          <div className="mt-6 rounded-xl border border-white/10 bg-slate-950/60 p-3 text-left">
            <span className="text-[10px] uppercase font-semibold text-slate-500">
              Session Access Token
            </span>
            <p className="font-mono text-xs text-emerald-300 break-all mt-1">
              {authenticatedToken}
            </p>
          </div>
          <div className="mt-6 flex flex-col gap-3">
            <Link
              to="/system-status"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/25"
            >
              View System Infrastructure
              <ArrowRight size={14} />
            </Link>
            <button
              type="button"
              onClick={() => setAuthenticatedToken(null)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Sign Out / New Authentication
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 lg:items-center">
          {/* Left Column: QR Card */}
          <div className="lg:col-span-7">
            <QrAuthCard
              onSuccess={(token) => {
                setAuthenticatedToken(token)
              }}
            />
          </div>

          {/* Right Column: Security Guarantees & Technical Details */}
          <div className="flex flex-col gap-5 lg:col-span-5">
            <div className="rounded-3xl border border-white/10 bg-slate-900/40 p-6 backdrop-blur-xl">
              <h3 className="font-display text-sm font-bold uppercase tracking-wider text-ip-teal-300 mb-4 flex items-center gap-2">
                <Lock size={16} />
                Security Specifications
              </h3>

              <ul className="flex flex-col gap-4 text-xs text-slate-300">
                <li className="flex items-start gap-3">
                  <div className="mt-0.5 grid size-5 flex-shrink-0 place-items-center rounded-lg bg-ip-teal-400/10 text-ip-teal-300 border border-ip-teal-400/20">
                    <Shield size={12} />
                  </div>
                  <div>
                    <span className="font-semibold text-white">
                      Anti QR-Jacking / Shoulder-Surfing (SEC-02):
                    </span>{' '}
                    The browser channel secret is never encoded in the QR code or URL.
                    Only the initiating browser can poll and retrieve the session access token.
                  </div>
                </li>

                <li className="flex items-start gap-3">
                  <div className="mt-0.5 grid size-5 flex-shrink-0 place-items-center rounded-lg bg-ip-gold-400/10 text-ip-gold-300 border border-ip-gold-400/20">
                    <Smartphone size={12} />
                  </div>
                  <div>
                    <span className="font-semibold text-white">
                      Hardware Keystore Bound:
                    </span>{' '}
                    Private keys are generated inside the Samsung A54 Secure Element / TEE and marked non-exportable.
                  </div>
                </li>

                <li className="flex items-start gap-3">
                  <div className="mt-0.5 grid size-5 flex-shrink-0 place-items-center rounded-lg bg-emerald-400/10 text-emerald-300 border border-emerald-400/20">
                    <CheckCircle2 size={12} />
                  </div>
                  <div>
                    <span className="font-semibold text-white">
                      Pessimistic Row-Locking (SEC-01):
                    </span>{' '}
                    PostgreSQL <code>SELECT ... FOR UPDATE</code> guarantees exact single-use challenge consumption with no race conditions.
                  </div>
                </li>
              </ul>
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-white/5 bg-slate-950/40 p-4 text-xs text-slate-400">
              <span>Looking for health checks?</span>
              <Link
                to="/system-status"
                className="inline-flex items-center gap-1.5 font-medium text-ip-teal-300 hover:text-ip-teal-200"
              >
                System Status
                <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
