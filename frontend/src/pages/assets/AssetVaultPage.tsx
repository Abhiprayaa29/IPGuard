import {
  Check,
  CheckCircle2,
  Copy,
  Download,
  Edit3,
  Eye,
  File,
  FileArchive,
  FileCode,
  FileText,
  FolderLock,
  Image as ImageIcon,
  KeyRound,
  Layers,
  LogOut,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Stamp,
  Trash2,
  Upload,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button, IconButton } from '../../components/ui/Button'
import { KeyValueGrid, PageHeader, Panel } from '../../components/ui/DataDisplay'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusIndicator,
  useToast,
} from '../../components/ui/Feedback'
import { SearchInput, TextareaInput, TextInput } from '../../components/ui/Input'
import { ConfirmationDialog, Modal } from '../../components/ui/Modal'
import { Tabs } from '../../components/ui/NavigationUi'
import {
  deleteAsset,
  downloadAsset,
  embedWatermark,
  extractWatermark,
  getAssets,
  renameAsset,
  uploadAsset,
  verifyWatermark,
} from '../../services/assets'
import type {
  Asset,
  StegoEmbedResponse,
  WatermarkExtractResponse,
  WatermarkPayloadData,
  WatermarkVerifyResponse,
} from '../../types/assets'
import { formatBytes } from '../../utils/format'
import {
  clearStoredSessionToken,
  getStoredSessionToken,
  saveSessionToken,
} from '../../utils/session'

type FilterCategory = 'all' | 'image' | 'watermarked' | 'doc' | 'archive'

function getFileIcon(mime: string | null, filename: string, isDerivative?: boolean) {
  if (isDerivative) {
    return <Stamp size={16} className="text-ip-accent-400" />
  }
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (mime?.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) {
    return <ImageIcon size={16} className="text-emerald-400" />
  }
  if (mime === 'application/pdf' || ext === 'pdf') {
    return <FileText size={16} className="text-red-400" />
  }
  if (
    mime?.includes('zip') ||
    mime?.includes('compressed') ||
    ['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)
  ) {
    return <FileArchive size={16} className="text-amber-300" />
  }
  if (['json', 'js', 'ts', 'tsx', 'py', 'html', 'css', 'md', 'csv'].includes(ext)) {
    return <FileCode size={16} className="text-zinc-300" />
  }
  return <File size={16} className="text-zinc-400" />
}

function decodeBase64Utf8(b64: string): string {
  try {
    return decodeURIComponent(
      Array.prototype.map
        .call(atob(b64), (c: string) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    )
  } catch {
    return atob(b64)
  }
}

export function AssetVaultPage() {
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

  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<FilterCategory>('all')

  // Upload
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Preview / Inspect
  const [inspectingAsset, setInspectingAsset] = useState<Asset | null>(null)
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  // Rename
  const [renamingAsset, setRenamingAsset] = useState<Asset | null>(null)
  const [newFilename, setNewFilename] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameError, setRenameError] = useState<string | null>(null)

  // Delete
  const [deletingAsset, setDeletingAsset] = useState<Asset | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Watermark Embed
  const [embeddingAsset, setEmbeddingAsset] = useState<Asset | null>(null)
  const [isEmbedding, setIsEmbedding] = useState(false)
  const [embedError, setEmbedError] = useState<string | null>(null)
  const [embedSuccess, setEmbedSuccess] = useState<StegoEmbedResponse | null>(null)
  const [wmCopyright, setWmCopyright] = useState('© 2026 IPGuard Vault. All rights reserved.')
  const [wmLicense, setWmLicense] = useState('Proprietary / All Rights Reserved')
  const [wmCustomText, setWmCustomText] = useState('')
  const [wmDescription, setWmDescription] = useState('')

  // Watermark Verify
  const [verifyingAsset, setVerifyingAsset] = useState<Asset | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState<WatermarkVerifyResponse | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  // Watermark Extract
  const [extractingAsset, setExtractingAsset] = useState<Asset | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractResult, setExtractResult] = useState<WatermarkExtractResponse | null>(null)
  const [extractError, setExtractError] = useState<string | null>(null)
  const [extractedMetadata, setExtractedMetadata] = useState<WatermarkPayloadData | null>(null)
  const [rawPayloadText, setRawPayloadText] = useState<string>('')
  const [copiedPayload, setCopiedPayload] = useState(false)

  const loadAssets = useCallback(async (authToken: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAssets(authToken)
      setAssets(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve digital assets.'
      setError(msg)
      if (msg.toLowerCase().includes('unauthorized') || msg.toLowerCase().includes('expired')) {
        clearStoredSessionToken()
        setToken(null)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (token) {
      void loadAssets(token)
    } else {
      setLoading(false)
    }
  }, [token, loadAssets])

  useEffect(() => {
    if (!inspectingAsset && previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl)
      setPreviewBlobUrl(null)
    }
  }, [inspectingAsset, previewBlobUrl])

  const handleDownload = async (asset: Asset) => {
    if (!token) return
    try {
      setDownloadingId(asset.id)
      const blob = await downloadAsset(token, asset.id)
      const blobUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = asset.original_filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Download failed.'
      setError(msg)
      pushToast(msg, 'danger')
    } finally {
      setDownloadingId(null)
    }
  }

  const handleInspect = async (asset: Asset) => {
    setInspectingAsset(asset)
    if (!token) return
    if (asset.content_type?.startsWith('image/')) {
      try {
        setIsPreviewLoading(true)
        const blob = await downloadAsset(token, asset.id)
        const url = URL.createObjectURL(blob)
        setPreviewBlobUrl(url)
      } catch {
        // Metadata view still renders cleanly without preview image
      } finally {
        setIsPreviewLoading(false)
      }
    }
  }

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedFile) return

    if (selectedFile.size === 0) {
      setUploadError('File cannot be empty (0 bytes).')
      return
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setUploadError('File exceeds the 50 MB size limit.')
      return
    }

    try {
      setIsUploading(true)
      setUploadProgress(0)
      setUploadError(null)
      const created = await uploadAsset(token, selectedFile, (pct) => {
        setUploadProgress(pct)
      })
      setAssets((prev) => [created, ...prev])
      setIsUploadModalOpen(false)
      setSelectedFile(null)
      setUploadProgress(0)
      pushToast(`Encrypted and uploaded "${created.original_filename}".`, 'success')
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !renamingAsset) return
    const cleanName = newFilename.trim()
    if (!cleanName) {
      setRenameError('Filename cannot be empty.')
      return
    }
    if (cleanName.includes('/') || cleanName.includes('\\')) {
      setRenameError('Filename cannot contain path separators.')
      return
    }

    try {
      setIsRenaming(true)
      setRenameError(null)
      const updated = await renameAsset(token, renamingAsset.id, { filename: cleanName })
      setAssets((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
      setRenamingAsset(null)
      pushToast(`Renamed asset to "${updated.original_filename}".`, 'success')
    } catch (err) {
      setRenameError(err instanceof Error ? err.message : 'Rename failed.')
    } finally {
      setIsRenaming(false)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!token || !deletingAsset) return
    try {
      setIsDeleting(true)
      await deleteAsset(token, deletingAsset.id)
      setAssets((prev) => prev.filter((a) => a.id !== deletingAsset.id))
      pushToast(`Deleted "${deletingAsset.original_filename}".`, 'info')
      setDeletingAsset(null)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Delete failed.'
      setError(msg)
      pushToast(msg, 'danger')
    } finally {
      setIsDeleting(false)
    }
  }

  const openEmbedModal = (asset: Asset) => {
    setEmbeddingAsset(asset)
    setEmbedError(null)
    setEmbedSuccess(null)
    setWmCustomText('')
    setWmDescription('')
  }

  const handleEmbedSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !embeddingAsset) return

    try {
      setIsEmbedding(true)
      setEmbedError(null)
      const payloadObj: WatermarkPayloadData = {
        copyright: wmCopyright.trim() || undefined,
        license: wmLicense.trim() || undefined,
        text: wmCustomText.trim() || undefined,
        description: wmDescription.trim() || undefined,
        timestamp: new Date().toISOString(),
      }
      const jsonStr = JSON.stringify(payloadObj)
      const base64Payload = btoa(
        encodeURIComponent(jsonStr).replace(/%([0-9A-F]{2})/g, (_, p1) =>
          String.fromCharCode(parseInt(p1, 16)),
        ),
      )

      const result = await embedWatermark(token, embeddingAsset.id, base64Payload)
      setEmbedSuccess(result)
      setAssets((prev) => [result.derivative, ...prev])
      pushToast(`Created watermarked derivative "${result.derivative.original_filename}".`, 'success')
    } catch (err) {
      setEmbedError(err instanceof Error ? err.message : 'Watermark embedding failed.')
    } finally {
      setIsEmbedding(false)
    }
  }

  const handleVerify = async (asset: Asset) => {
    if (!token) return
    setVerifyingAsset(asset)
    setIsVerifying(true)
    setVerifyResult(null)
    setVerifyError(null)
    try {
      const res = await verifyWatermark(token, asset.id)
      setVerifyResult(res)
    } catch (err) {
      setVerifyError(err instanceof Error ? err.message : 'Watermark verification failed.')
    } finally {
      setIsVerifying(false)
    }
  }

  const handleExtract = async (asset: Asset) => {
    if (!token) return
    setExtractingAsset(asset)
    setIsExtracting(true)
    setExtractResult(null)
    setExtractError(null)
    setExtractedMetadata(null)
    setRawPayloadText('')
    setCopiedPayload(false)

    try {
      const res = await extractWatermark(token, asset.id)
      setExtractResult(res)
      const rawText = decodeBase64Utf8(res.payload_b64)
      setRawPayloadText(rawText)
      try {
        setExtractedMetadata(JSON.parse(rawText) as WatermarkPayloadData)
      } catch {
        setExtractedMetadata(null)
      }
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Watermark extraction failed.')
    } finally {
      setIsExtracting(false)
    }
  }

  const handleCopyPayload = () => {
    if (rawPayloadText) {
      void navigator.clipboard.writeText(rawPayloadText)
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    }
  }

  const handleSignOut = () => {
    clearStoredSessionToken()
    setToken(null)
    navigate('/login')
  }

  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      const matchesSearch = asset.original_filename
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
      if (!matchesSearch) return false
      if (filterType === 'watermarked') return asset.derivative_type === 'PNG_LSB'
      if (filterType === 'image') return asset.content_type?.startsWith('image/')
      if (filterType === 'doc') {
        return (
          asset.content_type?.includes('pdf') ||
          asset.content_type?.includes('text') ||
          asset.content_type?.includes('word') ||
          asset.content_type?.includes('document')
        )
      }
      if (filterType === 'archive') {
        return asset.content_type?.includes('zip') || asset.content_type?.includes('compressed')
      }
      return true
    })
  }, [assets, searchQuery, filterType])

  const totalVolumeBytes = useMemo(
    () => assets.reduce((acc, curr) => acc + curr.size_bytes, 0),
    [assets],
  )
  const watermarkedCount = useMemo(
    () => assets.filter((a) => a.derivative_type === 'PNG_LSB').length,
    [assets],
  )

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Asset Vault"
          description="Encrypted file storage protected by XChaCha20-Poly1305 AEAD and PNG LSB steganography."
          breadcrumbs={[
            { label: 'Overview', to: '/overview' },
            { label: 'Asset Vault' },
          ]}
        />
        <Panel>
          <EmptyState
            icon={<FolderLock size={20} />}
            title="Authentication required"
            description="Sign in via QR challenge with your Android device to upload, decrypt, or manage assets."
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Vault"
        description="XChaCha20-Poly1305 encrypted asset storage with Ed25519 PNG LSB watermark lineage."
        breadcrumbs={[
          { label: 'Overview', to: '/overview' },
          { label: 'Asset Vault' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void loadAssets(token)}
              disabled={loading}
              loading={loading}
              iconLeft={!loading ? <RefreshCw size={13} /> : undefined}
            >
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setSelectedFile(null)
                setUploadError(null)
                setIsUploadModalOpen(true)
              }}
              iconLeft={<Plus size={14} />}
            >
              Upload Asset
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

      {error && (
        <ErrorState
          message={error}
          onRetry={() => void loadAssets(token)}
          onDismiss={() => setError(null)}
        />
      )}

      <div className="flex flex-col gap-3 rounded-xl border border-ip-border bg-ip-surface px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-zinc-400">
          <span>
            <strong className="font-semibold text-zinc-100 tabular-nums">
              {assets.length}
            </strong>{' '}
            encrypted assets
          </span>
          <span>
            <strong className="font-semibold text-zinc-100 tabular-nums">
              {formatBytes(totalVolumeBytes)}
            </strong>{' '}
            stored ciphertext
          </span>
          <span>
            <strong className="font-semibold text-ip-accent-300 tabular-nums">
              {watermarkedCount}
            </strong>{' '}
            watermarked derivatives
          </span>
        </div>
        <Link
          to="/steganography"
          className="text-xs font-medium text-ip-accent-400 hover:text-ip-accent-300"
        >
          Open Steganography Lab
        </Link>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="w-full lg:max-w-sm">
          <SearchInput
            value={searchQuery}
            onChangeValue={setSearchQuery}
            placeholder="Search decrypted filenames..."
          />
        </div>
        <Tabs
          options={[
            { id: 'all', label: 'All', count: assets.length },
            {
              id: 'watermarked',
              label: 'Watermarked',
              count: watermarkedCount,
            },
            { id: 'image', label: 'Images' },
            { id: 'doc', label: 'Documents' },
            { id: 'archive', label: 'Archives' },
          ]}
          activeId={filterType}
          onChange={(id) => setFilterType(id as FilterCategory)}
        />
      </div>

      <Panel noPadding>
        {loading && assets.length === 0 ? (
          <div className="p-6">
            <LoadingState message="Decrypting asset inventory..." />
          </div>
        ) : filteredAssets.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={<FolderLock size={20} />}
              title={searchQuery || filterType !== 'all' ? 'No matching assets' : 'Vault is empty'}
              description={
                searchQuery || filterType !== 'all'
                  ? 'Try adjusting your search query or filter category.'
                  : 'Upload your first file to encrypt it with XChaCha20-Poly1305 and a device-bound HKDF key.'
              }
              action={
                !searchQuery && filterType === 'all' ? (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null)
                      setUploadError(null)
                      setIsUploadModalOpen(true)
                    }}
                    iconLeft={<Upload size={14} />}
                  >
                    Upload First Asset
                  </Button>
                ) : (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchQuery('')
                      setFilterType('all')
                    }}
                  >
                    Reset Filters
                  </Button>
                )
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[780px] text-left text-xs">
              <thead className="border-b border-ip-border bg-ip-elevated/40 text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-medium">Asset</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium">Cipher</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ip-border text-zinc-300">
                {filteredAssets.map((asset) => {
                  const isDerivative = asset.derivative_type === 'PNG_LSB'
                  const isPngOriginal =
                    asset.content_type === 'image/png' && !asset.source_asset_id

                  return (
                    <tr key={asset.id} className="hover:bg-ip-elevated/30">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <span className="flex size-8 shrink-0 items-center justify-center rounded-md border border-ip-border bg-ip-elevated">
                            {getFileIcon(asset.content_type, asset.original_filename, isDerivative)}
                          </span>
                          <div className="min-w-0">
                            <p className="max-w-xs truncate font-medium text-zinc-100">
                              {asset.original_filename}
                            </p>
                            <p className="truncate font-mono text-[11px] text-zinc-500">
                              {asset.content_type || 'application/octet-stream'}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-3">
                        {isDerivative ? (
                          <div className="space-y-0.5">
                            <StatusIndicator label="PNG_LSB" tone="accent" />
                            {asset.source_asset_id && (
                              <p className="font-mono text-[11px] text-zinc-500">
                                src {asset.source_asset_id.slice(0, 8)}...
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-zinc-400">
                            <Layers size={12} />
                            Original
                          </span>
                        )}
                      </td>

                      <td className="px-4 py-3 font-mono tabular-nums text-zinc-300">
                        {formatBytes(asset.size_bytes)}
                      </td>

                      <td className="px-4 py-3">
                        <span className="font-mono text-[11px] text-zinc-300">
                          XChaCha20 ({asset.encryption_version})
                        </span>
                      </td>

                      <td className="px-4 py-3 font-mono tabular-nums text-zinc-400">
                        {new Date(asset.created_at).toLocaleDateString()}
                      </td>

                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {isPngOriginal && (
                            <Button
                              variant="secondary"
                              size="sm"
                              onClick={() => openEmbedModal(asset)}
                              iconLeft={<Stamp size={12} />}
                            >
                              Watermark
                            </Button>
                          )}

                          {isDerivative && (
                            <>
                              <IconButton
                                label={`Verify watermark on ${asset.original_filename}`}
                                onClick={() => void handleVerify(asset)}
                              >
                                <ShieldCheck size={14} />
                              </IconButton>
                              <IconButton
                                label={`Extract watermark payload from ${asset.original_filename}`}
                                onClick={() => void handleExtract(asset)}
                              >
                                <FileCode size={14} />
                              </IconButton>
                            </>
                          )}

                          <IconButton
                            label={`Download ${asset.original_filename}`}
                            disabled={downloadingId === asset.id}
                            onClick={() => void handleDownload(asset)}
                          >
                            {downloadingId === asset.id ? (
                              <RefreshCw size={14} className="animate-spin" />
                            ) : (
                              <Download size={14} />
                            )}
                          </IconButton>

                          <IconButton
                            label={`Inspect ${asset.original_filename}`}
                            onClick={() => void handleInspect(asset)}
                          >
                            <Eye size={14} />
                          </IconButton>

                          <IconButton
                            label={`Rename ${asset.original_filename}`}
                            onClick={() => {
                              setRenamingAsset(asset)
                              setNewFilename(asset.original_filename)
                              setRenameError(null)
                            }}
                          >
                            <Edit3 size={14} />
                          </IconButton>

                          <IconButton
                            label={`Delete ${asset.original_filename}`}
                            variant="danger"
                            onClick={() => setDeletingAsset(asset)}
                          >
                            <Trash2 size={14} />
                          </IconButton>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {/* Upload Modal */}
      <Modal
        open={isUploadModalOpen}
        onClose={() => {
          if (!isUploading) setIsUploadModalOpen(false)
        }}
        title="Upload Asset"
        description="Files are encrypted server-side with XChaCha20-Poly1305 bound to your enrolled device."
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          {uploadError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
              {uploadError}
            </div>
          )}

          <div>
            <label
              htmlFor="asset-file-input"
              className="block text-xs font-medium text-zinc-300"
            >
              Select file (max 50 MB)
            </label>
            <input
              id="asset-file-input"
              ref={fileInputRef}
              type="file"
              disabled={isUploading}
              onChange={(e) => {
                setSelectedFile(e.target.files?.[0] ?? null)
                setUploadError(null)
              }}
              className="mt-1.5 block w-full rounded-lg border border-ip-border bg-ip-elevated px-3 py-2 text-xs text-zinc-200 file:mr-3 file:rounded-md file:border-0 file:bg-zinc-700 file:px-2.5 file:py-1 file:text-xs file:font-medium file:text-zinc-100"
              required
            />
            {selectedFile && (
              <p className="mt-1.5 font-mono text-xs text-zinc-400">
                {selectedFile.name} ({formatBytes(selectedFile.size)})
              </p>
            )}
          </div>

          {isUploading && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-zinc-400">
                <span>Encrypting & uploading...</span>
                <span className="font-mono tabular-nums">{uploadProgress}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-ip-elevated">
                <div
                  className="h-full bg-ip-accent-500 transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={isUploading}
              onClick={() => setIsUploadModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!selectedFile || isUploading}
              loading={isUploading}
            >
              {isUploading ? 'Uploading...' : 'Encrypt & Upload'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Inspect / Preview Modal */}
      <Modal
        open={inspectingAsset !== null}
        onClose={() => setInspectingAsset(null)}
        title={inspectingAsset?.original_filename ?? 'Asset Details'}
        description="Cryptographic metadata and decrypted preview"
        maxWidthClass="max-w-xl"
      >
        {inspectingAsset && (
          <div className="space-y-4">
            {inspectingAsset.content_type?.startsWith('image/') && (
              <div className="flex min-h-[160px] items-center justify-center rounded-lg border border-ip-border bg-ip-elevated/50 p-3">
                {isPreviewLoading ? (
                  <LoadingState message="Decrypting image preview..." />
                ) : previewBlobUrl ? (
                  <img
                    src={previewBlobUrl}
                    alt={inspectingAsset.original_filename}
                    className="max-h-64 rounded object-contain"
                  />
                ) : (
                  <span className="text-xs text-zinc-500">Preview unavailable.</span>
                )}
              </div>
            )}

            <KeyValueGrid
              columns={2}
              items={[
                { label: 'Asset ID', value: inspectingAsset.id, mono: true },
                { label: 'Size', value: formatBytes(inspectingAsset.size_bytes), mono: true },
                {
                  label: 'Content Type',
                  value: inspectingAsset.content_type ?? 'application/octet-stream',
                  mono: true,
                },
                {
                  label: 'Encryption',
                  value: inspectingAsset.encryption_version,
                  mono: true,
                },
                { label: 'SHA-256 Digest', value: inspectingAsset.sha256_hash, mono: true },
                {
                  label: 'Derivative Lineage',
                  value: inspectingAsset.derivative_type ?? 'Original Asset',
                },
              ]}
            />

            <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => void handleDownload(inspectingAsset)}
                iconLeft={<Download size={13} />}
              >
                Download
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setInspectingAsset(null)}
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Rename Modal */}
      <Modal
        open={renamingAsset !== null}
        onClose={() => {
          if (!isRenaming) setRenamingAsset(null)
        }}
        title="Rename Asset"
        description={renamingAsset ? `Update filename for ${renamingAsset.original_filename}` : undefined}
      >
        <form onSubmit={handleRenameSubmit} className="space-y-4">
          {renameError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
              {renameError}
            </div>
          )}
          <TextInput
            id="rename-asset-input"
            label="Filename"
            value={newFilename}
            onChange={(e) => setNewFilename(e.target.value)}
            disabled={isRenaming}
            required
          />
          <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={isRenaming}
              onClick={() => setRenamingAsset(null)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isRenaming}
              loading={isRenaming}
            >
              {isRenaming ? 'Saving...' : 'Save Name'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        open={deletingAsset !== null}
        onClose={() => {
          if (!isDeleting) setDeletingAsset(null)
        }}
        onConfirm={() => {
          void handleDeleteConfirm()
        }}
        title="Delete Encrypted Asset"
        description={
          deletingAsset
            ? `Permanently delete "${deletingAsset.original_filename}"? The encrypted file and metadata will be removed.`
            : ''
        }
        confirmLabel="Delete Asset"
        confirmVariant="danger"
        isProcessing={isDeleting}
      />

      {/* Embed Watermark Modal */}
      <Modal
        open={embeddingAsset !== null}
        onClose={() => {
          if (!isEmbedding) setEmbeddingAsset(null)
        }}
        title="Embed PNG Watermark"
        description={
          embeddingAsset
            ? `Create an Ed25519-signed PNG_LSB derivative from "${embeddingAsset.original_filename}".`
            : undefined
        }
        maxWidthClass="max-w-lg"
      >
        {embedSuccess ? (
          <div className="space-y-4">
            <div className="flex items-start gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-200">
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-emerald-400" />
              <div>
                <p className="font-semibold text-zinc-100">Watermarked derivative created</p>
                <p className="mt-0.5 text-zinc-300">
                  Saved encrypted asset: {embedSuccess.derivative.original_filename}
                </p>
              </div>
            </div>
            <KeyValueGrid
              columns={2}
              items={[
                { label: 'Watermark ID', value: embedSuccess.watermark_id, mono: true },
                { label: 'Derivative ID', value: embedSuccess.derivative.id, mono: true },
              ]}
            />
            <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => void handleDownload(embedSuccess.derivative)}
                iconLeft={<Download size={13} />}
              >
                Download PNG
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setEmbeddingAsset(null)}
              >
                Done
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleEmbedSubmit} className="space-y-4">
            {embedError && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
                {embedError}
              </div>
            )}
            <TextInput
              id="wm-copyright"
              label="Copyright Attribution"
              value={wmCopyright}
              onChange={(e) => setWmCopyright(e.target.value)}
              disabled={isEmbedding}
            />
            <TextInput
              id="wm-license"
              label="License Notice"
              value={wmLicense}
              onChange={(e) => setWmLicense(e.target.value)}
              disabled={isEmbedding}
            />
            <TextInput
              id="wm-custom-text"
              label="Custom Attribution Text (Optional)"
              value={wmCustomText}
              onChange={(e) => setWmCustomText(e.target.value)}
              disabled={isEmbedding}
            />
            <TextareaInput
              id="wm-description"
              label="Description / Note (Optional)"
              rows={3}
              value={wmDescription}
              onChange={(e) => setWmDescription(e.target.value)}
              disabled={isEmbedding}
              hint="LSB watermarks are fragile to recompression or scaling. Keep confidential secrets in Secure Notes."
            />
            <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={isEmbedding}
                onClick={() => setEmbeddingAsset(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={isEmbedding}
                disabled={isEmbedding}
              >
                {isEmbedding ? 'Embedding...' : 'Embed & Encrypt Derivative'}
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Verify Watermark Modal */}
      <Modal
        open={verifyingAsset !== null}
        onClose={() => setVerifyingAsset(null)}
        title="Verify Watermark Signature"
        description={verifyingAsset?.original_filename}
      >
        {isVerifying ? (
          <LoadingState message="Verifying IPGW packet and Ed25519 signature..." />
        ) : verifyError ? (
          <ErrorState message={verifyError} />
        ) : verifyResult ? (
          <div className="space-y-4">
            <div
              className={`flex items-start gap-3 rounded-lg border p-3.5 text-xs ${
                verifyResult.verified
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                  : 'border-red-500/30 bg-red-500/10 text-red-200'
              }`}
            >
              {verifyResult.verified ? (
                <ShieldCheck size={18} className="mt-0.5 shrink-0 text-emerald-400" />
              ) : (
                <ShieldAlert size={18} className="mt-0.5 shrink-0 text-red-400" />
              )}
              <div>
                <p className="font-semibold text-zinc-100">
                  {verifyResult.verified
                    ? 'Watermark authentic'
                    : 'Watermark verification failed'}
                </p>
                <p className="mt-0.5 text-zinc-300">Status: {verifyResult.status}</p>
              </div>
            </div>

            <KeyValueGrid
              columns={2}
              items={[
                { label: 'Verification Status', value: verifyResult.status, mono: true },
                {
                  label: 'Watermark ID',
                  value: verifyResult.watermark_id ?? 'Unavailable',
                  mono: true,
                },
                {
                  label: 'Source Asset ID',
                  value: verifyResult.source_asset_id ?? 'Unavailable',
                  mono: true,
                },
                {
                  label: 'Format Version',
                  value: `IPGW v${verifyResult.format_version ?? 1}`,
                  mono: true,
                },
              ]}
            />

            <div className="flex justify-end gap-2 border-t border-ip-border pt-4">
              {verifyResult.verified && verifyingAsset && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    const target = verifyingAsset
                    setVerifyingAsset(null)
                    void handleExtract(target)
                  }}
                >
                  Extract Payload
                </Button>
              )}
              <Button
                variant="primary"
                size="sm"
                onClick={() => setVerifyingAsset(null)}
              >
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Extract Watermark Modal */}
      <Modal
        open={extractingAsset !== null}
        onClose={() => setExtractingAsset(null)}
        title="Extract Watermark Payload"
        description={extractingAsset?.original_filename}
        maxWidthClass="max-w-lg"
      >
        {isExtracting ? (
          <LoadingState message="Verifying signature and extracting payload..." />
        ) : extractError ? (
          <ErrorState message={extractError} />
        ) : extractResult ? (
          <div className="space-y-4">
            <StatusIndicator
              label={
                extractResult.verified
                  ? `Verified (${extractResult.status})`
                  : `Unverified (${extractResult.status})`
              }
              tone={extractResult.verified ? 'success' : 'danger'}
            />

            {extractedMetadata && (
              <KeyValueGrid
                columns={2}
                items={[
                  ...(extractedMetadata.copyright
                    ? [{ label: 'Copyright', value: extractedMetadata.copyright }]
                    : []),
                  ...(extractedMetadata.license
                    ? [{ label: 'License', value: extractedMetadata.license }]
                    : []),
                  ...(extractedMetadata.text
                    ? [{ label: 'Custom Text', value: extractedMetadata.text }]
                    : []),
                  ...(extractedMetadata.description
                    ? [{ label: 'Description', value: extractedMetadata.description }]
                    : []),
                ]}
              />
            )}

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">
                  Raw Payload
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyPayload}
                  iconLeft={copiedPayload ? <Check size={12} /> : <Copy size={12} />}
                >
                  {copiedPayload ? 'Copied' : 'Copy'}
                </Button>
              </div>
              <pre className="max-h-52 overflow-auto whitespace-pre-wrap break-all rounded-lg border border-ip-border bg-ip-elevated/60 p-3 font-mono text-xs text-zinc-200">
                {rawPayloadText}
              </pre>
            </div>

            <div className="flex justify-end border-t border-ip-border pt-4">
              <Button
                variant="primary"
                size="sm"
                onClick={() => setExtractingAsset(null)}
              >
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  )
}
