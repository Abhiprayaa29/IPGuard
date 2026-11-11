import type { LucideIcon } from 'lucide-react'
import type { CSSProperties } from 'react'
import type { UiStatus } from '../../types/system'
import { InfoRow } from './InfoRow'
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
  metrics: StatusCardMetric[]
  note?: string | null
  style?: CSSProperties
}

export function StatusCard({
  icon: Icon,
  eyebrow,
  title,
  description,
  status,
  metrics,
  note,
  style,
}: StatusCardProps) {
  return (
    <article
      style={style}
      className="flex flex-col justify-between rounded-xl border border-ip-border bg-ip-surface p-5"
    >
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex size-8 items-center justify-center rounded-lg border border-ip-border bg-ip-elevated text-zinc-300">
              <Icon size={16} aria-hidden="true" />
            </span>
            <div>
              <p className="text-[11px] font-medium text-zinc-500">{eyebrow}</p>
              <h3 className="text-sm font-semibold text-zinc-100">{title}</h3>
            </div>
          </div>
          <StatusBadge status={status} />
        </div>
        <p className="mt-3 text-xs leading-5 text-zinc-400">{description}</p>
        {note && (
          <p className="mt-2.5 rounded-md border border-red-500/30 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-200">
            {note}
          </p>
        )}
      </div>

      <dl className="mt-4 border-t border-ip-border pt-2">
        {metrics.map((m) => (
          <InfoRow key={m.label} label={m.label} value={m.value} mono />
        ))}
      </dl>
    </article>
  )
}
