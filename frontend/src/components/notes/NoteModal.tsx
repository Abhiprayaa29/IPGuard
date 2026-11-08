import { Lock, ShieldCheck, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { Note, NoteCreateRequest, NoteUpdateRequest } from '../../types/notes'

interface NoteModalProps {
  isOpen: boolean
  note: Note | null
  isSubmitting: boolean
  onClose: () => void
  onSubmit: (data: NoteCreateRequest | NoteUpdateRequest) => Promise<void>
}

export function NoteModal({
  isOpen,
  note,
  isSubmitting,
  onClose,
  onSubmit,
}: NoteModalProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (note) {
      setTitle(note.title)
      setContent(note.content)
    } else {
      setTitle('')
      setContent('')
    }
    setError(null)
  }, [note, isOpen])

  if (!isOpen) return null

  const isEdit = note !== null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Title cannot be empty.')
      return
    }
    if (!content.trim()) {
      setError('Content cannot be empty.')
      return
    }

    try {
      setError(null)
      await onSubmit({ title: title.trim(), content: content.trim() })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed.')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-white/10 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-2xl sm:p-8 animate-fade-up">
        {/* Glow decoration */}
        <div
          className="pointer-events-none absolute -top-20 -right-20 size-56 rounded-full bg-ip-teal-500/10 blur-3xl"
          aria-hidden="true"
        />

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-5">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl border border-ip-teal-400/20 bg-ip-teal-400/10 text-ip-teal-300">
              <Lock size={18} />
            </span>
            <div>
              <h3 className="font-display text-lg font-bold text-white">
                {isEdit ? 'Edit Secure Note' : 'Create Super-Encrypted Note'}
              </h3>
              <p className="text-[11px] font-medium text-slate-400">
                AES-256-GCM + Vigenère • Hardware-Bound Key Derivation
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white transition disabled:opacity-50"
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {error && (
            <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="note-title"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5"
            >
              Note Title
            </label>
            <input
              id="note-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Master Secret Plan 2026"
              maxLength={200}
              disabled={isSubmitting}
              className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-ip-teal-400/50 focus:outline-none focus:ring-1 focus:ring-ip-teal-400/50 transition"
              required
            />
          </div>

          <div>
            <label
              htmlFor="note-content"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5"
            >
              Plaintext Content
            </label>
            <textarea
              id="note-content"
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your confidential note content here..."
              disabled={isSubmitting}
              className="w-full rounded-xl border border-white/10 bg-slate-950/60 p-4 text-sm text-white placeholder-slate-500 focus:border-ip-teal-400/50 focus:outline-none focus:ring-1 focus:ring-ip-teal-400/50 transition resize-none font-mono"
              required
            />
          </div>

          {/* Security Guarantee Notice */}
          <div className="flex items-center gap-2 rounded-xl border border-ip-teal-400/20 bg-ip-teal-400/5 px-3 py-2 text-[11px] text-ip-teal-300">
            <ShieldCheck size={14} className="flex-shrink-0" />
            <span>
              Content is super-encrypted on submission. PostgreSQL will store only{' '}
              <code className="text-white font-mono">v1$</code> ciphertext.
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 mt-2 border-t border-white/10 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-ip-teal-400/40 bg-ip-teal-400/20 px-5 py-2 text-xs font-semibold text-ip-teal-200 hover:bg-ip-teal-400/30 hover:border-ip-teal-400/60 transition disabled:opacity-50 shadow-[0_0_20px_-5px_rgba(45,212,191,0.4)]"
            >
              {isSubmitting
                ? 'Encrypting...'
                : isEdit
                  ? 'Update Note'
                  : 'Encrypt & Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
