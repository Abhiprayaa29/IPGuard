import type { Asset } from './assets'

export interface StegoEncodeRequest {
  copyright?: string
  license?: string
  note?: string
}

export interface StegoEncodeResponse {
  derivative: Asset
  watermark_id: string
  format_version: number
  embedded_payload: Record<string, unknown>
}

export interface StegoCapacityInfo {
  asset_id: string
  filename: string
  width: number
  height: number
  mode: string
  total_pixels: number
  total_capacity_bytes: number
  header_overhead_bytes: number
  max_payload_bytes: number
  source_sha256: string
}

export type InspectorStatus =
  | 'VALID'
  | 'INVALID_SIGNATURE'
  | 'CORRUPTED'
  | 'NO_WATERMARK'
  | 'UNKNOWN_SIGNER'
  | 'UNSUPPORTED_VERSION'

export interface WatermarkInspectResponse {
  status: InspectorStatus
  watermark_detected: boolean
  signature_valid: boolean
  framing_valid: boolean
  checksum_valid: boolean
  format: string | null
  version: number | null
  watermark_id: string | null
  asset_reference: string | null
  derivative_asset_id: string | null
  owner_reference: string | null
  created_at: string | null
  source_sha256: string | null
  signature_algorithm: string | null
  signing_key_id: string | null
  inspected_image_sha256: string
  source_digest_matches: boolean | null
  metadata: Record<string, unknown> | null
  raw_payload_preview: string | null
  verified_at: string
  warnings: string[]
  input_mode: 'EXTERNAL_UPLOAD' | 'ASSET_VAULT'
}
