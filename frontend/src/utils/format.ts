export function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'Not available'
  }

  if (value < 1) {
    return '<1 ms'
  }

  return `${Math.round(value)} ms`
}

export function formatClock(value: string | null | undefined): string {
  if (!value) {
    return 'Not checked yet'
  }

  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(value))
}

export function formatBytes(bytes: number): string {
  if (bytes <= 0 || isNaN(bytes)) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1)
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}
