import type { ReactNode } from 'react'

interface InfoRowProps {
  label: string
  value: ReactNode
  mono?: boolean
}

export function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-ip-border py-2.5 last:border-b-0">
      <dt className="text-xs text-zinc-400">{label}</dt>
      <dd
        className={`min-w-0 truncate text-right text-[13px] font-medium text-zinc-100 ${
          mono ? 'font-mono text-xs tabular-nums' : ''
        }`}
      >
        {value}
      </dd>
    </div>
  )
}
