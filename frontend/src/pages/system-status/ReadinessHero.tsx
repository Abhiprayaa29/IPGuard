import { Clock3, ShieldCheck } from 'lucide-react'

import { RefreshButton } from '../../components/ui/RefreshButton'
import { StatusBadge } from '../../components/ui/StatusBadge'
import type { SystemStatusSnapshot, UiStatus } from '../../types/system'
import { formatClock } from '../../utils/format'
import { getOverallLabel } from '../../utils/status'

const orbTone: Record<UiStatus, string> = {
  online:
    'border-ip-teal-400/35 bg-ip-teal-400/[0.09] text-ip-teal-300 shadow-[0_0_110px_-24px_rgba(45,212,191,0.55)]',
  degraded:
    'border-ip-gold-400/35 bg-ip-gold-400/[0.09] text-ip-gold-300 shadow-[0_0_110px_-24px_rgba(231,200,115,0.5)]',
  offline:
    'border-rose-400/35 bg-rose-400/[0.08] text-rose-300 shadow-[0_0_110px_-24px_rgba(251,113,133,0.45)]',
  checking:
    'border-slate-400/25 bg-slate-400/[0.06] text-slate-300 shadow-[0_0_110px_-24px_rgba(148,163,184,0.35)]',
}

const ringTone: Record<UiStatus, string> = {
  online: 'border-ip-teal-400/20',
  degraded: 'border-ip-gold-400/20',
  offline: 'border-rose-400/20',
  checking: 'border-slate-400/15',
}

interface ReadinessHeroProps {
  status: UiStatus
  snapshot: SystemStatusSnapshot | undefined
  isRefreshing: boolean
  isInitialLoading: boolean
  onRefresh: () => void
}

export function ReadinessHero({
  status,
  snapshot,
  isRefreshing,
  isInitialLoading,
  onRefresh,
}: ReadinessHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-white/[0.08] bg-ip-navy-900/45 p-6 shadow-[0_40px_120px_-60px_rgba(0,0,0,0.9)] backdrop-blur-sm sm:p-8 lg:p-10 animate-fade-up">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_74%_24%,rgba(45,212,191,0.12),transparent_42%)]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-20 left-1/3 h-px w-72 bg-gradient-to-r from-transparent via-ip-gold-400/30 to-transparent"
        aria-hidden="true"
      />

      <div className="relative grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <p className="flex items-center gap-3 text-[10px] font-semibold uppercase tracking-[0.28em] text-slate-500">
            <span className="h-px w-8 bg-ip-gold-400/70" aria-hidden="true" />
            Foundation readiness · M0 + M1
          </p>

          <h1 className="mt-5 max-w-2xl font-display text-4xl font-semibold leading-[1.05] tracking-[-0.03em] text-white text-balance sm:text-5xl lg:text-[3.65rem]">
            IPGuard{' '}
            <span className="text-ip-teal-300 text-glow-teal">
              System Status
            </span>
          </h1>

          <p className="mt-5 max-w-xl text-sm leading-7 text-slate-400 sm:text-[15px]">
            A live readiness probe of the secure workspace foundation. Verify
            the React client, FastAPI control plane, and PostgreSQL connection
            before the next protection modules are introduced.
          </p>

          <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
            <RefreshButton
              onClick={onRefresh}
              isRefreshing={isRefreshing}
              disabled={isInitialLoading}
              busyLabel={
                isInitialLoading ? 'Checking systems' : 'Refreshing connection'
              }
            />
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Clock3 size={14} strokeWidth={1.8} aria-hidden="true" />
              <span>
                Last checked{' '}
                <span className="font-medium text-slate-300 tabular-nums">
                  {formatClock(snapshot?.checkedAt)}
                </span>
              </span>
            </div>
          </div>

          <div
            className="mt-6 flex flex-wrap items-center gap-3"
            aria-live="polite"
          >
            <StatusBadge status={status} />
            <span className="text-sm text-slate-400">
              {getOverallLabel(status)}
            </span>
          </div>
        </div>

        <div className="relative mx-auto grid aspect-square w-full max-w-[19rem] place-items-center">
          <div
            className={`absolute inset-0 rounded-full border border-dashed animate-orbit ${ringTone[status]}`}
            aria-hidden="true"
          >
            <span className="absolute left-1/2 top-0 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ip-teal-300 shadow-[0_0_14px_rgba(45,212,191,0.9)]" />
          </div>
          <div
            className={`absolute inset-6 rounded-full border animate-orbit-reverse ${ringTone[status]}`}
            aria-hidden="true"
          >
            <span className="absolute bottom-0 left-1/2 size-1.5 -translate-x-1/2 translate-y-1/2 rounded-full bg-ip-gold-400 shadow-[0_0_12px_rgba(231,200,115,0.8)]" />
          </div>
          <div
            className={`absolute inset-12 rounded-full blur-2xl animate-pulse-soft ${orbTone[status]}`}
            aria-hidden="true"
          />

          <div
            className={`relative grid size-36 place-items-center rounded-full border bg-ip-navy-900/80 backdrop-blur-md transition-colors duration-500 ${orbTone[status]}`}
          >
            <ShieldCheck
              size={52}
              strokeWidth={1.35}
              aria-hidden="true"
              className="drop-shadow-[0_0_18px_rgba(45,212,191,0.35)]"
            />
            <span
              className="absolute bottom-6 h-px w-10 bg-current opacity-40"
              aria-hidden="true"
            />
          </div>

          <p className="absolute -bottom-2 rounded-full border border-white/[0.07] bg-ip-navy-950/80 px-4 py-1.5 text-[9px] font-semibold uppercase tracking-[0.22em] text-slate-500 backdrop-blur">
            Secure readiness probe
          </p>
        </div>
      </div>
    </section>
  )
}
