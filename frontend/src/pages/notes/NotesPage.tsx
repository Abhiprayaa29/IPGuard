import { Edit3, Eye, KeyRound, Lock, LogOut, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { DeleteConfirmModal } from '../../components/notes/DeleteConfirmModal'
import { NoteModal } from '../../components/notes/NoteModal'
import { Button, IconButton } from '../../components/ui/Button'
import { PageHeader, Panel } from '../../components/ui/DataDisplay'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusIndicator,
  useToast,
} from '../../components/ui/Feedback'
import { SearchInput } from '../../components/ui/Input'
import { Modal } from '../../components/ui/Modal'
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
  const { pushToast } = useToast()

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

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<Note | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const [viewingNote, setViewingNote] = useState<Note | null>(null)

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
      void loadNotes(token)
    } else {
      setLoading(false)
    }
  }, [token, loadNotes])

  const handleSaveNote = async (data: NoteCreateRequest | NoteUpdateRequest) => {
    if (!token) return
    setIsSubmitting(true)
    try {
      if (editingNote) {
        const updated = await updateNote(editingNote.id, data, token)
        setNotes((prev) =>
          prev.map((n) => (n.id === updated.id ? updated : n)),
        )
        pushToast('Secure note updated.', 'success')
      } else {
        const created = await createNote(data as NoteCreateRequest, token)
        setNotes((prev) => [created, ...prev])
        pushToast('Secure note encrypted and saved.', 'success')
      }
      setIsModalOpen(false)
      setEditingNote(null)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirmDelete = async () => {
    if (!token || !deleteTarget) return
    setIsDeleting(true)
    try {
      await deleteNote(deleteTarget.id, token)
      setNotes((prev) => prev.filter((n) => n.id !== deleteTarget.id))
      pushToast(`Deleted "${deleteTarget.title}".`, 'info')
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

  const filteredNotes = notes.filter(
    (n) =>
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.content.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Secure Notes"
          description="Encrypted personal notes protected by AES-256-GCM and HKDF key derivation."
          breadcrumbs={[
            { label: 'Overview', to: '/overview' },
            { label: 'Secure Notes' },
          ]}
        />
        <Panel>
          <EmptyState
            icon={<KeyRound size={20} />}
            title="Authentication required"
            description="Sign in with your enrolled Android device using a QR challenge to decrypt and manage notes."
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
        title="Secure Notes"
        description="Device-bound notes encrypted with AES-256-GCM + Vigenere."
        breadcrumbs={[
          { label: 'Overview', to: '/overview' },
          { label: 'Secure Notes' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void loadNotes(token)}
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
                setEditingNote(null)
                setIsModalOpen(true)
              }}
              iconLeft={<Plus size={14} />}
            >
              New Note
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
          onRetry={() => void loadNotes(token)}
          onDismiss={() => setError(null)}
        />
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full sm:max-w-sm">
          <SearchInput
            value={searchQuery}
            onChangeValue={setSearchQuery}
            placeholder="Search decrypted notes..."
          />
        </div>
        <span className="text-xs text-zinc-500 tabular-nums">
          {filteredNotes.length} of {notes.length} notes shown
        </span>
      </div>

      {loading && notes.length === 0 ? (
        <LoadingState message="Decrypting notes workspace..." />
      ) : filteredNotes.length === 0 ? (
        <Panel>
          <EmptyState
            icon={<Lock size={20} />}
            title={searchQuery ? 'No matching notes' : 'No secure notes yet'}
            description={
              searchQuery
                ? 'No decrypted note title or body matches your filter.'
                : 'Create your first note. Plaintext is encrypted before storage.'
            }
            action={
              !searchQuery ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setEditingNote(null)
                    setIsModalOpen(true)
                  }}
                  iconLeft={<Plus size={14} />}
                >
                  Create First Note
                </Button>
              ) : (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setSearchQuery('')}
                >
                  Clear Filter
                </Button>
              )
            }
          />
        </Panel>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredNotes.map((note) => (
            <article
              key={note.id}
              className="flex flex-col justify-between rounded-xl border border-ip-border bg-ip-surface p-5 transition-colors hover:border-zinc-700"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <button
                    type="button"
                    onClick={() => setViewingNote(note)}
                    className="min-w-0 flex-1 text-left"
                  >
                    <h3 className="truncate text-sm font-semibold text-zinc-100 hover:text-ip-accent-300">
                      {note.title}
                    </h3>
                  </button>
                  <StatusIndicator label="AES-GCM" tone="accent" />
                </div>

                <button
                  type="button"
                  onClick={() => setViewingNote(note)}
                  className="mt-2.5 block w-full text-left"
                >
                  <p className="line-clamp-3 font-mono text-xs leading-5 text-zinc-400">
                    {note.content}
                  </p>
                </button>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-ip-border pt-3">
                <span className="font-mono text-[11px] text-zinc-500 tabular-nums">
                  {new Date(note.updated_at).toLocaleDateString()}
                </span>

                <div className="flex items-center gap-1">
                  <IconButton
                    label={`View ${note.title}`}
                    onClick={() => setViewingNote(note)}
                  >
                    <Eye size={14} />
                  </IconButton>
                  <IconButton
                    label={`Edit ${note.title}`}
                    onClick={() => {
                      setEditingNote(note)
                      setIsModalOpen(true)
                    }}
                  >
                    <Edit3 size={14} />
                  </IconButton>
                  <IconButton
                    label={`Delete ${note.title}`}
                    variant="danger"
                    onClick={() => setDeleteTarget(note)}
                  >
                    <Trash2 size={14} />
                  </IconButton>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        open={viewingNote !== null}
        onClose={() => setViewingNote(null)}
        title={viewingNote?.title ?? 'Secure Note'}
        description={
          viewingNote
            ? `Updated ${new Date(viewingNote.updated_at).toLocaleString()}`
            : undefined
        }
        maxWidthClass="max-w-xl"
      >
        {viewingNote && (
          <div className="space-y-4">
            <div className="max-h-96 overflow-y-auto whitespace-pre-wrap rounded-lg border border-ip-border bg-ip-elevated/60 p-4 font-mono text-xs leading-relaxed text-zinc-200">
              {viewingNote.content}
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-ip-border pt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  const toEdit = viewingNote
                  setViewingNote(null)
                  setEditingNote(toEdit)
                  setIsModalOpen(true)
                }}
              >
                Edit Note
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setViewingNote(null)}
              >
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

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
