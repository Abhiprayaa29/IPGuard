import { ConfirmationDialog } from '../ui/Modal'

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
  return (
    <ConfirmationDialog
      open={isOpen}
      onClose={onClose}
      onConfirm={() => {
        void onConfirm()
      }}
      title="Delete Secure Note"
      description={`Permanently delete "${noteTitle}"? The encrypted ciphertext will be purged from PostgreSQL and cannot be recovered.`}
      confirmLabel="Delete Note"
      confirmVariant="danger"
      isProcessing={isDeleting}
    />
  )
}
