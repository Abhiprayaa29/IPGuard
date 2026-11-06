interface InfoRowProps {
  label: string
  value: string
  mono?: boolean
}

export function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-white/[0.06] py-3 last:border-b-0">
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd
        className={`max-w-[65%] break-all text-right text-xs text-slate-200 ${
          mono ? 'font-mono text-[11px]' : ''
        }`}
      >
        {value}
      </dd>
    </div>
  )
}
