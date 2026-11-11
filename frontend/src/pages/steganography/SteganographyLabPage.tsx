import {
  AlertCircle,
  AlertTriangle,
  Download,
  FileSearch,
  Image as ImageIcon,
  KeyRound,
  Lock,
  LogOut,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Stamp,
  Upload,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from '../../components/ui/Button'
import { KeyValueGrid, PageHeader, Panel } from '../../components/ui/DataDisplay'
import {
  EmptyState,
  ErrorState,
  StatusIndicator,
  useToast,
} from '../../components/ui/Feedback'
import { SelectInput, TextareaInput, TextInput } from '../../components/ui/Input'
import { Tabs } from '../../components/ui/NavigationUi'
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

function getInspectorMeta(status: InspectorStatus): {
  tone: 'success' | 'danger' | 'warning' | 'neutral'
  title: string
  description: string
} {
  switch (status) {
    case 'VALID':
      return {
        tone: 'success',
        title: 'Valid IPGuard watermark verified',
        description:
          'LSB packet framing, payload SHA-256 checksum, and Ed25519 signature passed verification.',
      }
    case 'INVALID_SIGNATURE':
      return {
        tone: 'danger',
        title: 'Invalid digital signature',
        description:
          'An IPGuard header was found, but Ed25519 signature verification failed. Untrusted payload withheld.',
      }
    case 'CORRUPTED':
      return {
        tone: 'danger',
        title: 'Corrupted or truncated watermark',
        description:
          'Watermark marker detected, but framing length or checksum verification failed.',
      }
    case 'UNKNOWN_SIGNER':
      return {
        tone: 'warning',
        title: 'Unknown signing key ID',
        description:
          'Watermark framing is intact, but the embedded signing key ID is not trusted by this server.',
      }
    case 'UNSUPPORTED_VERSION':
      return {
        tone: 'warning',
        title: 'Unsupported watermark version',
        description:
          'The PNG contains an IPGuard marker with an unsupported format version.',
      }
    case 'NO_WATERMARK':
    default:
      return {
        tone: 'neutral',
        title: 'No IPGuard watermark detected',
        description:
          'No IPGuard RGB LSB header was found in this PNG image.',
      }
  }
}

export function SteganographyLabPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { pushToast } = useToast()

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

  // Encode state
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

  // Inspect state
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

  const handleAuthError = useCallback((errMsg: string) => {
    const lower = errMsg.toLowerCase()
    if (
      lower.includes('session') ||
      lower.includes('unauthorized') ||
      lower.includes('token') ||
      lower.includes('revoked')
    ) {
      clearStoredSessionToken()
      setToken(null)
    }
    setGlobalError(errMsg)
  }, [])

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
    void fetchVaultAssets()
  }, [fetchVaultAssets])

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
      pushToast(`Embedded watermark ${response.watermark_id.slice(0, 8)}...`, 'success')
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
      setEncodeError(err instanceof Error ? err.message : 'Failed to download derivative')
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
          setInspectError('Choose a PNG file to inspect.')
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
          setInspectError('Select a PNG asset from your Asset Vault.')
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

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Steganography Lab"
          description="Encode Ed25519-signed PNG LSB watermarks or inspect external images read-only."
          breadcrumbs={[
            { label: 'Overview', to: '/overview' },
            { label: 'Steganography Lab' },
          ]}
        />
        <Panel>
          <EmptyState
            icon={<Lock size={20} />}
            title="Authentication required"
            description="Sign in with your enrolled Android device to access Vault PNG assets and watermark inspection."
            action={
              <Link to="/login">
                <Button variant="primary" size="sm" iconLeft={<KeyRound size={14} />}>
                  Sign In with QR
                </Button>
              </Link>
            }
          />
        </Panel>
      </div>
    )
  }

  const inspectMeta = inspectResult ? getInspectorMeta(inspectResult.status) : null

  return (
    <div className="space-y-6">
      <PageHeader
        title="Steganography Lab"
        description="Embed canonical Ed25519 watermarks into Vault PNGs or verify any PNG read-only."
        breadcrumbs={[
          { label: 'Overview', to: '/overview' },
          { label: 'Steganography Lab' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void fetchVaultAssets()}
              disabled={loadingAssets}
              loading={loadingAssets}
              iconLeft={!loadingAssets ? <RefreshCw size={13} /> : undefined}
            >
              Sync Vault
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSignOut}
              iconLeft={<LogOut size={13} />}
            >
              Sign Out
            </Button>
          </div>
        }
      />

      {globalError && (
        <ErrorState
          message={globalError}
          onRetry={() => void fetchVaultAssets()}
          onDismiss={() => setGlobalError(null)}
        />
      )}

      <div>
        <Tabs
          options={[
            { id: 'encode', label: 'Encode Watermark' },
            { id: 'inspect', label: 'Decode & Inspect PNG' },
          ]}
          activeId={mode}
          onChange={(next) => setMode(next as LabMode)}
        />
      </div>

      {mode === 'encode' && (
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-5">
            <Panel
              title="1. Source Asset Selection"
              description="Choose an un-watermarked PNG from your encrypted Asset Vault."
            >
              <div className="space-y-4">
                <SelectInput
                  id="stego-source-select"
                  label="Vault PNG Asset"
                  value={selectedSourceId}
                  onChange={(e) => {
                    setSelectedSourceId(e.target.value)
                    setEncodeResult(null)
                    setEncodeError(null)
                  }}
                >
                  <option value="">-- Choose a Vault PNG asset --</option>
                  {sourceCandidates.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.original_filename} ({formatBytes(asset.size_bytes)})
                    </option>
                  ))}
                </SelectInput>

                {sourceCandidates.length === 0 && !loadingAssets && (
                  <p className="text-xs text-zinc-500">
                    No PNG source assets available. Upload a PNG in{' '}
                    <Link to="/assets" className="text-ip-accent-400 hover:underline">
                      Asset Vault
                    </Link>
                    .
                  </p>
                )}

                {sourcePreviewUrl && (
                  <div className="overflow-hidden rounded-lg border border-ip-border bg-ip-elevated/50 p-3">
                    <img
                      src={sourcePreviewUrl}
                      alt="Selected Vault PNG preview"
                      className="mx-auto max-h-48 rounded object-contain"
                    />
                  </div>
                )}

                {loadingCapacity && (
                  <p className="text-xs text-zinc-400">
                    Inspecting pixel dimensions and LSB capacity...
                  </p>
                )}

                {sourceCapacity && (
                  <KeyValueGrid
                    columns={2}
                    items={[
                      {
                        label: 'Dimensions',
                        value: `${sourceCapacity.width} × ${sourceCapacity.height} px`,
                        mono: true,
                      },
                      { label: 'Mode', value: sourceCapacity.mode, mono: true },
                      {
                        label: 'Max Payload',
                        value: `${formatBytes(sourceCapacity.max_payload_bytes)}`,
                        mono: true,
                      },
                      {
                        label: 'Source SHA-256',
                        value: `${sourceCapacity.source_sha256.slice(0, 16)}...`,
                        mono: true,
                      },
                    ]}
                  />
                )}
              </div>
            </Panel>
          </div>

          <div className="space-y-4 lg:col-span-7">
            <Panel
              title="2. Canonical Watermark Payload"
              description="Construct an Ed25519-signed packet embedded into PNG RGB LSBs and saved as a new XChaCha20-Poly1305 encrypted asset."
            >
              <form onSubmit={handleEncodeSubmit} className="space-y-4">
                <div className="rounded-lg border border-ip-border bg-ip-elevated/50 p-3 text-xs text-zinc-400">
                  <p>
                    <strong className="text-zinc-200">Fragility & Privacy Notice:</strong>{' '}
                    RGB 1-bit LSB steganography is sensitive to re-encoding, scaling, or lossy JPEG/WebP conversion. Watermark attribution metadata is embedded unencrypted in LSBs; do not place secrets or credentials here.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <TextInput
                    id="encode-copyright"
                    label="Copyright / Attribution (Optional)"
                    maxLength={200}
                    value={copyrightInput}
                    onChange={(e) => setCopyrightInput(e.target.value)}
                    placeholder="e.g. © 2026 IPGuard Lab"
                  />
                  <TextInput
                    id="encode-license"
                    label="License Identifier (Optional)"
                    maxLength={120}
                    value={licenseInput}
                    onChange={(e) => setLicenseInput(e.target.value)}
                    placeholder="e.g. Proprietary, CC-BY-NC-4.0"
                  />
                </div>

                <TextareaInput
                  id="encode-note"
                  label="Watermark Note / Context (Optional)"
                  rows={3}
                  maxLength={1000}
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  placeholder="Optional non-sensitive attribution description..."
                  hint="Automatically includes format: IPGUARD_WATERMARK, version: 1, watermark_id, asset_reference, opaque owner_reference, created_at, source_sha256, Ed25519 signature & signing_key_id."
                />

                {encodeError && (
                  <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                    <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-400" />
                    <span>{encodeError}</span>
                  </div>
                )}

                <div className="flex justify-end border-t border-ip-border pt-4">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    disabled={!selectedSourceId || isEncoding || loadingCapacity}
                    loading={isEncoding}
                    iconLeft={!isEncoding ? <Stamp size={15} /> : undefined}
                  >
                    {isEncoding
                      ? 'Signing, Embedding & Encrypting...'
                      : 'Embed Watermark & Create Derivative'}
                  </Button>
                </div>
              </form>
            </Panel>

            {encodeResult && (
              <Panel
                title="Watermarked Derivative Created"
                description="Your original source PNG remains unmodified."
                actions={<StatusIndicator label="Encrypted at Rest" tone="success" />}
              >
                <div className="space-y-4">
                  <KeyValueGrid
                    columns={2}
                    items={[
                      {
                        label: 'Derived Filename',
                        value: encodeResult.derivative.original_filename,
                      },
                      { label: 'Watermark ID', value: encodeResult.watermark_id, mono: true },
                      {
                        label: 'Derivative Asset ID',
                        value: encodeResult.derivative.id,
                        mono: true,
                      },
                      {
                        label: 'Encryption Status',
                        value: encodeResult.derivative.encryption_status,
                        mono: true,
                      },
                    ]}
                  />

                  <div className="flex flex-wrap items-center gap-2 border-t border-ip-border pt-4">
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={downloadingDerivative}
                      loading={downloadingDerivative}
                      onClick={() => void handleDownloadDerivative(encodeResult.derivative)}
                      iconLeft={<Download size={13} />}
                    >
                      {downloadingDerivative ? 'Decrypting...' : 'Download Watermarked PNG'}
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        void handleInspectDerivativeImmediately(encodeResult.derivative)
                      }
                      iconLeft={<FileSearch size={13} />}
                    >
                      Inspect Derivative Now
                    </Button>
                    <Link to="/assets">
                      <Button variant="ghost" size="sm">
                        View in Asset Vault
                      </Button>
                    </Link>
                  </div>
                </div>
              </Panel>
            )}
          </div>
        </div>
      )}

      {mode === 'inspect' && (
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-4 lg:col-span-5">
            <Panel
              title="3. PNG Input Source (Read-Only)"
              description="Inspection never modifies files or stores uploaded images into Asset Vault."
            >
              <div className="space-y-4">
                <Tabs
                  options={[
                    { id: 'external', label: 'External PNG Upload' },
                    { id: 'vault', label: 'Asset Vault PNG' },
                  ]}
                  activeId={inspectInputMode}
                  onChange={(next) => {
                    setInspectInputMode(next as InspectInputMode)
                    setInspectResult(null)
                    setInspectError(null)
                  }}
                />

                {inspectInputMode === 'external' ? (
                  <div className="space-y-3">
                    <label
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
                      className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed p-5 text-center transition-colors ${
                        isDragging
                          ? 'border-ip-accent-400 bg-ip-accent-500/5'
                          : 'border-ip-border bg-ip-elevated/40 hover:border-zinc-600'
                      }`}
                    >
                      <Upload size={20} className="mb-2 text-zinc-400" />
                      <p className="text-xs font-medium text-zinc-200">
                        {externalFile ? externalFile.name : 'Choose or drop PNG file'}
                      </p>
                      <p className="mt-1 text-[11px] text-zinc-500">
                        PNG format required for LSB bit-plane extraction
                      </p>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/png,.png"
                        onChange={(e) => handleSelectExternalFile(e.target.files?.[0])}
                        className="sr-only"
                      />
                    </label>

                    {externalPreviewUrl && (
                      <div className="overflow-hidden rounded-lg border border-ip-border bg-ip-elevated/50 p-3">
                        <img
                          src={externalPreviewUrl}
                          alt="External PNG preview"
                          className="mx-auto max-h-48 rounded object-contain"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <SelectInput
                      id="inspect-vault-select"
                      label="Vault PNG Asset"
                      value={selectedInspectAssetId}
                      onChange={(e) => {
                        setSelectedInspectAssetId(e.target.value)
                        setInspectResult(null)
                        setInspectError(null)
                      }}
                    >
                      <option value="">-- Choose a Vault PNG asset --</option>
                      {pngAssets.map((asset) => (
                        <option key={asset.id} value={asset.id}>
                          {asset.original_filename}{' '}
                          {asset.derivative_type === 'PNG_LSB' ? '[Watermarked]' : ''} (
                          {formatBytes(asset.size_bytes)})
                        </option>
                      ))}
                    </SelectInput>

                    {vaultInspectPreviewUrl && (
                      <div className="overflow-hidden rounded-lg border border-ip-border bg-ip-elevated/50 p-3">
                        <img
                          src={vaultInspectPreviewUrl}
                          alt="Decrypted Vault PNG preview"
                          className="mx-auto max-h-48 rounded object-contain"
                        />
                      </div>
                    )}
                  </div>
                )}

                <TextInput
                  id="expected-source-sha256"
                  label="Expected Source SHA-256 (Optional)"
                  maxLength={64}
                  value={expectedSourceSha256}
                  onChange={(e) => setExpectedSourceSha256(e.target.value)}
                  placeholder="64-character hex digest"
                  className="font-mono text-xs"
                />

                {inspectError && (
                  <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
                    <AlertCircle size={15} className="mt-0.5 shrink-0 text-red-400" />
                    <span>{inspectError}</span>
                  </div>
                )}

                <div className="flex items-center gap-2 border-t border-ip-border pt-3">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    disabled={
                      isInspecting ||
                      (inspectInputMode === 'external'
                        ? !externalFile
                        : !selectedInspectAssetId)
                    }
                    loading={isInspecting}
                    onClick={() => void handleRunInspect()}
                    iconLeft={!isInspecting ? <FileSearch size={14} /> : undefined}
                  >
                    {isInspecting ? 'Inspecting PNG...' : 'Inspect Watermark'}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleResetInspect}
                    iconLeft={<RotateCcw size={13} />}
                  >
                    Clear
                  </Button>
                </div>
              </div>
            </Panel>
          </div>

          <div className="space-y-4 lg:col-span-7">
            {!inspectResult ? (
              <Panel>
                <EmptyState
                  icon={<ImageIcon size={20} />}
                  title="Ready for read-only inspection"
                  description="Upload an external PNG or select an encrypted Vault PNG to verify framing, checksum, and Ed25519 signature authenticity."
                />
              </Panel>
            ) : (
              inspectMeta && (
                <div className="space-y-4">
                  <Panel
                    title="4. Verification Result"
                    actions={
                      <StatusIndicator
                        label={inspectResult.status}
                        tone={inspectMeta.tone}
                      />
                    }
                  >
                    <div className="space-y-3">
                      <div className="flex items-start gap-3">
                        {inspectResult.status === 'VALID' ? (
                          <ShieldCheck size={20} className="mt-0.5 shrink-0 text-emerald-400" />
                        ) : inspectResult.status === 'INVALID_SIGNATURE' ||
                          inspectResult.status === 'CORRUPTED' ? (
                          <ShieldAlert size={20} className="mt-0.5 shrink-0 text-red-400" />
                        ) : (
                          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-amber-300" />
                        )}
                        <div>
                          <p className="text-sm font-semibold text-zinc-100">
                            {inspectMeta.title}
                          </p>
                          <p className="mt-0.5 text-xs text-zinc-400">
                            {inspectMeta.description}
                          </p>
                        </div>
                      </div>

                      {inspectResult.warnings.length > 0 && (
                        <div className="space-y-1.5 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3 text-xs text-amber-200">
                          {inspectResult.warnings.map((w, idx) => (
                            <div key={idx} className="flex items-start gap-2">
                              <AlertTriangle size={13} className="mt-0.5 shrink-0 text-amber-300" />
                              <span>{w}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </Panel>

                  <Panel title="5. Extracted Payload & Attribution">
                    {inspectResult.status === 'VALID' ? (
                      <div className="space-y-4">
                        <KeyValueGrid
                          columns={2}
                          items={[
                            {
                              label: 'Watermark ID',
                              value: inspectResult.watermark_id ?? '—',
                              mono: true,
                            },
                            {
                              label: 'Format & Version',
                              value: `${inspectResult.format ?? 'IPGUARD_WATERMARK'} v${inspectResult.version ?? 1}`,
                              mono: true,
                            },
                            {
                              label: 'Asset Reference',
                              value: inspectResult.asset_reference ?? '—',
                              mono: true,
                            },
                            {
                              label: 'Owner Reference',
                              value: inspectResult.owner_reference ?? '—',
                              mono: true,
                            },
                            {
                              label: 'Watermark Timestamp',
                              value: inspectResult.created_at ?? '—',
                              mono: true,
                            },
                            {
                              label: 'Derivative Asset ID',
                              value: inspectResult.derivative_asset_id ?? '—',
                              mono: true,
                            },
                          ]}
                        />

                        {inspectResult.source_sha256 && (
                          <div className="rounded-lg border border-ip-border bg-ip-elevated/50 p-3">
                            <p className="text-[11px] font-medium text-zinc-500">
                              Embedded Source SHA-256
                            </p>
                            <p className="mt-0.5 break-all font-mono text-xs text-zinc-200">
                              {inspectResult.source_sha256}
                            </p>
                          </div>
                        )}

                        {inspectResult.metadata &&
                          Object.keys(inspectResult.metadata).length > 0 && (
                            <KeyValueGrid
                              columns={2}
                              items={Object.entries(inspectResult.metadata).map(([k, v]) => ({
                                label: k,
                                value: String(v),
                              }))}
                            />
                          )}

                        {inspectResult.raw_payload_preview && (
                          <pre className="whitespace-pre-wrap break-all rounded-lg border border-ip-border bg-ip-elevated/60 p-3 font-mono text-xs text-zinc-200">
                            {inspectResult.raw_payload_preview}
                          </pre>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs leading-5 text-zinc-400">
                        Unverified, invalid-signature, corrupted, or missing watermark payload metadata is withheld so unauthenticated data is never presented as trusted.
                      </p>
                    )}
                  </Panel>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <Panel title="Cryptographic Verification">
                      <KeyValueGrid
                        columns={2}
                        items={[
                          {
                            label: 'Algorithm',
                            value: inspectResult.signature_algorithm ?? '—',
                            mono: true,
                          },
                          {
                            label: 'Signature',
                            value: inspectResult.signature_valid ? 'VERIFIED' : 'NOT VERIFIED',
                          },
                          {
                            label: 'Signing Key ID',
                            value: inspectResult.signing_key_id ?? '—',
                            mono: true,
                          },
                          {
                            label: 'Verified At',
                            value: new Date(inspectResult.verified_at).toLocaleString(),
                            mono: true,
                          },
                        ]}
                      />
                    </Panel>

                    <Panel title="Integrity Summary">
                      <KeyValueGrid
                        columns={2}
                        items={[
                          { label: 'Input Mode', value: inspectResult.input_mode, mono: true },
                          {
                            label: 'Framing',
                            value: inspectResult.framing_valid ? 'VALID' : 'INVALID / ABSENT',
                          },
                          {
                            label: 'Checksum',
                            value: inspectResult.checksum_valid ? 'MATCHED' : 'FAILED / N/A',
                          },
                          {
                            label: 'Source Digest',
                            value:
                              inspectResult.source_digest_matches === true
                                ? 'MATCHED'
                                : inspectResult.source_digest_matches === false
                                  ? 'MISMATCH'
                                  : 'NOT COMPARED',
                          },
                        ]}
                      />
                      <div className="mt-3 rounded-lg border border-ip-border bg-ip-elevated/50 p-2.5">
                        <p className="text-[11px] font-medium text-zinc-500">
                          Inspected PNG SHA-256
                        </p>
                        <p className="mt-0.5 break-all font-mono text-[11px] text-zinc-300">
                          {inspectResult.inspected_image_sha256}
                        </p>
                      </div>
                    </Panel>
                  </div>

                  <p className="rounded-lg border border-ip-border bg-ip-surface px-4 py-3 text-xs leading-5 text-zinc-400">
                    <strong className="text-zinc-200">Trust Boundary:</strong> Signature verification confirms that the extracted payload was issued by the IPGuard signing service; non-LSB pixel modifications require comparing against the original source image SHA-256 digest.
                  </p>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}
