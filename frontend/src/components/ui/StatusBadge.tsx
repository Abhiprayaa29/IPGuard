import type { UiStatus } from '../../types/system'

const statusConfig: Record<
  UiStatus,
  { label: string; className: string; dotClassName: string }
> = {
  online: {
    label: 'Online',
    className: 'border-ip-teal-400/25 bg-ip-teal-400/10 text-ip-teal-300',
    dotClassName: 'bg-ip-teal-300',
  },
  offline: {
    label: 'Offline',
    className: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
    dotClassName: 'bg-rose-300',
  },
  degraded: {
    label: 'Degraded',
    className: 'border-ip-gold-400/25 bg-ip-gold-400/10 text-ip-gold-300',
    dotClassName: 'bg-ip-gold-300',
  },
  checking: {
    label: 'Checking',
    className: 'border-slate-400/20 bg-slate-400/10 text-slate-300',
    dotClassName: 'bg-slate-300',
  },
}

interface StatusBadgeProps {
  status: UiStatus
  label?: string
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] ${config.className}`}
    >
      <span className="relative flex size-1.5" aria-hidden="true">
        {status === 'online' || status === 'degraded' ? (
          <span
            className={`absolute inline-flex size-full animate-ping rounded-full opacity-60 ${config.dotClassName}`}
          />
        ) : null}
        <span
          className={`relative inline-flex size-1.5 rounded-full ${config.dotClassName}`}
        />
      </span>
      {label ?? config.label}
    </span>
  )
}
