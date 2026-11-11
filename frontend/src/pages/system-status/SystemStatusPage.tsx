import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { useSystemStatus } from '../../hooks/useSystemStatus'
import { getApiErrorMessage } from '../../services/api'
import { getOverallStatus } from '../../utils/status'
import { EnvironmentPanel } from './EnvironmentPanel'
import { BlockchainAnchorPanel } from './BlockchainAnchorPanel'
import { ReadinessHero } from './ReadinessHero'
import { ServiceOverview } from './ServiceOverview'

export function SystemStatusPage() {
  const { data, error, isError, isFetching, isPending, refetch } =
    useSystemStatus()

  const overallStatus = getOverallStatus(data, isPending)
  const messages: string[] = []

  if (isError) {
    messages.push(getApiErrorMessage(error))
  } else if (data) {
    if (data.health.state === 'offline') {
      messages.push(
        `Backend API — ${data.health.error ?? 'The API is unreachable.'}`,
      )
    } else {
      if (data.database.state === 'offline') {
        messages.push(
          `PostgreSQL — ${
            data.database.error ?? 'The database is unavailable.'
          }`,
        )
      }
      if (data.overview.state === 'offline') {
        messages.push(
          `System overview — ${
            data.overview.error ?? 'Overview endpoint failed.'
          }`,
        )
      }
      if (data.systemInfo.state === 'offline') {
        messages.push(
          `System metadata — ${
            data.systemInfo.error ?? 'Metadata could not be loaded.'
          }`,
        )
      }
    }
  }

  return (
    <div className="space-y-6">
      <ReadinessHero
        status={overallStatus}
        snapshot={data}
        isRefreshing={isFetching}
        isInitialLoading={isPending}
        onRefresh={() => {
          void refetch()
        }}
      />

      <ErrorBanner messages={messages} />

      <ServiceOverview snapshot={data} isLoading={isPending} />

      <BlockchainAnchorPanel />

      <EnvironmentPanel snapshot={data} isLoading={isPending} />
    </div>
  )
}
