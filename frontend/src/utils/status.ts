import type { SystemStatusSnapshot, UiStatus } from '../types/system'

export function getOverallStatus(
  snapshot: SystemStatusSnapshot | undefined,
  isLoading: boolean,
): UiStatus {
  if (isLoading) {
    return 'checking'
  }

  if (!snapshot || snapshot.health.state === 'offline') {
    return 'offline'
  }

  if (snapshot.database.state === 'offline') {
    return 'degraded'
  }

  return 'online'
}

export function getOverallLabel(status: UiStatus): string {
  switch (status) {
    case 'online':
      return 'All core systems operational'
    case 'degraded':
      return 'Database attention required'
    case 'offline':
      return 'Core services unreachable'
    case 'checking':
      return 'Establishing secure connection'
  }
}
