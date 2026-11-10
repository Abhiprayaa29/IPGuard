export interface Asset {
  id: string
  original_filename: string
  content_type: string | null
  size_bytes: number
  sha256_hash: string
  encryption_version: string
  source_asset_id?: string | null
  derivative_type?: string | null
  watermark_id?: string | null
  stego_format_version?: number | null
  created_at: string
  updated_at: string
  encryption_status: string
}

export interface AssetRenameRequest {
  filename: string
}

export interface StegoEmbedRequest {
  payload_b64: string
}

export interface StegoEmbedResponse {
  derivative: Asset
  watermark_id: string
  format_version: number
}

export interface WatermarkVerifyResponse {
  verified: boolean
  status: string
  watermark_id: string | null
  source_asset_id: string | null
  derivative_asset_id: string | null
  format_version: number | null
}

export interface WatermarkExtractResponse extends WatermarkVerifyResponse {
  payload_b64: string
}

export interface WatermarkPayloadData {
  owner_id?: string
  copyright?: string
  license?: string
  text?: string
  description?: string
  timestamp?: string
  custom?: Record<string, unknown>
}
