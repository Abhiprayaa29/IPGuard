import {
  AlertCircle,
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
  HardDrive,
  Image as ImageIcon,
  Layers,
  Lock,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

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

function getFileIcon(mime: string | null, filename: string, isDerivative?: boolean) {
  if (isDerivative) {
    return <Sparkles size={20} className="text-purple-400" />
  }
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (mime?.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) {
    return <ImageIcon size={20} className="text-emerald-400" />
  }
  if (mime === 'application/pdf' || ext === 'pdf') {
    return <FileText size={20} className="text-rose-400" />
  }
  if (
    mime?.includes('zip') ||
    mime?.includes('compressed') ||
    ['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)
  ) {
    return <FileArchive size={20} className="text-purple-400" />
  }
  if (['json', 'js', 'ts', 'tsx', 'py', 'html', 'css', 'md', 'csv'].includes(ext)) {
    return <FileCode size={20} className="text-sky-400" />
  }
  return <File size={20} className="text-slate-400" />
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

  // 1. Session Token Resolution
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
  const [filterType, setFilterType] = useState<'all' | 'image' | 'watermarked' | 'doc' | 'archive'>('all')

  // Modals & Action States
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Rename State
  const [renamingAsset, setRenamingAsset] = useState<Asset | null>(null)
  const [newFilename, setNewFilename] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameError, setRenameError] = useState<string | null>(null)

  // Delete State
  const [deletingAsset, setDeletingAsset] = useState<Asset | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Detail / Preview State
  const [inspectingAsset, setInspectingAsset] = useState<Asset | null>(null)
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)

  // Download State
  const [downloadingId, setDownloadingId] = useState<string | null>(null)

  // -------------------------------------------------------------------------
  // M4 Steganography & Watermarking States
  // -------------------------------------------------------------------------
  // Embed Watermark Modal
  const [embeddingAsset, setEmbeddingAsset] = useState<Asset | null>(null)
  const [isEmbedding, setIsEmbedding] = useState(false)
  const [embedError, setEmbedError] = useState<string | null>(null)
  const [embedSuccess, setEmbedSuccess] = useState<{
    derivative: Asset
    watermark_id: string
    format_version: number
  } | null>(null)

  // Custom metadata form
  const [wmCopyright, setWmCopyright] = useState('© 2026 IPGuard Vault. All rights reserved.')
  const [wmLicense, setWmLicense] = useState('Proprietary / All Rights Reserved')
  const [wmCustomText, setWmCustomText] = useState('')
  const [wmDescription, setWmDescription] = useState('')

  // Watermark Verification Modal
  const [verifyingAsset, setVerifyingAsset] = useState<Asset | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState<WatermarkVerifyResponse | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)

  // Watermark Extraction Modal
  const [extractingAsset, setExtractingAsset] = useState<Asset | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractResult, setExtractResult] = useState<WatermarkExtractResponse | null>(null)
  const [extractError, setExtractError] = useState<string | null>(null)
  const [extractedMetadata, setExtractedMetadata] = useState<WatermarkPayloadData | null>(null)
  const [rawPayloadText, setRawPayloadText] = useState<string>('')
  const [copiedPayload, setCopiedPayload] = useState(false)

  // Load assets from backend
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
      loadAssets(token)
    } else {
      setLoading(false)
    }
  }, [token, loadAssets])

  // Cleanup object URL when preview modal closes
  useEffect(() => {
    if (!inspectingAsset && previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl)
      setPreviewBlobUrl(null)
    }
  }, [inspectingAsset, previewBlobUrl])

  // Handle file download (works for both originals and watermarked derivatives)
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
      alert(err instanceof Error ? err.message : 'Download failed.')
    } finally {
      setDownloadingId(null)
    }
  }

  // Handle Inspect Asset & load preview
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
        // Fallback gracefully without preview
      } finally {
        setIsPreviewLoading(false)
      }
    }
  }

  // Handle Upload
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedFile) return

    if (selectedFile.size === 0) {
      setUploadError('File cannot be empty (0 bytes).')
      return
    }

    if (selectedFile.size > 50 * 1024 * 1024) {
      setUploadError('File exceeds the 50 MB security limit.')
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
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  // Handle Rename
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
    } catch (err) {
      setRenameError(err instanceof Error ? err.message : 'Rename failed.')
    } finally {
      setIsRenaming(false)
    }
  }

  // Handle Delete
  const handleDeleteConfirm = async () => {
    if (!token || !deletingAsset) return
    try {
      setIsDeleting(true)
      await deleteAsset(token, deletingAsset.id)
      setAssets((prev) => prev.filter((a) => a.id !== deletingAsset.id))
      setDeletingAsset(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed.')
    } finally {
      setIsDeleting(false)
    }
  }

  // -------------------------------------------------------------------------
  // M4 Steganography Actions
  // -------------------------------------------------------------------------

  // Open Embed Modal
  const openEmbedModal = (asset: Asset) => {
    setEmbeddingAsset(asset)
    setEmbedError(null)
    setEmbedSuccess(null)
    setWmCustomText('')
    setWmDescription('')
  }

  // Submit Watermark Embedding
  const handleEmbedSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !embeddingAsset) return

    try {
      setIsEmbedding(true)
      setEmbedError(null)

      // Construct structured metadata payload
      const payloadObj: WatermarkPayloadData = {
        copyright: wmCopyright.trim() || undefined,
        license: wmLicense.trim() || undefined,
        text: wmCustomText.trim() || undefined,
        description: wmDescription.trim() || undefined,
        timestamp: new Date().toISOString(),
      }

      // Convert JSON string to UTF-8 Base64
      const jsonStr = JSON.stringify(payloadObj)
      const base64Payload = btoa(
        encodeURIComponent(jsonStr).replace(/%([0-9A-F]{2})/g, (_, p1) =>
          String.fromCharCode(parseInt(p1, 16)),
        ),
      )

      const result = await embedWatermark(token, embeddingAsset.id, base64Payload)
      setEmbedSuccess(result)

      // Prepend the new derivative asset to the list
      setAssets((prev) => [result.derivative, ...prev])
    } catch (err) {
      setEmbedError(err instanceof Error ? err.message : 'Watermark embedding failed.')
    } finally {
      setIsEmbedding(false)
    }
  }

  // Handle Watermark Verification
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

  // Handle Watermark Extraction
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

      // Decode Base64 to text
      const rawText = decodeBase64Utf8(res.payload_b64)
      setRawPayloadText(rawText)

      // Attempt parsing as JSON metadata
      try {
        const parsed = JSON.parse(rawText) as WatermarkPayloadData
        setExtractedMetadata(parsed)
      } catch {
        // Plain string watermark
        setExtractedMetadata(null)
      }
    } catch (err) {
      setExtractError(err instanceof Error ? err.message : 'Watermark extraction failed.')
    } finally {
      setIsExtracting(false)
    }
  }

  // Copy payload to clipboard
  const handleCopyPayload = () => {
    if (rawPayloadText) {
      navigator.clipboard.writeText(rawPayloadText)
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    }
  }

  // Filter & Search Logic
  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      const matchesSearch = asset.original_filename
        .toLowerCase()
        .includes(searchQuery.toLowerCase())
      if (!matchesSearch) return false

      if (filterType === 'watermarked') {
        return asset.derivative_type === 'PNG_LSB'
      }
      if (filterType === 'image') {
        return asset.content_type?.startsWith('image/')
      }
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

  // Total storage volume and derivative counts
  const totalVolumeBytes = useMemo(() => {
    return assets.reduce((acc, curr) => acc + curr.size_bytes, 0)
  }, [assets])

  const watermarkedCount = useMemo(() => {
    return assets.filter((a) => a.derivative_type === 'PNG_LSB').length
  }, [assets])

  // -------------------------------------------------------------------------
  // Unauthenticated Fallback View
  // -------------------------------------------------------------------------
  if (!token) {
    return (
      <div className="mx-auto max-w-xl py-12 text-center animate-fade-in">
        <div className="mx-auto grid size-16 place-items-center rounded-3xl border border-amber-400/30 bg-amber-400/10 text-amber-400 mb-6">
          <FolderLock size={32} />
        </div>
        <h1 className="font-display text-2xl font-bold text-white">
          Asset Vault Locked
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Hardware authentication required. Please scan the QR code with your registered
          Android Authenticator to unlock military-grade encrypted storage.
        </p>
        <div className="mt-8">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 px-6 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/25 shadow-lg"
          >
            Authenticate via QR
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-white/[0.08] pb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-400/25 bg-purple-400/10 px-3 py-1 text-xs font-semibold text-purple-300 mb-2">
            <Sparkles size={13} />
            Milestone 4 • Cryptographic Steganography & Asset Vault
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Asset Vault & Steganography
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Encrypted with true XChaCha20-Poly1305 AEAD. Embed invisible, tamper-evident
            Ed25519-signed watermarks directly into PNG image bits with verified cryptographic lineage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => loadAssets(token)}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => {
              setSelectedFile(null)
              setUploadError(null)
              setIsUploadModalOpen(true)
            }}
            className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/20 px-4 py-2 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/30 shadow-md"
          >
            <Plus size={14} />
            Upload Asset
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Encrypted Assets</span>
            <FolderLock size={16} className="text-ip-teal-400" />
          </div>
          <p className="mt-2 text-2xl font-bold font-display text-white">{assets.length}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {watermarkedCount} watermarked derivative{watermarkedCount !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Stored Volume</span>
            <HardDrive size={16} className="text-ip-gold-400" />
          </div>
          <p className="mt-2 text-2xl font-bold font-display text-white">
            {formatBytes(totalVolumeBytes)}
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">XChaCha20-Poly1305 Ciphertexts</p>
        </div>

        <div className="rounded-2xl border border-purple-400/20 bg-purple-950/20 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Watermark Engine</span>
            <Sparkles size={16} className="text-purple-400" />
          </div>
          <p className="mt-2 text-xs font-mono font-semibold text-purple-300">
            IPGW v1 • Ed25519
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">1-bit LSB • SHA-256 Digest</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Session Status</span>
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="mt-2 text-xs font-semibold text-emerald-300">
            Hardware-Bound Active
          </p>
          <button
            type="button"
            onClick={() => {
              clearStoredSessionToken()
              setToken(null)
              navigate('/login')
            }}
            className="text-[10px] text-slate-400 hover:text-rose-300 mt-1 block"
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search and Filters Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search decrypted filenames..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-slate-900/60 pl-9 pr-4 py-2 text-xs text-white placeholder:text-slate-500 focus:border-ip-teal-400/50 focus:outline-none focus:ring-1 focus:ring-ip-teal-400/50"
          />
        </div>

        <div className="flex items-center gap-2">
          {(['all', 'image', 'watermarked', 'doc', 'archive'] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setFilterType(type)}
              className={`rounded-xl px-3 py-1.5 text-xs font-semibold capitalize transition ${
                filterType === type
                  ? 'border border-ip-teal-400/30 bg-ip-teal-400/15 text-ip-teal-300'
                  : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
              }`}
            >
              {type === 'watermarked' ? 'Watermarked (M4)' : type}
            </button>
          ))}
        </div>
      </div>

      {/* Asset Table / List */}
      {loading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-white/10 bg-slate-900/40">
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <RefreshCw size={16} className="animate-spin text-ip-teal-400" />
            Decrypting asset metadata...
          </div>
        </div>
      ) : filteredAssets.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/[0.08] bg-slate-900/30 py-16 text-center">
          <div className="grid size-12 place-items-center rounded-2xl border border-white/10 bg-white/5 text-slate-500 mb-3">
            <FolderLock size={24} />
          </div>
          <h3 className="font-display text-base font-semibold text-white">No Assets Found</h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            {searchQuery
              ? 'No encrypted files match your search query.'
              : 'Your vault is currently empty. Upload your first digital asset.'}
          </p>
          {!searchQuery && (
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              className="mt-4 inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/20 px-4 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/30"
            >
              <Upload size={13} />
              Upload Now
            </button>
          )}
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/10 bg-white/[0.02] text-slate-400">
                <tr>
                  <th className="px-5 py-3.5 font-semibold">Asset Name</th>
                  <th className="px-5 py-3.5 font-semibold">Type & Lineage</th>
                  <th className="px-5 py-3.5 font-semibold">Size</th>
                  <th className="px-5 py-3.5 font-semibold">Cipher Protocol</th>
                  <th className="px-5 py-3.5 font-semibold">Uploaded</th>
                  <th className="px-5 py-3.5 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.06] text-slate-300">
                {filteredAssets.map((asset) => {
                  const isDerivative = asset.derivative_type === 'PNG_LSB'
                  const isPngOriginal =
                    asset.content_type === 'image/png' && !asset.source_asset_id

                  return (
                    <tr key={asset.id} className="transition hover:bg-white/[0.02]">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="grid size-9 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/5">
                            {getFileIcon(asset.content_type, asset.original_filename, isDerivative)}
                          </div>
                          <div className="min-w-0">
                            <p className="font-semibold text-white truncate max-w-xs sm:max-w-md">
                              {asset.original_filename}
                            </p>
                            <p className="text-[10px] text-slate-500 truncate">
                              {asset.content_type || 'application/octet-stream'}
                            </p>
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        {isDerivative ? (
                          <div className="flex flex-col gap-1 items-start">
                            <span className="inline-flex items-center gap-1 rounded-full border border-purple-400/30 bg-purple-400/15 px-2 py-0.5 text-[10px] font-semibold text-purple-300">
                              <Sparkles size={10} />
                              PNG_LSB Derivative
                            </span>
                            {asset.source_asset_id && (
                              <span className="text-[9px] text-slate-500 font-mono">
                                from {asset.source_asset_id.slice(0, 8)}...
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400">
                            <Layers size={11} />
                            Original Asset
                          </span>
                        )}
                      </td>

                      <td className="px-5 py-4 font-mono text-slate-300">
                        {formatBytes(asset.size_bytes)}
                      </td>

                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-0.5 text-[10px] font-mono font-medium text-emerald-300">
                          <Lock size={10} />
                          XChaCha20 • {asset.encryption_version}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-slate-400">
                        {new Date(asset.created_at).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* M4 Steganography Actions */}
                          {isPngOriginal && (
                            <button
                              type="button"
                              onClick={() => openEmbedModal(asset)}
                              title="Embed Cryptographic Watermark"
                              className="inline-flex items-center gap-1 rounded-lg border border-purple-400/40 bg-purple-400/15 px-2.5 py-1.5 text-[11px] font-semibold text-purple-300 hover:bg-purple-400/25 transition shadow-sm"
                            >
                              <Sparkles size={12} />
                              <span>Watermark</span>
                            </button>
                          )}

                          {isDerivative && (
                            <>
                              <button
                                type="button"
                                onClick={() => handleVerify(asset)}
                                title="Verify Watermark Signature & Integrity"
                                className="grid size-8 place-items-center rounded-lg border border-emerald-400/30 bg-emerald-400/10 text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-400/20 transition"
                              >
                                <ShieldCheck size={14} />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleExtract(asset)}
                                title="Extract Watermark Payload"
                                className="grid size-8 place-items-center rounded-lg border border-purple-400/30 bg-purple-400/10 text-purple-300 hover:border-purple-400/50 hover:bg-purple-400/20 transition"
                              >
                                <FileCode size={14} />
                              </button>
                            </>
                          )}

                          {/* Standard Vault Actions */}
                          <button
                            type="button"
                            onClick={() => handleDownload(asset)}
                            disabled={downloadingId === asset.id}
                            title={isDerivative ? 'Download Decrypted Watermarked PNG' : 'Download & Decrypt Asset'}
                            className={`grid size-8 place-items-center rounded-lg border transition ${
                              isDerivative
                                ? 'border-ip-teal-400/40 bg-ip-teal-400/15 text-ip-teal-300 hover:bg-ip-teal-400/25'
                                : 'border-white/10 bg-white/5 text-slate-300 hover:border-ip-teal-400/40 hover:text-ip-teal-300 hover:bg-ip-teal-400/10'
                            }`}
                          >
                            {downloadingId === asset.id ? (
                              <RefreshCw size={13} className="animate-spin text-ip-teal-400" />
                            ) : (
                              <Download size={13} />
                            )}
                          </button>

                          <button
                            type="button"
                            onClick={() => handleInspect(asset)}
                            title="Inspect Metadata & Preview"
                            className="grid size-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-slate-300 hover:border-white/30 hover:text-white transition"
                          >
                            <Eye size={13} />
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              setRenamingAsset(asset)
                              setNewFilename(asset.original_filename)
                              setRenameError(null)
                            }}
                            title="Rename Asset"
                            className="grid size-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-slate-300 hover:border-amber-400/40 hover:text-amber-300 hover:bg-amber-400/10 transition"
                          >
                            <Edit3 size={13} />
                          </button>

                          <button
                            type="button"
                            onClick={() => setDeletingAsset(asset)}
                            title="Delete Asset"
                            className="grid size-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-slate-300 hover:border-rose-400/40 hover:text-rose-300 hover:bg-rose-400/10 transition"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* M4 Steganography: Embed Watermark Modal */}
      {/* --------------------------------------------------------------------- */}
      {embeddingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-xl rounded-3xl border border-purple-500/30 bg-slate-900 p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-xl border border-purple-400/40 bg-purple-400/15 text-purple-300">
                  <Sparkles size={16} />
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-white">
                    Embed Cryptographic Watermark
                  </h3>
                  <p className="text-[10px] text-slate-400">
                    Invisible PNG LSB Steganography with Ed25519 Hardware Signature
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => !isEmbedding && setEmbeddingAsset(null)}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            {embedSuccess ? (
              <div className="mt-6 flex flex-col gap-4 animate-fade-in">
                <div className="flex items-center gap-3 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-emerald-300">
                  <CheckCircle2 size={24} className="shrink-0" />
                  <div>
                    <h4 className="font-semibold text-sm">Watermark Embedded Successfully!</h4>
                    <p className="text-xs text-emerald-400/80 mt-0.5">
                      Derivative asset has been cryptographically signed and stored in the encrypted vault.
                    </p>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-slate-950 p-4 flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Derivative Filename:</span>
                    <span className="font-semibold text-white font-mono">
                      {embedSuccess.derivative.original_filename}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Derivative Asset ID:</span>
                    <span className="font-mono text-slate-300 text-[11px]">
                      {embedSuccess.derivative.id}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Watermark UUID:</span>
                    <span className="font-mono text-purple-300 text-[11px]">
                      {embedSuccess.watermark_id}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Steganography Framing:</span>
                    <span className="font-semibold text-slate-300">
                      IPGW Version {embedSuccess.format_version}
                    </span>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setEmbeddingAsset(null)}
                    className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      handleDownload(embedSuccess.derivative)
                      setEmbeddingAsset(null)
                    }}
                    className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/20 px-5 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/30"
                  >
                    <Download size={13} />
                    Download Watermarked Image
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleEmbedSubmit} className="mt-5 flex flex-col gap-4">
                {/* Source Asset Info Card */}
                <div className="rounded-2xl border border-white/10 bg-slate-950 p-3.5 text-xs">
                  <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">
                    Source PNG Image
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white truncate max-w-sm">
                      {embeddingAsset.original_filename}
                    </span>
                    <span className="font-mono text-slate-400">
                      {formatBytes(embeddingAsset.size_bytes)}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">
                    Original image will remain untouched. A watermarked derivative asset will be created.
                  </p>
                </div>

                {/* Cryptographic Parameters Preview (Automatic) */}
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
                    <span className="text-[9px] uppercase font-semibold text-slate-500 block">
                      Signing Algorithm
                    </span>
                    <span className="font-mono text-emerald-400 font-medium">Ed25519 (Hardware)</span>
                  </div>
                  <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
                    <span className="text-[9px] uppercase font-semibold text-slate-500 block">
                      Integrity Digest
                    </span>
                    <span className="font-mono text-ip-teal-400 font-medium">SHA-256 Digest</span>
                  </div>
                </div>

                {/* Metadata Fields */}
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Copyright Notice
                  </label>
                  <input
                    type="text"
                    value={wmCopyright}
                    onChange={(e) => setWmCopyright(e.target.value)}
                    placeholder="e.g. © 2026 Your Name / Company"
                    className="w-full rounded-xl border border-white/10 bg-slate-950 px-3.5 py-2 text-xs text-white focus:border-purple-400/50 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    License Information
                  </label>
                  <input
                    type="text"
                    value={wmLicense}
                    onChange={(e) => setWmLicense(e.target.value)}
                    placeholder="e.g. Proprietary / CC-BY-NC 4.0"
                    className="w-full rounded-xl border border-white/10 bg-slate-950 px-3.5 py-2 text-xs text-white focus:border-purple-400/50 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Custom Watermark Text / Statement (Optional)
                  </label>
                  <input
                    type="text"
                    value={wmCustomText}
                    onChange={(e) => setWmCustomText(e.target.value)}
                    placeholder="e.g. Confidential Asset - Licensed for John Doe"
                    className="w-full rounded-xl border border-white/10 bg-slate-950 px-3.5 py-2 text-xs text-white focus:border-purple-400/50 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Asset Description (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={wmDescription}
                    onChange={(e) => setWmDescription(e.target.value)}
                    placeholder="Additional context or distribution metadata..."
                    className="w-full rounded-xl border border-white/10 bg-slate-950 px-3.5 py-2 text-xs text-white focus:border-purple-400/50 focus:outline-none resize-none"
                  />
                </div>

                {embedError && (
                  <p className="text-xs text-rose-400 flex items-center gap-1.5">
                    <AlertCircle size={14} className="shrink-0" />
                    <span>{embedError}</span>
                  </p>
                )}

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    disabled={isEmbedding}
                    onClick={() => setEmbeddingAsset(null)}
                    className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isEmbedding}
                    className="inline-flex items-center gap-2 rounded-xl border border-purple-500/40 bg-purple-500/20 px-5 py-2 text-xs font-semibold text-purple-300 hover:bg-purple-500/30 disabled:opacity-50 shadow-md"
                  >
                    {isEmbedding ? (
                      <>
                        <RefreshCw size={13} className="animate-spin text-purple-400" />
                        Embedding & Signing...
                      </>
                    ) : (
                      <>
                        <Sparkles size={13} />
                        Embed Watermark
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* M4 Steganography: Verify Watermark Modal */}
      {/* --------------------------------------------------------------------- */}
      {verifyingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-xl border border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
                  <ShieldCheck size={16} />
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-white">
                    Watermark Cryptographic Verification
                  </h3>
                  <p className="text-[10px] text-slate-400 truncate max-w-xs">
                    {verifyingAsset.original_filename}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setVerifyingAsset(null)}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-5 flex flex-col gap-4">
              {isVerifying ? (
                <div className="flex flex-col items-center justify-center py-8 gap-3">
                  <RefreshCw size={24} className="animate-spin text-emerald-400" />
                  <p className="text-xs text-slate-400">
                    Extracting IPGW frame, verifying Ed25519 signature & SHA-256 digest...
                  </p>
                </div>
              ) : verifyError ? (
                <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
                  <ShieldAlert size={20} className="shrink-0 text-rose-400" />
                  <div>
                    <h4 className="font-semibold">Verification Request Failed</h4>
                    <p className="text-[11px] text-rose-400/90 mt-0.5">{verifyError}</p>
                  </div>
                </div>
              ) : verifyResult ? (
                <div className="flex flex-col gap-3">
                  {verifyResult.verified ? (
                    <div className="flex items-center gap-3 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 p-4 text-emerald-300">
                      <CheckCircle2 size={24} className="shrink-0 text-emerald-400" />
                      <div>
                        <h4 className="font-semibold text-sm">Watermark Verified & Authentic</h4>
                        <p className="text-xs text-emerald-400/80 mt-0.5">
                          Ed25519 digital signature and SHA-256 payload integrity check passed.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-300">
                      <ShieldAlert size={24} className="shrink-0 text-rose-400" />
                      <div>
                        <h4 className="font-semibold text-sm">Watermark Integrity Compromised</h4>
                        <p className="text-xs text-rose-400/80 mt-0.5">
                          Status: {verifyResult.status}. Image pixels or cryptographic frame have been tampered with.
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="rounded-2xl border border-white/10 bg-slate-950 p-4 flex flex-col gap-2 text-xs">
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Status Code:</span>
                      <span className="font-mono font-semibold text-white">
                        {verifyResult.status}
                      </span>
                    </div>
                    {verifyResult.watermark_id && (
                      <div className="flex justify-between items-center text-slate-400">
                        <span>Watermark ID:</span>
                        <span className="font-mono text-purple-300 text-[11px]">
                          {verifyResult.watermark_id}
                        </span>
                      </div>
                    )}
                    {verifyResult.source_asset_id && (
                      <div className="flex justify-between items-center text-slate-400">
                        <span>Source Asset ID:</span>
                        <span className="font-mono text-slate-300 text-[11px]">
                          {verifyResult.source_asset_id}
                        </span>
                      </div>
                    )}
                    {verifyResult.derivative_asset_id && (
                      <div className="flex justify-between items-center text-slate-400">
                        <span>Derivative ID:</span>
                        <span className="font-mono text-slate-300 text-[11px]">
                          {verifyResult.derivative_asset_id}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between items-center text-slate-400">
                      <span>Format Protocol:</span>
                      <span className="font-semibold text-slate-300">
                        IPGW Frame v{verifyResult.format_version || 1}
                      </span>
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setVerifyingAsset(null)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Close
                </button>
                {verifyResult?.verified && (
                  <button
                    type="button"
                    onClick={() => {
                      const target = verifyingAsset
                      setVerifyingAsset(null)
                      if (target) handleExtract(target)
                    }}
                    className="inline-flex items-center gap-2 rounded-xl border border-purple-400/30 bg-purple-400/20 px-5 py-2 text-xs font-semibold text-purple-300 hover:bg-purple-400/30"
                  >
                    <FileCode size={13} />
                    Extract Verified Payload
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* M4 Steganography: Extract Watermark Payload Modal */}
      {/* --------------------------------------------------------------------- */}
      {extractingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-xl rounded-3xl border border-purple-400/30 bg-slate-900 p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-xl border border-purple-400/40 bg-purple-400/15 text-purple-300">
                  <FileCode size={16} />
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-white">
                    Verified Watermark Payload
                  </h3>
                  <p className="text-[10px] text-slate-400 truncate max-w-xs">
                    {extractingAsset.original_filename}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setExtractingAsset(null)}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-5 flex flex-col gap-4">
              {isExtracting ? (
                <div className="flex flex-col items-center justify-center py-8 gap-3">
                  <RefreshCw size={24} className="animate-spin text-purple-400" />
                  <p className="text-xs text-slate-400">
                    Executing server verification & extracting authenticated payload...
                  </p>
                </div>
              ) : extractError ? (
                <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
                  <ShieldAlert size={20} className="shrink-0 text-rose-400" />
                  <div>
                    <h4 className="font-semibold">Payload Extraction Blocked</h4>
                    <p className="text-[11px] text-rose-400/90 mt-0.5">{extractError}</p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      Payloads are only released after the server cryptographically verifies the Ed25519 signature.
                    </p>
                  </div>
                </div>
              ) : extractResult ? (
                <div className="flex flex-col gap-4">
                  <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-3.5 py-2 text-xs text-emerald-300">
                    <Check size={14} className="text-emerald-400" />
                    <span>Cryptographically Authenticated (Ed25519 & SHA-256 Valid)</span>
                  </div>

                  {/* Parsed JSON Metadata Display */}
                  {extractedMetadata && (
                    <div className="rounded-2xl border border-white/10 bg-slate-950 p-4 flex flex-col gap-3 text-xs">
                      <span className="text-[10px] uppercase font-semibold text-slate-500">
                        Extracted Metadata
                      </span>
                      {extractedMetadata.copyright && (
                        <div>
                          <span className="text-[10px] text-slate-400 block">Copyright:</span>
                          <p className="font-semibold text-white">{extractedMetadata.copyright}</p>
                        </div>
                      )}
                      {extractedMetadata.license && (
                        <div>
                          <span className="text-[10px] text-slate-400 block">License:</span>
                          <p className="font-semibold text-slate-200">{extractedMetadata.license}</p>
                        </div>
                      )}
                      {extractedMetadata.text && (
                        <div>
                          <span className="text-[10px] text-slate-400 block">Custom Statement:</span>
                          <p className="font-mono text-purple-300 bg-purple-950/30 p-2 rounded-lg border border-purple-500/20">
                            {extractedMetadata.text}
                          </p>
                        </div>
                      )}
                      {extractedMetadata.description && (
                        <div>
                          <span className="text-[10px] text-slate-400 block">Description:</span>
                          <p className="text-slate-300">{extractedMetadata.description}</p>
                        </div>
                      )}
                      {extractedMetadata.timestamp && (
                        <div>
                          <span className="text-[10px] text-slate-400 block">Embedded At:</span>
                          <p className="text-slate-300 font-mono text-[11px]">
                            {new Date(extractedMetadata.timestamp).toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Raw Decoded Content Box */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                        Raw Decoded Payload
                      </label>
                      <button
                        type="button"
                        onClick={handleCopyPayload}
                        className="inline-flex items-center gap-1 text-[10px] text-slate-400 hover:text-white"
                      >
                        {copiedPayload ? (
                          <>
                            <Check size={11} className="text-emerald-400" />
                            <span className="text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy size={11} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="rounded-xl border border-white/10 bg-slate-950 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap break-all max-h-36 overflow-y-auto">
                      {rawPayloadText}
                    </pre>
                  </div>
                </div>
              ) : null}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setExtractingAsset(null)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Upload Modal with Drag and Drop */}
      {/* --------------------------------------------------------------------- */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300">
                  <Upload size={15} />
                </div>
                <h3 className="font-display text-lg font-bold text-white">Upload Digital Asset</h3>
              </div>
              <button
                type="button"
                onClick={() => !isUploading && setIsUploadModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="mt-5 flex flex-col gap-4">
              {/* Drag and Drop Zone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setIsDragging(true)
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setIsDragging(false)
                  if (e.dataTransfer.files?.[0]) {
                    setSelectedFile(e.dataTransfer.files[0])
                    setUploadError(null)
                  }
                }}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition ${
                  isDragging
                    ? 'border-ip-teal-400 bg-ip-teal-400/10'
                    : 'border-white/15 bg-white/[0.02] hover:border-white/30 hover:bg-white/[0.04]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setSelectedFile(e.target.files[0])
                      setUploadError(null)
                    }
                  }}
                />

                <div className="grid size-12 place-items-center rounded-2xl border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 mb-3">
                  <Upload size={20} />
                </div>

                {selectedFile ? (
                  <div className="flex flex-col items-center">
                    <p className="font-semibold text-white text-xs">{selectedFile.name}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {formatBytes(selectedFile.size)} • Ready for encryption
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <p className="text-xs font-semibold text-white">
                      Click to browse or drag and drop file here
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1">
                      PNG images (for watermarking), PDFs, Documents, Archives (Max: 50 MB)
                    </p>
                  </div>
                )}
              </div>

              {uploadProgress > 0 && isUploading && (
                <div className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-[10px] text-slate-400">
                    <span>Encrypting & Uploading</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-ip-teal-400 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {uploadError && (
                <p className="text-xs text-rose-400 flex items-center gap-1.5">
                  <AlertCircle size={13} />
                  {uploadError}
                </p>
              )}

              <div className="mt-2 flex justify-end gap-3">
                <button
                  type="button"
                  disabled={isUploading}
                  onClick={() => setIsUploadModalOpen(false)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/20 px-5 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/30 disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw size={13} className="animate-spin" />
                      Encrypting...
                    </>
                  ) : (
                    <>
                      <Lock size={13} />
                      Encrypt & Save
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Rename Modal */}
      {/* --------------------------------------------------------------------- */}
      {renamingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
            <h3 className="font-display text-lg font-bold text-white">Rename Asset</h3>
            <p className="mt-1 text-xs text-slate-400">
              Update original filename for identification. Encrypted contents remain untouched.
            </p>

            <form onSubmit={handleRenameSubmit} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
                  Filename
                </label>
                <input
                  type="text"
                  value={newFilename}
                  onChange={(e) => setNewFilename(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-slate-950 px-3.5 py-2.5 text-xs text-white focus:border-amber-400/50 focus:outline-none"
                  autoFocus
                />
              </div>

              {renameError && (
                <p className="text-xs text-rose-400 flex items-center gap-1.5">
                  <AlertCircle size={13} />
                  {renameError}
                </p>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  disabled={isRenaming}
                  onClick={() => setRenamingAsset(null)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRenaming}
                  className="rounded-xl border border-amber-400/30 bg-amber-400/20 px-5 py-2 text-xs font-semibold text-amber-300 hover:bg-amber-400/30"
                >
                  {isRenaming ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Delete Confirmation Modal */}
      {/* --------------------------------------------------------------------- */}
      {deletingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-3xl border border-rose-500/30 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-400 mb-3">
              <Trash2 size={22} />
              <h3 className="font-display text-lg font-bold text-white">Delete Digital Asset</h3>
            </div>
            <p className="text-xs text-slate-300">
              Are you sure you want to permanently delete{' '}
              <strong className="text-white">{deletingAsset.original_filename}</strong>?
            </p>
            <p className="mt-2 text-[11px] text-slate-500">
              This will irreversibly delete the metadata record from PostgreSQL and unlinks the
              encrypted ciphertext binary from physical storage.
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setDeletingAsset(null)}
                className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleDeleteConfirm}
                className="rounded-xl border border-rose-500/40 bg-rose-500/20 px-5 py-2 text-xs font-semibold text-rose-300 hover:bg-rose-500/30"
              >
                {isDeleting ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Inspect & Preview Modal */}
      {/* --------------------------------------------------------------------- */}
      {inspectingAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-slate-900 p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid size-8 place-items-center rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300">
                  <Eye size={15} />
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-white">
                    {inspectingAsset.original_filename}
                  </h3>
                  <p className="text-[10px] text-slate-500 font-mono">ID: {inspectingAsset.id}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setInspectingAsset(null)}
                className="text-slate-400 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            {/* Optional Image Preview */}
            {inspectingAsset.content_type?.startsWith('image/') && (
              <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950 p-3 flex items-center justify-center min-h-[180px]">
                {isPreviewLoading ? (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <RefreshCw size={14} className="animate-spin text-ip-teal-400" />
                    Decrypting preview...
                  </div>
                ) : previewBlobUrl ? (
                  <img
                    src={previewBlobUrl}
                    alt={inspectingAsset.original_filename}
                    className="max-h-72 object-contain rounded-xl shadow-lg"
                  />
                ) : (
                  <p className="text-xs text-slate-500">Preview not available.</p>
                )}
              </div>
            )}

            {/* Technical Specifications */}
            <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <span className="text-[10px] uppercase font-semibold text-slate-500">
                  MIME Content-Type
                </span>
                <p className="font-mono text-white mt-1">
                  {inspectingAsset.content_type || 'application/octet-stream'}
                </p>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <span className="text-[10px] uppercase font-semibold text-slate-500">File Size</span>
                <p className="font-mono text-white mt-1">
                  {formatBytes(inspectingAsset.size_bytes)} ({inspectingAsset.size_bytes} bytes)
                </p>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <span className="text-[10px] uppercase font-semibold text-slate-500">
                  Cipher Suite & Version
                </span>
                <p className="font-mono text-emerald-300 mt-1 flex items-center gap-1">
                  <Check size={12} />
                  XChaCha20-Poly1305 ({inspectingAsset.encryption_version})
                </p>
              </div>

              <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <span className="text-[10px] uppercase font-semibold text-slate-500">
                  Registration Timestamp
                </span>
                <p className="text-white mt-1">
                  {new Date(inspectingAsset.created_at).toLocaleString()}
                </p>
              </div>

              {/* M4 Stego Details if derivative */}
              {inspectingAsset.derivative_type === 'PNG_LSB' && (
                <>
                  <div className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-3">
                    <span className="text-[10px] uppercase font-semibold text-purple-400">
                      Steganography Lineage
                    </span>
                    <p className="font-mono text-[11px] text-purple-300 mt-1">
                      Source Asset: {inspectingAsset.source_asset_id}
                    </p>
                  </div>
                  <div className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-3">
                    <span className="text-[10px] uppercase font-semibold text-purple-400">
                      Watermark UUID
                    </span>
                    <p className="font-mono text-[11px] text-purple-300 mt-1">
                      {inspectingAsset.watermark_id || 'Embedded IPGW'}
                    </p>
                  </div>
                </>
              )}

              <div className="sm:col-span-2 rounded-xl border border-white/5 bg-white/[0.02] p-3">
                <span className="text-[10px] uppercase font-semibold text-slate-500">
                  SHA-256 Ciphertext Digest (M3 Baseline Integrity)
                </span>
                <p className="font-mono text-[11px] text-slate-300 break-all mt-1">
                  {inspectingAsset.sha256_hash}
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-between items-center gap-3">
              <div>
                {inspectingAsset.derivative_type === 'PNG_LSB' ? (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        const target = inspectingAsset
                        setInspectingAsset(null)
                        handleVerify(target)
                      }}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-400/20"
                    >
                      <ShieldCheck size={13} />
                      Verify Watermark
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const target = inspectingAsset
                        setInspectingAsset(null)
                        handleExtract(target)
                      }}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-purple-400/30 bg-purple-400/10 px-3 py-1.5 text-xs font-semibold text-purple-300 hover:bg-purple-400/20"
                    >
                      <FileCode size={13} />
                      Extract Payload
                    </button>
                  </div>
                ) : (
                  inspectingAsset.content_type === 'image/png' && !inspectingAsset.source_asset_id && (
                    <button
                      type="button"
                      onClick={() => {
                        const target = inspectingAsset
                        setInspectingAsset(null)
                        openEmbedModal(target)
                      }}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-purple-400/30 bg-purple-400/15 px-3.5 py-1.5 text-xs font-semibold text-purple-300 hover:bg-purple-400/25"
                    >
                      <Sparkles size={13} />
                      Watermark This PNG
                    </button>
                  )
                )}
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setInspectingAsset(null)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Close
                </button>
                <button
                  type="button"
                  onClick={() => {
                    handleDownload(inspectingAsset)
                  }}
                  className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/20 px-5 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/30"
                >
                  <Download size={13} />
                  {inspectingAsset.derivative_type === 'PNG_LSB'
                    ? 'Download Watermarked PNG'
                    : 'Download Decrypted File'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
