import { apiClient, getApiErrorMessage } from './api'
import type { Device, DeviceStatusResponse } from '../types/devices'
import { getStoredSessionToken } from '../utils/session'

const DEFAULT_DEV_ADMIN_KEY = 'ipguard-dev-admin-secret-key'

function getAuthHeaders(explicitAdminKey?: string): Record<string, string> {
  const headers: Record<string, string> = {}
  const adminKey = explicitAdminKey || localStorage.getItem('ipguard_admin_key') || DEFAULT_DEV_ADMIN_KEY
  if (adminKey) {
    headers['X-Dev-Admin-Key'] = adminKey
  }
  const token = getStoredSessionToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
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
  explicitAdminKey?: string
): Promise<Device> {
  try {
    const response = await apiClient.post<Device>(
      `/auth/devices/${deviceId}/revoke`,
      { reason: reason || 'Revoked via web console' },
      { headers: getAuthHeaders(explicitAdminKey) }
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}

export async function unregisterDevice(
  deviceId: string,
  reason?: string,
  explicitAdminKey?: string
): Promise<Device> {
  try {
    const response = await apiClient.post<Device>(
      `/auth/devices/${deviceId}/unregister`,
      { reason: reason || 'Unregistered via web console' },
      { headers: getAuthHeaders(explicitAdminKey) }
    )
    return response.data
  } catch (error) {
    throw new Error(getApiErrorMessage(error))
  }
}
