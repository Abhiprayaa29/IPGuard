import {
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Info,
  Loader2,
  RefreshCw,
  X,
  AlertTriangle,
} from 'lucide-react'
import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react'

import { Button } from './Button'

export type IndicatorTone = 'success' | 'warning' | 'danger' | 'neutral' | 'accent' | 'checking'

interface StatusIndicatorProps {
  label: string
  tone?: IndicatorTone
  className?: string
}

const toneStyles: Record<IndicatorTone, string> = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  danger: 'border-red-500/30 bg-red-500/10 text-red-300',
  accent: 'border-ip-accent/35 bg-ip-accent/10 text-ip-accent-hover',
  neutral: 'border-ip-border bg-ip-elevated text-zinc-300',
  checking: 'border-ip-border bg-ip-elevated text-zinc-300',
}

export function StatusIndicator({ label, tone = 'neutral', className = '' }: StatusIndicatorProps) {
  const icon = (() => {
    switch (tone) {
      case 'success':
        return <CheckCircle2 size={12} aria-hidden="true" />
      case 'warning':
        return <AlertTriangle size={12} aria-hidden="true" />
      case 'danger':
        return <AlertCircle size={12} aria-hidden="true" />
      case 'checking':
        return <Loader2 size={12} className="animate-spin" aria-hidden="true" />
      case 'accent':
        return <Info size={12} aria-hidden="true" />
      case 'neutral':
      default:
        return <HelpCircle size={12} aria-hidden="true" />
    }
  })()

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${toneStyles[tone]} ${className}`}
    >
      {icon}
      <span>{label}</span>
    </span>
  )
}

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-ip-border bg-ip-surface/60 px-6 py-12 text-center">
      {icon && (
        <div className="mb-3 flex size-10 items-center justify-center rounded-lg border border-ip-border bg-ip-elevated text-zinc-400">
          {icon}
        </div>
      )}
      <h3 className="text-sm font-semibold text-zinc-100">{title}</h3>
      <p className="mt-1 max-w-md text-[13px] text-zinc-400">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex items-center justify-center gap-2.5 rounded-xl border border-ip-border bg-ip-surface px-5 py-12 text-[13px] text-zinc-400">
      <Loader2 size={16} className="animate-spin text-ip-accent" aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}

interface ErrorStateProps {
  message: string
  onRetry?: () => void
  onDismiss?: () => void
}

export function ErrorState({ message, onRetry, onDismiss }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-500/35 bg-red-500/10 px-4 py-3 text-[13px] text-red-200"
    >
      <div className="flex items-center gap-2.5">
        <AlertCircle size={16} className="shrink-0 text-red-400" aria-hidden="true" />
        <span>{message}</span>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <Button size="sm" variant="danger" onClick={onRetry} iconLeft={<RefreshCw size={12} />}>
            Retry
          </Button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            aria-label="Dismiss error"
            className="rounded p-1 text-red-300 hover:bg-red-500/20"
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  )
}

interface ToastItem {
  id: number
  title: string
  tone: 'success' | 'danger' | 'info'
}

interface ToastContextValue {
  pushToast: (title: string, tone?: 'success' | 'danger' | 'info') => void
}

const ToastContext = createContext<ToastContextValue>({
  pushToast: () => {},
})

export function useToast() {
  return useContext(ToastContext)
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const pushToast = useCallback(
    (title: string, tone: 'success' | 'danger' | 'info' = 'info') => {
      const id = Date.now() + Math.floor(Math.random() * 1000)
      setToasts((prev) => [...prev, { id, title, tone }])
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, 3600)
    },
    [],
  )

  return (
    <ToastContext.Provider value={{ pushToast }}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-xs flex-col gap-2"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center justify-between gap-3 rounded-lg border px-3.5 py-2.5 text-xs shadow-lg animate-fade-in ${
              toast.tone === 'success'
                ? 'border-emerald-500/35 bg-ip-surface text-emerald-200'
                : toast.tone === 'danger'
                  ? 'border-red-500/35 bg-ip-surface text-red-200'
                  : 'border-ip-border bg-ip-surface text-zinc-200'
            }`}
          >
            <span>{toast.title}</span>
            <button
              type="button"
              onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
              aria-label="Close notification"
              className="text-zinc-400 hover:text-zinc-100"
            >
              <X size={13} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
