import { AlertTriangle, Trash2, X } from 'lucide-react'

interface DeleteConfirmModalProps {
  isOpen: boolean
  noteTitle: string
  isDeleting: boolean
  onClose: () => void
  onConfirm: () => Promise<void>
}

export function DeleteConfirmModal({
  isOpen,
  noteTitle,
  isDeleting,
  onClose,
  onConfirm,
}: DeleteConfirmModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl border border-rose-500/20 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-2xl sm:p-7 animate-fade-up">
        <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
          <div className="flex items-center gap-2.5 text-rose-400">
            <span className="grid size-9 place-items-center rounded-xl border border-rose-500/20 bg-rose-500/10">
              <AlertTriangle size={18} />
            </span>
            <h3 className="font-display text-base font-bold text-white">
              Permanently Delete Note?
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white transition disabled:opacity-50"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          Are you sure you want to delete{' '}
          <span className="font-semibold text-white">"{noteTitle}"</span>?
          This will permanently purge the ciphertext from the PostgreSQL database using atomic row-level locks.
        </p>

        <div className="flex items-center justify-end gap-3 mt-6 border-t border-white/10 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isDeleting}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-rose-500/30 bg-rose-500/20 px-4 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-500/30 hover:border-rose-500/50 transition disabled:opacity-50"
          >
            <Trash2 size={13} />
            {isDeleting ? 'Deleting...' : 'Delete Note'}
          </button>
        </div>
      </div>
    </div>
  )
}
