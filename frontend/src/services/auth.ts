import { apiClient, getApiErrorMessage } from './api'
import type {
  SessionCreateResponse,
  SessionStatusResponse,
  SessionType,
} from '../types/auth'

export async function createAuthSession(
  sessionType: SessionType = 'AUTHENTICATION',
  origin?: string,
): Promise<SessionCreateResponse> {
  try {
    const payload: { session_type: SessionType; origin?: string } = {
      session_type: sessionType,
    }
    if (origin) {
      payload.origin = origin
    }

    const response = await apiClient.post<SessionCreateResponse>(
      '/auth/sessions',
      payload,
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function pollAuthSessionStatus(
  sessionToken: string,
  browserChannelToken: string,
): Promise<SessionStatusResponse> {
  try {
    const response = await apiClient.get<SessionStatusResponse>(
      `/auth/sessions/${sessionToken}`,
      {
        headers: {
          'X-Browser-Channel-Token': browserChannelToken,
        },
      },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
