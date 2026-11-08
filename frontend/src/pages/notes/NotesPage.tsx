import {
  AlertCircle,
  Clock,
  Edit3,
  Eye,
  KeyRound,
  Lock,
  LogOut,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { DeleteConfirmModal } from '../../components/notes/DeleteConfirmModal'
import { NoteModal } from '../../components/notes/NoteModal'
import {
  createNote,
  deleteNote,
  getNotes,
  updateNote,
} from '../../services/notes'
import type { Note, NoteCreateRequest, NoteUpdateRequest } from '../../types/notes'
import {
  clearStoredSessionToken,
  getStoredSessionToken,
  saveSessionToken,
} from '../../utils/session'

export function NotesPage() {
  const location = useLocation()
  const navigate = useNavigate()

  // 1. Session Token Resolution: state -> sessionStorage
  const [token, setToken] = useState<string | null>(() => {
    const passedToken = (location.state as { token?: string })?.token
    if (passedToken) {
      saveSessionToken(passedToken)
      return passedToken
    }
    return getStoredSessionToken()
  })

  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<Note | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const [viewingNote, setViewingNote] = useState<Note | null>(null)

  // Fetch notes from backend
  const loadNotes = useCallback(async (authToken: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await getNotes(authToken)
      setNotes(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve notes.'
      setError(msg)
      if (msg.includes('401') || msg.includes('expired') || msg.includes('Unauthorized')) {
        clearStoredSessionToken()
        setToken(null)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (token) {
      loadNotes(token)
    } else {
      setLoading(false)
    }
  }, [token, loadNotes])

  // Handle Note Save (Create or Edit)
  const handleSaveNote = async (data: NoteCreateRequest | NoteUpdateRequest) => {
    if (!token) return
    setIsSubmitting(true)
    try {
      if (editingNote) {
        const updated = await updateNote(editingNote.id, data, token)
        setNotes((prev) =>
          prev.map((n) => (n.id === updated.id ? updated : n)),
        )
      } else {
        const created = await createNote(data as NoteCreateRequest, token)
        setNotes((prev) => [created, ...prev])
      }
      setIsModalOpen(false)
      setEditingNote(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle Note Delete
  const handleConfirmDelete = async () => {
    if (!token || !deleteTarget) return
    setIsDeleting(true)
    try {
      await deleteNote(deleteTarget.id, token)
      setNotes((prev) => prev.filter((n) => n.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed.')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleSignOut = () => {
    clearStoredSessionToken()
    setToken(null)
    navigate('/login')
  }

  // Filter notes by search query
  const filteredNotes = notes.filter(
    (n) =>
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.content.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  // State: Unauthorized / No Session
  if (!token) {
    return (
      <div className="mx-auto flex w-full max-w-lg flex-col items-center gap-6 rounded-3xl border border-white/10 bg-slate-900/80 p-8 text-center backdrop-blur-2xl shadow-2xl animate-fade-up">
        <div className="grid size-16 place-items-center rounded-3xl border border-amber-400/30 bg-amber-400/10 text-amber-400">
          <ShieldAlert size={36} />
        </div>
        <div>
          <h2 className="font-display text-2xl font-bold text-white">
            Authentication Required
          </h2>
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">
            Secure Notes are protected by Hardware-Backed Keystore credentials.
            Please authenticate using your enrolled Android device to access the vault.
          </p>
        </div>
        <Link
          to="/login"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-ip-teal-400/40 bg-ip-teal-400/20 px-6 py-2.5 text-xs font-semibold text-ip-teal-300 transition hover:bg-ip-teal-400/30"
        >
          <KeyRound size={14} />
          Sign In with QR Challenge
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8 animate-fade-in">
      {/* Top Banner / Hero */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-ip-teal-400/25 bg-ip-teal-400/10 px-3 py-1 text-xs font-semibold text-ip-teal-300 shadow-sm mb-2">
            <ShieldCheck size={13} />
            Milestone 3 • Super-Encrypted Digital Notes Vault
          </div>
          <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Secure Notes Vault
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Protected by AES-256-GCM + Vigenère. Decrypted in ephemeral browser memory only.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => loadNotes(token)}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-white/10 hover:text-white transition disabled:opacity-50"
            title="Refresh notes from server"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => {
              setEditingNote(null)
              setIsModalOpen(true)
            }}
            className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/40 bg-ip-teal-400/20 px-4 py-2 text-xs font-semibold text-ip-teal-200 hover:bg-ip-teal-400/30 hover:border-ip-teal-400/60 transition shadow-[0_0_20px_-5px_rgba(45,212,191,0.4)]"
          >
            <Plus size={15} />
            New Secure Note
          </button>
          <button
            type="button"
            onClick={handleSignOut}
            className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-slate-400 hover:bg-rose-500/10 hover:text-rose-300 transition"
            title="Sign out and clear session"
          >
            <LogOut size={13} />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center justify-between gap-3 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs text-rose-300 animate-fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => loadNotes(token)}
            className="rounded-lg bg-rose-500/20 px-2.5 py-1 text-[11px] font-semibold text-rose-200 hover:bg-rose-500/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search
          size={15}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500"
        />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search decrypted note titles or content..."
          className="w-full rounded-xl border border-white/10 bg-slate-900/60 pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:border-ip-teal-400/50 focus:outline-none focus:ring-1 focus:ring-ip-teal-400/50 transition"
        />
      </div>

      {/* Main Content Area */}
      {loading && notes.length === 0 ? (
        /* Loading Skeleton */
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-44 rounded-2xl border border-white/5 bg-slate-900/40 p-5 animate-pulse flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="h-4 w-3/4 rounded bg-white/10" />
                <div className="h-3 w-full rounded bg-white/5" />
                <div className="h-3 w-5/6 rounded bg-white/5" />
              </div>
              <div className="h-3 w-1/3 rounded bg-white/5" />
            </div>
          ))}
        </div>
      ) : filteredNotes.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center gap-4 rounded-3xl border border-dashed border-white/10 bg-slate-900/30 py-16 px-6 text-center">
          <div className="grid size-14 place-items-center rounded-2xl border border-ip-teal-400/20 bg-ip-teal-400/10 text-ip-teal-300">
            <Lock size={28} />
          </div>
          <div>
            <h3 className="font-display text-base font-bold text-white">
              {searchQuery ? 'No matching notes found' : 'No Super-Encrypted Notes Yet'}
            </h3>
            <p className="mt-1 text-xs text-slate-400 max-w-sm">
              {searchQuery
                ? 'Try different search keywords.'
                : 'Create your first note. It will be encrypted with AES-256-GCM and stored safely in PostgreSQL.'}
            </p>
          </div>
          {!searchQuery && (
            <button
              type="button"
              onClick={() => {
                setEditingNote(null)
                setIsModalOpen(true)
              }}
              className="inline-flex items-center gap-2 rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 px-4 py-2 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/25 transition"
            >
              <Plus size={14} />
              Create First Note
            </button>
          )}
        </div>
      ) : (
        /* Notes Grid */
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              className="group relative flex flex-col justify-between rounded-2xl border border-white/10 bg-slate-900/60 p-5 shadow-lg backdrop-blur-xl transition hover:border-ip-teal-400/30 hover:bg-slate-900/80 hover:shadow-ip-teal-500/5"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h3
                    className="font-display text-sm font-bold text-white group-hover:text-ip-teal-200 transition line-clamp-1 cursor-pointer"
                    onClick={() => setViewingNote(note)}
                  >
                    {note.title}
                  </h3>
                  <span className="flex-shrink-0 text-[10px] font-mono text-ip-teal-400/80 bg-ip-teal-400/10 px-2 py-0.5 rounded-full border border-ip-teal-400/20">
                    AES-GCM
                  </span>
                </div>
                <p
                  className="text-xs text-slate-400 line-clamp-3 font-mono leading-relaxed cursor-pointer"
                  onClick={() => setViewingNote(note)}
                >
                  {note.content}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
                <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono">
                  <Clock size={11} />
                  <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setViewingNote(note)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition"
                    title="View Full Note"
                    aria-label="View Full Note"
                  >
                    <Eye size={13} />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingNote(note)
                      setIsModalOpen(true)
                    }}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition"
                    title="Edit Note"
                    aria-label="Edit Note"
                  >
                    <Edit3 size={13} />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteTarget(note)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition"
                    title="Delete Note"
                    aria-label="Delete Note"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Note Detail / View Modal */}
      {viewingNote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-white/10 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-2xl sm:p-8 animate-fade-up">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-ip-teal-300">
                  Decrypted In-Memory
                </span>
                <h3 className="font-display text-lg font-bold text-white mt-0.5">
                  {viewingNote.title}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setViewingNote(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white transition"
              >
                ✕
              </button>
            </div>

            <div className="rounded-2xl border border-white/5 bg-slate-950/60 p-4 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
              {viewingNote.content}
            </div>

            <div className="flex items-center justify-between mt-5 border-t border-white/10 pt-4">
              <span className="text-[11px] text-slate-500 font-mono">
                Last updated: {new Date(viewingNote.updated_at).toLocaleString()}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const toEdit = viewingNote
                    setViewingNote(null)
                    setEditingNote(toEdit)
                    setIsModalOpen(true)
                  }}
                  className="rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/10 hover:text-white"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => setViewingNote(null)}
                  className="rounded-xl border border-ip-teal-400/30 bg-ip-teal-400/15 px-4 py-1.5 text-xs font-semibold text-ip-teal-300 hover:bg-ip-teal-400/25"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create / Edit Modal */}
      <NoteModal
        isOpen={isModalOpen}
        note={editingNote}
        isSubmitting={isSubmitting}
        onClose={() => {
          setIsModalOpen(false)
          setEditingNote(null)
        }}
        onSubmit={handleSaveNote}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteTarget !== null}
        noteTitle={deleteTarget?.title ?? ''}
        isDeleting={isDeleting}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </div>
  )
}
