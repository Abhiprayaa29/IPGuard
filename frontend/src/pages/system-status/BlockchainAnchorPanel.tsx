import { useCallback, useEffect, useState } from 'react'
import {
  CheckCircle2,
  ExternalLink,
  Link2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Panel } from '../../components/ui/DataDisplay'
import { InfoRow } from '../../components/ui/InfoRow'
import {
  fetchBlockchainOverview,
  triggerAuditBatchAnchor,
  verifyBlockchainAnchor,
} from '../../services/blockchain'
import type {
  AnchorVerifyResponse,
  BlockchainOverviewResponse,
} from '../../types/blockchain'
import { getStoredSessionToken } from '../../utils/session'

type VisualState =
  | 'Not Configured'
  | 'Ready to Anchor'
  | 'Anchoring'
  | 'Submitted'
  | 'Confirmed'
  | 'Failed'
  | 'Verification Failed'

function resolveVisualState(
  overview: BlockchainOverviewResponse | null,
  isAnchoring: boolean,
  anchorError: string | null,
  verifyResult: AnchorVerifyResponse | null,
): VisualState {
  if (isAnchoring) return 'Anchoring'
  if (verifyResult && !verifyResult.verified) return 'Verification Failed'
  if (anchorError) return 'Failed'
  if (!overview || !overview.configured || overview.status === 'NOT_CONFIGURED') {
    return 'Not Configured'
  }
  if (overview.status === 'FAILED') return 'Failed'
  if (overview.status === 'SUBMITTED') return 'Submitted'
  if (overview.pending_events > 0 || overview.status === 'READY') {
    return 'Ready to Anchor'
  }
  if (overview.status === 'CONFIRMED' || overview.latest_anchor?.status === 'CONFIRMED') {
    return 'Confirmed'
  }
  return 'Ready to Anchor'
}

const badgeStyles: Record<VisualState, string> = {
  'Not Configured': 'border-zinc-700 bg-zinc-800/70 text-zinc-300',
  'Ready to Anchor': 'border-ip-accent/40 bg-ip-accent/15 text-ip-accent-300',
  Anchoring: 'border-amber-500/40 bg-amber-500/15 text-amber-200',
  Submitted: 'border-amber-500/40 bg-amber-500/15 text-amber-200',
  Confirmed: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-200',
  Failed: 'border-red-500/40 bg-red-500/15 text-red-200',
  'Verification Failed': 'border-red-500/40 bg-red-500/15 text-red-200',
}

export function BlockchainAnchorPanel() {
  const token = getStoredSessionToken()
  const [overview, setOverview] = useState<BlockchainOverviewResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [isAnchoring, setIsAnchoring] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [verifyResult, setVerifyResult] = useState<AnchorVerifyResponse | null>(null)

  const loadOverview = useCallback(async () => {
    if (!token) return
    setLoading(true)
    setErrorMessage(null)
    try {
      const data = await fetchBlockchainOverview(token)
      setOverview(data)
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Unable to fetch blockchain status.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  async function handleAnchorBatch() {
    if (!token) return
    setIsAnchoring(true)
    setErrorMessage(null)
    setVerifyResult(null)
    try {
      await triggerAuditBatchAnchor(token)
      await loadOverview()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Batch anchoring failed.')
      await loadOverview().catch(() => {})
    } finally {
      setIsAnchoring(false)
    }
  }

  async function handleVerifyOnChain() {
    if (!token || !overview?.latest_anchor) return
    setIsVerifying(true)
    setErrorMessage(null)
    try {
      const res = await verifyBlockchainAnchor(overview.latest_anchor.id, token)
      setVerifyResult(res)
      await loadOverview()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'On-chain verification failed.')
    } finally {
      setIsVerifying(false)
    }
  }

  const latest = overview?.latest_anchor ?? null
  const visualState = resolveVisualState(overview, isAnchoring, errorMessage, verifyResult)
  const seqRangeLabel = latest
    ? `${latest.from_sequence}–${latest.to_sequence}`
    : overview && overview.last_anchored_sequence > 0
      ? `1–${overview.last_anchored_sequence}`
      : 'None'

  return (
    <Panel
      title="M5 Blockchain Audit Anchoring"
      description="Keccak-256 Merkle batch commitments anchored from verified PostgreSQL audit_events. Event payloads remain strictly off-chain."
      actions={
        token ? (
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`inline-flex items-center rounded-md border px-2.5 py-1 text-[11px] font-medium ${badgeStyles[visualState]}`}
            >
              {visualState}
            </span>
            <Button
              variant="secondary"
              size="sm"
              loading={isVerifying}
              disabled={!latest || !overview?.configured}
              iconLeft={<ShieldCheck size={14} />}
              onClick={() => {
                void handleVerifyOnChain()
              }}
            >
              Verify On-Chain
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={isAnchoring}
              disabled={
                loading ||
                !overview?.configured ||
                !overview.audit_chain_valid ||
                overview.pending_events <= 0
              }
              iconLeft={<Link2 size={14} />}
              onClick={() => {
                void handleAnchorBatch()
              }}
            >
              Anchor Audit Batch
            </Button>
          </div>
        ) : undefined
      }
    >
      {!token ? (
        <div className="rounded-lg border border-ip-border bg-ip-elevated/60 p-4 text-xs text-zinc-400">
          Sign in with your hardware authenticator to inspect your device audit-chain
          anchoring state, submit Keccak-256 Merkle batches, or verify commitments on-chain.
        </div>
      ) : loading && !overview ? (
        <div className="flex items-center gap-2 py-4 text-xs text-zinc-400">
          <RefreshCw size={14} className="animate-spin" />
          Loading blockchain anchoring posture...
        </div>
      ) : (
        <div className="space-y-4">
          {overview && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-ip-border bg-ip-elevated/50 px-3.5 py-2.5">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold tracking-wider text-ip-accent-300">
                  {overview.network_label}
                </span>
                <span className="text-xs text-zinc-500">
                  ({overview.network} · chainId {overview.chain_id})
                </span>
              </div>
              <span className="font-mono text-xs text-zinc-400">
                Audit Chain: {overview.audit_chain_id} ·{' '}
                <strong
                  className={
                    overview.audit_chain_valid ? 'text-emerald-300' : 'text-red-300'
                  }
                >
                  {overview.audit_chain_valid ? 'VALID' : 'INVALID'}
                </strong>
              </span>
            </div>
          )}

          {overview && !overview.configured && overview.configuration_issues.length > 0 && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
              {overview.configuration_issues.join(' ')}
            </div>
          )}

          {errorMessage && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
              <ShieldAlert size={15} className="mt-0.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {verifyResult && (
            <div
              className={`rounded-lg border p-3 text-xs ${
                verifyResult.verified
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                  : 'border-red-500/40 bg-red-500/10 text-red-200'
              }`}
            >
              <div className="flex items-center gap-2 font-medium">
                {verifyResult.verified ? (
                  <CheckCircle2 size={15} />
                ) : (
                  <ShieldAlert size={15} />
                )}
                <span>
                  On-Chain Verification:{' '}
                  {verifyResult.verified ? 'VERIFIED PASS' : 'VERIFICATION FAILED'}
                </span>
              </div>
              <p className="mt-1 text-[11px] opacity-90">
                DB Record: {verifyResult.checks.db_record_present ? 'OK' : 'FAIL'} · Audit
                Hash Chain: {verifyResult.checks.audit_chain_valid ? 'OK' : 'FAIL'} ·
                Local Merkle Recompute:{' '}
                {verifyResult.checks.local_merkle_recomputed_match ? 'MATCH' : 'MISMATCH'} ·
                Tx Receipt: {verifyResult.checks.tx_receipt_confirmed ? 'OK' : 'FAIL'} ·
                On-Chain Storage:{' '}
                {verifyResult.checks.onchain_contract_match ? 'MATCH' : 'MISMATCH'}
              </p>
              {verifyResult.reason && (
                <p className="mt-1 text-[11px] font-medium">{verifyResult.reason}</p>
              )}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <dl>
              <InfoRow
                label="Contract Address"
                value={overview?.contract_address ?? 'Not Configured'}
                mono
              />
              <InfoRow
                label="Authorized Signer"
                value={overview?.signer_address ?? 'Not Configured'}
                mono
              />
              <InfoRow label="Last Anchored Range" value={seqRangeLabel} mono />
              <InfoRow
                label="Events Anchored"
                value={`${overview?.total_anchored_events ?? 0} (${overview?.anchored_batch_count ?? 0} batch)`}
              />
              <InfoRow
                label="Unanchored Events"
                value={`${overview?.pending_events ?? 0}`}
              />
            </dl>

            <dl>
              <InfoRow
                label="Confirmation Status"
                value={latest ? latest.status : overview?.status ?? 'NONE'}
                mono
              />
              <InfoRow label="Merkle Root" value={latest?.merkle_root ?? '—'} mono />
              <InfoRow
                label="Transaction Hash"
                value={
                  latest?.tx_hash ? (
                    latest.explorer_url ? (
                      <a
                        href={latest.explorer_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-ip-accent-300 underline"
                      >
                        {latest.tx_hash}
                        <ExternalLink size={12} />
                      </a>
                    ) : (
                      latest.tx_hash
                    )
                  ) : (
                    '—'
                  )
                }
                mono
              />
              <InfoRow
                label="Block Number"
                value={latest?.block_number != null ? String(latest.block_number) : '—'}
                mono
              />
              <InfoRow
                label="Last Verification Result"
                value={
                  verifyResult
                    ? verifyResult.verified
                      ? 'PASS (On-Chain & Merkle Match)'
                      : `FAIL (${verifyResult.reason ?? 'Mismatch'})`
                    : 'Not run in this view'
                }
              />
            </dl>
          </div>
        </div>
      )}
    </Panel>
  )
}
