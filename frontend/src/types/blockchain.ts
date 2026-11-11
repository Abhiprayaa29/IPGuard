export interface BlockchainAnchorRecord {
  id: string
  audit_chain_id: string
  from_sequence: number
  to_sequence: number
  event_count: number
  merkle_root: string
  head_hash: string
  batch_reference: string
  network: string
  chain_id: number
  contract_address: string
  signer_address: string | null
  tx_hash: string | null
  block_number: number | null
  block_timestamp: string | null
  status: 'PENDING' | 'SUBMITTED' | 'CONFIRMED' | 'FAILED' | 'REORGED' | string
  explorer_url: string | null
  created_at: string
  confirmed_at: string | null
  error_message: string | null
}

export interface BlockchainOverviewResponse {
  configured: boolean
  network: string
  network_label: string
  chain_id: number
  contract_address: string | null
  signer_address: string | null
  audit_chain_id: string
  audit_chain_valid: boolean
  audit_chain_reason: string | null
  anchored_batch_count: number
  total_anchored_events: number
  pending_events: number
  last_anchored_sequence: number
  latest_anchor: BlockchainAnchorRecord | null
  recent_anchors: BlockchainAnchorRecord[]
  status:
    | 'NOT_CONFIGURED'
    | 'INVALID_AUDIT_CHAIN'
    | 'READY'
    | 'UP_TO_DATE'
    | 'SUBMITTED'
    | 'CONFIRMED'
    | 'FAILED'
    | string
  configuration_issues: string[]
}

export interface AnchorVerificationChecks {
  db_record_present: boolean
  audit_chain_valid: boolean
  local_merkle_recomputed_match: boolean
  tx_receipt_confirmed: boolean
  onchain_contract_match: boolean
  reorg_check_passed: boolean
}

export interface AnchorVerifyResponse {
  anchor_id: string
  verified: boolean
  status: string
  audit_chain_id: string
  from_sequence: number
  to_sequence: number
  event_count: number
  merkle_root: string
  head_hash: string
  network: string
  network_label: string
  chain_id: number
  contract_address: string
  tx_hash: string | null
  block_number: number | null
  explorer_url: string | null
  checks: AnchorVerificationChecks
  reason: string | null
}
