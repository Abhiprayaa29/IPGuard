export interface Asset {
  id: string
  original_filename: string
  content_type: string | null
  size_bytes: number
  sha256_hash: string
  encryption_version: string
  created_at: string
  updated_at: string
  encryption_status: string
}

export interface AssetRenameRequest {
  filename: string
}
