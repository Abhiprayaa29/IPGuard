import type { LucideIcon } from 'lucide-react'
import type { CSSProperties, ReactNode } from 'react'

import type { UiStatus } from '../../types/system'
import { StatusBadge } from './StatusBadge'

interface StatusCardMetric {
  label: string
  value: string
}

interface StatusCardProps {
  icon: LucideIcon
  eyebrow: string
  title: string
  description: string
  status: UiStatus
  statusLabel?: string
  metrics: StatusCardMetric[]
  note?: string | null
  footer?: ReactNode
  style?: CSSProperties
}

export function StatusCard({
  icon: Icon,
  eyebrow,
  title,
  description,
  status,
  statusLabel,
  metrics,
  note,
  footer,
  style,
}: StatusCardProps) {
  return (
    <article
      className="group relative overflow-hidden rounded-[1.75rem] border border-white/[0.08] bg-white/[0.025] p-6 shadow-[0_24px_80px_-48px_rgba(0,0,0,0.9)] backdrop-blur-sm transition duration-300 hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-white/[0.04] motion-reduce:transform-none"
      style={style}
    >
      <div
        className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-ip-teal-300/50 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        aria-hidden="true"
      />

      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl border border-ip-teal-400/20 bg-ip-teal-400/[0.08] text-ip-teal-300">
            <Icon size={20} strokeWidth={1.8} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-500">
              {eyebrow}
            </p>
            <h3 className="mt-1 truncate font-display text-lg font-semibold text-slate-100">
              {title}
            </h3>
          </div>
        </div>
        <StatusBadge status={status} label={statusLabel} />
      </div>

      <p className="mt-5 min-h-10 text-sm leading-6 text-slate-400">
        {description}
      </p>

      <dl className="mt-5 grid grid-cols-2 gap-3 border-t border-white/[0.07] pt-4">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <dt className="text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500">
              {metric.label}
            </dt>
            <dd className="mt-1.5 truncate text-sm font-medium text-slate-200 tabular-nums">
              {metric.value}
            </dd>
          </div>
        ))}
      </dl>

      {note ? (
        <p className="mt-4 rounded-xl border border-rose-400/15 bg-rose-400/[0.06] px-3 py-2 text-xs leading-5 text-rose-200/80">
          {note}
        </p>
      ) : null}

      {footer ? <div className="mt-4">{footer}</div> : null}
    </article>
  )
}
