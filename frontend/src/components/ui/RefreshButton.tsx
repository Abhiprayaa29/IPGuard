import { RefreshCw } from 'lucide-react'

interface RefreshButtonProps {
  onClick: () => void
  isRefreshing: boolean
  disabled?: boolean
  busyLabel?: string
}

export function RefreshButton({
  onClick,
  isRefreshing,
  disabled = false,
  busyLabel = 'Refreshing connection',
}: RefreshButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || isRefreshing}
      aria-busy={isRefreshing}
      className="group inline-flex items-center justify-center gap-2.5 rounded-full bg-ip-teal-400 px-5 py-3 text-sm font-semibold text-ip-navy-950 shadow-[0_12px_36px_-12px_rgba(45,212,191,0.7)] transition duration-200 hover:bg-ip-teal-300 hover:shadow-[0_16px_44px_-12px_rgba(45,212,191,0.8)] disabled:cursor-not-allowed disabled:opacity-60"
    >
      <RefreshCw
        size={16}
        strokeWidth={2.2}
        aria-hidden="true"
        className={isRefreshing ? 'animate-spin' : 'transition group-hover:rotate-45'}
      />
      {isRefreshing ? busyLabel : 'Refresh connection'}
    </button>
  )
}
