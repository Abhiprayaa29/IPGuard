import { RefreshCw } from 'lucide-react'
import { Button } from './Button'

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
  busyLabel = 'Checking status...',
}: RefreshButtonProps) {
  return (
    <Button
      variant="primary"
      onClick={onClick}
      disabled={disabled}
      loading={isRefreshing}
      iconLeft={<RefreshCw size={14} />}
    >
      {isRefreshing ? busyLabel : 'Refresh status'}
    </Button>
  )
}
