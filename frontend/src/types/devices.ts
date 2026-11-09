export interface Device {
  id: string
  device_id: string
  device_name: string
  model: string
  android_version: string
  public_key_fingerprint: string
  security_level: string
  status: 'ACTIVE' | 'REVOKED' | 'UNREGISTERED' | string
  registration_status?: 'REGISTERED' | 'UNREGISTERED' | string
  access_status?: 'ACTIVE' | 'REVOKED' | string
  enrolled_at: string
  last_used_at: string | null
  revoked_at: string | null
  unregistered_at: string | null
}

export interface DeviceStatusResponse {
  device_id: string
  status: string
  registration_status: string
  access_status: string
  public_key_fingerprint: string | null
  enrolled_at: string | null
}
