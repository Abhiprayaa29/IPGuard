import { Clock } from 'lucide-react'

interface QrSessionTimerProps {
  secondsRemaining: number
  totalSeconds?: number
}

export function QrSessionTimer({
  secondsRemaining,
  totalSeconds = 60,
}: QrSessionTimerProps) {
  const percentage = Math.max(0, Math.min(100, (secondsRemaining / totalSeconds) * 100))
  const isLow = secondsRemaining <= 15
  const isVeryLow = secondsRemaining <= 5

  const minutes = Math.floor(secondsRemaining / 60)
  const seconds = secondsRemaining % 60
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`

  const toneClass = isVeryLow
    ? 'text-red-400'
    : isLow
      ? 'text-amber-300'
      : 'text-ip-accent-400'

  const strokeDashoffset = 100 - percentage

  return (
    <div className="flex items-center gap-2.5">
      <div className="relative size-7 shrink-0">
        <svg className="size-full -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-ip-border"
            strokeWidth="3.5"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            className={`${toneClass} transition-all duration-500 ease-linear`}
            strokeDasharray="100, 100"
            strokeDashoffset={strokeDashoffset}
            strokeWidth="3.5"
            strokeLinecap="round"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <span
          className="absolute inset-0 flex items-center justify-center text-zinc-400"
          aria-hidden="true"
        >
          <Clock size={11} className={toneClass} />
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-[11px] font-medium text-zinc-500">
          Expires in
        </span>
        <span
          className={`font-mono text-sm font-semibold tabular-nums ${
            isVeryLow
              ? 'text-red-400'
              : isLow
                ? 'text-amber-300'
                : 'text-zinc-100'
          }`}
        >
          {formattedTime}
        </span>
      </div>
    </div>
  )
}
