import { AlertTriangle } from 'lucide-react'

interface ErrorBannerProps {
  messages: string[]
}

export function ErrorBanner({ messages }: ErrorBannerProps) {
  if (messages.length === 0) {
    return null
  }

  return (
    <section
      role="alert"
      className="flex gap-4 rounded-2xl border border-rose-400/20 bg-rose-400/[0.06] p-5 text-rose-100 animate-fade-up"
    >
      <span className="grid size-10 shrink-0 place-items-center rounded-xl border border-rose-400/20 bg-rose-400/10 text-rose-300">
        <AlertTriangle size={18} strokeWidth={1.9} aria-hidden="true" />
      </span>
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-rose-100">
          Connection attention required
        </h2>
        <ul className="mt-2 space-y-1.5 text-xs leading-5 text-rose-100/70">
          {messages.map((message, index) => (
            <li key={`${message}-${index}`}>{message}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}
