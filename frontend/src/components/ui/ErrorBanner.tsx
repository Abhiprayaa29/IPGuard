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
      className="flex gap-3 rounded-lg border border-red-500/35 bg-red-500/10 p-4 text-red-100"
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0 text-red-400" aria-hidden="true" />
      <div className="min-w-0">
        <h2 className="text-xs font-semibold text-red-200">Connection attention required</h2>
        <ul className="mt-1.5 space-y-1 text-xs text-red-200/80">
          {messages.map((message, index) => (
            <li key={`${message}-${index}`}>{message}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}
