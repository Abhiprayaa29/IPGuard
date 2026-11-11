import { X } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'

import { Button } from './Button'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  maxWidthClass?: string
  children: ReactNode
}

export function Modal({
  open,
  onClose,
  title,
  description,
  maxWidthClass = 'max-w-md',
  children,
}: ModalProps) {
  useEffect(() => {
    if (!open) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className={`w-full ${maxWidthClass} max-h-[90vh] overflow-y-auto rounded-xl border border-ip-border bg-ip-surface shadow-2xl`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-ip-border px-5 py-4">
          <div>
            <h2 id="modal-title" className="text-base font-semibold text-zinc-100">
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-[13px] text-zinc-400">{description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-md p-1 text-zinc-400 transition-colors hover:bg-ip-elevated hover:text-zinc-100"
          >
            <X size={16} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

interface ConfirmationDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description: string
  confirmLabel: string
  cancelLabel?: string
  confirmVariant?: 'primary' | 'danger'
  isProcessing?: boolean
  children?: ReactNode
}

export function ConfirmationDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel,
  cancelLabel = 'Cancel',
  confirmVariant = 'danger',
  isProcessing = false,
  children,
}: ConfirmationDialogProps) {
  return (
    <Modal open={open} onClose={onClose} title={title} description={description}>
      <div className="space-y-4">
        {children}
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <Button variant="secondary" onClick={onClose} disabled={isProcessing}>
            {cancelLabel}
          </Button>
          <Button variant={confirmVariant} onClick={onConfirm} loading={isProcessing}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
