import type { UiStatus } from '../../types/system'
import { StatusIndicator, type IndicatorTone } from './Feedback'

interface StatusBadgeProps {
  status: UiStatus
  label?: string
}

const labelByStatus: Record<UiStatus, string> = {
  online: 'Operational',
  checking: 'Checking',
  degraded: 'Degraded',
  offline: 'Unavailable',
  unknown: 'Unknown',
}

const toneByStatus: Record<UiStatus, IndicatorTone> = {
  online: 'success',
  checking: 'checking',
  degraded: 'warning',
  offline: 'danger',
  unknown: 'neutral',
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return <StatusIndicator label={label ?? labelByStatus[status]} tone={toneByStatus[status]} />
}
