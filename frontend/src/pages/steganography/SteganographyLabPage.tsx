import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSearch,
  FolderLock,
  Image as ImageIcon,
  Info,
  KeyRound,
  Layers,
  Lock,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Upload,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { downloadAsset, getAssets } from '../../services/assets'
import {
  encodeCanonicalWatermark,
  getAssetStegoCapacity,
  inspectExternalPng,
  inspectVaultAssetPng,
} from '../../services/steganography'
import type { Asset } from '../../types/assets'
import type {
  InspectorStatus,
  StegoCapacityInfo,
  StegoEncodeResponse,
  WatermarkInspectResponse,
} from '../../types/steganography'
import { formatBytes } from '../../utils/format'
import {
  clearStoredSessionToken,
  getStoredSessionToken,
  saveSessionToken,
} from '../../utils/session'

type LabMode = 'encode' | 'inspect'
type InspectInputMode = 'external' | 'vault'

function getStatusBannerStyle(status: InspectorStatus) {
  switch (status) {
    case 'VALID':
      return {
        border: 'border-emerald-400/35',
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-300',
        badge: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/30',
        title: 'Valid IPGuard Watermark Verified',
        description:
          'LSB packet framing, payload SHA-256 checksum, and Ed25519 digital signature all passed cryptographic verification.',
        icon: <ShieldCheck size={22} className="text-emerald-300" />,
      }
    case 'INVALID_SIGNATURE':
      return {
        border: 'border-rose-400/40',
        bg: 'bg-rose-500/10',
        text: 'text-rose-300',
        badge: 'bg-rose-500/20 text-rose-200 border-rose-400/30',
        title: 'Invalid Digital Signature',
        description:
          'An IPGuard packet header was found, but Ed25519 signature verification failed. Do NOT trust this payload.',
        icon: <ShieldAlert size={22} className="text-rose-300" />,
      }
    case 'CORRUPTED':
      return {
        border: 'border-rose-400/35',
        bg: 'bg-rose-500/10',
        text: 'text-rose-300',
        badge: 'bg-rose-500/20 text-rose-200 border-rose-400/30',
        title: 'Corrupted or Truncated Watermark',
        description:
          'IPGuard marker was detected, but framing, length, or payload checksum integrity failed (likely modified or cropped).',
        icon: <AlertCircle size={22} className="text-rose-300" />,
      }
    case 'UNKNOWN_SIGNER':
      return {
        border: 'border-amber-400/35',
        bg: 'bg-amber-500/10',
        text: 'text-amber-300',
        badge: 'bg-amber-500/20 text-amber-200 border-amber-400/30',
        title: 'Unknown Signing Key ID',
        description:
          'Watermark structure is intact, but the embedded signing key ID is not configured in this instance’s trusted public key store.',
        icon: <KeyRound size={22} className="text-amber-300" />,
      }
    case 'UNSUPPORTED_VERSION':
      return {
        border: 'border-amber-400/35',
        bg: 'bg-amber-500/10',
        text: 'text-amber-300',
        badge: 'bg-amber-500/20 text-amber-200 border-amber-400/30',
        title: 'Unsupported Watermark Version',
        description:
          'The PNG contains an IPGuard marker with an unsupported format version.',
        icon: <AlertTriangle size={22} className="text-amber-300" />,
      }
    case 'NO_WATERMARK':
    default:
      return {
        border: 'border-slate-500/30',
        bg: 'bg-slate-800/40',
        text: 'text-slate-300',
        badge: 'bg-slate-700/60 text-slate-300 border-slate-500/30',
        title: 'No IPGuard Watermark Detected',
        description:
          'No IPGuard RGB LSB magic header was found in this PNG image.',
        icon: <FileSearch size={22} className="text-slate-400" />,
      }
  }
}

export function SteganographyLabPage() {
  const location = useLocation()
  const navigate = useNavigate()

  const [token, setToken] = useState<string | null>(() => {
    const passedToken = (location.state as { token?: string })?.token
    if (passedToken) {
      saveSessionToken(passedToken)
      return passedToken
    }
    return getStoredSessionToken()
  })

  const [mode, setMode] = useState<LabMode>('encode')
  const [assets, setAssets] = useState<Asset[]>([])
  const [loadingAssets, setLoadingAssets] = useState(false)
  const [globalError, setGlobalError] = useState<string | null>(null)

  // Encode Mode State
  const [selectedSourceId, setSelectedSourceId] = useState<string>('')
  const [sourceCapacity, setSourceCapacity] = useState<StegoCapacityInfo | null>(null)
  const [loadingCapacity, setLoadingCapacity] = useState(false)
  const [sourcePreviewUrl, setSourcePreviewUrl] = useState<string | null>(null)
  const [copyrightInput, setCopyrightInput] = useState('')
  const [licenseInput, setLicenseInput] = useState('Proprietary')
  const [noteInput, setNoteInput] = useState('')
  const [isEncoding, setIsEncoding] = useState(false)
  const [encodeError, setEncodeError] = useState<string | null>(null)
  const [encodeResult, setEncodeResult] = useState<StegoEncodeResponse | null>(null)
  const [downloadingDerivative, setDownloadingDerivative] = useState(false)

  // Inspect Mode State
  const [inspectInputMode, setInspectInputMode] = useState<InspectInputMode>('external')
  const [externalFile, setExternalFile] = useState<File | null>(null)
  const [externalPreviewUrl, setExternalPreviewUrl] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [selectedInspectAssetId, setSelectedInspectAssetId] = useState<string>('')
  const [vaultInspectPreviewUrl, setVaultInspectPreviewUrl] = useState<string | null>(null)
  const [expectedSourceSha256, setExpectedSourceSha256] = useState('')
  const [isInspecting, setIsInspecting] = useState(false)
  const [inspectError, setInspectError] = useState<string | null>(null)
  const [inspectResult, setInspectResult] = useState<WatermarkInspectResponse | null>(null)

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const pngAssets = useMemo(
    () => assets.filter((a) => a.content_type === 'image/png'),
    [assets],
  )
  const sourceCandidates = useMemo(
    () => pngAssets.filter((a) => a.derivative_type !== 'PNG_LSB'),
    [pngAssets],
  )

  const handleAuthError = useCallback(
    (errMsg: string) => {
      if (
        errMsg.toLowerCase().includes('session') ||
        errMsg.toLowerCase().includes('unauthorized') ||
        errMsg.toLowerCase().includes('token') ||
        errMsg.toLowerCase().includes('revoked')
      ) {
        clearStoredSessionToken()
        setToken(null)
      }
      setGlobalError(errMsg)
    },
    [],
  )

  const fetchVaultAssets = useCallback(async () => {
    if (!token) return
    setLoadingAssets(true)
    setGlobalError(null)
    try {
      const list = await getAssets(token)
      setAssets(list)
    } catch (err) {
      handleAuthError(err instanceof Error ? err.message : 'Failed to load Asset Vault')
    } finally {
      setLoadingAssets(false)
    }
  }, [token, handleAuthError])

  useEffect(() => {
    fetchVaultAssets()
  }, [fetchVaultAssets])

  // Revoke object URLs on unmount or change
  useEffect(() => {
    return () => {
      if (sourcePreviewUrl) URL.revokeObjectURL(sourcePreviewUrl)
    }
  }, [sourcePreviewUrl])

  useEffect(() => {
    return () => {
      if (externalPreviewUrl) URL.revokeObjectURL(externalPreviewUrl)
    }
  }, [externalPreviewUrl])

  useEffect(() => {
    return () => {
      if (vaultInspectPreviewUrl) URL.revokeObjectURL(vaultInspectPreviewUrl)
    }
  }, [vaultInspectPreviewUrl])

  // Load capacity and decrypted preview when source PNG changes
  useEffect(() => {
    if (!token || !selectedSourceId) {
      setSourceCapacity(null)
      setSourcePreviewUrl(null)
      return
    }
    let cancelled = false
    setLoadingCapacity(true)
    setEncodeError(null)

    Promise.resolve()
      .then(async () => {
        const cap = await getAssetStegoCapacity(token, selectedSourceId)
        if (cancelled) return
        setSourceCapacity(cap)
        const blob = await downloadAsset(token, selectedSourceId)
        if (cancelled) return
        const nextUrl = URL.createObjectURL(blob)
        setSourcePreviewUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return nextUrl
        })
      })
      .catch((err) => {
        if (cancelled) return
        setEncodeError(err instanceof Error ? err.message : 'Failed to inspect source PNG')
        setSourceCapacity(null)
      })
      .finally(() => {
        if (!cancelled) setLoadingCapacity(false)
      })

    return () => {
      cancelled = true
    }
  }, [token, selectedSourceId])

  // Load decrypted preview when Asset Vault inspect selection changes
  useEffect(() => {
    if (!token || inspectInputMode !== 'vault' || !selectedInspectAssetId) {
      setVaultInspectPreviewUrl(null)
      return
    }
    let cancelled = false
    downloadAsset(token, selectedInspectAssetId)
      .then((blob) => {
        if (cancelled) return
        const nextUrl = URL.createObjectURL(blob)
        setVaultInspectPreviewUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return nextUrl
        })
      })
      .catch(() => {
        if (!cancelled) setVaultInspectPreviewUrl(null)
      })
    return () => {
      cancelled = true
    }
  }, [token, inspectInputMode, selectedInspectAssetId])

  const handleEncodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedSourceId) return
    setIsEncoding(true)
    setEncodeError(null)
    setEncodeResult(null)
    try {
      const response = await encodeCanonicalWatermark(token, selectedSourceId, {
        copyright: copyrightInput || undefined,
        license: licenseInput || undefined,
        note: noteInput || undefined,
      })
      setEncodeResult(response)
      await fetchVaultAssets()
    } catch (err) {
      setEncodeError(err instanceof Error ? err.message : 'Watermark encoding failed')
    } finally {
      setIsEncoding(false)
    }
  }

  const handleDownloadDerivative = async (asset: Asset) => {
    if (!token) return
    setDownloadingDerivative(true)
    try {
      const blob = await downloadAsset(token, asset.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = asset.original_filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      setEncodeError(err instanceof Error ? err.message : 'Failed to download derived asset')
    } finally {
      setDownloadingDerivative(false)
    }
  }

  const handleInspectDerivativeImmediately = async (derivative: Asset) => {
    if (!token) return
    setMode('inspect')
    setInspectInputMode('vault')
    setSelectedInspectAssetId('')
    setInspectResult(null)
    setInspectError(null)
    setIsInspecting(true)
    try {
      const res = await inspectVaultAssetPng(token, derivative.id, expectedSourceSha256 || undefined)
      setInspectResult(res)
      setSelectedInspectAssetId(derivative.id)
    } catch (err) {
      setInspectError(err instanceof Error ? err.message : 'Inspection failed')
    } finally {
      setIsInspecting(false)
    }
  }

  const handleSelectExternalFile = (file: File | undefined | null) => {
    if (!file) return
    setInspectResult(null)
    setInspectError(null)
    setExternalFile(file)
    const nextUrl = URL.createObjectURL(file)
    setExternalPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return nextUrl
    })
  }

  const handleRunInspect = async () => {
    if (!token) return
    setInspectError(null)
    setInspectResult(null)
    setIsInspecting(true)
    try {
      if (inspectInputMode === 'external') {
        if (!externalFile) {
          setInspectError('Please choose a PNG file to inspect.')
          return
        }
        const res = await inspectExternalPng(
          token,
          externalFile,
          expectedSourceSha256 || undefined,
        )
        setInspectResult(res)
      } else {
        if (!selectedInspectAssetId) {
          setInspectError('Please select a PNG asset from your Asset Vault.')
          return
        }
        const res = await inspectVaultAssetPng(
          token,
          selectedInspectAssetId,
          expectedSourceSha256 || undefined,
        )
        setInspectResult(res)
      }
    } catch (err) {
      setInspectError(err instanceof Error ? err.message : 'Watermark inspection failed')
    } finally {
      setIsInspecting(false)
    }
  }

  const handleResetInspect = () => {
    setExternalFile(null)
    setExternalPreviewUrl(null)
    setSelectedInspectAssetId('')
    setVaultInspectPreviewUrl(null)
    setExpectedSourceSha256('')
    setInspectError(null)
    setInspectResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSignOut = () => {
    clearStoredSessionToken()
    setToken(null)
    navigate('/login')
  }

  // Unauthenticated Guard
  if (!token) {
    return (
      <div className="mx-auto max-w-lg py-12 text-center">
        <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/60 p-8 backdrop-blur-xl shadow-2xl">
          <div className="mx-auto mb-5 grid size-16 place-items-center rounded-2xl border border-ip-teal-400/20 bg-ip-teal-400/10 text-ip-teal-300">
            <Lock size={28} />
          </div>
          <h1 className="font-display text-2xl font-bold text-white">
            Steganography Lab Locked
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Sign in with your enrolled IPGuard hardware authenticator to encode or inspect PNG LSB watermarks.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-ip-teal-500 px-6 py-3 text-sm font-semibold text-ip-navy-950 transition hover:bg-ip-teal-400"
          >
            Authorize via QR Sign-In
          </Link>
        </div>
      </div>
    )
  }

  const statusStyle = inspectResult ? getStatusBannerStyle(inspectResult.status) : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-purple-400/25 bg-purple-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-purple-300">
            <Sparkles size={12} />
            Milestone 4 • LSB Watermarking &amp; Inspector
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-white">
            IPGuard Steganography Lab
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Embed Ed25519-signed canonical watermarks into encrypted Asset Vault PNGs or verify any external PNG read-only.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={fetchVaultAssets}
            disabled={loadingAssets}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/10 disabled:opacity-50"
          >
            <RefreshCw size={14} className={loadingAssets ? 'animate-spin' : ''} />
            Refresh Vault
          </button>
          <button
            type="button"
            onClick={handleSignOut}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-300 transition hover:bg-rose-500/10 hover:text-rose-300"
          >
            Sign Out
          </button>
        </div>
      </div>

      {globalError && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          <AlertCircle size={18} className="shrink-0 text-rose-400" />
          <span>{globalError}</span>
        </div>
      )}

      {/* Primary Mode Switcher */}
      <div className="inline-flex rounded-2xl border border-white/[0.08] bg-ip-navy-900/70 p-1.5 backdrop-blur-md">
        <button
          type="button"
          onClick={() => setMode('encode')}
          className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
            mode === 'encode'
              ? 'bg-ip-teal-500 text-ip-navy-950 shadow-lg'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          <Layers size={16} />
          Encode Watermark
        </button>
        <button
          type="button"
          onClick={() => setMode('inspect')}
          className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition ${
            mode === 'inspect'
              ? 'bg-ip-teal-500 text-ip-navy-950 shadow-lg'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          <FileSearch size={16} />
          Decode / Inspect Watermark
        </button>
      </div>

      {/* MODE 1: ENCODE WATERMARK */}
      {mode === 'encode' && (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Source PNG Picker & Capacity Card */}
          <div className="space-y-5 lg:col-span-5">
            <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-6 backdrop-blur-xl">
              <h2 className="flex items-center gap-2 font-display text-base font-semibold text-white">
                <FolderLock size={18} className="text-ip-teal-400" />
                1. Select Source PNG from Asset Vault
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Only 8-bit RGB/RGBA PNGs stored in your Vault can carry LSB watermarks. Your original asset remains untouched.
              </p>

              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-medium text-slate-300">
                  Source PNG Asset
                </label>
                <select
                  value={selectedSourceId}
                  onChange={(e) => {
                    setSelectedSourceId(e.target.value)
                    setEncodeResult(null)
                    setEncodeError(null)
                  }}
                  className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2.5 text-sm text-white focus:border-ip-teal-400 focus:outline-none"
                >
                  <option value="">-- Choose a PNG asset ({sourceCandidates.length} available) --</option>
                  {sourceCandidates.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.original_filename} ({formatBytes(asset.size_bytes)})
                    </option>
                  ))}
                </select>
              </div>

              {sourceCandidates.length === 0 && !loadingAssets && (
                <div className="mt-4 rounded-xl border border-amber-400/20 bg-amber-500/5 p-3.5 text-xs text-amber-200">
                  No source PNG images found in your Asset Vault.{' '}
                  <Link to="/assets" className="font-semibold underline hover:text-white">
                    Upload a PNG in Asset Vault
                  </Link>{' '}
                  first.
                </div>
              )}

              {loadingCapacity && (
                <div className="mt-5 flex items-center gap-2 text-xs text-slate-400">
                  <RefreshCw size={14} className="animate-spin text-ip-teal-400" />
                  Decrypting in memory &amp; calculating RGB LSB capacity...
                </div>
              )}

              {sourcePreviewUrl && (
                <div className="mt-5 overflow-hidden rounded-2xl border border-white/10 bg-ip-navy-950/70 p-3">
                  <img
                    src={sourcePreviewUrl}
                    alt="Decrypted source PNG preview"
                    className="mx-auto max-h-56 rounded-xl object-contain"
                  />
                </div>
              )}

              {sourceCapacity && (
                <div className="mt-4 space-y-2 rounded-2xl border border-white/[0.07] bg-ip-navy-950/60 p-4 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Dimensions / Mode</span>
                    <span className="font-mono text-white">
                      {sourceCapacity.width} × {sourceCapacity.height} ({sourceCapacity.mode})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Raw RGB LSB Capacity</span>
                    <span className="font-mono text-ip-teal-300">
                      {formatBytes(sourceCapacity.total_capacity_bytes)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">IPGW Header Overhead</span>
                    <span className="font-mono text-slate-300">
                      {sourceCapacity.header_overhead_bytes} bytes
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-white/10 pt-2">
                    <span className="font-semibold text-slate-300">Usable Payload Limit</span>
                    <span className="font-mono font-semibold text-emerald-300">
                      {formatBytes(sourceCapacity.max_payload_bytes)}
                    </span>
                  </div>
                  <div className="pt-1">
                    <span className="block text-[10px] uppercase tracking-wider text-slate-500">
                      Source Plaintext SHA-256
                    </span>
                    <span className="block break-all font-mono text-[11px] text-slate-300">
                      {sourceCapacity.source_sha256}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Watermark Metadata Form & Encryption Output */}
          <div className="space-y-5 lg:col-span-7">
            <form
              onSubmit={handleEncodeSubmit}
              className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-6 backdrop-blur-xl"
            >
              <h2 className="flex items-center gap-2 font-display text-base font-semibold text-white">
                <Sparkles size={18} className="text-purple-400" />
                2. Canonical Signed Payload &amp; LSB Embedding
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                IPGuard constructs a canonical versioned payload signed with a dedicated server-side Ed25519 key, embeds it in RGB LSBs, and saves the result encrypted with XChaCha20-Poly1305.
              </p>

              <div className="mt-4 rounded-2xl border border-sky-400/20 bg-sky-500/5 p-3.5 text-xs text-sky-200">
                <div className="flex items-start gap-2.5">
                  <Info size={16} className="mt-0.5 shrink-0 text-sky-400" />
                  <span>
                    <strong>Privacy Notice:</strong> LSB watermarking hides metadata inside PNG pixels without encrypting those payload bits. Confidentiality at rest is provided by Asset Vault XChaCha20-Poly1305 encryption. Do not enter passwords or secrets here.
                  </span>
                </div>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-300">
                    Copyright / Attribution (Optional)
                  </label>
                  <input
                    type="text"
                    maxLength={200}
                    value={copyrightInput}
                    onChange={(e) => setCopyrightInput(e.target.value)}
                    placeholder="e.g., © 2026 IPGuard Research Lab"
                    className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-ip-teal-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-300">
                    License Identifier (Optional)
                  </label>
                  <input
                    type="text"
                    maxLength={120}
                    value={licenseInput}
                    onChange={(e) => setLicenseInput(e.target.value)}
                    placeholder="e.g., Proprietary, CC-BY-NC-4.0"
                    className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-ip-teal-400 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-medium text-slate-300">
                  Watermark Note / Context (Optional)
                </label>
                <textarea
                  rows={3}
                  maxLength={1000}
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  placeholder="Optional non-sensitive description..."
                  className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-ip-teal-400 focus:outline-none"
                />
              </div>

              <div className="mt-4 rounded-2xl border border-white/[0.06] bg-ip-navy-950/50 p-3.5 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Automatically Signed Fields:</span>{' '}
                <code>format: IPGUARD_WATERMARK</code>, <code>version: 1</code>,{' '}
                <code>watermark_id</code>, <code>asset_reference</code>, opaque{' '}
                <code>owner_reference</code>, <code>created_at</code>, <code>source_sha256</code>,{' '}
                <code>signature_algorithm: Ed25519</code>, and <code>signing_key_id</code>.
              </div>

              {encodeError && (
                <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-200">
                  <AlertCircle size={16} className="shrink-0 text-rose-400" />
                  <span>{encodeError}</span>
                </div>
              )}

              <div className="mt-6 flex items-center justify-end gap-3">
                <button
                  type="submit"
                  disabled={!selectedSourceId || isEncoding || loadingCapacity}
                  className="inline-flex items-center gap-2 rounded-xl bg-ip-teal-500 px-6 py-3 text-sm font-semibold text-ip-navy-950 transition hover:bg-ip-teal-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isEncoding ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Signing, Embedding &amp; Encrypting...
                    </>
                  ) : (
                    <>
                      <Lock size={16} />
                      Embed Watermark &amp; Encrypt Derived Asset
                    </>
                  )}
                </button>
              </div>
            </form>

            {encodeResult && (
              <div className="rounded-3xl border border-emerald-400/30 bg-emerald-500/10 p-6 backdrop-blur-xl">
                <div className="flex items-start gap-3">
                  <CheckCircle2 size={22} className="mt-0.5 shrink-0 text-emerald-300" />
                  <div className="flex-1">
                    <h3 className="font-display text-base font-bold text-emerald-200">
                      Watermarked Derived Asset Created &amp; Encrypted
                    </h3>
                    <p className="mt-1 text-xs text-emerald-100/80">
                      The watermarked PNG has been encrypted with XChaCha20-Poly1305 (per-device HKDF + new nonce/AAD). Your original source PNG remains intact.
                    </p>

                    <div className="mt-4 grid gap-2 rounded-2xl border border-emerald-400/20 bg-ip-navy-950/60 p-4 text-xs sm:grid-cols-2">
                      <div>
                        <span className="text-slate-400">Derived Asset Filename</span>
                        <p className="font-semibold text-white">
                          {encodeResult.derivative.original_filename}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">Watermark ID</span>
                        <p className="font-mono text-emerald-300">{encodeResult.watermark_id}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Derived Asset ID</span>
                        <p className="font-mono text-slate-200">{encodeResult.derivative.id}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Encryption Status</span>
                        <p className="font-mono text-ip-teal-300">
                          {encodeResult.derivative.encryption_status}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2.5">
                      <button
                        type="button"
                        onClick={() => handleDownloadDerivative(encodeResult.derivative)}
                        disabled={downloadingDerivative}
                        className="inline-flex items-center gap-2 rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-ip-navy-950 transition hover:bg-emerald-300"
                      >
                        <Download size={14} />
                        {downloadingDerivative ? 'Decrypting...' : 'Download Watermarked PNG'}
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          handleInspectDerivativeImmediately(encodeResult.derivative)
                        }
                        className="inline-flex items-center gap-2 rounded-xl border border-emerald-300/30 bg-emerald-400/15 px-4 py-2 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-400/25"
                      >
                        <FileSearch size={14} />
                        Inspect Derivative Now
                      </button>
                      <Link
                        to="/assets"
                        className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/10"
                      >
                        View in Asset Vault
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODE 2: DECODE / INSPECT WATERMARK */}
      {mode === 'inspect' && (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Input Selection Panel */}
          <div className="space-y-5 lg:col-span-5">
            <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-6 backdrop-blur-xl">
              <h2 className="flex items-center gap-2 font-display text-base font-semibold text-white">
                <FileSearch size={18} className="text-ip-teal-400" />
                1. Select PNG Input Source (Read-Only)
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Inspection never modifies the source PNG or automatically persists external uploads into Asset Vault.
              </p>

              {/* Input Sub-mode Tabs */}
              <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-white/10 bg-ip-navy-950/70 p-1">
                <button
                  type="button"
                  onClick={() => {
                    setInspectInputMode('external')
                    setInspectResult(null)
                    setInspectError(null)
                  }}
                  className={`rounded-lg px-3 py-2 text-xs font-semibold transition ${
                    inspectInputMode === 'external'
                      ? 'bg-white/15 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  External PNG Upload
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInspectInputMode('vault')
                    setInspectResult(null)
                    setInspectError(null)
                  }}
                  className={`rounded-lg px-3 py-2 text-xs font-semibold transition ${
                    inspectInputMode === 'vault'
                      ? 'bg-white/15 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Asset Vault PNG
                </button>
              </div>

              {/* Sub-mode A: External Drag-and-Drop */}
              {inspectInputMode === 'external' && (
                <div className="mt-4">
                  <div
                    onDragOver={(e) => {
                      e.preventDefault()
                      setIsDragging(true)
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={(e) => {
                      e.preventDefault()
                      setIsDragging(false)
                      handleSelectExternalFile(e.dataTransfer.files?.[0])
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    className={`cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition ${
                      isDragging
                        ? 'border-ip-teal-400 bg-ip-teal-400/10'
                        : 'border-white/15 bg-ip-navy-950/50 hover:border-ip-teal-400/50'
                    }`}
                  >
                    <Upload size={26} className="mx-auto mb-2 text-ip-teal-400" />
                    <p className="text-sm font-medium text-white">
                      {externalFile ? externalFile.name : 'Drop PNG file here or click to browse'}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {externalFile
                        ? `${formatBytes(externalFile.size)} • Inspection-only`
                        : 'Supports 8-bit RGB/RGBA PNG up to 50 MB'}
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".png,image/png"
                      className="hidden"
                      onChange={(e) => handleSelectExternalFile(e.target.files?.[0])}
                    />
                  </div>

                  {externalPreviewUrl && (
                    <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-ip-navy-950/70 p-3">
                      <img
                        src={externalPreviewUrl}
                        alt="External PNG preview"
                        className="mx-auto max-h-48 rounded-xl object-contain"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Sub-mode B: Asset Vault Selector */}
              {inspectInputMode === 'vault' && (
                <div className="mt-4 space-y-4">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-slate-300">
                      Select PNG from Asset Vault ({pngAssets.length} available)
                    </label>
                    <select
                      value={selectedInspectAssetId}
                      onChange={(e) => {
                        setSelectedInspectAssetId(e.target.value)
                        setInspectResult(null)
                        setInspectError(null)
                      }}
                      className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2.5 text-sm text-white focus:border-ip-teal-400 focus:outline-none"
                    >
                      <option value="">-- Choose a Vault PNG asset --</option>
                      {pngAssets.map((asset) => (
                        <option key={asset.id} value={asset.id}>
                          {asset.original_filename}{' '}
                          {asset.derivative_type === 'PNG_LSB' ? '[Watermarked]' : ''} (
                          {formatBytes(asset.size_bytes)})
                        </option>
                      ))}
                    </select>
                  </div>

                  {vaultInspectPreviewUrl && (
                    <div className="overflow-hidden rounded-2xl border border-white/10 bg-ip-navy-950/70 p-3">
                      <img
                        src={vaultInspectPreviewUrl}
                        alt="Decrypted Vault PNG preview"
                        className="mx-auto max-h-48 rounded-xl object-contain"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Optional Expected Source SHA-256 Digest */}
              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-medium text-slate-300">
                  Expected Original Source SHA-256 (Optional Comparison)
                </label>
                <input
                  type="text"
                  maxLength={64}
                  value={expectedSourceSha256}
                  onChange={(e) => setExpectedSourceSha256(e.target.value)}
                  placeholder="Optional 64-char hex digest of original source PNG"
                  className="w-full rounded-xl border border-white/10 bg-ip-navy-950/80 px-3.5 py-2 font-mono text-xs text-white placeholder-slate-500 focus:border-ip-teal-400 focus:outline-none"
                />
              </div>

              {inspectError && (
                <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-200">
                  <AlertCircle size={16} className="shrink-0 text-rose-400" />
                  <span>{inspectError}</span>
                </div>
              )}

              <div className="mt-5 flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={handleRunInspect}
                  disabled={
                    isInspecting ||
                    (inspectInputMode === 'external' ? !externalFile : !selectedInspectAssetId)
                  }
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-ip-teal-500 px-5 py-2.5 text-sm font-semibold text-ip-navy-950 transition hover:bg-ip-teal-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isInspecting ? (
                    <>
                      <RefreshCw size={15} className="animate-spin" />
                      Inspecting Pixels &amp; Signature...
                    </>
                  ) : (
                    <>
                      <FileSearch size={15} />
                      Inspect Watermark
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleResetInspect}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-xs font-semibold text-slate-300 transition hover:bg-white/10"
                >
                  <RotateCcw size={14} />
                  Clear
                </button>
              </div>
            </div>
          </div>

          {/* Inspection Results Panel */}
          <div className="space-y-5 lg:col-span-7">
            {!inspectResult && !isInspecting && (
              <div className="flex h-full min-h-[360px] flex-col items-center justify-center rounded-3xl border border-dashed border-white/10 bg-ip-navy-900/35 p-8 text-center">
                <ImageIcon size={36} className="mb-3 text-slate-600" />
                <h3 className="font-display text-base font-semibold text-slate-300">
                  Ready for Read-Only Watermark Inspection
                </h3>
                <p className="mt-1 max-w-md text-xs text-slate-500">
                  Upload an external PNG or select an encrypted PNG from your Asset Vault to extract IPGuard LSB framing, parse signed metadata, and verify Ed25519 authenticity.
                </p>
              </div>
            )}

            {inspectResult && statusStyle && (
              <div className="space-y-5">
                {/* Status Banner */}
                <div
                  className={`rounded-3xl border ${statusStyle.border} ${statusStyle.bg} p-6 backdrop-blur-xl`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 shrink-0">{statusStyle.icon}</div>
                      <div>
                        <h3 className={`font-display text-lg font-bold ${statusStyle.text}`}>
                          {statusStyle.title}
                        </h3>
                        <p className="mt-1 text-xs text-slate-200/80">
                          {statusStyle.description}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`shrink-0 rounded-full border px-3 py-1 font-mono text-[11px] font-bold uppercase ${statusStyle.badge}`}
                    >
                      {inspectResult.status}
                    </span>
                  </div>

                  {inspectResult.warnings.length > 0 && (
                    <div className="mt-4 space-y-1.5 rounded-2xl border border-white/10 bg-ip-navy-950/60 p-3.5 text-xs text-amber-200">
                      {inspectResult.warnings.map((w, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <AlertTriangle size={14} className="mt-0.5 shrink-0 text-amber-400" />
                          <span>{w}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Section 1: Watermark Information (Only shown as trusted when VALID) */}
                <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-6 backdrop-blur-xl">
                  <h3 className="font-display text-sm font-bold uppercase tracking-wider text-ip-teal-300">
                    Watermark Information
                  </h3>

                  {inspectResult.status === 'VALID' ? (
                    <div className="mt-4 space-y-3 text-xs">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">Watermark ID</span>
                          <p className="mt-0.5 break-all font-mono text-white">
                            {inspectResult.watermark_id ?? '—'}
                          </p>
                        </div>
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Format &amp; Version
                          </span>
                          <p className="mt-0.5 font-mono text-white">
                            {inspectResult.format ?? 'IPGUARD_WATERMARK'} v{inspectResult.version ?? 1}
                          </p>
                        </div>
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Asset Reference
                          </span>
                          <p className="mt-0.5 break-all font-mono text-slate-200">
                            {inspectResult.asset_reference ?? '—'}
                          </p>
                        </div>
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Owner Reference (Opaque)
                          </span>
                          <p className="mt-0.5 break-all font-mono text-slate-200">
                            {inspectResult.owner_reference ?? '—'}
                          </p>
                        </div>
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Watermark Timestamp
                          </span>
                          <p className="mt-0.5 font-mono text-slate-200">
                            {inspectResult.created_at ?? '—'}
                          </p>
                        </div>
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Derivative Asset ID
                          </span>
                          <p className="mt-0.5 break-all font-mono text-slate-200">
                            {inspectResult.derivative_asset_id ?? '—'}
                          </p>
                        </div>
                      </div>

                      {inspectResult.source_sha256 && (
                        <div className="rounded-xl border border-white/[0.06] bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Embedded Source Image SHA-256
                          </span>
                          <p className="mt-0.5 break-all font-mono text-slate-200">
                            {inspectResult.source_sha256}
                          </p>
                        </div>
                      )}

                      {inspectResult.metadata &&
                        Object.keys(inspectResult.metadata).length > 0 && (
                          <div className="rounded-xl border border-ip-teal-400/20 bg-ip-teal-400/[0.04] p-3.5">
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-ip-teal-300">
                              Embedded Attribution Metadata
                            </span>
                            <div className="mt-2 space-y-1.5">
                              {Object.entries(inspectResult.metadata).map(([k, v]) => (
                                <div key={k} className="flex justify-between gap-4">
                                  <span className="capitalize text-slate-400">{k}</span>
                                  <span className="text-right font-medium text-white">
                                    {String(v)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {inspectResult.raw_payload_preview && (
                        <div className="rounded-xl border border-white/10 bg-ip-navy-950/60 p-3">
                          <span className="text-[10px] uppercase text-slate-500">
                            Extracted Payload Preview
                          </span>
                          <pre className="mt-1 whitespace-pre-wrap break-all font-mono text-slate-200">
                            {inspectResult.raw_payload_preview}
                          </pre>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3 rounded-xl border border-white/10 bg-ip-navy-950/50 p-4 text-xs text-slate-400">
                      Unverified or missing watermark payload metadata is withheld so partial or forged data is never presented as trusted.
                    </div>
                  )}
                </div>

                {/* Section 2 & 3: Cryptographic Verification + Integrity Status */}
                <div className="grid gap-5 sm:grid-cols-2">
                  <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-5 backdrop-blur-xl">
                    <h3 className="font-display text-xs font-bold uppercase tracking-wider text-purple-300">
                      Cryptographic Verification
                    </h3>
                    <div className="mt-3 space-y-2.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Signature Algorithm</span>
                        <span className="font-mono text-white">
                          {inspectResult.signature_algorithm ?? '—'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Signature Status</span>
                        <span
                          className={`font-semibold ${
                            inspectResult.signature_valid ? 'text-emerald-300' : 'text-rose-300'
                          }`}
                        >
                          {inspectResult.signature_valid ? 'VERIFIED' : 'NOT VERIFIED'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">Signing Key ID</span>
                        <p className="mt-0.5 break-all font-mono text-[11px] text-slate-200">
                          {inspectResult.signing_key_id ?? '—'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">Verification Timestamp</span>
                        <p className="mt-0.5 font-mono text-[11px] text-slate-300">
                          {new Date(inspectResult.verified_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-3xl border border-white/[0.08] bg-ip-navy-900/65 p-5 backdrop-blur-xl">
                    <h3 className="font-display text-xs font-bold uppercase tracking-wider text-amber-300">
                      Integrity Status
                    </h3>
                    <div className="mt-3 space-y-2.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Input Mode</span>
                        <span className="font-mono text-white">{inspectResult.input_mode}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Payload Framing</span>
                        <span
                          className={
                            inspectResult.framing_valid ? 'text-emerald-300' : 'text-slate-400'
                          }
                        >
                          {inspectResult.framing_valid ? 'VALID' : 'ABSENT / INVALID'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Payload Checksum</span>
                        <span
                          className={
                            inspectResult.checksum_valid ? 'text-emerald-300' : 'text-slate-400'
                          }
                        >
                          {inspectResult.checksum_valid ? 'MATCHED' : 'FAILED / N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Source Digest Check</span>
                        <span
                          className={
                            inspectResult.source_digest_matches === true
                              ? 'text-emerald-300'
                              : inspectResult.source_digest_matches === false
                                ? 'text-rose-300'
                                : 'text-slate-400'
                          }
                        >
                          {inspectResult.source_digest_matches === true
                            ? 'MATCHED'
                            : inspectResult.source_digest_matches === false
                              ? 'MISMATCH'
                              : 'NOT COMPARED'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">Inspected PNG SHA-256</span>
                        <p className="mt-0.5 break-all font-mono text-[10px] text-slate-300">
                          {inspectResult.inspected_image_sha256}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Boundary Disclaimer */}
                <div className="rounded-2xl border border-white/[0.06] bg-ip-navy-950/50 px-4 py-3 text-[11px] text-slate-400">
                  <strong className="text-slate-300">Trust Boundary Note:</strong> Digital signature verification proves that the extracted watermark payload was issued by the trusted IPGuard signing service; it does not prove that every non-LSB pixel of the host image is unmodified without comparing against the original image digest.
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
