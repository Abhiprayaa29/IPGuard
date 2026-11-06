import axios from 'axios'

import type { ApiErrorEnvelope } from '../types/system'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
const defaultBaseUrl = 'http://localhost:8000/api/v1'

export const apiBaseUrl = (configuredBaseUrl || defaultBaseUrl).replace(
  /\/+$/,
  '',
)

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 8_000,
  headers: {
    Accept: 'application/json',
  },
})

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorEnvelope>(error)) {
    const serverMessage = error.response?.data?.error?.message
    if (serverMessage) {
      return serverMessage
    }

    if (error.code === 'ECONNABORTED') {
      return 'The request timed out before the service responded.'
    }

    if (!error.response) {
      return 'The service could not be reached.'
    }

    return `The service responded with HTTP ${error.response.status}.`
  }

  return 'An unexpected connection error occurred.'
}
