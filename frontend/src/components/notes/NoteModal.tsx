import { useEffect, useState } from 'react'
import type { Note, NoteCreateRequest, NoteUpdateRequest } from '../../types/notes'
import { Button } from '../ui/Button'
import { TextareaInput, TextInput } from '../ui/Input'
import { Modal } from '../ui/Modal'

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

  const isEdit = note !== null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Note title cannot be empty.')
      return
    }
    if (!content.trim()) {
      setError('Plaintext content cannot be empty.')
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
    <Modal
      open={isOpen}
      onClose={() => {
        if (!isSubmitting) onClose()
      }}
      title={isEdit ? 'Edit Secure Note' : 'New Secure Note'}
      description="Encrypted with AES-256-GCM + Vigenere using your device-bound HKDF key."
      maxWidthClass="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
            {error}
          </div>
        )}

        <TextInput
          id="note-title"
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Recovery backup codes"
          maxLength={200}
          disabled={isSubmitting}
          required
        />

        <TextareaInput
          id="note-content"
          label="Plaintext Content"
          rows={7}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Write confidential note content..."
          disabled={isSubmitting}
          hint="Only encrypted v1$ ciphertext is persisted in PostgreSQL."
          required
        />

        <div className="flex items-center justify-end gap-2.5 border-t border-ip-border pt-4">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Encrypting...'
              : isEdit
                ? 'Save Changes'
                : 'Encrypt & Save'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
