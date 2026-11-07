export type SessionType = 'AUTHENTICATION' | 'ENROLLMENT'

export type AuthStatus =
  | 'INITIAL'
  | 'CREATING'
  | 'READY'
  | 'SCANNED'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'ERROR'

export interface QRPayload {
  version: string
  type: SessionType
  session_token: string
  nonce: string
  origin: string
  timestamp: number
}

export interface SessionCreateResponse {
  session_token: string
  challenge_nonce: string
  session_type: SessionType
  status: string
  client_origin: string
  qr_payload: QRPayload
  created_at: string
  expires_at: string
  poll_interval_ms: number
  browser_channel_token: string
}

export interface DeviceSummary {
  device_id: string
  device_name: string
  model: string
  android_version: string
  public_key_fingerprint: string
  security_level: string
}

export interface SessionStatusResponse {
  session_token: string
  session_type: SessionType
  status: 'PENDING' | 'SCANNED' | 'APPROVED' | 'REJECTED' | 'EXPIRED'
  expires_at: string
  device?: DeviceSummary | null
  access_token?: string | null
}
