import { apiClient, getApiErrorMessage } from './api'
import type {
  Device,
  DeviceLifecycleSummary,
  DeviceStatusResponse,
} from '../types/devices'
import { getStoredSessionToken } from '../utils/session'

function getAuthHeaders(explicitAdminKey?: string): Record<string, string> {
  const headers: Record<string, string> = {}
  const adminKey =
    explicitAdminKey || localStorage.getItem('ipguard_admin_key') || undefined
  if (adminKey) {
    headers['X-Dev-Admin-Key'] = adminKey
  }
  const token = getStoredSessionToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function getDeviceLifecycleSummary(
  accountId?: string,
  explicitAdminKey?: string,
): Promise<DeviceLifecycleSummary> {
  try {
    const response = await apiClient.get<DeviceLifecycleSummary>('/auth/devices/summary', {
      params: accountId ? { account_id: accountId } : undefined,
      headers: getAuthHeaders(explicitAdminKey),
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function listDevices(explicitAdminKey?: string): Promise<Device[]> {
  try {
    const response = await apiClient.get<Device[]>('/auth/devices', {
      headers: getAuthHeaders(explicitAdminKey),
    })
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function getDeviceStatus(deviceId: string): Promise<DeviceStatusResponse> {
  try {
    const response = await apiClient.get<DeviceStatusResponse>(`/auth/devices/${deviceId}/status`)
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function revokeDevice(
  deviceId: string,
  reason?: string,
  explicitAdminKey?: string,
): Promise<Device> {
  try {
    const response = await apiClient.post<Device>(
      `/auth/devices/${deviceId}/revoke`,
      { reason: reason || 'Revoked via web console' },
      { headers: getAuthHeaders(explicitAdminKey) },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function restoreDevice(
  deviceId: string,
  reason?: string,
  recoveryKey?: string,
): Promise<Device> {
  try {
    const resolvedRecoveryKey =
      recoveryKey?.trim() || localStorage.getItem('ipguard_recovery_key')?.trim()
    if (!resolvedRecoveryKey) {
      throw new Error('Account recovery authorization key is required.')
    }
    const headers: Record<string, string> = {
      'X-Account-Recovery-Key': resolvedRecoveryKey,
    }

    const response = await apiClient.post<Device>(
      `/auth/devices/${deviceId}/restore`,
      { reason: reason || 'Restored via web console recovery authorization' },
      { headers },
    )
    return response.data
  } catch (error) {
    if (error instanceof Error && error.message === 'Account recovery authorization key is required.') {
      throw error
    }
    throw new Error(getApiErrorMessage(error))
  }
}

export async function unregisterDevice(
  deviceId: string,
  reason?: string,
  explicitAdminKey?: string,
): Promise<Device> {
  try {
    const response = await apiClient.post<Device>(
      `/auth/devices/${deviceId}/unregister`,
      { reason: reason || 'Unregistered via web console' },
      { headers: getAuthHeaders(explicitAdminKey) },
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
