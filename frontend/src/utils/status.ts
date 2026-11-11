import type { SystemStatusSnapshot, UiStatus } from '../types/system'

export function getOverallStatus(
  snapshot: SystemStatusSnapshot | undefined,
  isLoading: boolean,
): UiStatus {
  if (isLoading) {
    return 'checking'
  }

  if (!snapshot) {
    return 'unknown'
  }

  if (snapshot.health.state === 'offline') {
    return 'offline'
  }

  if (snapshot.database.state === 'offline' || snapshot.overview.state === 'offline') {
    return 'degraded'
  }

  return 'online'
}

export function getOverallLabel(status: UiStatus): string {
  switch (status) {
    case 'online':
      return 'Operational'
    case 'degraded':
      return 'Degraded'
    case 'offline':
      return 'Unavailable'
    case 'checking':
      return 'Checking'
    case 'unknown':
    default:
      return 'Unknown'
  }
}
